import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../domain/entities/ai_model_type.dart';
import '../controllers/app_controller.dart';

class AiModelSettingsSheet extends StatelessWidget {
  final AppController controller;

  const AiModelSettingsSheet({super.key, required this.controller});

  static void show(BuildContext context, AppController controller) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => AiModelSettingsSheet(controller: controller),
    );
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: controller,
      builder: (context, _) {
        final ready = controller.isModelReady;
        final benchmarking = controller.isBenchmarking;
        final comparison = controller.latestComparison;
        return Container(
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
          ),
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 28),
          child: SafeArea(
            top: false,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(
                    width: 40,
                    height: 4,
                    margin: const EdgeInsets.only(bottom: 16),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade300,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                const Text(
                  'Mô hình AI on-device',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900),
                ),
                const SizedBox(height: 16),
                Wrap(
                  spacing: 8,
                  children: AiModelType.values.map((model) {
                    final available =
                        model == AiModelType.onnx || controller.isPteReady;
                    return ChoiceChip(
                      label: Text(model.badgeText),
                      selected: controller.currentModel == model,
                      onSelected: available
                          ? (_) => controller.switchAiModel(model)
                          : null,
                    );
                  }).toList(),
                ),
                SwitchListTile.adaptive(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('So sánh ONNX và PTE thật'),
                  subtitle: Text(
                    controller.isPteReady
                        ? 'Chạy cùng tensor qua cả hai runtime'
                        : 'ExecuTorch chỉ sẵn sàng trên Android sau khi nạp PTE',
                  ),
                  value: controller.isDualComparison,
                  onChanged: controller.isPteReady
                      ? controller.toggleDualComparison
                      : null,
                ),
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF9FAFB),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: const Color(0xFFE5E7EB)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.bolt_rounded, color: Color(0xFF2563EB)),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              controller.currentModel.name,
                              style: const TextStyle(
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                            Text(
                              ready
                                  ? '${controller.currentModel.name} · letterbox 224×224'
                                  : 'Đang nạp model on-device...',
                              style: const TextStyle(
                                fontSize: 12,
                                color: Color(0xFF6B7280),
                              ),
                            ),
                          ],
                        ),
                      ),
                      Icon(
                        ready ? Icons.check_circle : Icons.hourglass_top,
                        color: ready
                            ? const Color(0xFF16A34A)
                            : const Color(0xFFEA580C),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: benchmarking
                        ? null
                        : () async {
                            final result = await controller
                                .testModelBenchmark();
                            if (!context.mounted) return;
                            final message = result == null
                                ? 'Không thể chạy benchmark ${controller.currentModel.name}.'
                                : '${result.label}: ${(result.confidence * 100).toStringAsFixed(1)}% · ${result.durationMs} ms';
                            ScaffoldMessenger.of(
                              context,
                            ).showSnackBar(SnackBar(content: Text(message)));
                          },
                    icon: benchmarking
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.speed_rounded),
                    label: const Text('Benchmark model trên thiết bị'),
                  ),
                ),
                if (comparison != null) ...[
                  const SizedBox(height: 12),
                  Text(
                    'ONNX ${comparison.durationMsOnnx} ms · '
                    'PTE ${comparison.durationMsPte} ms · '
                    '${comparison.isIdentical ? 'cùng nhãn' : 'khác nhãn'}',
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                ],
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () => Navigator.pop(context),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primaryRed,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                    child: const Text(
                      'Đóng',
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
