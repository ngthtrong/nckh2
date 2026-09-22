import 'location_data_source.dart';
import 'location_native_data_source.dart'
    if (dart.library.js_interop) 'location_web_data_source.dart'
    as platform;

LocationDataSource createLocationDataSource() =>
    platform.createLocationDataSource();
