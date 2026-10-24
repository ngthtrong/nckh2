// Đọc gói E2E, lưu tiến độ và chạy luồng AI/gửi/outbox thật qua AppController; không giả lập kết quả Android.
import 'dart:convert';
import 'dart:typed_data';
import 'dart:ui' as ui;
import 'package:crypto/crypto.dart';
import 'package:dio/dio.dart';
import 'package:geolocator/geolocator.dart';
import '../../config.dart';
import '../../presentation/controllers/app_controller.dart';
import '../entities/ai_model_type.dart';
import '../entities/ai_tag.dart';
import '../entities/rescue_record.dart';
import '../entities/send_mode.dart';

const mobileE2eStages = [
  'online',
  'offline_recovery',
  'adaptive_300',
  'adaptive_20',
  'no_gps',
  'feedback',
];
const mobileE2eEnabled = bool.fromEnvironment(
  'ENABLE_MOBILE_E2E',
  defaultValue: kAdminModelTools,
);
const _prefix = '/api/experiments/e2e';

class MobileE2eInterrupted implements Exception {
  final String detail;
  MobileE2eInterrupted(this.detail);
  @override
  String toString() => detail;
}

void validateMobileE2eMetadata(
  RescueRecord local,
  Map<String, dynamic> remote,
) {
  bool equal(dynamic a, dynamic b) {
    if (a is num && b is num) return (a - b).abs() < 0.000001;
    if (a is List && b is List) {
      return a.length == b.length &&
          List.generate(a.length, (i) => equal(a[i], b[i])).every((v) => v);
    }
    if (a is Map && b is Map) {
      return a.length == b.length &&
          a.keys.every((k) => b.containsKey(k) && equal(a[k], b[k]));
    }
    return a == b;
  }

  final expected = <String, dynamic>{
    'id': local.id,
    'description': local.description,
    'sendMode': local.sendMode,
    'lat': local.lat,
    'lng': local.lng,
    'trappedCount': local.trappedCount,
    'injuredCount': local.injuredCount,
    'vulnerableGroups': local.vulnerableGroups,
    'aiTags': local.aiTags.map((tag) => tag.toJson()).toList(),
  };
  for (final entry in expected.entries) {
    if (!equal(entry.value, remote[entry.key])) {
      throw StateError('Server nhận sai trường ${entry.key} của ${local.id}.');
    }
  }
  final time = DateTime.tryParse('${remote['createdAt']}');
  if (time == null ||
      time.difference(local.createdAt).inMilliseconds.abs() > 1) {
    throw StateError('Server nhận sai createdAt của ${local.id}.');
  }
}

Future<Map<String, dynamic>> verifyMobileE2eImage(
  Uint8List source,
  Uint8List received, {
  required bool fullImage,
}) async {
  final hash = sha256.convert(received).toString();
  if (fullImage) {
    if (hash != sha256.convert(source).toString()) {
      throw StateError('Ảnh gốc trên server sai SHA-256.');
    }
    return {'method': 'sha256', 'sha256': hash, 'bytes': received.length};
  }
  Future<({Uint8List pixels, int width, int height})> sample(
    Uint8List bytes,
  ) async {
    final codec = await ui.instantiateImageCodec(bytes, targetWidth: 64);
    try {
      final frame = await codec.getNextFrame();
      try {
        final pixels = await frame.image.toByteData(
          format: ui.ImageByteFormat.rawRgba,
        );
        if (pixels == null) {
          throw StateError('Không đọc được ảnh nhận từ server.');
        }
        return (
          pixels: pixels.buffer.asUint8List(),
          width: frame.image.width,
          height: frame.image.height,
        );
      } finally {
        frame.image.dispose();
      }
    } finally {
      codec.dispose();
    }
  }

  final original = await sample(source);
  final uploaded = await sample(received);
  if (original.width != uploaded.width ||
      (original.height - uploaded.height).abs() > 1 ||
      original.pixels.length != uploaded.pixels.length) {
    throw StateError(
      'Ảnh nén nhận từ server sai tỷ lệ/kích thước mẫu đối chiếu.',
    );
  }
  var error = 0;
  var count = 0;
  for (var i = 0; i < original.pixels.length; i++) {
    if (i % 4 == 3) continue;
    error += (original.pixels[i] - uploaded.pixels[i]).abs();
    count++;
  }
  final mae = error / count;
  if (mae > 20) {
    throw StateError(
      'Nội dung ảnh nén không khớp fixture (MAE pixel=$mae > 20/255).',
    );
  }
  return {
    'method': 'decoded_rgb_sample_width64_mae_le20',
    'pixelMae': mae,
    'sha256': hash,
    'bytes': received.length,
  };
}

class MobileE2ePackage {
  final Map<String, dynamic> manifest;
  final Uint8List image;
  final String hash;
  MobileE2ePackage._(this.manifest, this.image, this.hash);
  factory MobileE2ePackage.decode(Uint8List data, String expectedHash) {
    if (data.length < 8 ||
        data.length > 20 * 1024 * 1024 ||
        ascii.decode(data.sublist(0, 4), allowInvalid: true) != 'RHE1' ||
        sha256.convert(data).toString() != expectedHash) {
      throw const FormatException(
        'Gói E2E sai định dạng/hash. Tải lại từ coordinator.',
      );
    }
    final size = ByteData.sublistView(data).getUint32(4, Endian.big);
    if (size == 0 || size > 1024 * 1024 || size > data.length - 8) {
      throw const FormatException('Manifest E2E không hợp lệ.');
    }
    final m = Map<String, dynamic>.from(
      jsonDecode(utf8.decode(data.sublist(8, 8 + size))) as Map,
    );
    final image = Uint8List.sublistView(data, 8 + size);
    final info = m['image'] as Map;
    final model = m['model'] as Map;
    final path = '${info['relativePath']}';
    final version = m['schemaVersion'];
    if (![1, 2].contains(version) ||
        !RegExp(r'^run_\d{3}$').hasMatch('${m['goldRun']}') ||
        (version == 1 &&
            !RegExp(r'^[A-Za-z0-9_-]{1,80}$').hasMatch('${m['sessionId']}')) ||
        (version == 2 && m.containsKey('sessionId')) ||
        jsonEncode(m['stages']) != jsonEncode(mobileE2eStages) ||
        path.startsWith('/') ||
        path.contains('\\') ||
        path.split('/').contains('..') ||
        !['high', 'medium'].contains(info['label']) ||
        !path.startsWith('${info['label']}/') ||
        image.length != info['length'] ||
        sha256.convert(image).toString() != info['sha256'] ||
        model['runtime'] != 'pte' ||
        model['seed'] != 1024 ||
        model['variant'] != 'pruning' ||
        !RegExp(r'^[a-f0-9]{64}$').hasMatch('${model['sha256']}')) {
      throw const FormatException('Gói không đúng run/ảnh/model E2E đã khóa.');
    }
    return MobileE2ePackage._(m, image, expectedHash);
  }

  MobileE2ePackage forBenchmark(String name) {
    if (!RegExp(r'^[A-Za-z0-9_-]{1,80}$').hasMatch(name)) {
      throw const FormatException('Tên benchmark không hợp lệ.');
    }
    if (manifest['schemaVersion'] != 2) {
      throw StateError('Cần gói assets phiên bản 2 để mở lượt mới.');
    }
    return MobileE2ePackage._({...manifest, 'sessionId': name}, image, hash);
  }
}

RescueRecord? findMobileE2eRecord(
  Iterable<RescueRecord> records,
  String marker,
) {
  final matches = records.where((r) => r.description == marker).toList();
  if (matches.length > 1) {
    throw StateError('Có nhiều báo cáo cùng stage; dừng để kiểm tra trùng.');
  }
  return matches.isEmpty ? null : matches.single;
}

class MobileE2eCheckpoint {
  final String sessionId;
  final String installationId;
  final String packageSha256;
  Map<String, dynamic> environment = {};
  Map<String, dynamic> inference = {};
  Map<String, dynamic> evidence = {};
  final Map<String, String> reports = {};
  final Map<String, String> intents = {};
  final Map<String, Map<String, dynamic>> checks = {};
  final List<String> skipped = [];
  MobileE2eCheckpoint(MobileE2ePackage package, this.installationId)
    : sessionId = package.manifest['sessionId'] as String,
      packageSha256 = package.hash {
    for (final stage in [
      ...mobileE2eStages,
      'manual_android_ui',
      'manual_physical_network',
      'dashboard',
    ]) {
      checks[stage] = {
        'stage': stage,
        'status': 'NOT_RUN',
        'detail': 'Chưa thực hiện',
        'method': stage.startsWith('manual_')
            ? 'manual'
            : stage == 'dashboard'
            ? 'coordinator'
            : 'app',
      };
    }
  }
  factory MobileE2eCheckpoint.restore(
    MobileE2ePackage package,
    String installation,
    Map<String, dynamic> json,
  ) {
    final state = MobileE2eCheckpoint(package, installation);
    if (json['sessionId'] != state.sessionId ||
        json['packageSha256'] != state.packageSha256 ||
        json['installationId'] != installation) {
      throw StateError('Checkpoint không cùng benchmark/gói/lần cài app.');
    }
    state.environment = Map<String, dynamic>.from(json['environment'] as Map);
    state.inference = Map<String, dynamic>.from(json['inference'] as Map);
    state.evidence = Map<String, dynamic>.from(json['evidence'] as Map);
    state.reports.addAll(Map<String, String>.from(json['reports'] as Map));
    state.intents.addAll(Map<String, String>.from(json['intents'] as Map));
    state.skipped.addAll((json['skipped'] as List).cast<String>());
    for (final c in json['checks'] as List) {
      final check = Map<String, dynamic>.from(c as Map);
      if (!state.checks.containsKey(check['stage'])) {
        throw StateError('Checkpoint chứa stage không hợp lệ.');
      }
      state.checks[check['stage'] as String] = check;
    }
    return state;
  }
  String? get nextStage => mobileE2eStages
      .where((s) => checks[s]!['status'] != 'PASS' && !skipped.contains(s))
      .firstOrNull;
  void _archive() {
    final history = (evidence['attemptHistory'] as List?) ?? [];
    final snapshot = jsonDecode(jsonEncode(toJson())) as Map<String, dynamic>;
    (snapshot['evidence'] as Map).remove('attemptHistory');
    evidence['attemptHistory'] = [...history, snapshot];
  }

  void _resetStage(String stage) {
    checks[stage] = {
      ...checks[stage]!,
      'status': 'NOT_RUN',
      'detail': 'Chưa thực hiện lần thử mới',
    };
    skipped.remove(stage);
    reports.remove(stage);
    inference.remove(stage);
    evidence.remove(stage);
    evidence.remove('${stage}_policy');
    evidence.remove('${stage}_timing');
    if (stage == 'offline_recovery') evidence.remove('offlineObserved');
    if (stage == 'no_gps') evidence.remove('gpsPermission');
    intents[stage] =
        'Benchmark $sessionId $stage attempt ${DateTime.now().microsecondsSinceEpoch}';
  }

  void resetStage(String stage) {
    if (!mobileE2eStages.contains(stage)) throw ArgumentError(stage);
    _archive();
    evidence['attemptStartedAtUtc'] = DateTime.now().toUtc().toIso8601String();
    _resetStage(stage);
    if (stage == 'online') _resetStage('feedback');
    checks['dashboard']!['status'] = 'NOT_RUN';
    checks['dashboard']!['detail'] = 'Cần kiểm tra lại sau lần thử mới';
  }

  void restart() {
    _archive();
    final history = evidence['attemptHistory'];
    evidence = {
      'attemptHistory': history,
      'attemptStartedAtUtc': DateTime.now().toUtc().toIso8601String(),
    };
    inference.clear();
    reports.clear();
    intents.clear();
    skipped.clear();
    for (final stage in checks.keys) {
      _resetStage(stage);
    }
    intents.removeWhere((key, _) => !mobileE2eStages.contains(key));
  }

  Map<String, dynamic> toJson() => {
    'sessionId': sessionId,
    'installationId': installationId,
    'packageSha256': packageSha256,
    'environment': environment,
    'inference': inference,
    'evidence': evidence,
    'reports': reports,
    'intents': intents,
    'skipped': skipped,
    'checks': checks.values.toList(),
  };
  Map<String, dynamic> resultsJson() => Map<String, dynamic>.from(toJson())
    ..remove('intents')
    ..remove('skipped');
}

class MobileE2eRunner {
  final AppController controller;
  final MobileE2ePackage package;
  final MobileE2eCheckpoint state;
  final Dio dio;
  final String server;
  final String controlPath;
  final String imagePath;
  final Future<void> Function(Map<String, dynamic>) save;
  final bool Function() cancelled;
  MobileE2eRunner({
    required this.controller,
    required this.package,
    required this.state,
    required this.dio,
    required this.server,
    this.controlPath = '',
    required this.imagePath,
    required this.save,
    required this.cancelled,
  });

  Options get auth {
    final token = controller.adminSession.token;
    if (cancelled() || !controller.isAdmin || token == null) {
      throw StateError('Đăng nhập lại admin trước khi tiếp tục.');
    }
    return Options(headers: {'Authorization': 'Bearer $token'});
  }

  Future<Map<String, dynamic>> get(String path) async =>
      Map<String, dynamic>.from(
        (await dio.get<dynamic>(
              '$server$controlPath$_prefix$path',
              options: auth,
            )).data
            as Map,
      );
  Future<Map<String, dynamic>> post(
    String path,
    Map<String, dynamic> data,
  ) async => Map<String, dynamic>.from(
    (await dio.post<dynamic>(
          '$server$controlPath$_prefix$path',
          options: auth,
          data: data,
        )).data
        as Map,
  );
  Future<void> persist() => save(state.toJson());
  Future<void> profile(String name) async {
    await post('/profile', {
      'profile': name,
      'installationId': state.installationId,
    });
  }

  void check(bool condition, String detail) {
    if (!condition) throw StateError(detail);
  }

  void _runtime() {
    check(
      controller.currentModel == AiModelType.pte &&
          controller.isPteReady &&
          !controller.isDualComparison,
      'Phải dùng PTE thật, tắt so sánh hai runtime.',
    );
    check(
      controller.adminServerUrl == server,
      'App đã đổi server; không gửi dữ liệu sang DB ngoài benchmark.',
    );
  }

  Future<void> preflight() async {
    _runtime();
    check(
      kEmergencyPhone == kPlaceholderEmergencyPhone,
      'Bản thử nghiệm không được cấu hình số SMS thật.',
    );
    final session = await get('/session');
    check(
      session['sessionId'] == state.sessionId &&
          session['packageSha256'] == package.hash,
      'Coordinator đã đổi benchmark/gói.',
    );
    await post('/claim', {
      'installationId': state.installationId,
      'packageSha256': package.hash,
    });
    final foreign = controller.records.where(
      (r) =>
          r.awaitingSync &&
          !r.description.startsWith('Benchmark ${state.sessionId} '),
    );
    check(
      foreign.isEmpty,
      'Có báo cáo pending ngoài benchmark. Không tự xóa dữ liệu; xử lý chúng trước.',
    );
  }

  Future<Map<String, dynamic>> observations() => get('/observations');
  Future<Map<String, dynamic>> waitReport(
    String id, {
    bool image = false,
  }) async {
    final deadline = DateTime.now().add(const Duration(seconds: 90));
    while (DateTime.now().isBefore(deadline)) {
      auth;
      final data = await observations();
      final matches = (data['reports'] as List)
          .where((r) => r['id'] == id)
          .toList();
      if (matches.length == 1 &&
          (!image || matches.single['imageUrl'] != null)) {
        return Map<String, dynamic>.from(matches.single as Map);
      }
      await controller.syncPending();
      await Future<void>.delayed(const Duration(seconds: 2));
    }
    throw StateError('Server chưa nhận đúng báo cáo/ảnh sau 90 giây.');
  }

  Future<RescueRecord> report(String stage, {required bool image}) async {
    final marker = state.intents.putIfAbsent(
      stage,
      () => 'Benchmark ${state.sessionId} $stage',
    );
    await persist(); // Journal before creation: recover by marker if the process stops before saving the new ID.
    final existing = findMobileE2eRecord(controller.records, marker);
    if (existing != null) {
      state.reports[stage] = existing.id;
      await persist();
      return existing;
    }
    final remote = (await observations())['reports'] as List;
    check(
      !remote.any((r) => r['description'] == marker),
      'Báo cáo đã có trên server nhưng mất bản local; không tạo lại.',
    );
    var tags = <AiTag>[];
    if (image) {
      _runtime();
      final result = await controller.inferenceRepository.classifyImage(
        package.image,
      );
      _runtime();
      check(
        result != null &&
            result.modelType == AiModelType.pte &&
            ['low', 'medium', 'high', 'non_flood'].contains(result.label) &&
            result.confidence.isFinite &&
            result.confidence >= 0 &&
            result.confidence <= 1,
        'AI native không trả kết quả hợp lệ.',
      );
      final output = result!;
      tags = controller.inferenceRepository.generateAiTags(
        output.label,
        output.confidence,
      );
      check(tags.isNotEmpty, 'AI không tạo được tag gửi báo cáo.');
      state.inference[stage] = {
        'truth': (package.manifest['image'] as Map)['label'],
        'prediction': output.label,
        'confidence': output.confidence,
        'durationMs': output.durationMs,
        'runtime': 'pte',
      };
      await persist();
    }
    final record = await controller.submitPost(
      trappedCount: 1,
      injuredCount: 0,
      vulnerableGroups: [],
      cannotMove: false,
      severeSigns: [],
      description: marker,
      imagePath: image ? imagePath : null,
      aiTags: tags,
    );
    _runtime();
    check(
      record != null,
      controller.submissionError ?? 'App không tạo được báo cáo.',
    );
    state.reports[stage] = record!.id;
    state.evidence['${stage}_policy'] = {
      'throughputKbps': controller.lastThroughputKbps,
      'sendMode': record.sendMode,
    };
    await persist();
    return record;
  }

  Future<String> onlineStage(String stage, String network) async {
    await profile(network);
    final record = await report(stage, image: true);
    final policy = state.evidence['${stage}_policy'] as Map?;
    final kbps = (policy?['throughputKbps'] as num?)?.toInt();
    // For resumed records, the send mode saved by the actual policy is authoritative.
    final actualMode = sendModeFromName(record.sendMode);
    check(actualMode != null, 'App lưu sendMode không hợp lệ.');
    if (actualMode == SendMode.queuedOffline ||
        actualMode == SendMode.smsFallback ||
        policy == null) {
      await controller.syncPending();
      await waitReport(record.id);
      throw MobileE2eInterrupted(
        'Đã phục hồi cùng ID ${record.id}; thiếu bằng chứng policy của lần gửi ban đầu. Giữ NOT_RUN; dùng benchmark mới nếu cần đo lại.',
      );
    }
    if (kbps != null) {
      final expected = chooseMode(
        hasData: true,
        confidence: record.maxAiConfidence,
        throughputKbps: kbps,
        strongKbps: kStrongKbps,
        minUsefulKbps: kMinUsefulKbps,
        highConfidence: kHighConfidence,
        preferTextWhenConfident: kPreferTextWhenConfident,
      );
      check(
        actualMode == expected,
        'sendMode không khớp policy/confidence/throughput.',
      );
    }
    check(
      actualMode != SendMode.queuedOffline &&
          actualMode != SendMode.smsFallback,
      'Bước online chưa gửi bằng dữ liệu; kiểm tra mạng rồi tiếp tục.',
    );
    final wantsImage =
        actualMode == SendMode.fullImage ||
        actualMode == SendMode.compressedImage;
    final remote = await waitReport(record.id, image: wantsImage);
    validateMobileE2eMetadata(record, remote);
    Map<String, dynamic>? attachment;
    if (wantsImage) {
      final path = '${remote['imageUrl']}';
      check(
        path.startsWith('/uploads/') && !path.contains('..'),
        'Đường ảnh server không hợp lệ.',
      );
      final downloaded = await dio.get<List<int>>(
        '$server$path',
        options: Options(
          responseType: ResponseType.bytes,
          headers: auth.headers,
        ),
      );
      attachment = await verifyMobileE2eImage(
        package.image,
        Uint8List.fromList(downloaded.data!),
        fullImage: actualMode == SendMode.fullImage,
      );
    }
    if (actualMode == SendMode.textOnly) {
      check(remote['imageUrl'] == null, 'Metadata-only vẫn có ảnh upload.');
    }
    state.evidence[stage] = {
      'profile': network,
      'throughputKbps': kbps,
      'sendMode': remote['sendMode'],
      'imageUrlPresent': remote['imageUrl'] != null,
      'reportId': record.id,
      'attachmentVerification': attachment,
    };
    return 'PTE thật; báo cáo ${record.id}; profile=$network, probe=$kbps kbit/s, mode=${remote['sendMode']}.';
  }

  Future<String> offlineStage() async {
    RescueRecord record;
    try {
      if (state.evidence['offlineObserved'] == null) {
        final oldId = state.reports['offline_recovery'];
        final received = (await observations())['reports'] as List;
        final marker = state.intents['offline_recovery'];
        final oldRemote = received
            .where(
              (r) =>
                  r['id'] == oldId ||
                  (marker != null && r['description'] == marker),
            )
            .firstOrNull;
        if (oldRemote != null) {
          state.reports['offline_recovery'] = oldRemote['id'] as String;
          await controller.syncPending();
          await waitReport(oldRemote['id'] as String);
          throw MobileE2eInterrupted(
            'Báo cáo đã đến server sau gián đoạn nhưng chưa lưu bằng chứng offline; phục hồi đúng ID và giữ NOT_RUN.',
          );
        }
        await profile('offline');
        record = await report('offline_recovery', image: false);
        final data = await observations();
        check(
          !(data['reports'] as List).any((r) => r['id'] == record.id),
          'Server đã nhận khi đường dữ liệu đang bị chặn.',
        );
        final local = controller.rescueRepository.getRecord(record.id);
        check(
          local != null && local.awaitingSync && controller.pendingCount > 0,
          'App không giữ báo cáo trong outbox.',
        );
        state.evidence['offlineObserved'] = {
          'reportId': record.id,
          'observedAtUtc': DateTime.now().toUtc().toIso8601String(),
          'method': 'proxy HTTP 503 on data endpoints; control remains online',
        };
        await persist();
      }
    } finally {
      await profile('online');
    }
    final id = state.reports['offline_recovery'];
    check(id != null, 'Checkpoint thiếu ID báo cáo offline.');
    await controller.syncPending();
    await waitReport(id!);
    final data = await observations();
    final marker = state.intents['offline_recovery'];
    check(
      (data['reports'] as List)
              .where((r) => r['description'] == marker)
              .length ==
          1,
      'Khôi phục tạo báo cáo trùng.',
    );
    check(controller.pendingCount == 0, 'Outbox chưa về 0 sau khôi phục.');
    return 'Chặn đường dữ liệu HTTP → giữ outbox → mở lại → server nhận đúng một báo cáo, outbox=0. Không phải tắt Wi-Fi/4G vật lý.';
  }

  Future<String> noGpsStage() async {
    final permission = await Geolocator.checkPermission();
    check(
      permission == LocationPermission.denied ||
          permission == LocationPermission.deniedForever,
      'Vào Cài đặt Android → quyền của Cứu hộ Admin → từ chối Vị trí rồi quay lại chạy bước này.',
    );
    await profile('online');
    final record = await report('no_gps', image: false);
    final remote = await waitReport(record.id);
    check(
      record.lat == null &&
          record.lng == null &&
          remote['lat'] == null &&
          remote['lng'] == null,
      'App/server có tọa độ dù bị từ chối quyền.',
    );
    check(
      ((await observations())['review'] as List).contains(record.id),
      'Báo cáo thiếu GPS không vào hàng xem xét.',
    );
    state.evidence['gpsPermission'] = permission.name;
    return 'Quyền Android bị từ chối; app gửi không có tọa độ; server đưa vào hàng xem xét.';
  }

  Future<String> feedbackStage() async {
    final id = state.reports['online'];
    check(id != null, 'Cần chạy online trước khi thử phản hồi.');
    await post('/feedback/$id', {'installationId': state.installationId});
    await controller.refreshStatuses();
    final local = controller.rescueRepository.getRecord(id!);
    check(
      local?.status == 'dispatched',
      'App chưa nhận trạng thái điều phối từ server.',
    );
    return 'Backend điều phối $id; refreshStatuses của app nhận dispatched. Giao diện Lịch sử cần xác nhận thủ công riêng.';
  }

  Future<void> runNext() => runStage(state.nextStage);

  Future<void> retryStage(String stage) async {
    await preflight();
    check(!controller.isBusy, 'App đang có tác vụ khác.');
    check(
      controller.pendingCount == 0,
      'Đồng bộ hết hàng đợi trước khi chạy lại.',
    );
    state.resetStage(stage);
    await persist();
    await runStage(stage);
  }

  Future<void> restart() async {
    await preflight();
    check(!controller.isBusy, 'App đang có tác vụ khác.');
    check(
      controller.pendingCount == 0,
      'Đồng bộ hết hàng đợi trước khi chạy lại.',
    );
    state.restart();
    await persist();
  }

  Future<void> runStage(String? stage) async {
    if (stage == null) return;
    check(mobileE2eStages.contains(stage), 'Stage không hợp lệ');
    await preflight();
    check(
      !controller.isBusy && controller.beginBenchmark(),
      'App đang có tác vụ khác.',
    );
    final started = DateTime.now().toUtc();
    try {
      final detail = switch (stage) {
        'online' => await onlineStage(stage, 'online'),
        'offline_recovery' => await offlineStage(),
        'adaptive_300' => await onlineStage(stage, '300'),
        'adaptive_20' => await onlineStage(stage, '20'),
        'no_gps' => await noGpsStage(),
        'feedback' => await feedbackStage(),
        _ => throw StateError('Stage không hợp lệ'),
      };
      state.checks[stage] = {
        'stage': stage,
        'status': 'PASS',
        'detail': detail,
        'method': 'app',
      };
    } on MobileE2eInterrupted catch (error) {
      state.skipped.add(stage);
      state.checks[stage] = {
        'stage': stage,
        'status': 'NOT_RUN',
        'detail': error.detail,
        'method': 'app',
      };
    } catch (error) {
      state.checks[stage] = {
        'stage': stage,
        'status': 'FAIL',
        'detail': error.toString(),
        'method': 'app',
      };
      rethrow;
    } finally {
      state.evidence['${stage}_timing'] = {
        'startedAtUtc': started.toIso8601String(),
        'finishedAtUtc': DateTime.now().toUtc().toIso8601String(),
      };
      try {
        await persist();
      } finally {
        try {
          await profile('online');
        } finally {
          controller.endBenchmark();
        }
      }
    }
  }

  Future<void> skipNext() async {
    final stage = state.nextStage;
    if (stage == null) return;
    state.skipped.add(stage);
    state.checks[stage] = {
      'stage': stage,
      'status': 'NOT_RUN',
      'detail': 'Người chạy bỏ qua; không tính PASS.',
      'method': 'manual',
    };
    await persist();
  }

  Future<void> confirmManual(String stage) => recordManual(stage, passed: true);

  Future<void> recordManual(
    String stage, {
    required bool passed,
    String detail = '',
    String reportId = '',
    String evidenceFile = '',
  }) async {
    if (!['manual_android_ui', 'manual_physical_network'].contains(stage)) {
      throw ArgumentError(stage);
    }
    final note = detail.trim();
    if ((!passed && note.isEmpty) ||
        note.length > 1200 ||
        reportId.length > 200 ||
        evidenceFile.length > 400) {
      throw ArgumentError('Có lỗi cần mô tả; ghi chú tối đa 1200 ký tự.');
    }
    final now = DateTime.now().toUtc();
    final event = {
      'id': '$stage-${now.microsecondsSinceEpoch}',
      'atUtc': now.toIso8601String(),
      'stage': stage,
      'status': passed ? 'PASS' : 'FAIL',
      'detail': note.isEmpty ? 'Đã kiểm tra và lưu bằng chứng' : note,
      'reportId': reportId.trim(),
      'evidenceFile': evidenceFile.trim(),
    };
    state.evidence['manualChecks'] = [
      ...(state.evidence['manualChecks'] as List? ?? []),
      event,
    ];
    state.checks[stage] = {
      'stage': stage,
      'status': event['status'],
      'method': 'manual',
      'detail':
          '${event['detail']} (người chạy ghi nhận lúc ${event['atUtc']}).',
    };
    await persist();
  }

  Future<Map<String, dynamic>> uploadResults() =>
      post('/results', state.resultsJson());
}
