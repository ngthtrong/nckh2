import 'dart:async';
import 'dart:convert';

import 'dart:io' if (dart.library.html) 'benchmark_file_stub.dart';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';

import '../../config.dart';
import '../../core/platform/benchmark_environment.dart';
import '../../core/constants/app_colors.dart';
import '../../domain/services/model_benchmark.dart';
import '../controllers/app_controller.dart';
import 'benchmark_report_export_button.dart';

class ModelBenchmarkCard extends StatefulWidget {
  final AppController controller;
  final Dio? dio;

  const ModelBenchmarkCard({super.key, required this.controller, this.dio});

  @override
  State<ModelBenchmarkCard> createState() => _ModelBenchmarkCardState();
}

class _ModelBenchmarkCardState extends State<ModelBenchmarkCard> {
  late final _dio =
      widget.dio ??
      Dio(
        BaseOptions(
          connectTimeout: const Duration(seconds: 8),
          followRedirects: false,
        ),
      );
  bool _running = false;
  bool _downloading = false;
  bool _loadingCachedPackage = false;
  bool _cancelled = false;
  final _downloadCancel = CancelToken();
  int _resourceRevision = 0;
  String? _packagePath;
  String? _message;
  double _downloadProgress = 0;
  int _total = 0;
  int _completed = 0;
  BenchmarkRuntime _runtime = BenchmarkRuntime.pte;
  String _datasetName = '';
  String? _splitCsvSha256;
  List<String> _labels = const [];
  List<BenchmarkSample> _samples = const [];
  List<ModelBenchmarkReport> _reports = const [];

  String get _server => widget.controller.adminServerUrl;

  @override
  void initState() {
    super.initState();
    _resourceRevision = widget.controller.benchmarkResourcesRevision;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted && widget.controller.isAdmin) {
        unawaited(widget.controller.ensureModelLoaded());
        if (!kIsWeb) unawaited(_loadCachedPackage());
      }
    });
  }

  @override
  void didUpdateWidget(covariant ModelBenchmarkCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (_resourceRevision != widget.controller.benchmarkResourcesRevision) {
      _resourceRevision = widget.controller.benchmarkResourcesRevision;
      _packagePath = null;
      _samples = const [];
      _labels = const [];
      _runtime = BenchmarkRuntime.pte;
    }
  }

  Future<void> _loadCachedPackage() async {
    if (widget.controller.isDeletingBenchmarkResources) return;
    widget.controller.setPreparingBenchmark(true);
    _loadingCachedPackage = true;
    try {
      final directory = await getApplicationSupportDirectory();
      final file = File(
        '${directory.path}${Platform.pathSeparator}benchmark.rhb',
      );
      if (!await file.exists()) return;
      await _readPackage(file.path);
      if (mounted) {
        setState(() => _packagePath = file.path);
      }
    } catch (error) {
      if (mounted) {
        setState(
          () => _message = 'Không đọc được gói benchmark đã lưu: $error',
        );
      }
    } finally {
      widget.controller.setPreparingBenchmark(false);
      if (mounted) setState(() => _loadingCachedPackage = false);
    }
  }

  Future<void> _readPackage(String path) async {
    final file = File(path);
    final stream = await file.open();
    try {
      if (await stream.length() < 8) {
        throw const FormatException('Gói quá ngắn.');
      }
      final prefix = await stream.read(8);
      if (ascii.decode(prefix.sublist(0, 4)) != 'RHB1') {
        throw const FormatException('Định dạng gói không hợp lệ.');
      }
      final headerLength = ByteData.sublistView(
        Uint8List.fromList(prefix),
        4,
        8,
      ).getUint32(0, Endian.big);
      if (headerLength == 0 || headerLength > (await stream.length()) - 8) {
        throw const FormatException('Manifest benchmark không hợp lệ.');
      }
      final manifest =
          jsonDecode(utf8.decode(await stream.read(headerLength)))
              as Map<String, dynamic>;
      final labels = (manifest['labels'] as List).cast<String>();
      final samples = (manifest['samples'] as List)
          .map((item) => BenchmarkSample.fromJson(item as Map<String, dynamic>))
          .toList(growable: false);
      final packageLength = await stream.length();
      if (samples.isEmpty ||
          samples.any(
            (sample) =>
                sample.offset < 8 + headerLength ||
                sample.offset + sample.length > packageLength ||
                !labels.contains(sample.label),
          )) {
        throw const FormatException('Ảnh benchmark nằm ngoài phạm vi gói.');
      }
      _datasetName = manifest['datasetName'] as String;
      final splitHash = manifest['splitCsvSha256'];
      if (splitHash is! String ||
          !RegExp(r'^[a-f0-9]{64}$').hasMatch(splitHash)) {
        throw const FormatException(
          'Gói benchmark thiếu SHA-256 CSV chia tập. Xóa và tải lại gói.',
        );
      }
      _splitCsvSha256 = splitHash;
      _labels = labels;
      _samples = samples;
    } finally {
      await stream.close();
    }
  }

  Future<void> _downloadPackage() async {
    if (_downloading ||
        _loadingCachedPackage ||
        widget.controller.isDeletingBenchmarkResources) {
      return;
    }
    final token = widget.controller.adminSession.token;
    if (token == null) return;
    widget.controller.setPreparingBenchmark(true);
    setState(() {
      _downloading = true;
      _downloadProgress = 0;
      _message = null;
    });
    String? partialPath;
    try {
      if (!await widget.controller.validateAdmin() || !mounted) return;
      requireAllowedServerUrl(_server);
      final directory = await getApplicationSupportDirectory();
      final path = '${directory.path}${Platform.pathSeparator}benchmark.rhb';
      partialPath = '$path.part';
      await _deleteIfExists(partialPath);
      await _dio.download(
        '$_server/api/benchmark/package',
        partialPath,
        cancelToken: _downloadCancel,
        options: Options(
          receiveTimeout: const Duration(seconds: 60),
          headers: {'Authorization': 'Bearer $token'},
        ),
        onReceiveProgress: (received, total) {
          if (mounted && total > 0) {
            setState(() => _downloadProgress = received / total);
          }
        },
      );
      await _readPackage(partialPath);
      await File(partialPath).rename(path);
      partialPath = null;
      if (mounted) {
        setState(() => _packagePath = path);
      }
    } on DioException catch (e) {
      if (mounted) {
        setState(
          () => _message = e.response?.statusCode == 403
              ? 'Phiên admin không có quyền tải gói.'
              : 'Không tải được gói benchmark từ server.',
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() => _message = 'Gói benchmark tải về không hợp lệ: $e');
      }
    } finally {
      try {
        if (partialPath != null) {
          await _deleteIfExists(partialPath);
        }
      } finally {
        widget.controller.setPreparingBenchmark(false);
        if (mounted) {
          setState(() => _downloading = false);
        }
      }
    }
  }

  Future<void> _deleteIfExists(String path) async {
    final file = File(path);
    if (await file.exists()) await file.delete();
  }

  Future<void> _deletePackage() async {
    if (_running || _downloading || _loadingCachedPackage) return;
    try {
      final removedBytes = await widget.controller.deleteBenchmarkResources();
      if (mounted) {
        setState(() {
          _packagePath = null;
          _samples = const [];
          _labels = const [];
          _runtime = BenchmarkRuntime.pte;
          _message = null;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Đã giải phóng ${(removedBytes / 1000000).toStringAsFixed(1)} MB. PTE và kết quả JSON vẫn được giữ.',
            ),
          ),
        );
      }
    } catch (error) {
      if (mounted) {
        setState(() => _message = 'Không xóa được tài nguyên: $error');
      }
    }
  }

  Future<void> _run() async {
    if (_running ||
        _loadingCachedPackage ||
        !widget.controller.beginBenchmark()) {
      return;
    }
    setState(() {
      _running = true;
      _cancelled = false;
      _completed = 0;
      _message = null;
      _reports = const [];
    });
    RandomAccessFile? package;
    try {
      if (!await widget.controller.validateAdmin() || !mounted) return;
      await widget.controller.ensureModelLoaded();
      final path = _packagePath;
      if (path == null || _samples.isEmpty) {
        throw StateError('Tải gói benchmark trước khi chạy.');
      }
      final imagePackage = await File(path).open();
      package = imagePackage;
      final samples = _samples;
      setState(
        () => _total =
            samples.length * (_runtime == BenchmarkRuntime.both ? 2 : 1),
      );
      final reports = await const ModelBenchmarkRunner().run(
        provenance: {
          ...await benchmarkEnvironment(),
          'splitCsvSha256': _splitCsvSha256,
        },
        repository: widget.controller.inferenceRepository,
        samples: samples,
        labels: _labels,
        datasetName: _datasetName,
        runtime: _runtime,
        loadImage: (sample) async {
          await imagePackage.setPosition(sample.offset);
          return Uint8List.fromList(await imagePackage.read(sample.length));
        },
        cancelled: () => _cancelled || !mounted || !widget.controller.isAdmin,
        onProgress: (progress) {
          if (!mounted) return;
          setState(
            () => _completed =
                progress.completed +
                (progress.runtime == BenchmarkRuntime.pte &&
                        _runtime == BenchmarkRuntime.both
                    ? samples.length
                    : 0),
          );
        },
      );
      if (mounted) setState(() => _reports = reports);
    } catch (e) {
      if (mounted) setState(() => _message = 'Không chạy được benchmark: $e');
    } finally {
      await package?.close();
      if (mounted) setState(() => _running = false);
      widget.controller.endBenchmark();
    }
  }

  @override
  void dispose() {
    _cancelled = true;
    _downloadCancel.cancel();
    _dio.close(force: true);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.controller.isAdmin) return const SizedBox.shrink();
    final canRunPte = widget.controller.isPteReady;
    final canRunOnnx = widget.controller.isOnnxReady;
    final deleting = widget.controller.isDeletingBenchmarkResources;
    final runtimeReady = switch (_runtime) {
      BenchmarkRuntime.pte => canRunPte,
      BenchmarkRuntime.onnx => canRunOnnx,
      BenchmarkRuntime.both => canRunPte && canRunOnnx,
    };
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFF9FAFB),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFE5E7EB)),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Tập test gồm 256 ảnh, 4 lớp. Chỉ admin được tải và chạy benchmark.',
            style: TextStyle(color: Colors.grey.shade700, height: 1.4),
          ),
          const SizedBox(height: 12),
          if (kIsWeb)
            const Text('Benchmark ảnh chỉ hỗ trợ ứng dụng cài trên điện thoại.')
          else if (_samples.isEmpty) ...[
            FilledButton.icon(
              onPressed: _downloading || _loadingCachedPackage || deleting
                  ? null
                  : _downloadPackage,
              icon: const Icon(Icons.download_rounded),
              label: Text(
                _downloading ? 'Đang tải gói…' : 'Tải gói benchmark (~40 MB)',
              ),
              style: FilledButton.styleFrom(
                backgroundColor: AppColors.primaryRed,
              ),
            ),
            if (_downloading) ...[
              const SizedBox(height: 8),
              LinearProgressIndicator(
                value: _downloadProgress == 0 ? null : _downloadProgress,
              ),
              Text('${(_downloadProgress * 100).toStringAsFixed(0)}%'),
            ],
            if (_message != null)
              Text(_message!, style: const TextStyle(color: Colors.red)),
          ] else ...[
            Row(
              children: [
                Expanded(
                  child: _runtimeChoice(
                    'ONNX',
                    BenchmarkRuntime.onnx,
                    enabled: canRunOnnx,
                  ),
                ),
                Expanded(
                  child: _runtimeChoice(
                    'PTE',
                    BenchmarkRuntime.pte,
                    enabled: canRunPte,
                  ),
                ),
                Expanded(
                  child: _runtimeChoice(
                    'Cả hai',
                    BenchmarkRuntime.both,
                    enabled: canRunPte && canRunOnnx,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            FilledButton.icon(
              onPressed:
                  _running ||
                      _loadingCachedPackage ||
                      deleting ||
                      !runtimeReady ||
                      widget.controller.isBenchmarking
                  ? null
                  : _run,
              icon: const Icon(Icons.speed_rounded),
              label: Text(_running ? 'Đang đo…' : 'Chạy benchmark thật'),
              style: FilledButton.styleFrom(
                backgroundColor: AppColors.primaryRed,
              ),
            ),
            if (_running) ...[
              const SizedBox(height: 8),
              LinearProgressIndicator(
                value: _total == 0 ? null : _completed / _total,
              ),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('$_completed / $_total ảnh'),
                  TextButton(
                    onPressed: () => setState(() => _cancelled = true),
                    child: const Text('Dừng'),
                  ),
                ],
              ),
            ],
            if (_message != null)
              Text(_message!, style: const TextStyle(color: Colors.red)),
          ],
          for (final report in _reports) _reportView(report),
          if (!kIsWeb)
            TextButton.icon(
              onPressed:
                  _running ||
                      _loadingCachedPackage ||
                      _downloading ||
                      deleting ||
                      widget.controller.isDownloadingOnnx ||
                      widget.controller.isBenchmarking ||
                      widget.controller.isModelLoading
                  ? null
                  : _deletePackage,
              icon: const Icon(Icons.delete_outline, size: 16),
              label: Text(
                deleting
                    ? 'Đang xóa tài nguyên…'
                    : 'Xóa ONNX và tập benchmark đã tải',
              ),
            ),
        ],
      ),
    );
  }

  Widget _runtimeChoice(
    String title,
    BenchmarkRuntime value, {
    bool enabled = true,
  }) => ChoiceChip(
    label: Text(title, style: const TextStyle(fontSize: 12)),
    selected: _runtime == value,
    onSelected: enabled && !_running
        ? (selected) {
            if (selected) setState(() => _runtime = value);
          }
        : null,
  );

  Widget _reportView(ModelBenchmarkReport report) {
    String percent(double? value) =>
        value == null ? '—' : '${(value * 100).toStringAsFixed(1)}%';
    String ms(double? value) =>
        value == null ? '—' : '${value.toStringAsFixed(1)} ms';
    return Padding(
      padding: const EdgeInsets.only(top: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  '${report.runtime.name.toUpperCase()} · ${report.complete ? 'ĐỦ DỮ LIỆU' : 'CHƯA HOÀN TẤT'}',
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
              ),
              if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android)
                BenchmarkReportExportButton(report: report),
              IconButton(
                tooltip: 'Sao chép kết quả JSON',
                onPressed: () => Clipboard.setData(
                  ClipboardData(
                    text: const JsonEncoder.withIndent(
                      '  ',
                    ).convert(report.toJson()),
                  ),
                ),
                icon: const Icon(Icons.copy, size: 18),
              ),
            ],
          ),
          Wrap(
            spacing: 14,
            runSpacing: 8,
            children: [
              Text('Accuracy ${percent(report.accuracy)}'),
              Text('Macro F1 ${percent(report.macroF1)}'),
              Text('Median ${ms(report.medianLatencyMs)}'),
              Text('P95 ${ms(report.p95LatencyMs)}'),
              Text('Lỗi ${report.failedSamples}'),
            ],
          ),
          const SizedBox(height: 6),
          for (final entry in report.classMetrics.entries)
            Text(
              '${entry.key}: F1 ${percent(entry.value['f1'])} · P ${percent(entry.value['precision'])} · R ${percent(entry.value['recall'])}',
              style: TextStyle(fontSize: 12, color: Colors.grey.shade700),
            ),
        ],
      ),
    );
  }
}
