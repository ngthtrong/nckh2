import 'package:geolocator/geolocator.dart';
import 'package:permission_handler/permission_handler.dart';

import 'location_data_source.dart';

LocationDataSource createLocationDataSource() => NativeLocationDataSource();

class NativeLocationDataSource implements LocationDataSource {
  @override
  Future<LocationPoint> current() async {
    final permission = await Permission.locationWhenInUse.request();
    if (!permission.isGranted) {
      throw const LocationException('Quyền truy cập vị trí đã bị từ chối.');
    }

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
    } catch (error) {
      throw LocationException('Không thể lấy vị trí hiện tại: $error');
    }
  }
}
