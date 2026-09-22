import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../domain/entities/rescue_record.dart';
import '../../core/platform/local_file.dart';
import 'status_badge.dart';
import 'tag_chip.dart';

class PostCard extends StatelessWidget {
  final RescueRecord record;

  const PostCard({super.key, required this.record});

  @override
  Widget build(BuildContext context) {
    final timeStr = DateFormat('HH:mm · dd/MM/yyyy').format(record.createdAt);
    final idShort = record.id.length > 8
        ? record.id.substring(record.id.length - 8).toUpperCase()
        : record.id.toUpperCase();

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 0,
      color: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: const BorderSide(color: Color(0xFFF3F4F6)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(
                  '#$idShort',
                  style: const TextStyle(
                    color: Color(0xFF374151),
                    fontWeight: FontWeight.w800,
                    fontSize: 13,
                  ),
                ),
                const Spacer(),
                StatusBadge(status: record.status),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                const Icon(
                  Icons.access_time,
                  size: 14,
                  color: Color(0xFF9CA3AF),
                ),
                const SizedBox(width: 4),
                Text(
                  timeStr,
                  style: const TextStyle(
                    color: Color(0xFF6B7280),
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Row(
              children: [
                const Icon(
                  Icons.location_on,
                  size: 14,
                  color: Color(0xFFDC2626),
                ),
                const SizedBox(width: 4),
                Text(
                  '${record.lat.toStringAsFixed(4)}, ${record.lng.toStringAsFixed(4)}',
                  style: const TextStyle(
                    color: Color(0xFF374151),
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
            if (record.trappedCount > 0 ||
                record.injuredCount > 0 ||
                record.vulnerableGroups.isNotEmpty) ...[
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: const Color(0xFFFEF2F2),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFFFECACA)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (record.trappedCount > 0)
                      Text(
                        '• Mắc kẹt: ${record.trappedCount} người',
                        style: const TextStyle(
                          color: Color(0xFF991B1B),
                          fontWeight: FontWeight.w800,
                          fontSize: 12,
                        ),
                      ),
                    if (record.injuredCount > 0)
                      Text(
                        '• Bị thương: ${record.injuredCount} người',
                        style: const TextStyle(
                          color: Color(0xFF991B1B),
                          fontWeight: FontWeight.w800,
                          fontSize: 12,
                        ),
                      ),
                    if (record.vulnerableGroups.isNotEmpty)
                      Text(
                        '• Ưu tiên: ${record.vulnerableGroups.join(", ")}',
                        style: const TextStyle(
                          color: Color(0xFF991B1B),
                          fontWeight: FontWeight.w800,
                          fontSize: 12,
                        ),
                      ),
                  ],
                ),
              ),
            ],
            if (record.description.isNotEmpty) ...[
              const SizedBox(height: 10),
              Text(
                record.description,
                style: const TextStyle(
                  color: Color(0xFF1F2937),
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
            if (record.imagePath != null &&
                localFileExists(record.imagePath!)) ...[
              const SizedBox(height: 12),
              ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: Image(
                  image: localImageProvider(record.imagePath!),
                  height: 160,
                  width: double.infinity,
                  fit: BoxFit.cover,
                ),
              ),
            ],
            if (record.aiTags.isNotEmpty) ...[
              const SizedBox(height: 12),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: record.aiTags
                    .map((tag) => TagChip(tag: tag, isSmall: true))
                    .toList(),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
