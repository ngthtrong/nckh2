import 'dart:io';
import 'package:flutter/services.dart';

const _lanChannel = MethodChannel('rescue/lan');

Future<List<String>> lanCandidates(int port) async {
  try {
    final networks = await _lanChannel.invokeListMethod<dynamic>(
      'getIpv4Networks',
    );
    if (networks != null) {
      final candidates = <String>{};
      for (final network in networks) {
        if (network is! Map<Object?, Object?>) continue;
        final address = network['address'];
        final prefixLength = network['prefixLength'];
        if (address is String && prefixLength is int) {
          candidates.addAll(
            lanCandidatesForSubnet(address, prefixLength, port),
          );
        }
      }
      if (candidates.isNotEmpty) return candidates.toList();
    }
  } on MissingPluginException {
    // Background isolates don't register this activity channel; keep the /24 fallback.
  } on PlatformException {
    // Keep the /24 fallback if Android cannot enumerate interfaces.
  }

  return _lanCandidatesForIpv4Interfaces(port);
}

List<String> lanCandidatesForSubnet(
  String address,
  int prefixLength,
  int port,
) {
  final octets = address.split('.').map(int.tryParse).toList();
  if (octets.length != 4 ||
      octets.any((octet) => octet == null || octet < 0 || octet > 255) ||
      port < 1 ||
      port > 65535 ||
      prefixLength < 1 ||
      prefixLength > 30) {
    return [];
  }

  final first = octets[0]!;
  final second = octets[1]!;
  if (first != 10 &&
      !(first == 172 && second >= 16 && second <= 31) &&
      !(first == 192 && second == 168)) {
    return [];
  }

  // shortcut: subnets wider than /20 scan only this device's /24 to cap probes.
  final scanPrefix = prefixLength < 20 ? 24 : prefixLength;
  final deviceAddress = octets.fold<int>(
    0,
    (value, octet) => (value << 8) | octet!,
  );
  final mask = (0xffffffff << (32 - scanPrefix)) & 0xffffffff;
  final network = deviceAddress & mask;
  final broadcast = network | (~mask & 0xffffffff);
  final device24 = deviceAddress & 0xffffff00;
  final sameSubnet = <int>[];
  final otherSubnets = <int>[];

  for (var candidate = network + 1; candidate < broadcast; candidate++) {
    if (candidate == deviceAddress) continue;
    if ((candidate & 0xffffff00) == device24) {
      sameSubnet.add(candidate);
    } else {
      otherSubnets.add(candidate);
    }
  }

  return [
    ...sameSubnet,
    ...otherSubnets,
  ].map((candidate) => 'http://${_ipv4(candidate)}:$port').toList();
}

String _ipv4(int value) =>
    '${(value >> 24) & 255}.${(value >> 16) & 255}.${(value >> 8) & 255}.${value & 255}';

Future<List<String>> _lanCandidatesForIpv4Interfaces(int port) async {
  final interfaces = await NetworkInterface.list(
    type: InternetAddressType.IPv4,
    includeLoopback: false,
  );
  final prefixes = <String>{};
  for (final interface in interfaces) {
    final name = interface.name.toLowerCase();
    if (!name.contains('wlan') &&
        !name.contains('wi-fi') &&
        !name.contains('wifi') &&
        !name.startsWith('eth') &&
        !name.startsWith('en')) {
      continue;
    }
    for (final address in interface.addresses) {
      final parts = address.address.split('.').map(int.tryParse).toList();
      if (parts.length != 4 || parts.any((part) => part == null)) continue;
      final a = parts[0]!, b = parts[1]!;
      if ((a == 10 ||
              (a == 172 && b >= 16 && b <= 31) ||
              (a == 192 && b == 168)) &&
          port >= 1 &&
          port <= 65535) {
        prefixes.add('${parts[0]}.${parts[1]}.${parts[2]}');
      }
    }
  }
  return [
    for (final prefix in prefixes)
      for (var host = 1; host <= 254; host++) 'http://$prefix.$host:$port',
  ];
}
