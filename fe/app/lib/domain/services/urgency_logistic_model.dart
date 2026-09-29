import 'dart:math' as math;

import '../entities/rescue_record.dart';

class UrgencyLogisticModel {
  static const _features = {
    'unresponsive',
    'respiratory_distress_or_cyanosis',
    'heavy_bleeding',
    'active_convulsions',
    'high_risk_trauma',
  };

  final List<String> featureOrder;
  final Map<String, double> coefficients;
  final double intercept;

  UrgencyLogisticModel._(this.featureOrder, this.coefficients, this.intercept);

  factory UrgencyLogisticModel.fromJson(Map<String, dynamic> json) {
    if (json['schema_version'] != '1.0' ||
        json['model_type'] != 'logistic_regression') {
      throw const FormatException('Unsupported urgency model');
    }
    final order = (json['feature_order'] as List).cast<String>();
    if (order.length != _features.length ||
        order.toSet().length != _features.length ||
        !order.toSet().containsAll(_features)) {
      throw const FormatException('Unexpected urgency features');
    }
    final rawCoefficients = json['coefficients'] as Map<String, dynamic>;
    final coefficients = {
      for (final feature in order)
        feature: (rawCoefficients[feature] as num).toDouble(),
    };
    final intercept = (json['intercept'] as num).toDouble();
    if (!intercept.isFinite ||
        coefficients.values.any((value) => !value.isFinite)) {
      throw const FormatException('Non-finite urgency coefficients');
    }
    return UrgencyLogisticModel._(order, coefficients, intercept);
  }

  double score(Iterable<String> severeSigns) {
    final selected = severeSigns.map(canonicalSevereSign).toSet();
    var logit = intercept;
    for (final feature in featureOrder) {
      if (selected.contains(feature)) logit += coefficients[feature]!;
    }
    return 1 / (1 + math.exp(-logit));
  }
}
