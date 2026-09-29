import 'dart:convert';

import 'package:flutter/material.dart';

class PayloadDemoPanel extends StatelessWidget {
  final Map<String, dynamic> payload;

  const PayloadDemoPanel({super.key, required this.payload});

  @override
  Widget build(BuildContext context) {
    final formatted = const JsonEncoder.withIndent('  ').convert(payload);
    return Container(
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        border: Border.all(color: const Color(0xFFE5E7EB)),
        borderRadius: BorderRadius.circular(8),
      ),
      child: ExpansionTile(
        tilePadding: const EdgeInsets.symmetric(horizontal: 14),
        childrenPadding: EdgeInsets.zero,
        title: const Text(
          'Xem payload demo (dành cho phát triển)',
          style: TextStyle(
            color: Color(0xFF6B7280),
            fontSize: 13,
            fontWeight: FontWeight.w800,
          ),
        ),
        children: [
          Container(
            width: double.infinity,
            color: const Color(0xFF121827),
            padding: const EdgeInsets.all(16),
            child: SelectableText(
              formatted,
              style: const TextStyle(
                color: Color(0xFFE5E7EB),
                fontFamily: 'monospace',
                fontSize: 12,
                height: 1.45,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
