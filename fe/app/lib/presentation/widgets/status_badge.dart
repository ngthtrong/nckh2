import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';

class StatusBadge extends StatelessWidget {
  final String status;

  const StatusBadge({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color text;
    Color border;
    String label;

    switch (status) {
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
      case 'processing':
      default:
        bg = AppColors.statusProcessingBg;
        text = AppColors.statusProcessingText;
        border = AppColors.statusProcessingBorder;
        label = 'Đã nhận';
        break;
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
