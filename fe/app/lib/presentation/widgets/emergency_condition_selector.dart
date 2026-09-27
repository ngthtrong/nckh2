import 'package:flutter/material.dart';

import '../../core/constants/app_colors.dart';

class EmergencyConditionSelector extends StatelessWidget {
  static const options = [
    (key: 'unresponsive', label: 'Bất tỉnh / không phản ứng'),
    (key: 'respiratory_distress', label: 'Khó thở nghiêm trọng / tím tái'),
    (key: 'heavy_bleeding', label: 'Chảy máu nhiều'),
    (key: 'seizure', label: 'Co giật'),
    (key: 'major_trauma', label: 'Chấn thương nặng rõ ràng'),
  ];

  final bool cannotMove;
  final List<String> severeSigns;
  final ValueChanged<bool> onCannotMoveChanged;
  final ValueChanged<List<String>> onSevereSignsChanged;

  const EmergencyConditionSelector({
    super.key,
    required this.cannotMove,
    required this.severeSigns,
    required this.onCannotMoveChanged,
    required this.onSevereSignsChanged,
  });

  void _toggle(String key) {
    final updated = List<String>.from(severeSigns);
    updated.contains(key) ? updated.remove(key) : updated.add(key);
    onSevereSignsChanged(updated);
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Row(
          children: [
            Expanded(
              child: Text(
                'TÌNH TRẠNG KHẨN CẤP',
                style: TextStyle(
                  color: AppColors.textMuted,
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 1.2,
                ),
              ),
            ),
            Text(
              'Chọn nếu có',
              style: TextStyle(color: Color(0xFF9CA3AF), fontSize: 12),
            ),
          ],
        ),
        const SizedBox(height: 8),
        _OptionTile(
          selected: cannotMove,
          title: 'Có người không thể tự di chuyển',
          subtitle: 'Không thể tự đi hoặc cần người khác hỗ trợ di chuyển.',
          onTap: () => onCannotMoveChanged(!cannotMove),
        ),
        const SizedBox(height: 14),
        const Text(
          'Dấu hiệu nguy hiểm nghiêm trọng',
          style: TextStyle(
            color: AppColors.textDark,
            fontSize: 15,
            fontWeight: FontWeight.w800,
          ),
        ),
        const SizedBox(height: 4),
        const Text(
          'Chọn nhanh nếu có ít nhất một dấu hiệu:',
          style: TextStyle(color: AppColors.textMuted, fontSize: 12),
        ),
        const SizedBox(height: 10),
        ...options.map((option) {
          final selected = severeSigns.contains(option.key);
          return Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: _OptionTile(
              selected: selected,
              title: option.label,
              onTap: () => _toggle(option.key),
            ),
          );
        }),
      ],
    );
  }
}

class _OptionTile extends StatelessWidget {
  final bool selected;
  final String title;
  final String? subtitle;
  final VoidCallback onTap;

  const _OptionTile({
    required this.selected,
    required this.title,
    this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: selected ? const Color(0xFFFFF5F5) : Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(
          color: selected ? const Color(0xFFE9A3A3) : const Color(0xFFE5E7EB),
        ),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(
                width: 32,
                height: 32,
                child: Checkbox(
                  value: selected,
                  onChanged: (_) => onTap(),
                  activeColor: AppColors.primaryRed,
                  side: const BorderSide(color: Color(0xFFD1D5DB), width: 2),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(6),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: TextStyle(
                        color: selected
                            ? const Color(0xFFA72D2D)
                            : AppColors.textDark,
                        fontSize: 14,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    if (subtitle != null) ...[
                      const SizedBox(height: 2),
                      Text(
                        subtitle!,
                        style: const TextStyle(
                          color: AppColors.textMuted,
                          fontSize: 12,
                          height: 1.35,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
