import 'dart:async';

import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../controllers/app_controller.dart';
import '../../widgets/app_header.dart';
import '../../widgets/compose_cta_card.dart';
import '../../widgets/sos_button.dart';
import '../../widgets/emergency_call.dart';
import '../../../domain/entities/sms_delivery.dart';

class HomeScreen extends StatefulWidget {
  final AppController controller;
  final VoidCallback onComposePressed;

  const HomeScreen({
    super.key,
    required this.controller,
    required this.onComposePressed,
  });

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  SosState _sosState = SosState.idle;
  Timer? _sosResetTimer;

  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_onControllerChange);
  }

  void _onControllerChange() {
    if (mounted) setState(() {});
  }

  @override
  void didUpdateWidget(covariant HomeScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.controller != widget.controller) {
      oldWidget.controller.removeListener(_onControllerChange);
      widget.controller.addListener(_onControllerChange);
    }
  }

  @override
  void dispose() {
    _sosResetTimer?.cancel();
    widget.controller.removeListener(_onControllerChange);
    super.dispose();
  }

  Future<void> _handleSos({bool retrySms = false}) async {
    if (_sosState == SosState.pressed || widget.controller.isBusy) return;
    _sosResetTimer?.cancel();
    setState(() => _sosState = SosState.pressed);

    final record =
        await (retrySms
                ? widget.controller.retrySosSms()
                : widget.controller.sendSos())
            .catchError((_) => null);

    if (mounted) {
      final syncError = record?.syncError;
      final state = record == null || syncError != null
          ? SosState.failed
          : record.synced
          ? SosState.accepted
          : record.smsStatus == SmsStatus.sent
          ? SosState.sms
          : record.smsStatus == SmsStatus.unknown ||
                record.smsStatus == SmsStatus.sending
          ? SosState.smsUnknown
          : record.smsStatus == SmsStatus.failed
          ? SosState.smsFailed
          : SosState.queued;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(switch (state) {
            SosState.accepted => 'Máy chủ đã tiếp nhận SOS.',
            SosState.sms => smsStatusMessage(SmsStatus.sent),
            SosState.smsUnknown => smsStatusMessage(SmsStatus.unknown),
            SosState.smsFailed => smsStatusMessage(SmsStatus.failed),
            SosState.queued => 'SOS trong hàng đợi, sẽ gửi khi có mạng.',
            _ =>
              syncError != null
                  ? 'Máy chủ từ chối SOS ($syncError), hãy gọi 112.'
                  : 'Không gửi được SOS, hãy gọi 112.',
          }),
        ),
      );
      setState(() => _sosState = state);
      _sosResetTimer = Timer(const Duration(seconds: 3), () {
        if (mounted) {
          setState(() => _sosState = SosState.idle);
        }
      });
    }
  }

  Future<void> _makeCall(String number) async {
    await openEmergencyDialer(context, number);
  }

  Future<void> _retrySms() async {
    final record = widget.controller.latestSos;
    final attemptedAt = record?.smsAttemptedAt;
    if (record == null || attemptedAt == null) return;
    final remaining = 30 - DateTime.now().difference(attemptedAt).inSeconds;
    if (remaining > 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Chờ $remaining giây trước khi thử lại SMS.')),
      );
      return;
    }
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Thử gửi lại SMS?'),
        content: const Text(
          'Lần trước gửi lỗi. Một số phần có thể đã gửi được; gửi lại có thể phát sinh phí SMS.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Hủy'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Gửi lại'),
          ),
        ],
      ),
    );
    if (confirmed == true && mounted) await _handleSos(retrySms: true);
  }

  @override
  Widget build(BuildContext context) {
    final c = widget.controller;

    return SingleChildScrollView(
      physics: const BouncingScrollPhysics(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Top Red Header
          AppHeader(networkLabel: c.networkLabel),

          // SOS Section
          SosButtonSection(state: _sosState, onPressed: _handleSos),
          if (c.latestSos case final last?
              when last.smsStatus == SmsStatus.failed &&
                  !last.metadataSynced &&
                  last.syncError == null)
            TextButton(
              onPressed: c.isBusy ? null : _retrySms,
              child: const Text('Thử lại SMS cho SOS đã lưu'),
            ),

          // Compose CTA Card (Giữ nguyên kích thước như cũ)
          ComposeCtaCard(onPressed: widget.onComposePressed),

          // SỐ KHẨN CẤP
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'SỐ KHẨN CẤP',
                  style: TextStyle(
                    color: Color(0xFF6B7280),
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 1.2,
                  ),
                ),
                const SizedBox(height: 10),
                _buildQuickEmergencyNumbers(),
              ],
            ),
          ),

          // TRẠNG THÁI THIẾT BỊ
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
            child: _buildDeviceStatusSection(c),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickEmergencyNumbers() {
    final items = [('112', 'Cứu nạn'), ('114', 'Cứu hỏa'), ('115', 'Cấp cứu')];

    return Row(
      children: items.map((c) {
        return Expanded(
          child: Container(
            margin: const EdgeInsets.symmetric(horizontal: 4),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: const Color(0xFFF3F4F6)),
            ),
            child: Material(
              color: Colors.transparent,
              borderRadius: BorderRadius.circular(16),
              child: GestureDetector(
                onTap: () => _makeCall(c.$1),
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  child: Column(
                    children: [
                      Text(
                        c.$1,
                        style: const TextStyle(
                          color: AppColors.primaryRed,
                          fontSize: 22,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        c.$2,
                        style: const TextStyle(
                          color: Color(0xFF6B7280),
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildDeviceStatusSection(AppController c) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'TRẠNG THÁI THIẾT BỊ',
          style: TextStyle(
            color: Color(0xFF6B7280),
            fontSize: 11,
            fontWeight: FontWeight.w800,
            letterSpacing: 1.2,
          ),
        ),
        const SizedBox(height: 10),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: const Color(0xFFF3F4F6)),
          ),
          child: Column(
            children: [
              _statusRow(
                icon: Icons.wifi,
                label: 'Kết nối mạng',
                value: c.networkLabel,
                isGreen: c.networkLabel != 'none',
              ),
              const Divider(height: 24, color: Color(0xFFF3F4F6)),
              _statusRow(
                icon: Icons.cloud_upload_outlined,
                label: 'Hàng đợi đồng bộ',
                value: '${c.pendingCount} bản ghi',
                isGreen: true,
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _statusRow({
    required IconData icon,
    required String label,
    required String value,
    required bool isGreen,
    String? actionLabel,
    VoidCallback? onTap,
  }) {
    final rowContent = Row(
      children: [
        Icon(icon, color: AppColors.primaryRed, size: 20),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: const TextStyle(
                  color: Color(0xFF374151),
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                ),
              ),
              if (actionLabel != null)
                Text(
                  actionLabel,
                  style: TextStyle(
                    color: Colors.grey.shade500,
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                  ),
                ),
            ],
          ),
        ),
        Text(
          value,
          style: TextStyle(
            color: isGreen ? const Color(0xFF16A34A) : const Color(0xFFEA580C),
            fontSize: 13,
            fontWeight: FontWeight.w800,
          ),
        ),
        const SizedBox(width: 6),
        if (onTap != null)
          const Icon(Icons.tune_rounded, size: 16, color: Color(0xFF6B7280))
        else
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: isGreen
                  ? const Color(0xFF16A34A)
                  : const Color(0xFFEA580C),
            ),
          ),
      ],
    );

    if (onTap != null) {
      return GestureDetector(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: rowContent,
        ),
      );
    }

    return rowContent;
  }
}
