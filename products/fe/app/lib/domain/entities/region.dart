import 'emergency_number.dart';

class Region {
  final String label;
  final List<EmergencyNumber> numbers;
  final List<String> guides;

  const Region({
    required this.label,
    required this.numbers,
    required this.guides,
  });
}
