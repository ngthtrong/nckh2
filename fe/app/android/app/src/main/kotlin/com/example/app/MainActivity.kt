package com.example.app

import android.os.Build
import android.telephony.SmsManager
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import org.pytorch.executorch.EValue
import org.pytorch.executorch.Module
import org.pytorch.executorch.Tensor
import java.util.concurrent.Executors

class MainActivity : FlutterActivity() {
    private val pteExecutor = Executors.newSingleThreadExecutor()
    private var pteModule: Module? = null

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

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "rescue/executorch")
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "load" -> {
                        val modelPath = call.argument<String>("modelPath")
                        if (modelPath == null) {
                            result.error("invalid_path", "Missing PTE model path", null)
                            return@setMethodCallHandler
                        }
                        pteExecutor.execute {
                            try {
                                pteModule?.close()
                                pteModule = Module.load(modelPath)
                                runOnUiThread { result.success(true) }
                            } catch (error: Exception) {
                                runOnUiThread {
                                    result.error("pte_load_failed", error.message, null)
                                }
                            }
                        }
                    }
                    "forward" -> {
                        val input = call.argument<FloatArray>("input")
                        val module = pteModule
                        if (input == null || input.size != 1 * 3 * 224 * 224) {
                            result.error("invalid_input", "Expected Float32[1,3,224,224]", null)
                            return@setMethodCallHandler
                        }
                        if (module == null) {
                            result.error("pte_not_loaded", "PTE model is not loaded", null)
                            return@setMethodCallHandler
                        }
                        pteExecutor.execute {
                            try {
                                val tensor = Tensor.fromBlob(
                                    input,
                                    longArrayOf(1, 3, 224, 224),
                                )
                                val output = module.forward(EValue.from(tensor))[0]
                                    .toTensor()
                                    .dataAsFloatArray
                                    .map { it.toDouble() }
                                runOnUiThread { result.success(output) }
                            } catch (error: Exception) {
                                runOnUiThread {
                                    result.error("pte_forward_failed", error.message, null)
                                }
                            }
                        }
                    }
                    else -> result.notImplemented()
                }
            }
    }

    override fun onDestroy() {
        pteModule?.close()
        pteExecutor.shutdownNow()
        super.onDestroy()
    }
}

