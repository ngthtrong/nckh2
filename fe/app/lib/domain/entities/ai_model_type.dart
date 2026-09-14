enum AiModelType {
  onnx(
    id: 'onnx',
    name: 'ONNX Runtime',
    extension: '.onnx',
    assetPath: 'assets/models/model.onnx',
    badgeText: 'ONNX (.onnx)',
    description: 'Chạy qua ONNX Runtime native, tối ưu hoá CPU thiết bị.',
  ),
  pte(
    id: 'pte',
    name: 'ExecuTorch Mobile',
    extension: '.pte',
    assetPath: 'assets/models/model.pte',
    badgeText: 'ExecuTorch (.pte)',
    description: 'Mô hình PyTorch Edge Native chuyên dụng cho thiết bị di động.',
  );

  final String id;
  final String name;
  final String extension;
  final String assetPath;
  final String badgeText;
  final String description;

  const AiModelType({
    required this.id,
    required this.name,
    required this.extension,
    required this.assetPath,
    required this.badgeText,
    required this.description,
  });
}

class ModelBenchmarkComparison {
  final AiModelType activeModel;
  final String labelOnnx;
  final double confOnnx;
  final int durationMsOnnx;

  final String labelPte;
  final double confPte;
  final int durationMsPte;

  final bool isIdentical;

  const ModelBenchmarkComparison({
    required this.activeModel,
    required this.labelOnnx,
    required this.confOnnx,
    required this.durationMsOnnx,
    required this.labelPte,
    required this.confPte,
    required this.durationMsPte,
    required this.isIdentical,
  });
}
