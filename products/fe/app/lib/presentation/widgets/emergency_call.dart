import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

Future<void> openEmergencyDialer(BuildContext context, String number) async {
  final normalized = number.replaceAll(' ', '');
  try {
    if (await launchUrl(Uri(scheme: 'tel', path: normalized))) return;
  } catch (_) {
    // Keep the number visible even when no dialer is installed.
  }
  if (context.mounted) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Không mở được trình gọi. Hãy gọi trực tiếp $number.'),
      ),
    );
  }
}
