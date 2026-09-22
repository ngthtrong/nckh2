import 'package:flutter/material.dart';

Future<bool> showSmsConfirmation(
  BuildContext context, {
  required String recipient,
}) async {
  final maskedRecipient = recipient.length <= 4
      ? recipient
      : '${'•' * (recipient.length - 4)}${recipient.substring(recipient.length - 4)}';

  return await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Xác nhận gửi SMS'),
          content: Text(
            'Gửi cảnh báo tới $maskedRecipient? Nhà cung cấp SMS có thể tính phí cho tin nhắn này.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Chỉ gửi báo cáo'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Gửi báo cáo + SMS'),
            ),
          ],
        ),
      ) ??
      false;
}
