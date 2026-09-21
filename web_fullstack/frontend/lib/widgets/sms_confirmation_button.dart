import 'package:flutter/material.dart';

class SmsConfirmationButton extends StatelessWidget {
  const SmsConfirmationButton({
    super.key,
    required this.recipient,
    required this.onConfirmed,
  });

  final String recipient;
  final Future<void> Function() onConfirmed;

  String get _maskedRecipient {
    if (recipient.length <= 4) return recipient;
    return '${'•' * (recipient.length - 4)}${recipient.substring(recipient.length - 4)}';
  }

  @override
  Widget build(BuildContext context) {
    return FilledButton.icon(
      onPressed: () async {
        final confirmed = await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('Xác nhận gửi SMS'),
            content: Text(
              'Gửi cảnh báo tới $_maskedRecipient? Nhà cung cấp SMS có thể tính phí cho tin nhắn này.',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: const Text('Chưa gửi'),
              ),
              FilledButton(
                onPressed: () => Navigator.pop(context, true),
                child: const Text('Xác nhận gửi SMS'),
              ),
            ],
          ),
        );
        if (confirmed == true) await onConfirmed();
      },
      icon: const Icon(Icons.sms_outlined),
      label: const Text('Gửi SMS khẩn cấp'),
    );
  }
}

