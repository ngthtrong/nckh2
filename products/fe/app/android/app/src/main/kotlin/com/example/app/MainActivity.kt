package com.example.app

import android.app.Activity
import android.content.Intent
import android.os.Build
import android.telephony.SmsManager
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import org.pytorch.executorch.EValue
import org.pytorch.executorch.Module
import org.pytorch.executorch.Tensor
import java.net.Inet4Address
import java.net.NetworkInterface
import java.util.concurrent.Executors

class MainActivity : FlutterActivity() {
    private val pteExecutor = Executors.newSingleThreadExecutor()
    private var pteModule: Module? = null
    private val benchmarkExportExecutor = Executors.newSingleThreadExecutor()
    private var pendingBenchmarkExport: BenchmarkExport? = null

    private data class BenchmarkExport(val json: String, val result: MethodChannel.Result)

    private companion object {
        const val SAVE_BENCHMARK = 0x5248
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "rescue/lan")
            .setMethodCallHandler { call, result ->
                if (call.method == "getIpv4Networks") {
                    try {
                        result.success(localIpv4Networks())
                    } catch (error: Exception) {
                        result.error("lan_networks_failed", error.message, null)
                    }
                } else {
                    result.notImplemented()
                }
            }
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "rescue/benchmark_export")
            .setMethodCallHandler { call, result ->
                if (call.method == "saveJson") {
                    saveBenchmark(call.argument<String>("fileName"), call.argument<String>("json"), result)
                } else if (call.method == "getEnvironment") {
                    @Suppress("DEPRECATION")
                    val info = packageManager.getPackageInfo(packageName, 0)
                    result.success(mapOf(
                        "device" to mapOf(
                            "manufacturer" to Build.MANUFACTURER,
                            "model" to Build.MODEL,
                            "androidRelease" to Build.VERSION.RELEASE,
                            "androidSdk" to Build.VERSION.SDK_INT,
                            "supportedAbis" to Build.SUPPORTED_ABIS.toList(),
                        ),
                        "app" to mapOf(
                            "packageName" to packageName,
                            "versionName" to info.versionName,
                            "versionCode" to if (Build.VERSION.SDK_INT >= 28) info.longVersionCode else {
                                @Suppress("DEPRECATION")
                                info.versionCode.toLong()
                            },
                        ),
                    ))
                } else {
                    result.notImplemented()
                }
            }
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
                        if (input == null || input.size != 1 * 3 * 256 * 256) {
                            result.error("invalid_input", "Expected Float32[1,3,256,256]", null)
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
                                    longArrayOf(1, 3, 256, 256),
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

    private fun localIpv4Networks(): List<Map<String, Any>> {
        val result = mutableListOf<Map<String, Any>>()
        val interfaces = NetworkInterface.getNetworkInterfaces() ?: return result
        while (interfaces.hasMoreElements()) {
            val networkInterface = interfaces.nextElement()
            val name = networkInterface.name.lowercase()
            if (!networkInterface.isUp || networkInterface.isLoopback || networkInterface.isVirtual ||
                (!name.contains("wlan") && !name.contains("wi-fi") && !name.contains("wifi") &&
                    !name.startsWith("eth") && !name.startsWith("en"))
            ) continue

            for (interfaceAddress in networkInterface.interfaceAddresses) {
                val address = interfaceAddress.address
                val prefixLength = interfaceAddress.networkPrefixLength.toInt()
                if (address !is Inet4Address || !address.isSiteLocalAddress || prefixLength !in 1..30) continue
                result.add(mapOf("address" to address.hostAddress, "prefixLength" to prefixLength))
            }
        }
        return result
    }

    @Suppress("DEPRECATION")
    private fun saveBenchmark(fileName: String?, json: String?, result: MethodChannel.Result) {
        if (fileName == null || !fileName.matches(Regex("[A-Za-z0-9_.-]+\\.json")) || json.isNullOrEmpty()) {
            result.error("invalid_export", "Missing JSON or invalid file name", null)
            return
        }
        if (pendingBenchmarkExport != null) {
            result.error("export_busy", "A file export is already open", null)
            return
        }
        val pending = BenchmarkExport(json, result)
        pendingBenchmarkExport = pending
        try {
            val intent = Intent(Intent.ACTION_CREATE_DOCUMENT).apply {
                addCategory(Intent.CATEGORY_OPENABLE)
                type = "application/json"
                putExtra(Intent.EXTRA_TITLE, fileName)
            }
            startActivityForResult(intent, SAVE_BENCHMARK)
        } catch (error: Exception) {
            finishBenchmarkExport(pending, false, error)
        }
    }

    @Suppress("DEPRECATION")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != SAVE_BENCHMARK) return
        val pending = pendingBenchmarkExport ?: return
        if (resultCode != Activity.RESULT_OK) {
            finishBenchmarkExport(pending, false)
            return
        }
        val uri = data?.data
        if (uri == null) {
            finishBenchmarkExport(pending, false, IllegalStateException("No destination selected"))
            return
        }
        benchmarkExportExecutor.execute {
            try {
                val stream = contentResolver.openOutputStream(uri, "w")
                    ?: throw IllegalStateException("Cannot open destination")
                stream.use { it.write(pending.json.toByteArray(Charsets.UTF_8)) }
                runOnUiThread { finishBenchmarkExport(pending, true) }
            } catch (error: Exception) {
                runCatching { contentResolver.delete(uri, null, null) }
                runOnUiThread { finishBenchmarkExport(pending, false, error) }
            }
        }
    }

    private fun finishBenchmarkExport(pending: BenchmarkExport, saved: Boolean, error: Exception? = null) {
        if (pendingBenchmarkExport !== pending) return
        pendingBenchmarkExport = null
        if (error == null) pending.result.success(saved)
        else pending.result.error("export_failed", error.message, null)
    }

    override fun onDestroy() {
        pendingBenchmarkExport?.let { finishBenchmarkExport(it, false) }
        benchmarkExportExecutor.shutdown()
        pteModule?.close()
        pteExecutor.shutdownNow()
        super.onDestroy()
    }
}

