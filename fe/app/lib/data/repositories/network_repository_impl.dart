import 'package:connectivity_plus/connectivity_plus.dart';

import '../../domain/repositories/network_repository.dart';
import '../datasources/network_remote_datasource.dart';

class NetworkRepositoryImpl implements NetworkRepository {
  final NetworkRemoteDataSource dataSource;

  NetworkRepositoryImpl(this.dataSource);

  @override
  Stream<List<ConnectivityResult>> get networkChanges => dataSource.changes;

  @override
  Future<String> getCurrentNetworkType() {
    return dataSource.currentTypeName();
  }
}
