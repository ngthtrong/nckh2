package com.example.app

import android.os.Build
import android.telephony.SmsManager
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "rescue/sms")
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "sendSms" -> {
                        val to = call.argument<String>("to")!!
                        val body = call.argument<String>("body")!!
                        try {
                            val sm: SmsManager =
                                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S)
                                    getSystemService(SmsManager::class.java)
                                else
                                    @Suppress("DEPRECATION") SmsManager.getDefault()
                            // Tin nhắn >160 ký tự → gửi nhiều phần.
                            val parts = sm.divideMessage(body)
                            if (parts.size <= 1) {
                                sm.sendTextMessage(to, null, body, null, null)
                            } else {
                                sm.sendMultipartTextMessage(to, null, parts, null, null)
                            }
                            result.success(true)
                        } catch (e: Exception) {
                            result.error("sms_failed", e.message, null)
                        }
                    }
                    else -> result.notImplemented()
                }
            }
    }
}

