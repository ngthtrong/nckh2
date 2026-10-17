import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../domain/services/model_benchmark.dart';

class BenchmarkReportExportButton extends StatefulWidget {
  final ModelBenchmarkReport report;

  const BenchmarkReportExportButton({super.key, required this.report});

  @override
  State<BenchmarkReportExportButton> createState() =>
      _BenchmarkReportExportButtonState();
}

class _BenchmarkReportExportButtonState
    extends State<BenchmarkReportExportButton> {
  static const _channel = MethodChannel('rescue/benchmark_export');
  bool _saving = false;

  Future<void> _save() async {
    if (_saving) return;
    setState(() => _saving = true);
    final timestamp = DateTime.now().toUtc().toIso8601String().replaceAll(
      RegExp(r'[:.]'),
      '-',
    );
    final fileName = 'benchmark_${widget.report.runtime.name}_$timestamp.json';
    try {
      final saved = await _channel.invokeMethod<bool>('saveJson', {
        'fileName': fileName,
        'json': const JsonEncoder.withIndent(
          '  ',
        ).convert(widget.report.toJson()),
      });
      if (saved == true && mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('Đã lưu file JSON.')));
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Không lưu được file JSON. Vui lòng thử lại.'),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) => TextButton.icon(
    onPressed: _saving ? null : _save,
    icon: const Icon(Icons.download_rounded, size: 18),
    label: Text(_saving ? 'Đang lưu…' : 'Tải JSON'),
  );
}
