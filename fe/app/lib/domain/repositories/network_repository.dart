import 'package:connectivity_plus/connectivity_plus.dart';

abstract class NetworkRepository {
  Stream<List<ConnectivityResult>> get networkChanges;
  Future<String> getCurrentNetworkType();
}
