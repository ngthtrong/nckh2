import 'package:connectivity_plus/connectivity_plus.dart';

class NetworkRemoteDataSource {
  final Connectivity _connectivity = Connectivity();

  Stream<List<ConnectivityResult>> get changes =>
      _connectivity.onConnectivityChanged;

  Future<String> currentTypeName() async {
    final results = await _connectivity.checkConnectivity();
    return typeName(results);
  }

  String typeName(List<ConnectivityResult> results) {
    if (results.contains(ConnectivityResult.wifi)) return 'WiFi';
    if (results.contains(ConnectivityResult.mobile)) return '4G/5G';
    return 'none';
  }
}
