import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../domain/entities/rescue_record.dart';
import '../../widgets/quick_call_panel.dart';
import '../../widgets/status_tracker.dart';
import '../../widgets/tag_chip.dart';

class SubmittedScreen extends StatelessWidget {
  final RescueRecord record;
  final VoidCallback onHomePressed;

  const SubmittedScreen({
    super.key,
    required this.record,
    required this.onHomePressed,
  });

  @override
  Widget build(BuildContext context) {
    final timeStr = DateFormat('HH:mm · dd/MM/yyyy').format(record.createdAt);
    final idShort = record.id.length > 8
        ? record.id.substring(record.id.length - 8).toUpperCase()
        : record.id.toUpperCase();

    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
                physics: const BouncingScrollPhysics(),
                child: Column(
                  children: [
                    Container(
                      width: 80,
                      height: 80,
                      decoration: const BoxDecoration(
                        color: Color(0xFFDCFCE7),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.check_circle_rounded,
                        color: Color(0xFF16A34A),
                        size: 56,
                      ),
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      'Đã gửi thành công!',
                      style: TextStyle(
                        color: Color(0xFF1F2937),
                        fontSize: 22,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 6),
                    const Text(
                      'Đội cứu hộ đã nhận bài và đang xử lý. Vui lòng giữ điện thoại để nhận phản hồi.',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: Color(0xFF6B7280),
                        fontSize: 13,
                        fontWeight: FontWeight.w500,
                        height: 1.4,
                      ),
                    ),
                    const SizedBox(height: 20),

                    // Summary Card
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: const Color(0xFFF9FAFB),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: const Color(0xFFF3F4F6)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _summaryRow('Mã yêu cầu', '#$idShort', isMono: true),
                          const Divider(height: 20),
                          _summaryRow('Thời gian', timeStr),
                          const Divider(height: 20),
                          _summaryRow(
                            'Vị trí GPS',
                            '${record.lat.toStringAsFixed(4)}, ${record.lng.toStringAsFixed(4)}',
                          ),
                          if (record.trappedCount > 0 ||
                              record.injuredCount > 0 ||
                              record.vulnerableGroups.isNotEmpty) ...[
                            const Divider(height: 20),
                            if (record.trappedCount > 0)
                              _summaryRow(
                                'Số người mắc kẹt',
                                '${record.trappedCount} người',
                              ),
                            if (record.injuredCount > 0) ...[
                              const SizedBox(height: 8),
                              _summaryRow(
                                'Số người bị thương',
                                '${record.injuredCount} người',
                              ),
                            ],
                            if (record.vulnerableGroups.isNotEmpty) ...[
                              const SizedBox(height: 8),
                              _summaryRow(
                                'Đối tượng ưu tiên',
                                record.vulnerableGroups.join(', '),
                              ),
                            ],
                          ],
                          if (record.aiTags.isNotEmpty) ...[
                            const Divider(height: 20),
                            const Text(
                              'AI PHÂN TÍCH',
                              style: TextStyle(
                                color: Color(0xFF9CA3AF),
                                fontSize: 11,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                            const SizedBox(height: 8),
                            Wrap(
                              spacing: 6,
                              runSpacing: 6,
                              children: record.aiTags
                                  .map((t) => TagChip(tag: t, isSmall: true))
                                  .toList(),
                            ),
                          ],
                        ],
                      ),
                    ),
                    const SizedBox(height: 24),

                    // Status Tracker
                    StatusTracker(currentStatus: record.status),
                    const SizedBox(height: 24),

                    // Quick Call Panel
                    const QuickCallPanel(),
                  ],
                ),
              ),
            ),

            // Bottom Home Button
            Padding(
              padding: const EdgeInsets.all(16),
              child: SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: onHomePressed,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFF3F4F6),
                    foregroundColor: const Color(0xFF374151),
                    elevation: 0,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                  child: const Text(
                    'Về trang chủ',
                    style: TextStyle(
                      fontWeight: FontWeight.w800,
                      fontSize: 15,
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _summaryRow(String label, String value, {bool isMono = false}) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: const TextStyle(
            color: Color(0xFF6B7280),
            fontSize: 12,
            fontWeight: FontWeight.w600,
          ),
        ),
        Text(
          value,
          style: TextStyle(
            color: const Color(0xFF1F2937),
            fontSize: 13,
            fontWeight: FontWeight.w800,
            fontFamily: isMono ? 'monospace' : null,
          ),
        ),
      ],
    );
  }
}
