import 'package:app/domain/entities/ai_model_type.dart';
import 'package:app/presentation/widgets/ai_model_runtime_card.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets(
    'model settings card gives ListTile a visible Material ancestor',
    (tester) async {
      final errors = <FlutterErrorDetails>[];
      final previousHandler = FlutterError.onError;
      FlutterError.onError = errors.add;
      addTearDown(() => FlutterError.onError = previousHandler);

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AiModelRuntimeCard(
              currentModel: AiModelType.onnx,
              isPteReady: false,
              isDualComparison: false,
              onModelChanged: (_) {},
              onDualComparisonChanged: (_) {},
            ),
          ),
        ),
      );
      await tester.pump();

      expect(
        errors.where(
          (error) => error.exceptionAsString().contains(
            'ListTile background color or ink splashes may be invisible',
          ),
        ),
        isEmpty,
      );
    },
  );
}
