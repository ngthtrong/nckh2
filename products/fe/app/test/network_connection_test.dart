import 'package:app/data/datasources/network_remote_datasource.dart';
import 'package:app/data/repositories/network_repository_impl.dart';
import 'package:app/domain/entities/send_mode.dart';
import 'package:app/domain/services/adaptive_send_policy.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter_test/flutter_test.dart';

class _Connection extends NetworkRemoteDataSource {
  _Connection(this.type);
  final ConnectivityResult type;
  @override
  Future<String> currentTypeName() async => typeName([type]);
}

void main() {
  for (final type in ConnectivityResult.values) {
    test('$type is classified consistently for SOS delivery', () async {
      final dataSource = _Connection(type);
      final online = type != ConnectivityResult.none;
      expect(await dataSource.currentTypeName() != 'none', online);
      final decision = await AdaptiveSendPolicy(
        NetworkRepositoryImpl(dataSource),
      ).decide(hasImage: false, confidence: 0);
      expect(decision.mode, online ? SendMode.textOnly : SendMode.smsFallback);
    });
  }
  test('empty list is offline and mixed none/VPN remains online', () {
    final source = NetworkRemoteDataSource();
    expect(source.typeName([]), 'none');
    expect(
      source.typeName([ConnectivityResult.none, ConnectivityResult.vpn]),
      'VPN',
    );
  });
}
