import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:permission_handler/permission_handler.dart';

import '../../../config.dart';
import 'sms_gateway.dart';

const _smsChannel = MethodChannel('rescue/sms');

SmsGateway createSmsGateway() => NativeSmsGateway();

class NativeSmsGateway implements SmsGateway {
  @override
  Future<SmsCapabilities> capabilities() async {
    final configured =
        kSmsRecipient.startsWith('+') && kSmsRecipient != '+840000000000';
    final available =
        defaultTargetPlatform == TargetPlatform.android && configured;
    return SmsCapabilities(
      available: available,
      recipient: configured ? kSmsRecipient : null,
      provider: 'android-sim',
      message: available
          ? null
          : 'SMS Android chưa có số nhận hợp lệ trong SMS_RECIPIENT.',
    );
  }

  @override
  Future<SmsSendResult> sendConfirmed({
    required String reportId,
    required String recipient,
    required String idempotencyKey,
  }) async {
    final permission = await Permission.sms.request();
    if (!permission.isGranted) {
      throw StateError('Quyền gửi SMS đã bị từ chối.');
    }
    final sent = await _smsChannel.invokeMethod<bool>('sendSms', {
      'to': recipient,
      'body': 'SOS Flood Rescue | report=$reportId',
    });
    if (sent != true) throw StateError('Thiết bị không xác nhận đã gửi SMS.');
    return const SmsSendResult(status: 'sent');
  }
}
