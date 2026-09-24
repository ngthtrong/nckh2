import 'package:flutter/material.dart';
import '../../domain/entities/ai_tag.dart';

class TagChip extends StatelessWidget {
  final AiTag tag;
  final bool isSmall;

  const TagChip({
    super.key,
    required this.tag,
    this.isSmall = false,
  });

  @override
  Widget build(BuildContext context) {
    final confidencePct = (tag.confidence * 100).round();
    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: isSmall ? 8 : 10,
        vertical: isSmall ? 3 : 5,
      ),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF7ED),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFFED7AA)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            tag.label,
            style: TextStyle(
              color: const Color(0xFFC2410C),
              fontSize: isSmall ? 11 : 12,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(width: 4),
          Text(
            '$confidencePct%',
            style: TextStyle(
              color: const Color(0xFFF97316),
              fontSize: isSmall ? 10 : 11,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}
