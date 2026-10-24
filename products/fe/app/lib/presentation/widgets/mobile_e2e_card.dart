// Công cụ admin tải run, chạy từng stage E2E thật, tiếp tục checkpoint và xuất kết quả; chỉ bật ở APK thử nghiệm.
import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../core/platform/benchmark_environment.dart';
import '../../core/platform/mobile_e2e_storage.dart';
import '../../core/platform/mobile_e2e_bundle.dart';
import '../../domain/entities/ai_model_type.dart';
import '../../domain/services/mobile_e2e_runner.dart';
import '../controllers/app_controller.dart';
import 'mobile_e2e_manual_section.dart';

class MobileE2eCard extends StatefulWidget {
  final AppController controller;
  const MobileE2eCard({super.key, required this.controller});
  @override
  State<MobileE2eCard> createState() => _MobileE2eCardState();
}

class _MobileE2eCardState extends State<MobileE2eCard> {
  final _dio = Dio(
    BaseOptions(
      connectTimeout: const Duration(seconds: 8),
      receiveTimeout: const Duration(seconds: 90),
    ),
  );
  bool _busy = false;
  String? _message;
  MobileE2eRunner? _runner;
  MobileE2eBundle? _bundle;
  Map<String, dynamic>? _selectedRun;
  String? _selectedServer;
  AppController get c => widget.controller;
  Future<void> _action(Future<void> Function() work) async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _message = null;
    });
    try {
      await work();
    } catch (e) {
      if (mounted) setState(() => _message = e.toString());
    } finally {
      if (mounted) {
        setState(() {
          _busy = false;
        });
      }
    }
  }

  Future<void> _chooseRun() async {
    if (!await c.validateAdmin()) throw StateError('Đăng nhập admin trước.');
    final base = c.adminServerUrl;
    final bundle = await MobileE2eBundle.load();
    final runs = bundle.runs;
    if (!mounted) return;
    final run = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (context) => SimpleDialog(
        title: const Text('Chọn run'),
        children: [
          for (final value in runs)
            SimpleDialogOption(
              key: Key('mobile-e2e-run-${value['goldRun']}'),
              onPressed: () => Navigator.pop(
                context,
                Map<String, dynamic>.from(value as Map),
              ),
              child: ListTile(
                title: Text('${value['goldRun']}'),
                subtitle: Text(
                  'Ảnh: ${(value['image'] as Map)['relativePath']}',
                ),
                trailing: const Icon(Icons.chevron_right),
              ),
            ),
        ],
      ),
    );
    if (run == null || !mounted) return;
    setState(() {
      if (_selectedRun?['goldRun'] != run['goldRun'] ||
          _selectedServer != base) {
        _runner = null;
      }
      _bundle = bundle;
      _selectedRun = run;
      _selectedServer = base;
      _message =
          'Đã chọn ${run['goldRun']}. Bấm Tải gói benchmark để tiếp tục.';
    });
  }

  Future<void> _download() async {
    final run = _selectedRun;
    if (run == null) throw StateError('Chọn run trước khi tải gói.');
    if (!await c.validateAdmin()) throw StateError('Đăng nhập admin trước.');
    final base = c.adminServerUrl;
    if (base != _selectedServer) {
      throw StateError('Địa chỉ server đã đổi. Bấm Chọn run để chọn lại.');
    }
    final auth = Options(
      headers: {'Authorization': 'Bearer ${c.adminSession.token}'},
    );
    c.setPreparingBenchmark(true);
    try {
      final storage = await MobileE2eStorage.open();
      final local = _bundle!.packages[run['goldRun']]!;
      final response = await _dio.get<dynamic>(
        '$base/api/experiments/e2e/runs',
        options: auth,
      );
      final available = ((response.data as Map)['runs'] as List)
          .where((item) => item['goldRun'] == run['goldRun'])
          .toList();
      if (available.length != 1 ||
          available.single['packageSha256'] != local.hash) {
        throw StateError(
          'Gói hai run trên máy tính khác APK. Chuẩn bị assets và build lại cùng dữ liệu.',
        );
      }
      final live = Map<String, dynamic>.from(available.single as Map);
      final sessionId = live['sessionId'] as String;
      final controlPath = live['controlPath'] as String? ?? '';
      if (controlPath.isNotEmpty &&
          !RegExp(r'^/mobile-e2e/run_00[12]$').hasMatch(controlPath)) {
        throw StateError('Đường dẫn điều phối không hợp lệ.');
      }
      final fixture = local.forBenchmark(sessionId);
      final imageName = '$sessionId.jpg';
      await storage.writeBytes(imageName, fixture.image);
      final checkpointName = '$sessionId.json';
      final checkpoint = await storage.readJson(checkpointName);
      final state = checkpoint == null
          ? MobileE2eCheckpoint(fixture, storage.installationId)
          : MobileE2eCheckpoint.restore(
              fixture,
              storage.installationId,
              checkpoint,
            );
      final environment = await benchmarkEnvironment();
      final asset = await rootBundle.load('assets/models/model.pte');
      final actualHash = sha256
          .convert(
            asset.buffer.asUint8List(asset.offsetInBytes, asset.lengthInBytes),
          )
          .toString();
      final expected = (fixture.manifest['model'] as Map)['sha256'];
      if (actualHash != expected ||
          (environment['model'] as Map)['pte_sha256'] != expected) {
        throw StateError(
          'APK chưa đóng đúng seed 1024 pruning/PTE. Chạy prepare_assets.py rồi build APK tại fe/app.',
        );
      }
      if (environment['device'] is! Map ||
          (environment['device'] as Map)['model'] == null) {
        throw StateError(
          'Không lấy được metadata Android thật; không giả kết quả thiết bị.',
        );
      }
      state.environment = {
        'device': environment['device'],
        'app': environment['app'],
        'model': fixture.manifest['model'],
        'actualPteSha256': actualHash,
        'platform': 'android',
      };
      await c.ensureModelLoaded();
      c.toggleDualComparison(false);
      c.switchAiModel(AiModelType.pte);
      final runner = MobileE2eRunner(
        controller: c,
        package: fixture,
        state: state,
        dio: _dio,
        server: base,
        controlPath: controlPath,
        imagePath: storage.path(imageName),
        save: (json) => storage.writeJson(checkpointName, json),
        cancelled: () => !mounted || !c.isAdmin,
      );
      await runner.preflight();
      await runner.persist();
      if (mounted) {
        setState(() {
          _runner = runner;
          _message =
              'Đã tải ${run['goldRun']}. Tiến độ được lưu theo tên benchmark.';
        });
      }
    } finally {
      c.setPreparingBenchmark(false);
    }
  }

  Future<void> _next({String? retry}) async {
    final runner = _runner!;
    try {
      if (retry == null) {
        await runner.runNext();
      } else {
        await runner.retryStage(retry);
      }
    } finally {
      try {
        await _upload();
      } catch (_) {
        /* Checkpoint local is preserved if the coordinator cannot be reached. */
      }
    }
  }

  Future<void> _restart() async {
    final accepted = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Chạy lại toàn bộ run?'),
        content: const Text(
          'Lưu lần thử hiện tại vào lịch sử và đặt lại tất cả case. Bạn sẽ chạy từng case từ đầu. Trước case online, hãy cấp lại quyền Vị trí nếu đã tắt.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Chạy lại'),
          ),
        ],
      ),
    );
    if (accepted != true || !mounted) return;
    await _runner!.restart();
    if (mounted) {
      setState(() => _message = 'Đã tạo lần thử mới. Bắt đầu từ case 1.');
    }
  }

  Future<void> _upload() async {
    final runner = _runner!;
    final result = await runner.uploadResults();
    final checks = result['checks'];
    if (checks is List) {
      for (final check in checks) {
        final item = Map<String, dynamic>.from(check as Map);
        if (runner.state.checks.containsKey(item['stage'])) {
          runner.state.checks[item['stage'] as String] = item;
        }
      }
      await runner.persist();
    }
    if (mounted) {
      setState(
        () => _message =
            'Máy tính đã lưu: ${result['status']} — ${result['counts']}',
      );
    }
  }

  Future<void> _exportJson() async {
    await const MethodChannel(
      'rescue/benchmark_export',
    ).invokeMethod<bool>('saveJson', {
      'fileName': '${_runner!.state.sessionId}.json',
      'json': const JsonEncoder.withIndent(
        '  ',
      ).convert(_runner!.state.toJson()),
    });
  }

  Future<void> _manual(String stage) async {
    final result = await showDialog<ManualCheckResult>(
      context: context,
      builder: (_) => MobileE2eManualDialog(stage: stage),
    );
    if (result == null) return;
    await _runner!.recordManual(
      stage,
      passed: result.passed,
      detail: result.detail,
      reportId: result.reportId,
      evidenceFile: result.evidenceFile,
    );
    await _upload();
  }

  Future<void> _confirmDashboard() async {
    await _upload();
    final status = _runner!.state.checks['dashboard']!['status'];
    if (!mounted) return;
    setState(
      () => _message = status == 'NOT_RUN'
          ? 'Case 9: chưa có kết quả dashboard hợp lệ cho lượt này. Chạy lệnh trên máy tính rồi bấm xác nhận lại.'
          : 'Case 9: $status — đã lấy kết quả từ máy tính.',
    );
  }

  String _stageTitle(String stage) => switch (stage) {
    'online' => 'Gửi bài khi có mạng',
    'offline_recovery' => 'Mất mạng và khôi phục hàng đợi',
    'adaptive_300' => 'Mạng giới hạn 300 kbit/s',
    'adaptive_20' => 'Mạng giới hạn 20 kbit/s',
    'no_gps' => 'Gửi bài khi từ chối vị trí',
    'feedback' => 'Nhận phản hồi điều phối',
    _ => stage,
  };

  @override
  void dispose() {
    _dio.close(force: true);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!mobileE2eEnabled ||
        !c.isAdmin ||
        kIsWeb ||
        defaultTargetPlatform != TargetPlatform.android) {
      return const SizedBox.shrink();
    }
    final runner = _runner;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'E2E DI ĐỘNG — MÔI TRƯỜNG THỬ NGHIỆM',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            const Text(
              'Dùng backend flood-rescue. APK chứa sẵn dữ liệu cả run_001 và run_002. Mỗi run lưu tiến độ riêng; tên lượt theo ngày giờ. Không đánh giá Accuracy từ ảnh E2E.',
            ),
            if (_busy) const LinearProgressIndicator(),
            OutlinedButton.icon(
              key: const Key('mobile-e2e-select-run'),
              onPressed: _busy || c.isBenchmarking
                  ? null
                  : () => _action(_chooseRun),
              icon: const Icon(Icons.list_alt),
              label: const Text('Chọn run'),
            ),
            Text(
              _selectedRun == null
                  ? 'Chọn run trước khi tải gói.'
                  : 'Đã chọn: ${_selectedRun!['goldRun']}',
            ),
            FilledButton.icon(
              key: const Key('mobile-e2e-download'),
              onPressed: _busy || c.isBenchmarking || _selectedRun == null
                  ? null
                  : () => _action(_download),
              icon: const Icon(Icons.download),
              label: const Text('Tải gói benchmark'),
            ),
            if (runner != null) ...[
              Text(
                '${runner.package.manifest['goldRun']} — ${(runner.package.manifest['image'] as Map)['label']}\n${runner.state.sessionId}',
              ),
              const SizedBox(height: 16),
              const Text(
                '1. Kiểm thử luồng xử lý',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const Text(
                'App gọi trực tiếp hàm nhận diện, gửi bài và đồng bộ; không tự thao tác các màn hình. PASS xác nhận các điều kiện của luồng xử lý, không xác nhận nhãn nhận diện đúng hay giao diện hoạt động đúng.',
              ),
              Text(
                'Đã xử lý ${mobileE2eStages.where((s) => runner.state.checks[s]!['status'] == 'PASS' || runner.state.skipped.contains(s)).length}/${mobileE2eStages.length} case luồng xử lý',
              ),
              for (final (index, stage) in mobileE2eStages.indexed)
                Container(
                  key: Key('mobile-e2e-case-$stage'),
                  margin: const EdgeInsets.only(top: 8),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    border: Border.all(
                      color: Theme.of(context).colorScheme.outlineVariant,
                    ),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Case ${index + 1}. ${_stageTitle(stage)}',
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                      Text('$stage: ${runner.state.checks[stage]!['status']}'),
                      Text('${runner.state.checks[stage]!['detail']}'),
                      if (stage == 'no_gps')
                        const Text(
                          'Trước khi chạy: từ chối quyền Vị trí trong Cài đặt Android.',
                        ),
                      if (stage == runner.state.nextStage &&
                          runner.state.checks[stage]!['status'] == 'NOT_RUN')
                        FilledButton.icon(
                          key: const Key('mobile-e2e-next'),
                          onPressed: _busy || c.isBenchmarking
                              ? null
                              : () => _action(_next),
                          icon: const Icon(Icons.play_arrow),
                          label: Text(
                            _busy ? 'Đang kiểm tra…' : 'Chạy case ${index + 1}',
                          ),
                        ),
                      if (runner.state.checks[stage]!['status'] != 'NOT_RUN' ||
                          runner.state.skipped.contains(stage))
                        OutlinedButton.icon(
                          key: Key('mobile-e2e-retry-$stage'),
                          onPressed: _busy || c.isBenchmarking
                              ? null
                              : () => _action(() => _next(retry: stage)),
                          icon: const Icon(Icons.replay),
                          label: Text('Chạy lại case ${index + 1}'),
                        ),
                      if (stage == runner.state.nextStage)
                        TextButton(
                          onPressed: _busy || c.isBenchmarking
                              ? null
                              : () => _action(runner.skipNext),
                          child: Text('Bỏ qua case ${index + 1} (NOT_RUN)'),
                        ),
                    ],
                  ),
                ),
              if (runner.state.nextStage == null)
                const Text(
                  'Đã hết case luồng xử lý. Có thể chạy lại từng case hoặc toàn bộ run.',
                ),
              OutlinedButton.icon(
                key: const Key('mobile-e2e-restart'),
                onPressed: _busy || c.isBenchmarking
                    ? null
                    : () => _action(_restart),
                icon: const Icon(Icons.restart_alt),
                label: const Text('Chạy lại toàn bộ run'),
              ),
              const Divider(height: 32),
              MobileE2eManualSection(
                checks: runner.state.checks,
                goldRun: runner.package.manifest['goldRun'] as String,
                busy: _busy || c.isBenchmarking,
                onManual: (stage) => _action(() => _manual(stage)),
                onDashboard: () => _action(_confirmDashboard),
              ),
              const Divider(height: 32),
              const Text(
                '3. Lưu và xuất kết quả',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              Text(
                'Lịch sử: ${(runner.state.evidence['attemptHistory'] as List?)?.length ?? 0} lần thử đã lưu',
              ),
              OutlinedButton.icon(
                onPressed: _busy || c.isBenchmarking
                    ? null
                    : () => _action(_upload),
                icon: const Icon(Icons.cloud_upload_outlined),
                label: const Text('Lưu JSON/CSV lên máy tính'),
              ),
              OutlinedButton.icon(
                onPressed: _busy || c.isBenchmarking
                    ? null
                    : () => _action(_exportJson),
                icon: const Icon(Icons.save_alt),
                label: const Text('Xuất JSON trên điện thoại'),
              ),
            ],
            if (_message != null) SelectableText(_message!),
          ],
        ),
      ),
    );
  }
}
