import 'package:connectivity_plus/connectivity_plus.dart';

abstract class NetworkRepository {
  Stream<List<ConnectivityResult>> get networkChanges;
  Future<String> getCurrentNetworkType();

  /// Throughput tới server (kbit/s) đo qua `GET /probe`; null khi không tới được server.
  Future<int?> probeThroughputKbps();
}
