import 'package:flutter/material.dart';

import '../../core/constants/app_colors.dart';
import '../../domain/entities/ai_model_type.dart';

class AiModelRuntimeCard extends StatelessWidget {
  const AiModelRuntimeCard({
    super.key,
    required this.currentModel,
    required this.isPteReady,
    required this.isDualComparison,
    required this.onModelChanged,
    required this.onDualComparisonChanged,
  });

  final AiModelType currentModel;
  final bool isPteReady;
  final bool isDualComparison;
  final ValueChanged<AiModelType> onModelChanged;
  final ValueChanged<bool> onDualComparisonChanged;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: const Color(0xFFF9FAFB),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: const BorderSide(color: Color(0xFFE5E7EB)),
      ),
      clipBehavior: Clip.antiAlias,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ...AiModelType.values.map((model) {
              final available = model == AiModelType.onnx || isPteReady;
              final selected = currentModel == model;
              return ListTile(
                contentPadding: EdgeInsets.zero,
                onTap: available ? () => onModelChanged(model) : null,
                title: Text(model.name),
                subtitle: Text(
                  available
                      ? model.description
                      : 'Runtime chưa sẵn sàng trên thiết bị này',
                ),
                trailing: Icon(
                  selected
                      ? Icons.radio_button_checked
                      : Icons.radio_button_off,
                  color: selected
                      ? AppColors.primaryRed
                      : const Color(0xFF9CA3AF),
                ),
              );
            }),
            const Divider(height: 16),
            SwitchListTile.adaptive(
              contentPadding: EdgeInsets.zero,
              title: const Text('So sánh ONNX và PTE thật'),
              subtitle: const Text(
                'Chạy cả hai runtime trên cùng tensor đầu vào',
              ),
              value: isDualComparison,
              onChanged: isPteReady ? onDualComparisonChanged : null,
            ),
          ],
        ),
      ),
    );
  }
}
