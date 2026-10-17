import 'package:flutter/material.dart';
import '../controllers/app_controller.dart';

class AdminModelDownloadButton extends StatelessWidget {
  const AdminModelDownloadButton({super.key, required this.controller});
  final AppController controller;

  @override
  Widget build(BuildContext context) {
    if (!controller.isAdmin) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        OutlinedButton.icon(
          onPressed:
              controller.isDownloadingOnnx ||
                  controller.isOnnxReady ||
                  controller.isDeletingBenchmarkResources ||
                  controller.isBenchmarking ||
                  controller.isModelLoading
              ? null
              : controller.downloadOnnx,
          icon: const Icon(Icons.download_rounded),
          label: Text(
            controller.isOnnxReady
                ? 'ONNX đã sẵn sàng'
                : controller.isDownloadingOnnx
                ? 'Đang tải ONNX…'
                : 'Tải / nạp ONNX để so sánh',
          ),
        ),
        if (controller.isDownloadingOnnx)
          LinearProgressIndicator(value: controller.onnxDownloadProgress),
        if (controller.onnxDownloadError != null)
          Text(
            controller.onnxDownloadError!,
            style: const TextStyle(color: Colors.red),
          ),
      ],
    );
  }
}
