import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';

class VulnerableGroupSelector extends StatelessWidget {
  final List<String> selectedGroups;
  final ValueChanged<List<String>> onChanged;

  const VulnerableGroupSelector({
    super.key,
    required this.selectedGroups,
    required this.onChanged,
  });

  static const List<({String key, String label, String icon})> _options = [
    (key: 'elderly', label: 'Người già', icon: '👴'),
    (key: 'children', label: 'Trẻ em', icon: '👶'),
    (key: 'pregnant', label: 'Phụ nữ mang thai', icon: '🤰'),
    (key: 'disabled', label: 'Người khuyết tật', icon: '♿'),
  ];

  void _toggleGroup(String label) {
    final updated = List<String>.from(selectedGroups);
    if (updated.contains(label)) {
      updated.remove(label);
    } else {
      updated.add(label);
    }
    onChanged(updated);
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'ĐỐI TƯỢNG ƯU TIÊN (NẾU CÓ)',
          style: TextStyle(
            color: Color(0xFF6B7280),
            fontSize: 11,
            fontWeight: FontWeight.w800,
            letterSpacing: 1.2,
          ),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: _options.map((opt) {
            final isSelected = selectedGroups.contains(opt.label);
            return FilterChip(
              selected: isSelected,
              showCheckmark: false,
              avatar: Text(opt.icon, style: const TextStyle(fontSize: 14)),
              label: Text(
                opt.label,
                style: TextStyle(
                  color: isSelected ? Colors.white : const Color(0xFF374151),
                  fontWeight: isSelected ? FontWeight.w800 : FontWeight.w600,
                  fontSize: 13,
                ),
              ),
              selectedColor: AppColors.primaryRed,
              backgroundColor: const Color(0xFFF3F4F6),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(20),
                side: BorderSide(
                  color: isSelected ? AppColors.primaryRed : const Color(0xFFE5E7EB),
                ),
              ),
              onSelected: (_) => _toggleGroup(opt.label),
            );
          }).toList(),
        ),
      ],
    );
  }
}
