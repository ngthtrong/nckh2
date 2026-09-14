import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/constants/app_colors.dart';
import '../../controllers/app_controller.dart';
import '../../widgets/ai_model_settings_sheet.dart';
import '../../widgets/app_header.dart';
import '../../widgets/compose_cta_card.dart';
import '../../widgets/sos_button.dart';

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

  Future<void> _handleSos() async {
    if (_sosState != SosState.idle) return;
    setState(() => _sosState = SosState.pressed);

    await widget.controller.sendSos();

    if (mounted) {
      setState(() => _sosState = SosState.sent);
      Future.delayed(const Duration(seconds: 3), () {
        if (mounted) {
          setState(() => _sosState = SosState.idle);
        }
      });
    }
  }

  Future<void> _makeCall(String number) async {
    final Uri uri = Uri.parse('tel:$number');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    }
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
          SosButtonSection(
            state: _sosState,
            onPressed: _handleSos,
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
    final items = [
      ('112', 'Cứu nạn'),
      ('114', 'Cứu hỏa'),
      ('115', 'Cấp cứu'),
    ];

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
              child: InkWell(
                onTap: () => _makeCall(c.$1),
                borderRadius: BorderRadius.circular(16),
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
                icon: Icons.memory,
                label: 'Mô hình AI offline',
                value: c.isModelReady ? c.currentModel.badgeText : 'Đang nạp',
                isGreen: c.isModelReady,
                actionLabel: 'Cài đặt',
                onTap: () => AiModelSettingsSheet.show(context, c),
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
                  'Chạm để đổi (.onnx / .pte) · So sánh',
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
              color: isGreen ? const Color(0xFF16A34A) : const Color(0xFFEA580C),
            ),
          ),
      ],
    );

    if (onTap != null) {
      return InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(10),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: rowContent,
        ),
      );
    }

    return rowContent;
  }
}
