import '../../domain/entities/rescue_record.dart';

Map<String, dynamic> rescueRecordPayload(RescueRecord record) => {
  'id': record.id,
  'createdAt': record.createdAt.toUtc().toIso8601String(),
  'lat': record.lat,
  'lng': record.lng,
  'trappedCount': record.trappedCount,
  'injuredCount': record.injuredCount,
  'vulnerableGroups': record.vulnerableGroups,
  'description': record.description,
  'aiTags': record.aiTags.map((tag) => tag.toJson()).toList(),
  'sendMode': record.sendMode,
  'L_i': {'lat': record.lat, 'lon': record.lng},
  'T_i': record.createdAt.toUtc().toIso8601String(),
  'N_i': record.trappedCount,
  'injury_count': record.injuredCount,
  'urgency_features': {
    'cannot_move': record.cannotMove,
    'severe_condition': record.severeCondition,
    'severe_signs': record.severeSigns.map(canonicalSevereSign).toList(),
  },
  'E_i': record.urgencyScore,
  'vulnerability_flags': record.vulnerableGroups,
  'V_i': record.vulnerableGroups.length,
  'note': record.description.isEmpty ? null : record.description,
  'image_attached': record.imagePath != null,
};
