# Flood Rescue Web Frontend and Browser AI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây dựng Flutter Web/PWA độc lập chạy AI ONNX thật trong Chrome, lưu offline và đồng bộ báo cáo với backend.

**Architecture:** Flutter Web quản lý UI/domain và IndexedDB; JavaScript bridge chỉ đảm nhiệm ONNX Runtime Web và preprocessing pixel. Model được xuất từ checkpoint thật, kiểm tra parity, rồi đóng gói cùng PWA; WebGPU là ưu tiên và WASM là fallback.

**Tech Stack:** Flutter Web, Dart 3, `image_picker`, `geolocator`, `dio`, `hive_ce`, ONNX Runtime Web, PyTorch/ONNX/ONNX Runtime (công cụ xuất model), flutter_test, pytest.

**Spec:** `web_fullstack/DESIGN.md`

## Global Constraints

- Mọi file mới thuộc `web_fullstack/`; không sửa `fe/app`.
- Frontend không chứa khóa Twilio hay secret backend.
- Inference dùng model thật; không mock, no-op hoặc sinh kết quả giả trong runtime production.
- Nhãn theo đúng thứ tự `low`, `medium`, `high`, `non_flood`; input `1x3x224x224`, letterbox RGB và ImageNet mean/std.
- WebGPU lỗi phải tự chuyển sang WebAssembly.
- Báo cáo luôn được lưu offline trước khi thử đồng bộ.

---

### Task 1: Exportable ONNX artifact and parity verification

**Files:**
- Create: `web_fullstack/model_tools/pyproject.toml`
- Create: `web_fullstack/model_tools/export_model.py`
- Create: `web_fullstack/model_tools/test_export_model.py`
- Create: `web_fullstack/model_tools/model_config.json`
- Create: `web_fullstack/scripts/export_web_model.ps1`

**Interfaces:**
- Consumes: `fe/app/model.pth` read-only.
- Produces: `web_fullstack/frontend/web/models/flood_mobilenetv3_large.onnx`.
- Produces: `web_fullstack/frontend/web/models/model_manifest.json` with `version`, `onnx_sha256`, `checkpoint_sha256`, `input_size`, `class_order`, `mean`, `std`, `letterbox_fill`.

- [ ] **Step 1: Write failing unit tests for checkpoint normalization and manifest**

```python
def test_remove_module_prefix():
    state = {"module.features.0.0.weight": torch.zeros(1)}
    assert list(remove_module_prefix(state)) == ["features.0.0.weight"]

def test_manifest_has_runtime_contract(tmp_path):
    manifest = build_manifest(tmp_path / "model.pth", tmp_path / "model.onnx")
    assert manifest["class_order"] == ["low", "medium", "high", "non_flood"]
    assert manifest["input_size"] == 224
    assert manifest["mean"] == [0.485, 0.456, 0.406]
    assert manifest["std"] == [0.229, 0.224, 0.225]
```

- [ ] **Step 2: Run tests and verify missing module failure**

Run: `cd web_fullstack/model_tools && python -m pytest -v`

Expected: FAIL because `export_model` does not exist.

- [ ] **Step 3: Implement model construction and export**

Build `torchvision.models.mobilenet_v3_large(weights=None)` and replace its final classifier exactly as the existing training code: preserve preceding classifier layers, then append `Dropout(0.35)` and `Linear(in_features, 4)`. Load `model_state_dict`, `state_dict`, `model`, or a raw tensor dictionary; remove `module.` prefixes; require zero missing/unexpected keys; wrap logits with `softmax(dim=1)`; export opset 17 with names `image` and `probabilities`.

- [ ] **Step 4: Implement parity check and manifest generation**

Create a deterministic RGB gradient image, preprocess with `ImageOps.pad(..., color=(124,116,104), method=BICUBIC)`, tensor conversion and ImageNet normalization. Compare PyTorch and ONNX Runtime arrays with `numpy.testing.assert_allclose(rtol=1e-4, atol=1e-5)`, require the same argmax, run `onnx.checker.check_model`, and only then copy artifacts to the frontend model directory.

- [ ] **Step 5: Run export and parity tests**

Run: `powershell -ExecutionPolicy Bypass -File web_fullstack/scripts/export_web_model.ps1`

Expected: ONNX and manifest exist, checker passes, parity passes, hashes are printed.

- [ ] **Step 6: Commit source and manifest; handle binary according to repository size policy**

```powershell
git add web_fullstack/model_tools web_fullstack/scripts/export_web_model.ps1 web_fullstack/frontend/web/models/model_manifest.json
git commit -m "feat(web): export browser ONNX model with parity checks"
```

### Task 2: Flutter Web project and domain contracts

**Files:**
- Create: `web_fullstack/frontend/` via `flutter create --platforms=web`
- Create: `web_fullstack/frontend/lib/domain/report.dart`
- Create: `web_fullstack/frontend/lib/domain/inference_result.dart`
- Create: `web_fullstack/frontend/lib/config/app_config.dart`
- Create: `web_fullstack/frontend/test/domain/report_test.dart`
- Modify: `web_fullstack/frontend/pubspec.yaml`

**Interfaces:**
- Produces: immutable `RescueReport` with JSON/IndexedDB serialization.
- Produces: `InferenceResult(label, confidence, probabilities, durationMs, executionProvider)`.
- Produces: `AppConfig.apiBaseUrl` from `--dart-define=API_BASE_URL`, default `http://127.0.0.1:8000`.

- [ ] **Step 1: Scaffold project and add dependencies**

Use dependencies `dio`, `geolocator`, `image_picker`, `hive_ce`, `hive_ce_flutter`, `uuid`, `image`, and `web`. Do not add `onnxruntime`, `dart:io`, `path_provider`, `permission_handler` or `workmanager`.

- [ ] **Step 2: Write failing serialization tests**

```dart
test('report preserves image bytes and pending state', () {
  final report = RescueReport.draft(id: 'r1', imageBytes: Uint8List.fromList([1, 2, 3]));
  final restored = RescueReport.fromMap(report.toMap());
  expect(restored.id, 'r1');
  expect(restored.imageBytes, [1, 2, 3]);
  expect(restored.syncState, SyncState.pending);
});
```

- [ ] **Step 3: Run test and verify missing domain type**

Run: `cd web_fullstack/frontend && flutter test test/domain/report_test.dart`

Expected: FAIL because `RescueReport` is undefined.

- [ ] **Step 4: Implement domain and config types**

Include report fields from the backend contract plus `imageName`, `imageMimeType`, `syncState`, `syncError`, and optional SMS status. Serialization must use primitive values supported by Hive Web and preserve `Uint8List`.

- [ ] **Step 5: Run focused test**

Run: `cd web_fullstack/frontend && flutter test test/domain/report_test.dart`

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add web_fullstack/frontend
git commit -m "feat(web): scaffold standalone Flutter frontend"
```

### Task 3: Browser ONNX bridge with WebGPU-to-WASM fallback

**Files:**
- Create: `web_fullstack/frontend/web/onnx_bridge.js`
- Create: `web_fullstack/frontend/lib/services/web_inference_service.dart`
- Create: `web_fullstack/frontend/lib/services/inference_contract.dart`
- Create: `web_fullstack/frontend/test/services/web_inference_service_test.dart`
- Modify: `web_fullstack/frontend/web/index.html`
- Modify: `web_fullstack/frontend/pubspec.yaml`

**Interfaces:**
- Produces JS: `window.floodAi.initialize(modelUrl, manifestUrl) -> Promise<object>`.
- Produces JS: `window.floodAi.predict(imageBytes) -> Promise<object>`.
- Produces Dart: `Future<void> initialize()` and `Future<InferenceResult> analyze(Uint8List bytes)`.

- [ ] **Step 1: Write failing Dart adapter tests with a fake bridge**

```dart
test('maps real bridge response to inference result', () async {
  final service = WebInferenceService.withBridge(FakeBridge({
    'label': 'high',
    'confidence': 0.91,
    'probabilities': [0.01, 0.03, 0.91, 0.05],
    'durationMs': 18.0,
    'executionProvider': 'webgpu',
  }));
  final result = await service.analyze(Uint8List.fromList([1]));
  expect(result.label, 'high');
  expect(result.executionProvider, 'webgpu');
});
```

- [ ] **Step 2: Run test and verify bridge types are missing**

Run: `cd web_fullstack/frontend && flutter test test/services/web_inference_service_test.dart`

Expected: FAIL.

- [ ] **Step 3: Implement JavaScript runtime**

Load the local `ort.min.js`. Decode image bytes with `createImageBitmap`, draw letterboxed to `OffscreenCanvas(224,224)` using fill `[124,116,104]`, extract RGBA, build NCHW Float32 RGB values using manifest mean/std, and call `session.run({image: tensor})`. Initialization first calls `InferenceSession.create(modelUrl, {executionProviders:['webgpu']})`; on any exception it records the failure and retries once with `['wasm']`. Return the actual provider and probability vector; never synthesize a prediction.

- [ ] **Step 4: Implement typed Dart JS interop and error mapping**

Use `dart:js_interop` and `dart:js_interop_unsafe` only in the web project. Validate four finite probabilities, label order from manifest and confidence bounds. Expose initialization/download failures as user-readable `InferenceException` values.

- [ ] **Step 5: Run adapter tests and browser smoke test**

Run: `cd web_fullstack/frontend && flutter test test/services/web_inference_service_test.dart`

Run: `cd web_fullstack/frontend && flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8000`

Expected: browser console reports `webgpu` or `wasm`; one selected image returns four real probabilities.

- [ ] **Step 6: Commit**

```powershell
git add web_fullstack/frontend
git commit -m "feat(web): run ONNX inference inside Chrome"
```

### Task 4: Offline report store, API client and synchronization

**Files:**
- Create: `web_fullstack/frontend/lib/services/offline_report_store.dart`
- Create: `web_fullstack/frontend/lib/services/report_api_client.dart`
- Create: `web_fullstack/frontend/lib/services/sync_coordinator.dart`
- Create: `web_fullstack/frontend/lib/services/send_mode_selector.dart`
- Create: `web_fullstack/frontend/test/services/offline_report_store_test.dart`
- Create: `web_fullstack/frontend/test/services/send_mode_selector_test.dart`
- Create: `web_fullstack/frontend/test/services/sync_coordinator_test.dart`

**Interfaces:**
- Produces: `OfflineReportStore.save`, `watchAll`, `pending`, `markSynced`, `markFailed`.
- Produces: `ReportApiClient.createReport`, `listReports`, `capabilities`, `requestSms`.
- Produces: `SyncCoordinator.syncPending()` with one in-flight run and report-ID idempotency.

- [ ] **Step 1: Write failing queue and mode-selection tests**

```dart
test('failed upload stays pending with an error', () async {
  final store = MemoryReportStore([pendingReport]);
  final sync = SyncCoordinator(store: store, api: ThrowingReportApi());
  await sync.syncPending();
  expect((await store.get('r1'))!.syncState, SyncState.pending);
  expect((await store.get('r1'))!.syncError, isNotEmpty);
});

test('slow network chooses compressed image', () {
  expect(selectSendMode(bytesPerSecond: 30 * 1024, hasImage: true), SendMode.compressed);
});
```

- [ ] **Step 2: Run tests and verify missing services**

Run: `cd web_fullstack/frontend && flutter test test/services`

Expected: FAIL.

- [ ] **Step 3: Implement IndexedDB-backed store and multipart client**

Initialize Hive Web box `rescue_reports_v1`; always persist before calling the API. Upload exact backend fields and image bytes. Measure `/probe` elapsed time; use original at at least 256 KiB/s, JPEG-compressed at 32–256 KiB/s, and text-only below 32 KiB/s or when no image. Keep original bytes in local history regardless of upload mode.

- [ ] **Step 4: Implement synchronization triggers**

Call `syncPending` at app startup, after a new save and on browser `online`. Guard concurrent runs with a stored future. Process oldest first, continue after individual failures, and mark synced only after 200/201 response with matching report ID.

- [ ] **Step 5: Run service tests**

Run: `cd web_fullstack/frontend && flutter test test/services`

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add web_fullstack/frontend
git commit -m "feat(web): add offline-first report synchronization"
```

### Task 5: Responsive rescue UI, location, image capture and explicit SMS confirmation

**Files:**
- Create: `web_fullstack/frontend/lib/main.dart`
- Create: `web_fullstack/frontend/lib/app.dart`
- Create: `web_fullstack/frontend/lib/controllers/rescue_controller.dart`
- Create: `web_fullstack/frontend/lib/screens/home_screen.dart`
- Create: `web_fullstack/frontend/lib/screens/compose_screen.dart`
- Create: `web_fullstack/frontend/lib/screens/history_screen.dart`
- Create: `web_fullstack/frontend/lib/widgets/capability_strip.dart`
- Create: `web_fullstack/frontend/lib/widgets/inference_card.dart`
- Create: `web_fullstack/frontend/test/widgets/compose_screen_test.dart`
- Create: `web_fullstack/frontend/test/widgets/sms_confirmation_test.dart`

**Interfaces:**
- Consumes all services from Tasks 3–4.
- Produces complete user flow: capture/select → inference → location → local save → sync → history → confirmed SMS request.

- [ ] **Step 1: Write failing widget tests**

```dart
testWidgets('SMS is not requested before final confirmation', (tester) async {
  final sms = FakeSmsRequestService();
  await tester.pumpWidget(testApp(sms: sms, report: syncedReport));
  await tester.tap(find.text('Gửi SMS khẩn cấp'));
  await tester.pumpAndSettle();
  expect(sms.calls, isEmpty);
  await tester.tap(find.text('Xác nhận gửi SMS'));
  await tester.pumpAndSettle();
  expect(sms.calls, hasLength(1));
});
```

- [ ] **Step 2: Run widget tests and verify screens are absent**

Run: `cd web_fullstack/frontend && flutter test test/widgets`

Expected: FAIL.

- [ ] **Step 3: Implement UI and controller state**

Use a responsive max-width shell with emergency red `#C62828`, high-contrast status cards, keyboard-accessible controls and Vietnamese copy. Compose accepts camera/gallery bytes, counts, vulnerable groups, description and GPS. Show model loading/progress/error and exact AI label/confidence/provider. Never enable submit with no meaningful content.

- [ ] **Step 4: Implement SMS confirmation and capability states**

Only show the SMS action for a saved report. First fetch capabilities; when SMS is disabled show the names of missing environment variables without exposing values. Confirmation displays the target number masked except final four digits and states that provider fees may apply. Generate a fresh UUID idempotency key once per user-confirmed attempt.

- [ ] **Step 5: Run widget and full Flutter tests**

Run: `cd web_fullstack/frontend && flutter test`

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add web_fullstack/frontend
git commit -m "feat(web): add full rescue reporting interface"
```

### Task 6: PWA caching, integrated scripts and project documentation

**Files:**
- Modify: `web_fullstack/frontend/web/manifest.json`
- Modify: `web_fullstack/frontend/web/index.html`
- Create: `web_fullstack/scripts/run_frontend.ps1`
- Create: `web_fullstack/scripts/run_all.ps1`
- Create: `web_fullstack/scripts/verify.ps1`
- Create: `web_fullstack/README.md`
- Modify: `web_fullstack/frontend/README.md`

**Interfaces:**
- Produces: frontend at `http://localhost:8080`, backend at `http://127.0.0.1:8000`.

- [ ] **Step 1: Configure installable PWA metadata and local runtime assets**

Set Vietnamese app name, emergency-red theme/background colors and icons. Bundle ONNX Runtime JS/WASM locally under `web/vendor/ort`; do not load a CDN. Ensure the release build contains model, manifest, JS and WASM files so Flutter's generated service worker includes them in its asset manifest.

- [ ] **Step 2: Add run and verification scripts**

`run_frontend.ps1` prepares local ONNX Runtime assets and runs Chrome on port 8080. `run_all.ps1` starts the backend hidden, waits for `/health`, then starts frontend. `verify.ps1` runs model-tool tests, backend tests, Flutter tests, `flutter analyze`, `flutter build web --release`, verifies expected files in `build/web`, and checks `git diff --exit-code -- fe/app` relative to the baseline commit recorded before execution.

- [ ] **Step 3: Document every added component and key**

`web_fullstack/README.md` must contain: folder map and purpose; prerequisites; exact run commands; model export command; `.env` setup; SMS cost boundary; key names; offline limitations; Chrome camera/GPS permission notes; verification command; assurance that `fe/app` remains the Android source.

- [ ] **Step 4: Execute release verification**

Run: `powershell -ExecutionPolicy Bypass -File web_fullstack/scripts/verify.ps1`

Expected: model/backend/Flutter tests PASS, analyze has no errors, web release build succeeds, runtime/model files exist, and Android source diff check is clean.

- [ ] **Step 5: Manual localhost acceptance**

Run: `powershell -ExecutionPolicy Bypass -File web_fullstack/scripts/run_all.ps1`

Expected: Chrome opens `http://localhost:8080`; an image produces real ONNX probabilities; a report appears in history and backend; disabling the backend leaves it pending; reconnecting syncs it; SMS disabled shows configuration guidance and never calls a provider.

- [ ] **Step 6: Commit**

```powershell
git add web_fullstack
git commit -m "docs(web): document and verify standalone full-stack app"
```
