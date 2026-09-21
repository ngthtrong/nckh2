class InferenceResult {
  const InferenceResult({
    required this.label,
    required this.confidence,
    required this.probabilities,
    required this.durationMs,
    required this.executionProvider,
  });

  final String label;
  final double confidence;
  final List<double> probabilities;
  final double durationMs;
  final String executionProvider;
}

