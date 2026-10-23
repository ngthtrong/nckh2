import 'package:flutter/material.dart';

const mobileManualGuides = {
  'manual_android_ui':
      'Trang chủ → Gửi bài cứu hộ → chọn ảnh, nhập mô tả → Gửi → Lịch sử → mở bài → đối chiếu dashboard → lưu ảnh bằng chứng.',
  'manual_physical_network':
      'Tắt Wi-Fi và dữ liệu di động → Gửi bài → chụp hàng đợi → bật lại Wi-Fi → kiểm tra hết chờ gửi và dashboard có đúng 1 bài → lưu ảnh.',
};

class ManualCheckResult {
  final bool passed;
  final String detail;
  final String reportId;
  final String evidenceFile;
  const ManualCheckResult(
    this.passed,
    this.detail,
    this.reportId,
    this.evidenceFile,
  );
}

class MobileE2eManualDialog extends StatefulWidget {
  final String stage;
  const MobileE2eManualDialog({super.key, required this.stage});
  @override
  State<MobileE2eManualDialog> createState() => _MobileE2eManualDialogState();
}

class _MobileE2eManualDialogState extends State<MobileE2eManualDialog> {
  final _detail = TextEditingController();
  final _report = TextEditingController();
  final _evidence = TextEditingController();
  String? _error;
  void _finish(bool passed) {
    if (!passed && _detail.text.trim().isEmpty) {
      setState(() => _error = 'Nhập mô tả lỗi trước khi ghi FAIL.');
      return;
    }
    Navigator.pop(
      context,
      ManualCheckResult(
        passed,
        _detail.text.trim(),
        _report.text.trim(),
        _evidence.text.trim(),
      ),
    );
  }

  @override
  void dispose() {
    _detail.dispose();
    _report.dispose();
    _evidence.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Ghi kết quả kiểm tra thủ công'),
    content: SingleChildScrollView(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(mobileManualGuides[widget.stage]!),
          const SizedBox(height: 12),
          const Text(
            'Chỉ chọn Đạt sau khi đã kiểm tra và lưu bằng chứng. Tên file bên dưới là ghi chú, không tự đính kèm ảnh.',
          ),
          TextField(
            controller: _detail,
            key: const Key('manual-note'),
            maxLength: 1200,
            minLines: 2,
            maxLines: 4,
            decoration: InputDecoration(
              labelText: 'Mô tả lỗi / ghi chú',
              errorText: _error,
            ),
          ),
          TextField(
            controller: _report,
            maxLength: 200,
            decoration: const InputDecoration(labelText: 'ID bài gửi (nếu có)'),
          ),
          TextField(
            controller: _evidence,
            maxLength: 400,
            decoration: const InputDecoration(
              labelText: 'Tên ảnh/video bằng chứng (nếu có)',
            ),
          ),
        ],
      ),
    ),
    actions: [
      TextButton(
        onPressed: () => Navigator.pop(context),
        child: const Text('Chưa kiểm tra'),
      ),
      OutlinedButton(
        key: const Key('manual-fail'),
        onPressed: () => _finish(false),
        child: const Text('Có lỗi (FAIL)'),
      ),
      FilledButton(
        key: const Key('manual-pass'),
        onPressed: () => _finish(true),
        child: const Text('Đạt (PASS)'),
      ),
    ],
  );
}

class MobileE2eManualSection extends StatelessWidget {
  final Map<String, Map<String, dynamic>> checks;
  final String goldRun;
  final bool busy;
  final void Function(String stage) onManual;
  final VoidCallback onDashboard;
  const MobileE2eManualSection({
    super.key,
    required this.checks,
    required this.goldRun,
    required this.busy,
    required this.onManual,
    required this.onDashboard,
  });

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      const Text(
        '2. Kiểm tra thủ công',
        style: TextStyle(fontWeight: FontWeight.bold),
      ),
      for (final stage in mobileManualGuides.keys) ...[
        const SizedBox(height: 12),
        Text(
          stage == 'manual_android_ui'
              ? 'Case 7. Giao diện Android: ${checks[stage]!['status']}'
              : 'Case 8. Tắt/bật mạng vật lý: ${checks[stage]!['status']}',
        ),
        Text(mobileManualGuides[stage]!),
        if (stage == 'manual_android_ui')
          const Text(
            'Cấp lại quyền Vị trí nếu đã tắt. Màn SOS chỉ kiểm tra giao diện; không gọi/SMS thật.',
          ),
        TextButton(
          key: Key('manual-result-$stage'),
          onPressed: busy ? null : () => onManual(stage),
          child: Text(
            stage == 'manual_android_ui'
                ? 'Ghi kết quả Case 7'
                : 'Ghi kết quả Case 8',
          ),
        ),
      ],
      const SizedBox(height: 12),
      Text('Case 9. Dashboard: ${checks['dashboard']!['status']}'),
      const Text(
        'Máy tính: chạy lệnh bên dưới → quay lại app → bấm Xác nhận đã chạy dashboard. Kết quả lấy từ máy tính.',
      ),
      SelectableText(
        'python products/fe/experiment_mobile/coordinator.py dashboard --run ${int.parse(goldRun.substring(4))} --headed',
      ),
      TextButton(
        key: const Key('manual-dashboard-confirm'),
        onPressed: busy ? null : onDashboard,
        child: const Text('Xác nhận đã chạy dashboard'),
      ),
    ],
  );
}
