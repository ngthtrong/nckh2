import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';

enum SosState { idle, pressed, accepted, queued, sms, failed }

class SosButtonSection extends StatelessWidget {
  final SosState state;
  final VoidCallback onPressed;

  const SosButtonSection({
    super.key,
    required this.state,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    final (icon, label, message, color) = switch (state) {
      SosState.idle => (null, 'SOS', null, AppColors.primaryRed),
      SosState.pressed => (
        Icons.hourglass_top,
        'Đang gửi',
        'Đang gửi SOS…',
        AppColors.primaryRedDark,
      ),
      SosState.accepted => (
        Icons.check,
        'Đã tiếp nhận',
        'Máy chủ đã tiếp nhận SOS.',
        const Color(0xFF16A34A),
      ),
      SosState.queued => (
        Icons.schedule,
        'Đã xếp hàng',
        'SOS trong hàng đợi, sẽ gửi khi có mạng.',
        const Color(0xFFB45309),
      ),
      SosState.sms => (
        Icons.sms_outlined,
        'Đã gửi SMS',
        'Đã gửi SMS; chưa xác nhận tiếp nhận.',
        const Color(0xFF2563EB),
      ),
      SosState.failed => (
        Icons.error_outline,
        'Thử lại SOS',
        'Chưa gửi được SOS. Hãy gọi 112.',
        AppColors.primaryRed,
      ),
    };
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
      color: Colors.white,
      child: Column(
        children: [
          const Text(
            'Nhấn SOS để gửi yêu cầu cứu hộ',
            style: TextStyle(
              color: Color(0xFF374151),
              fontSize: 15,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 2),
          const Text(
            'Vị trí GPS sẽ được gửi tự động',
            style: TextStyle(
              color: Color(0xFF6B7280),
              fontSize: 12,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 18),
          Stack(
            alignment: Alignment.center,
            children: [
              Semantics(
                button: true,
                enabled: state != SosState.pressed,
                child: GestureDetector(
                  onTap: state == SosState.pressed ? null : onPressed,
                  child: Container(
                    width: 100,
                    height: 100,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: color,
                      boxShadow: const [
                        BoxShadow(
                          color: Colors.black26,
                          blurRadius: 12,
                          offset: Offset(0, 6),
                        ),
                      ],
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        if (icon != null) ...[
                          Icon(icon, color: Colors.white, size: 38),
                          const SizedBox(height: 2),
                          Text(
                            label,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 10,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ] else ...[
                          const Text(
                            'SOS',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 30,
                              fontWeight: FontWeight.w900,
                              letterSpacing: 1.5,
                            ),
                          ),
                          const SizedBox(height: 2),
                          const Text(
                            'Nhấn để gửi',
                            style: TextStyle(
                              color: Colors.white70,
                              fontSize: 10,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
          if (message != null) ...[
            const SizedBox(height: 12),
            Text(
              message,
              textAlign: TextAlign.center,
              style: TextStyle(
                color: color,
                fontSize: 12,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
