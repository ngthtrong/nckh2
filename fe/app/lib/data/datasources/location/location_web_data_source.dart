import 'package:geolocator/geolocator.dart';

import 'location_data_source.dart';

LocationDataSource createLocationDataSource() => WebLocationDataSource();

class WebLocationDataSource implements LocationDataSource {
  @override
  Future<LocationPoint> current() async {
    try {
      final position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: Duration(seconds: 5),
        ),
      );
      return LocationPoint(
        latitude: position.latitude,
        longitude: position.longitude,
      );
    } on PermissionDeniedException {
      throw const LocationException('Chrome đã từ chối quyền truy cập vị trí.');
    } catch (error) {
      throw LocationException('Không thể lấy vị trí trên trình duyệt: $error');
    }
  }
}
