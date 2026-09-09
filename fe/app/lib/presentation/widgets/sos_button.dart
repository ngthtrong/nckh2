import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';

enum SosState { idle, pressed, sent }

class SosButtonSection extends StatefulWidget {
  final SosState state;
  final VoidCallback onPressed;

  const SosButtonSection({
    super.key,
    required this.state,
    required this.onPressed,
  });

  @override
  State<SosButtonSection> createState() => _SosButtonSectionState();
}

class _SosButtonSectionState extends State<SosButtonSection>
    with SingleTickerProviderStateMixin {
  late AnimationController _animController;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat();
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
      color: Colors.white,
      child: Column(
        children: [
          const Text(
            'Nhấn SOS để gọi cứu hộ ngay',
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
              if (widget.state == SosState.idle)
                AnimatedBuilder(
                  animation: _animController,
                  builder: (context, child) {
                    final value = _animController.value;
                    return Container(
                      width: 100 + (value * 30),
                      height: 100 + (value * 30),
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: AppColors.primaryRed.withOpacity(0.25 * (1 - value)),
                      ),
                    );
                  },
                ),
              GestureDetector(
                onTap: widget.onPressed,
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  width: 100,
                  height: 100,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: widget.state == SosState.sent
                        ? const Color(0xFF16A34A)
                        : widget.state == SosState.pressed
                            ? AppColors.primaryRedDark
                            : AppColors.primaryRed,
                    boxShadow: const [
                      BoxShadow(
                        color: Colors.black26,
                        blurRadius: 12,
                        offset: Offset(0, 6),
                      )
                    ],
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      if (widget.state == SosState.sent) ...[
                        const Icon(Icons.check, color: Colors.white, size: 38),
                        const SizedBox(height: 2),
                        const Text(
                          'Đã gửi!',
                          style: TextStyle(
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
                          'Nhấn để gọi',
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
            ],
          ),
          if (widget.state == SosState.sent) ...[
            const SizedBox(height: 12),
            const Text(
              '✓ Đội cứu hộ đã nhận vị trí của bạn',
              style: TextStyle(
                color: Color(0xFF15803D),
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
