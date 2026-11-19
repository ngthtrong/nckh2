import 'package:app/config.dart';
import 'package:app/data/datasources/inference_local_datasource.dart';
import 'package:app/domain/entities/ai_model_type.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test(
    'user variant cannot activate ONNX even if comparison is requested',
    () async {
      final source = InferenceLocalDataSource();
      source.setComparisonAccess(true);
      source.setModel(AiModelType.onnx);
      source.setDualComparison(true);
      expect(source.currentModel, AiModelType.pte);
      expect(source.onnxReady, isFalse);
      expect(source.isDualComparison, isFalse);
      await expectLater(
        source.loadComparisonModel('unused.onnx'),
        throwsStateError,
      );
    },
    skip: kAdminModelTools,
  );
}
