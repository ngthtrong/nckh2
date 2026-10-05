import 'dart:async';
import 'dart:convert';

import 'dart:io' if (dart.library.html) 'benchmark_file_stub.dart';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';

import '../../../config.dart';
import '../../../core/constants/app_colors.dart';
import '../../../domain/services/model_benchmark.dart';
import '../controllers/app_controller.dart';

class ModelBenchmarkCard extends StatefulWidget {
  final AppController controller;

  const ModelBenchmarkCard({super.key, required this.controller});

  @override
  State<ModelBenchmarkCard> createState() => _ModelBenchmarkCardState();
}

class _ModelBenchmarkCardState extends State<ModelBenchmarkCard> {
  final _dio = Dio(BaseOptions(connectTimeout: const Duration(seconds: 8)));
  bool _unlocked = false;
  bool _running = false;
  bool _downloading = false;
  bool _cancelled = false;
  String? _sessionToken;
  String? _packagePath;
  String? _message;
  double _downloadProgress = 0;
  int _total = 0;
  int _completed = 0;
  BenchmarkRuntime _runtime = BenchmarkRuntime.onnx;
  String _datasetName = '';
  List<String> _labels = const [];
  List<BenchmarkSample> _samples = const [];
  List<ModelBenchmarkReport> _reports = const [];

  String get _server => (widget.controller.connectedServerUrl ?? kServerBaseUrl)
      .replaceAll(RegExp(r'/$'), '');

  Future<void> _unlock() async {
    final password = TextEditingController();
    String? error;
    String? loginToken;
    var busy = false;
    final accepted = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Xác thực quyền benchmark'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Đăng nhập tài khoản điều phối viên rhna trên server.',
              ),
              const SizedBox(height: 16),
              TextField(
                controller: password,
                autofocus: true,
                obscureText: true,
                decoration: const InputDecoration(
                  labelText: 'Mật khẩu server',
                  border: OutlineInputBorder(),
                ),
                onSubmitted: (_) async {
                  if (busy) return;
                  setDialogState(() => busy = true);
                  loginToken = await _verify(password.text, (value) {
                    setDialogState(() => error = value);
                  });
                  if (dialogContext.mounted) {
                    if (loginToken != null) {
                      Navigator.pop(dialogContext, true);
                    } else {
                      setDialogState(() => busy = false);
                    }
                  }
                },
              ),
              if (error != null) ...[
                const SizedBox(height: 8),
                Text(error!, style: const TextStyle(color: Colors.red)),
              ],
              if (busy) ...[
                const SizedBox(height: 12),
                const LinearProgressIndicator(),
              ],
            ],
          ),
          actions: [
            TextButton(
              onPressed: busy
                  ? null
                  : () => Navigator.pop(dialogContext, false),
              child: const Text('Hủy'),
            ),
            FilledButton(
              onPressed: busy
                  ? null
                  : () async {
                      setDialogState(() => busy = true);
                      loginToken = await _verify(password.text, (value) {
                        setDialogState(() => error = value);
                      });
                      if (dialogContext.mounted) {
                        if (loginToken != null) {
                          Navigator.pop(dialogContext, true);
                        } else {
                          setDialogState(() => busy = false);
                        }
                      }
                    },
              child: const Text('Xác thực'),
            ),
          ],
        ),
      ),
    );
    password.dispose();
    if (accepted == true && loginToken != null && mounted) {
      setState(() {
        _sessionToken = loginToken;
        _unlocked = true;
        _message = null;
      });
      await _loadCachedPackage();
    }
  }

  Future<String?> _verify(
    String password,
    void Function(String) setError,
  ) async {
    if (password.isEmpty) {
      setError('Nhập mật khẩu server.');
      return null;
    }
    try {
      final response = await _dio.post<dynamic>(
        '$_server/api/auth/login',
        data: {'username': 'rhna', 'password': password},
        options: Options(contentType: Headers.jsonContentType),
      );
      final data = response.data;
      if (data is! Map ||
          data['username'] != 'rhna' ||
          !const {'admin', 'operator'}.contains(data['role']) ||
          data['token'] is! String) {
        setError('Tài khoản không có quyền điều phối viên hợp lệ.');
        return null;
      }
      return data['token'] as String;
    } on DioException catch (e) {
      setError(
        e.response?.statusCode == 429
            ? 'Server tạm khóa đăng nhập do thử sai nhiều lần.'
            : e.response?.statusCode == 401
            ? 'Sai mật khẩu hoặc server không nhận tài khoản rhna.'
            : 'Không kết nối được server tại $_server.',
      );
      return null;
    } catch (_) {
      setError('Không thể xác thực với server.');
      return null;
    }
  }

  Future<void> _logoutSession() async {
    final token = _sessionToken;
    _sessionToken = null;
    if (token == null) return;
    try {
      await _dio.post<void>(
        '$_server/api/auth/logout',
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );
    } catch (_) {
      // Server-side session expiry remains the fallback if offline.
    }
  }

  Future<void> _loadCachedPackage() async {
    final directory = await getApplicationSupportDirectory();
    final file = File(
      '${directory.path}${Platform.pathSeparator}benchmark.rhb',
    );
    if (!await file.exists()) {
      return;
    }
    try {
      await _readPackage(file.path);
      if (mounted) {
        setState(() => _packagePath = file.path);
      }
    } catch (_) {
      await file.delete();
      if (mounted) {
        setState(() => _message = 'Gói benchmark lưu trên máy bị lỗi.');
      }
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
      _labels = labels;
      _samples = samples;
    } finally {
      await stream.close();
    }
  }

  Future<void> _downloadPackage() async {
    final token = _sessionToken;
    if (token == null) return;
    setState(() {
      _downloading = true;
      _downloadProgress = 0;
      _message = null;
    });
    String? partialPath;
    try {
      final directory = await getApplicationSupportDirectory();
      final path = '${directory.path}${Platform.pathSeparator}benchmark.rhb';
      partialPath = '$path.part';
      await _deleteIfExists(partialPath);
      await _dio.download(
        '$_server/api/benchmark/package',
        partialPath,
        options: Options(headers: {'Authorization': 'Bearer $token'}),
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
      await _logoutSession();
    } on DioException catch (e) {
      if (mounted) {
        setState(
          () => _message = e.response?.statusCode == 403
              ? 'Server chỉ cho tài khoản rhna tải gói.'
              : 'Không tải được gói benchmark từ server.',
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() => _message = 'Gói benchmark tải về không hợp lệ: $e');
      }
    } finally {
      if (partialPath != null) {
        await _deleteIfExists(partialPath);
      }
      if (mounted) {
        setState(() => _downloading = false);
      }
    }
  }

  Future<void> _deleteIfExists(String path) async {
    final file = File(path);
    if (await file.exists()) await file.delete();
  }

  Future<void> _lock() async {
    await _logoutSession();
    if (mounted) {
      setState(() {
        _unlocked = false;
        _samples = const [];
        _labels = const [];
        _reports = const [];
        _message = null;
      });
    }
  }

  Future<void> _deletePackage() async {
    final path = _packagePath;
    if (path != null) await _deleteIfExists(path);
    if (mounted) {
      setState(() {
        _packagePath = null;
        _samples = const [];
        _labels = const [];
        _reports = const [];
      });
    }
  }

  Future<void> _run() async {
    setState(() {
      _running = true;
      _cancelled = false;
      _completed = 0;
      _message = null;
      _reports = const [];
    });
    RandomAccessFile? package;
    try {
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
        repository: widget.controller.inferenceRepository,
        samples: samples,
        labels: _labels,
        datasetName: _datasetName,
        runtime: _runtime,
        loadImage: (sample) async {
          await imagePackage.setPosition(sample.offset);
          return Uint8List.fromList(await imagePackage.read(sample.length));
        },
        cancelled: () => _cancelled,
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
    }
  }

  @override
  void dispose() {
    if (_sessionToken == null) {
      _dio.close();
    } else {
      unawaited(_logoutSession().whenComplete(() => _dio.close()));
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final canRunPte = widget.controller.isPteReady;
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
            'Tập test gồm 256 ảnh, 4 lớp. Gói chỉ tải từ server sau khi tài khoản rhna xác thực.',
            style: TextStyle(color: Colors.grey.shade700, height: 1.4),
          ),
          const SizedBox(height: 12),
          if (kIsWeb)
            const Text('Benchmark ảnh chỉ hỗ trợ ứng dụng cài trên điện thoại.')
          else if (!_unlocked)
            OutlinedButton.icon(
              onPressed: _unlock,
              icon: const Icon(Icons.lock_outline),
              label: const Text('Xác thực rhna để mở benchmark'),
              style: OutlinedButton.styleFrom(
                foregroundColor: AppColors.primaryRed,
              ),
            )
          else if (_samples.isEmpty) ...[
            FilledButton.icon(
              onPressed: _downloading ? null : _downloadPackage,
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
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                onPressed: _downloading ? null : _lock,
                child: const Text('Đăng xuất'),
              ),
            ),
          ] else ...[
            Row(
              children: [
                Expanded(child: _runtimeChoice('ONNX', BenchmarkRuntime.onnx)),
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
                    enabled: canRunPte,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            FilledButton.icon(
              onPressed: _running ? null : _run,
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
            for (final report in _reports) _reportView(report),
            Wrap(
              alignment: WrapAlignment.end,
              children: [
                TextButton.icon(
                  onPressed: _running ? null : _deletePackage,
                  icon: const Icon(Icons.delete_outline, size: 16),
                  label: const Text('Xóa gói đã tải'),
                ),
                TextButton.icon(
                  onPressed: _running ? null : _lock,
                  icon: const Icon(Icons.lock, size: 16),
                  label: const Text('Khóa lại'),
                ),
              ],
            ),
          ],
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
