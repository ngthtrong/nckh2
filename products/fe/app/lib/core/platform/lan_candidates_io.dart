import 'dart:io';

Future<List<String>> lanCandidates(int port) async {
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
      if (a == 10 ||
          (a == 172 && b >= 16 && b <= 31) ||
          (a == 192 && b == 168)) {
        prefixes.add('${parts[0]}.${parts[1]}.${parts[2]}');
      }
    }
  }
  // ponytail: /24 đủ cho mạng demo; mạng dùng subnet khác cần lấy netmask nền tảng.
  return [
    for (final prefix in prefixes)
      for (var host = 1; host <= 254; host++) 'http://$prefix.$host:$port',
  ];
}
