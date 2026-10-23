import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';
import '../../domain/entities/rescue_record.dart';

class StatusBadge extends StatelessWidget {
  final RescueRecord record;

  const StatusBadge({super.key, required this.record});

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color text;
    Color border;
    String label;

    if (record.syncError != null) {
      bg = const Color(0xFFFEF2F2);
      text = AppColors.primaryRed;
      border = const Color(0xFFFECACA);
      label = 'Bị từ chối';
    } else if (!record.metadataSynced && !record.synced) {
      bg = AppColors.statusProcessingBg;
      text = AppColors.statusProcessingText;
      border = AppColors.statusProcessingBorder;
      label = 'Chờ gửi';
    } else {
      switch (record.status) {
        case 'dispatched':
          bg = AppColors.statusDispatchedBg;
          text = AppColors.statusDispatchedText;
          border = AppColors.statusDispatchedBorder;
          label = 'Đang đến';
          break;
        case 'resolved':
          bg = AppColors.statusResolvedBg;
          text = AppColors.statusResolvedText;
          border = AppColors.statusResolvedBorder;
          label = 'Hoàn thành';
          break;
        case 'cancelled':
          bg = AppColors.statusCancelledBg;
          text = AppColors.statusCancelledText;
          border = AppColors.statusCancelledBorder;
          label = 'Đã đóng';
          break;
        case 'processing':
        default:
          bg = AppColors.statusProcessingBg;
          text = AppColors.statusProcessingText;
          border = AppColors.statusProcessingBorder;
          label = 'Đã nhận';
          break;
      }
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: border),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: text,
          fontSize: 11,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}
