import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../domain/entities/ai_model_type.dart';
import '../controllers/app_controller.dart';

class AiModelSettingsSheet extends StatelessWidget {
  final AppController controller;

  const AiModelSettingsSheet({super.key, required this.controller});

  static void show(BuildContext context, AppController controller) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => AiModelSettingsSheet(controller: controller),
    );
  }

  @override
  Widget build(BuildContext context) {
    final active = controller.currentModel;
    final comparison = controller.latestComparison;
    final isDual = controller.isDualComparison;

    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 28),
      child: SafeArea(
        top: false,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Drag handle
            Center(
              child: Container(
                width: 40,
                height: 4,
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(
                  color: Colors.grey.shade300,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),

            // Header
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: AppColors.primaryRed.withValues(alpha: 0.1),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.settings_suggest_rounded,
                    color: AppColors.primaryRed,
                    size: 24,
                  ),
                ),
                const SizedBox(width: 12),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Cài Đặt Mô Hình AI On-Device',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w900,
                          color: Color(0xFF1F2937),
                        ),
                      ),
                      Text(
                        'Lựa chọn engine mô hình chạy ngoại tuyến',
                        style: TextStyle(
                          fontSize: 12,
                          color: Color(0xFF6B7280),
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),

            const SizedBox(height: 20),

            // Model Selection Cards
            const Text(
              'LỰA CHỌN MÔ HÌNH CHÍNH',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w800,
                color: Color(0xFF6B7280),
                letterSpacing: 1.1,
              ),
            ),
            const SizedBox(height: 10),

            _buildModelCard(
              context: context,
              type: AiModelType.onnx,
              isSelected: active == AiModelType.onnx,
              icon: Icons.bolt_rounded,
              iconColor: const Color(0xFF2563EB),
              badgeColor: const Color(0xFFEFF6FF),
              badgeTextColor: const Color(0xFF1D4ED8),
              fileSize: '16.0 MB',
            ),

            const SizedBox(height: 10),

            _buildModelCard(
              context: context,
              type: AiModelType.pte,
              isSelected: active == AiModelType.pte,
              icon: Icons.smartphone_rounded,
              iconColor: const Color(0xFF059669),
              badgeColor: const Color(0xFFECFDF5),
              badgeTextColor: const Color(0xFF047857),
              fileSize: '16.2 MB',
            ),

            const SizedBox(height: 18),

            // Dual Comparison Toggle Switch
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: const Color(0xFFF9FAFB),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFFE5E7EB)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.compare_arrows_rounded,
                      color: Color(0xFFD97706), size: 24),
                  const SizedBox(width: 12),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Chế độ So Sánh Song Song',
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w800,
                            color: Color(0xFF1F2937),
                          ),
                        ),
                        Text(
                          'Chạy cả .onnx & .pte để đối chiếu độ trễ và nhãn',
                          style: TextStyle(
                            fontSize: 11,
                            color: Color(0xFF6B7280),
                          ),
                        ),
                      ],
                    ),
                  ),
                  Switch.adaptive(
                    value: isDual,
                    activeTrackColor: AppColors.primaryRed,
                    onChanged: (val) {
                      controller.toggleDualComparison(val);
                    },
                  ),
                ],
              ),
            ),

            // Latest Comparison Scorecard (if available)
            if (comparison != null) ...[
              const SizedBox(height: 18),
              const Text(
                'KẾT QUẢ ĐỐI CHIẾU GẦN NHẤT',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  color: Color(0xFF6B7280),
                  letterSpacing: 1.1,
                ),
              ),
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: const Color(0xFFFFFBEB),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFFFDE68A)),
                ),
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        _buildMetricCol('⚡ ONNX (.onnx)', comparison.labelOnnx,
                            '${(comparison.confOnnx * 100).toStringAsFixed(1)}%', '${comparison.durationMsOnnx} ms'),
                        Container(width: 1, height: 45, color: const Color(0xFFFCD34D)),
                        _buildMetricCol('📱 ExecuTorch (.pte)', comparison.labelPte,
                            '${(comparison.confPte * 100).toStringAsFixed(1)}%', '${comparison.durationMsPte} ms'),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: comparison.isIdentical ? const Color(0xFFDCFCE7) : const Color(0xFFFEE2E2),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        comparison.isIdentical
                            ? '✓ Nhãn phân loại đồng nhất 100%'
                            : '⚠️ Có sai lệch nhãn phân loại',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w800,
                          color: comparison.isIdentical ? const Color(0xFF166534) : const Color(0xFF991B1B),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],

            const SizedBox(height: 20),

            // Close button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => Navigator.pop(context),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primaryRed,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
                child: const Text(
                  'Xác Nhận & Đóng',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w800,
                    fontSize: 15,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildModelCard({
    required BuildContext context,
    required AiModelType type,
    required bool isSelected,
    required IconData icon,
    required Color iconColor,
    required Color badgeColor,
    required Color badgeTextColor,
    required String fileSize,
  }) {
    return InkWell(
      onTap: () {
        controller.switchAiModel(type);
      },
      borderRadius: BorderRadius.circular(18),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFFFEF2F2) : const Color(0xFFF9FAFB),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(
            color: isSelected ? AppColors.primaryRed : const Color(0xFFE5E7EB),
            width: isSelected ? 2 : 1,
          ),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: isSelected ? Colors.white : Colors.white70,
                shape: BoxShape.circle,
                border: Border.all(color: const Color(0xFFE5E7EB)),
              ),
              child: Icon(icon, color: iconColor, size: 22),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(
                        type.name,
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w800,
                          color: Color(0xFF1F2937),
                        ),
                      ),
                      const SizedBox(width: 6),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: badgeColor,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          type.extension,
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.w800,
                            color: badgeTextColor,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(
                    type.description,
                    style: const TextStyle(
                      fontSize: 11,
                      color: Color(0xFF6B7280),
                    ),
                  ),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  fileSize,
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w800,
                    color: Color(0xFF4B5563),
                  ),
                ),
                Icon(
                  isSelected ? Icons.check_circle_rounded : Icons.radio_button_unchecked_rounded,
                  color: isSelected ? AppColors.primaryRed : const Color(0xFF9CA3AF),
                  size: 20,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricCol(String title, String label, String conf, String ms) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: Color(0xFF78350F))),
        const SizedBox(height: 2),
        Text('$label ($conf)', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w900, color: Color(0xFF1F2937))),
        Text('Thời gian: $ms', style: const TextStyle(fontSize: 11, color: Color(0xFF4B5563), fontWeight: FontWeight.w600)),
      ],
    );
  }
}
