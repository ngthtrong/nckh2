class LocationPoint {
  const LocationPoint({required this.latitude, required this.longitude});

  final double latitude;
  final double longitude;
}

abstract interface class LocationDataSource {
  Future<LocationPoint> current();
}

class LocationException implements Exception {
  const LocationException(this.message);

  final String message;

  @override
  String toString() => message;
}
