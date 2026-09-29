import 'dart:convert';

import 'package:app/domain/services/urgency_logistic_model.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('bundled urgency artifact scores all 32 feature profiles', () async {
    final artifact =
        jsonDecode(
              await rootBundle.loadString(
                'assets/models/urgency_logistic.json',
              ),
            )
            as Map<String, dynamic>;
    final model = UrgencyLogisticModel.fromJson(artifact);
    final features = (artifact['feature_order'] as List).cast<String>();
    final threshold = (artifact['threshold'] as num).toDouble();

    for (var mask = 0; mask < 1 << features.length; mask++) {
      final signs = [
        for (var i = 0; i < features.length; i++)
          if (mask & (1 << i) != 0) features[i],
      ];
      final score = model.score(signs);
      expect(score, inInclusiveRange(0.0, 1.0));
      expect(score >= threshold, mask != 0, reason: 'profile $mask');
    }

    expect(
      model.score(const []),
      closeTo((artifact['negative_probability'] as num).toDouble(), 1e-12),
    );
    expect(
      model.score(const ['seizure']),
      closeTo(model.score(const ['active_convulsions']), 1e-12),
    );
  });
}
