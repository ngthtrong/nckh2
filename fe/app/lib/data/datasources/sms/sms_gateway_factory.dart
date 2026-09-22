import 'sms_gateway.dart';
import 'sms_gateway_native.dart'
    if (dart.library.js_interop) 'sms_gateway_web.dart'
    as platform;

SmsGateway createSmsGateway() => platform.createSmsGateway();
