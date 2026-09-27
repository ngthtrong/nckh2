import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';

class StatusTracker extends StatelessWidget {
  final String currentStatus;

  const StatusTracker({super.key, required this.currentStatus});

  @override
  Widget build(BuildContext context) {
    if (currentStatus == 'cancelled') {
      // Điều phối viên đóng báo cáo (trùng, không xác minh được...): không hiện tiến trình.
      return Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppColors.statusCancelledBg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.statusCancelledBorder),
        ),
        child: const Row(
          children: [
            Icon(Icons.info_outline, color: AppColors.statusCancelledText, size: 20),
            SizedBox(width: 8),
            Expanded(
              child: Text(
                'Điều phối viên đã đóng báo cáo này. Nếu vẫn cần cứu, hãy gửi báo cáo mới hoặc bấm SOS.',
                style: TextStyle(
                  color: AppColors.statusCancelledText,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
      );
    }

    final steps = [
      ('processing', 'Đã nhận'),
      ('dispatched', 'Đang đến'),
      ('resolved', 'Hoàn thành'),
    ];

    int activeIndex = 0;
    if (currentStatus == 'dispatched') activeIndex = 1;
    if (currentStatus == 'resolved') activeIndex = 2;

    return Column(
      children: [
        Row(
          children: List.generate(steps.length, (index) {
            final isDone = index <= activeIndex;
            return Expanded(
              child: Column(
                children: [
                  Container(
                    width: 32,
                    height: 32,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: isDone ? AppColors.primaryRed : Colors.white,
                      border: Border.all(
                        color: isDone ? AppColors.primaryRed : const Color(0xFFE5E7EB),
                        width: 2,
                      ),
                    ),
                    child: isDone
                        ? const Icon(Icons.check, color: Colors.white, size: 18)
                        : Container(
                            margin: const EdgeInsets.all(10),
                            decoration: const BoxDecoration(
                              shape: BoxShape.circle,
                              color: Color(0xFFD1D5DB),
                            ),
                          ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    steps[index].$2,
                    style: TextStyle(
                      color: isDone ? AppColors.primaryRed : const Color(0xFF9CA3AF),
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            );
          }),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: Container(
                height: 3,
                color: activeIndex >= 0 ? AppColors.primaryRed : const Color(0xFFE5E7EB),
              ),
            ),
            Expanded(
              child: Container(
                height: 3,
                color: activeIndex >= 1 ? AppColors.primaryRed : const Color(0xFFE5E7EB),
              ),
            ),
          ],
        ),
      ],
    );
  }
}
