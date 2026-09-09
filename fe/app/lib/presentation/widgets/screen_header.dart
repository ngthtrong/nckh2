import 'package:flutter/material.dart';

class ScreenHeader extends StatelessWidget {
  final String title;
  final VoidCallback onBack;
  final Widget? action;

  const ScreenHeader({
    super.key,
    required this.title,
    required this.onBack,
    this.action,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(
          bottom: BorderSide(color: Color(0xFFF3F4F6), width: 1),
        ),
      ),
      child: Row(
        children: [
          IconButton(
            onPressed: onBack,
            icon: const Icon(Icons.close, color: Color(0xFF374151), size: 24),
          ),
          Expanded(
            child: Text(
              title,
              style: const TextStyle(
                color: Color(0xFF1F2937),
                fontSize: 18,
                fontWeight: FontWeight.w800,
              ),
            ),
          ),
          if (action != null) action!,
        ],
      ),
    );
  }
}
