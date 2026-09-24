class AiTag {
  final String label;
  final double confidence;

  const AiTag({
    required this.label,
    required this.confidence,
  });

  Map<String, dynamic> toJson() => {
        'label': label,
        'confidence': confidence,
      };

  factory AiTag.fromJson(Map<String, dynamic> json) => AiTag(
        label: json['label'] as String? ?? '',
        confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      );
}
