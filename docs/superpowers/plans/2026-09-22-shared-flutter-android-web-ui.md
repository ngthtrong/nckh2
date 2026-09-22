# Shared Flutter Android/Web UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `fe/app` the only Flutter UI source and run that exact interface on Android and Chrome with real platform-specific AI, storage, location, synchronization, upload, and SMS implementations.

**Architecture:** Keep `presentation`, domain entities, repository contracts, use cases, and controller behavior shared. Move every native/browser dependency behind small interfaces selected with Dart conditional imports, then migrate the proven ONNX Web, IndexedDB, browser-event, and backend integrations out of `web_fullstack/frontend` into `fe/app`.

**Tech Stack:** Flutter 3.47.5, Dart 3.13.4, Android Gradle Plugin 9.0.1, Kotlin 2.3.20, ONNX Runtime native 1.4.1, ONNX Runtime Web, Hive CE, Dio, FastAPI, pytest.

**Spec:** `docs/superpowers/specs/2026-09-22-shared-flutter-android-web-ui-design.md`

## Global Constraints

- `fe/app/lib/presentation/` remains the single UI source for Android and Chrome.
- Do not introduce a second web-only screen tree or controller.
- Do not mock or silently no-op platform features; use real adapters and report unavailable capabilities explicitly.
- Do not import `dart:io`, `dart:ffi`, WorkManager, MethodChannel, or browser JS APIs from shared presentation/domain code.
- Android keeps ONNX FFI, ExecuTorch PTE, WorkManager, native permissions, and native SMS support.
- Chrome uses ONNX Runtime Web, IndexedDB-backed Hive, browser online events, browser permissions, and the FastAPI SMS endpoint.
- PTE is reported as Android-only until a real browser PTE runtime exists; it must not be simulated with ONNX.
- Preserve the existing theme, navigation, labels, screens, and widget layout.
- SMS remains disabled unless the backend advertises the capability and the user confirms the send action.
- Do not delete `web_fullstack/frontend` until Android and web parity checks pass from `fe/app`.

---

## Planned File Structure

```text
fe/app/lib/
├── main.dart
├── domain/entities/rescue_image.dart
├── data/datasources/
│   ├── inference/inference_data_source.dart
│   ├── inference/inference_data_source_factory.dart
│   ├── inference/inference_native_data_source.dart
│   ├── inference/inference_web_data_source.dart
│   ├── inference/web_inference_bridge.dart
│   ├── inference/web_inference_bridge_stub.dart
│   ├── inference/web_inference_bridge_web.dart
│   ├── location/location_data_source.dart
│   ├── location/location_data_source_factory.dart
│   ├── location/location_native_data_source.dart
│   ├── location/location_web_data_source.dart
│   ├── sync/platform_sync.dart
│   ├── sync/platform_sync_factory.dart
│   ├── sync/platform_sync_native.dart
│   ├── sync/platform_sync_web.dart
│   ├── image/image_compressor.dart
│   ├── image/image_compressor_factory.dart
│   ├── image/image_compressor_native.dart
│   └── image/image_compressor_web.dart
├── data/datasources/record_local_datasource.dart
├── data/datasources/sender_remote_datasource.dart
├── data/repositories/inference_repository_impl.dart
├── data/repositories/rescue_repository_impl.dart
└── presentation/                         # existing shared UI, no fork

fe/app/web/
├── onnx_bridge.js
├── models/model.onnx
├── models/model_manifest.json
└── vendor/ort/*

fe/app/assets/models/
├── model.onnx
├── model.pte
└── model_manifest.json
```

---

### Task 1: Restore a Passing Android Baseline

**Files:**
- Create: `fe/app/test/assets/model_assets_test.dart`
- Create: `fe/app/assets/models/model.onnx` from `web_fullstack/frontend/web/models/flood_mobilenetv3_large.onnx`
- Create: `fe/app/assets/models/model.pte` from `fe/model/Edge Ai/flood_mobilenetv3_large.pte`
- Create: `fe/app/assets/models/model_manifest.json` from `web_fullstack/frontend/web/models/model_manifest.json`
- Modify: `fe/app/android/gradle.properties`
- Modify: `fe/app/lib/presentation/screens/compose/compose_screen.dart`
- Modify: `fe/app/lib/presentation/screens/guide/guide_screen.dart`
- Modify: `fe/app/lib/presentation/widgets/compose_cta_card.dart`
- Modify: `fe/app/lib/presentation/widgets/screen_header.dart`
- Modify: `fe/app/lib/presentation/widgets/sos_button.dart`

**Interfaces:**
- Consumes: the existing asset paths used by `InferenceLocalDataSource`.
- Produces: three non-empty bundled model assets and an Android build that does not use Kotlin incremental caches.

- [ ] **Step 1: Write the failing model asset test**

```dart
import 'dart:convert';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('bundles the ONNX, PTE and manifest assets', () async {
    for (final path in const [
      'assets/models/model.onnx',
      'assets/models/model.pte',
      'assets/models/model_manifest.json',
    ]) {
      final data = await rootBundle.load(path);
      expect(data.lengthInBytes, greaterThan(0), reason: path);
    }
    final manifest = jsonDecode(
      await rootBundle.loadString('assets/models/model_manifest.json'),
    ) as Map<String, dynamic>;
    expect(manifest['input_size'], 224);
    expect(manifest['class_order'], ['low', 'medium', 'high', 'non_flood']);
  });
}
```

- [ ] **Step 2: Run the test and verify the missing-asset failure**

Run: `cd fe/app; flutter test test/assets/model_assets_test.dart`

Expected: FAIL because `assets/models/` does not exist.

- [ ] **Step 3: Restore the model assets and Kotlin workaround**

Copy the three real files to the exact target names above. Add this line after the Gradle daemon settings:

```properties
kotlin.incremental=false
```

- [ ] **Step 4: Fix the five existing analyzer findings without changing layout**

Replace deprecated `withOpacity(x)` calls with `withValues(alpha: x)`, remove the unnecessary `.toList()` inside the spread in `guide_screen.dart`, and use a null-aware collection element in `screen_header.dart`.

- [ ] **Step 5: Verify Android baseline**

Run:

```powershell
cd fe/app
flutter analyze
flutter test
flutter build apk --debug
```

Expected: analyzer has no issues, all tests pass, and `build/app/outputs/flutter-apk/app-debug.apk` exists.

- [ ] **Step 6: Commit the baseline**

```powershell
git add fe/app/android/gradle.properties fe/app/assets/models fe/app/test/assets fe/app/lib/presentation
git commit -m "fix: restore Android build baseline"
```

---

### Task 2: Replace File Paths with a Platform-Neutral Image Value

**Files:**
- Create: `fe/app/lib/domain/entities/rescue_image.dart`
- Create: `fe/app/test/domain/rescue_image_test.dart`
- Modify: `fe/app/lib/domain/entities/rescue_record.dart`
- Modify: `fe/app/lib/data/datasources/record_local_datasource.dart`
- Modify: `fe/app/lib/data/repositories/rescue_repository_impl.dart`
- Modify: `fe/app/lib/presentation/controllers/app_controller.dart`
- Modify: `fe/app/lib/presentation/screens/compose/compose_screen.dart`
- Modify: `fe/app/lib/presentation/widgets/post_card.dart`
- Modify: `fe/app/lib/domain/usecases/submit_rescue_post_usecase.dart`

**Interfaces:**
- Produces: `RescueImage({required Uint8List bytes, required String fileName, required String mimeType})` with `toMap()` and `RescueImage.fromMap(Map<dynamic, dynamic>)`.
- Produces: `AppController.pickImage()` returning `Future<RescueImage?>` and `analyzeImage(RescueImage image)` reading `image.bytes`.
- Consumes later: sender, inference, Hive, preview widgets.

- [ ] **Step 1: Write failing round-trip tests**

```dart
import 'dart:typed_data';

import 'package:app/domain/entities/rescue_image.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('RescueImage preserves bytes and metadata through Hive map', () {
    final image = RescueImage(
      bytes: Uint8List.fromList([1, 2, 3]),
      fileName: 'scene.jpg',
      mimeType: 'image/jpeg',
    );
    final restored = RescueImage.fromMap(image.toMap());
    expect(restored.bytes, image.bytes);
    expect(restored.fileName, 'scene.jpg');
    expect(restored.mimeType, 'image/jpeg');
  });
}
```

- [ ] **Step 2: Verify the test fails because `RescueImage` is absent**

Run: `cd fe/app; flutter test test/domain/rescue_image_test.dart`

- [ ] **Step 3: Implement the image value and persist it in `RescueRecord`**

```dart
class RescueImage {
  const RescueImage({
    required this.bytes,
    required this.fileName,
    required this.mimeType,
  });

  final Uint8List bytes;
  final String fileName;
  final String mimeType;

  Map<String, dynamic> toMap() => {
    'bytes': bytes,
    'fileName': fileName,
    'mimeType': mimeType,
  };

  factory RescueImage.fromMap(Map<dynamic, dynamic> map) => RescueImage(
    bytes: map['bytes'] is Uint8List
        ? map['bytes'] as Uint8List
        : Uint8List.fromList(List<int>.from(map['bytes'] as List)),
    fileName: map['fileName'] as String,
    mimeType: map['mimeType'] as String,
  );
}
```

Replace `imagePath`/`images` in new records with `RescueImage? image`. When reading old Hive rows, accept missing `image` and preserve the rest of the record; do not call `File` from the migration path.

- [ ] **Step 4: Make the controller and widgets consume bytes**

Use `XFile.readAsBytes()` and determine MIME from the file extension. Render previews and history with `Image.memory(image.bytes)` while preserving sizes, borders, and positioning.

- [ ] **Step 5: Verify shared code no longer imports `dart:io`**

Run:

```powershell
rg -n "import 'dart:io'" fe/app/lib/presentation fe/app/lib/domain fe/app/lib/data/repositories
flutter test
```

Expected: `rg` finds no matches in those shared paths and tests pass.

- [ ] **Step 6: Commit the image boundary**

```powershell
git add fe/app/lib fe/app/test
git commit -m "refactor: share image data across Android and web"
```

---

### Task 3: Split Native and Web AI Behind One Repository Contract

**Files:**
- Create: `fe/app/lib/data/datasources/inference/inference_data_source.dart`
- Create: `fe/app/lib/data/datasources/inference/inference_data_source_factory.dart`
- Create: `fe/app/lib/data/datasources/inference/inference_native_data_source.dart`
- Create: `fe/app/lib/data/datasources/inference/inference_web_data_source.dart`
- Create: `fe/app/lib/data/datasources/inference/web_inference_bridge.dart`
- Create: `fe/app/lib/data/datasources/inference/web_inference_bridge_stub.dart`
- Create: `fe/app/lib/data/datasources/inference/web_inference_bridge_web.dart`
- Create: `fe/app/test/data/inference_repository_test.dart`
- Move logic from: `fe/app/lib/data/datasources/inference_local_datasource.dart`
- Modify: `fe/app/lib/data/repositories/inference_repository_impl.dart`
- Modify: `fe/app/lib/main.dart`
- Modify: `fe/app/pubspec.yaml`
- Copy: `web_fullstack/frontend/web/onnx_bridge.js` to `fe/app/web/onnx_bridge.js`
- Copy: `web_fullstack/frontend/web/vendor/ort/` to `fe/app/web/vendor/ort/`
- Copy: `fe/app/assets/models/model.onnx` to `fe/app/web/models/model.onnx`
- Copy: `fe/app/assets/models/model_manifest.json` to `fe/app/web/models/model_manifest.json`

**Interfaces:**
- Produces: `abstract interface class InferenceDataSource` with the existing readiness/model/benchmark getters plus `loadModel()`, `setModel()`, `setDualComparison()`, and `classifyImage(Uint8List)`.
- Produces: `InferenceDataSource createInferenceDataSource()` selected with `if (dart.library.js_interop)`.
- Native implementation contains all `onnxruntime`, `dart:ffi` transitively, path-provider, and MethodChannel usage.
- Web implementation contains the migrated JavaScript bridge and returns the existing shared `InferenceResult`.

- [ ] **Step 1: Write a repository contract test using a real fake object**

Define `FakeInferenceDataSource implements InferenceDataSource`, return an `InferenceResult`, construct `InferenceRepositoryImpl(fake)`, and assert the repository forwards bytes and model state. Do not mock method calls.

- [ ] **Step 2: Run the contract test and verify it fails before the interface exists**

Run: `cd fe/app; flutter test test/data/inference_repository_test.dart`

- [ ] **Step 3: Extract the native implementation without changing its behavior**

Move the current `InferenceLocalDataSource` implementation to `InferenceNativeDataSource implements InferenceDataSource`. Rename only the class and imports; retain ONNX preprocessing, PTE MethodChannel, benchmark comparison, labels, and error handling.

- [ ] **Step 4: Port the real ONNX Web implementation**

Use the existing `InferenceBridge` contract and JS interop from `web_fullstack/frontend`. Configure URLs as:

```dart
static const modelUrl = 'models/model.onnx';
static const manifestUrl = 'models/model_manifest.json';
```

Map the bridge response into the shared `InferenceResult` and `AiTag` types. Validate exactly four finite probabilities in `[0, 1]` and provider `webgpu` or `wasm`.

- [ ] **Step 5: Add the conditional factory**

```dart
import 'inference_native_data_source.dart'
    if (dart.library.js_interop) 'inference_web_data_source.dart' as platform;

InferenceDataSource createInferenceDataSource() =>
    platform.createInferenceDataSource();
```

`main.dart` must call this factory and never import the native file.

- [ ] **Step 6: Verify both AI compilation paths**

Run:

```powershell
cd fe/app
flutter test test/data/inference_repository_test.dart
flutter test test/ai_model_test.dart
flutter build apk --debug
flutter build web --debug
```

Expected: neither web build output nor shared files contain a `dart:ffi` error.

- [ ] **Step 7: Commit AI adapters**

```powershell
git add fe/app/lib fe/app/test fe/app/web fe/app/pubspec.yaml fe/app/pubspec.lock
git commit -m "feat: run shared AI flow on Android and web"
```

---

### Task 4: Split Location and Synchronization Bootstrap by Platform

**Files:**
- Create: `fe/app/lib/data/datasources/location/location_data_source.dart`
- Create: `fe/app/lib/data/datasources/location/location_data_source_factory.dart`
- Create: `fe/app/lib/data/datasources/location/location_native_data_source.dart`
- Create: `fe/app/lib/data/datasources/location/location_web_data_source.dart`
- Create: `fe/app/lib/data/datasources/sync/platform_sync.dart`
- Create: `fe/app/lib/data/datasources/sync/platform_sync_factory.dart`
- Create: `fe/app/lib/data/datasources/sync/platform_sync_native.dart`
- Create: `fe/app/lib/data/datasources/sync/platform_sync_web.dart`
- Create: `fe/app/lib/data/datasources/sync/browser_online_events_web.dart`
- Create: `fe/app/test/presentation/app_controller_test.dart`
- Modify: `fe/app/lib/main.dart`
- Modify: `fe/app/lib/presentation/controllers/app_controller.dart`
- Modify: `fe/app/pubspec.yaml`

**Interfaces:**
- Produces: `LocationPoint(latitude, longitude)` and `LocationDataSource.current()`.
- Produces: `PlatformSync.start(Future<void> Function() syncPending)` and `dispose()`.
- Android `PlatformSync` initializes/registers WorkManager.
- Web `PlatformSync` listens to the browser `online` event and calls the real sync callback while the application is open.

- [ ] **Step 1: Write controller tests with fake location and sync implementations**

Test that initialization publishes a returned location and that an emitted reconnect event invokes the same pending-sync use case. The fake classes must implement the real interfaces and use a `StreamController<void>`.

- [ ] **Step 2: Run tests and verify missing constructor dependencies fail**

Run: `cd fe/app; flutter test test/presentation/app_controller_test.dart`

- [ ] **Step 3: Implement native and web location adapters**

Native requests `Permission.locationWhenInUse` before calling Geolocator. Web calls Geolocator directly so Chrome owns the permission prompt. Both return the same `LocationPoint` and propagate permission-denied errors with readable messages.

- [ ] **Step 4: Implement real platform sync adapters**

Move `callbackDispatcher` and all WorkManager imports into the native file. Port `browserOnlineEvents` using `package:web/web.dart` and `dart:js_interop` into the web file. The web adapter subscribes and invokes `syncPending`; it does not claim to run after the browser closes.

- [ ] **Step 5: Inject both interfaces into `AppController`**

Remove `dart:io`, `permission_handler`, and direct Geolocator calls from the controller. Store location/sync error text in controller state so the existing UI can surface it without crashing.

- [ ] **Step 6: Verify Android and web startup compile**

Run:

```powershell
cd fe/app
flutter test test/presentation/app_controller_test.dart
flutter analyze
flutter build apk --debug
flutter build web --debug
```

- [ ] **Step 7: Commit platform bootstrap**

```powershell
git add fe/app/lib fe/app/test fe/app/pubspec.yaml fe/app/pubspec.lock
git commit -m "feat: share location and sync flow across platforms"
```

---

### Task 5: Unify Offline Storage, Upload, Compression, and SMS

**Files:**
- Create: `fe/app/lib/data/datasources/image/image_compressor.dart`
- Create: `fe/app/lib/data/datasources/image/image_compressor_factory.dart`
- Create: `fe/app/lib/data/datasources/image/image_compressor_native.dart`
- Create: `fe/app/lib/data/datasources/image/image_compressor_web.dart`
- Create: `fe/app/lib/data/datasources/sms/sms_gateway.dart`
- Create: `fe/app/lib/data/datasources/sms/sms_gateway_factory.dart`
- Create: `fe/app/lib/data/datasources/sms/sms_gateway_native.dart`
- Create: `fe/app/lib/data/datasources/sms/sms_gateway_web.dart`
- Create: `fe/app/test/data/record_local_datasource_test.dart`
- Create: `fe/app/test/data/sender_remote_datasource_test.dart`
- Modify: `fe/app/lib/data/datasources/record_local_datasource.dart`
- Modify: `fe/app/lib/data/datasources/sender_remote_datasource.dart`
- Modify: `fe/app/lib/data/repositories/rescue_repository_impl.dart`
- Modify: `fe/app/lib/presentation/controllers/app_controller.dart`
- Modify: `fe/app/lib/presentation/widgets/sos_button.dart`
- Modify: `fe/app/pubspec.yaml`

**Interfaces:**
- Produces: `ImageCompressor.compress(Uint8List source) -> Future<RescueImage>`.
- Produces: `SmsGateway.capabilities()` and `sendConfirmed({reportId, recipient, idempotencyKey})`.
- `SenderRemoteDataSource.upload` sends the individual FastAPI fields used by the existing web client, not the obsolete single `meta` field.
- `RecordLocalDataSource` persists the same `RescueRecord` maps on Android Hive and browser IndexedDB.

- [ ] **Step 1: Write storage and API contract tests**

Test a record containing image bytes survives save/read, a failed upload stays pending with an error, and the multipart request contains `report_id`, `created_at`, counts, coordinates, JSON vulnerable groups, and optional image bytes.

- [ ] **Step 2: Verify the tests fail against the current path-based record and `meta` request**

Run: `cd fe/app; flutter test test/data/record_local_datasource_test.dart test/data/sender_remote_datasource_test.dart`

- [ ] **Step 3: Port the proven web API contract into the shared sender**

Use the field names from `web_fullstack/frontend/lib/services/report_api_client.dart`. Preserve adaptive original/compressed/text-only selection and validate that the backend returns the same report ID.

- [ ] **Step 4: Implement real compression adapters**

Native uses `FlutterImageCompress.compressWithList`; web uses `package:image` to decode, resize to at most 1280 pixels wide, and encode JPEG quality 72. Both return actual bytes and `image/jpeg` metadata.

- [ ] **Step 5: Implement explicit SMS gateways**

Native calls `rescue/sms` only after controller confirmation. Web reads `/api/capabilities` and calls `/api/reports/{id}/sms` with `confirmed: true` and a UUID idempotency key. Remove automatic fallback to the literal emergency number `114` from `RescueRepositoryImpl`.

- [ ] **Step 6: Preserve the existing SOS button layout and add confirmation behavior**

Keep the same button widget, colors, spacing, and label. The press callback opens a standard confirmation dialog before invoking SMS; if SMS is unavailable, save/sync the report normally and expose a readable status message.

- [ ] **Step 7: Verify persistence, upload, and safety**

Run:

```powershell
cd fe/app
flutter test test/data/record_local_datasource_test.dart test/data/sender_remote_datasource_test.dart
flutter test
flutter build apk --debug
flutter build web --release --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

- [ ] **Step 8: Commit shared data services**

```powershell
git add fe/app/lib fe/app/test fe/app/pubspec.yaml fe/app/pubspec.lock
git commit -m "feat: share real rescue services across platforms"
```

---

### Task 6: Point Full-Stack Scripts at `fe/app`

**Files:**
- Create: `fe/app/web_runtime/package.json`
- Create: `fe/app/web_runtime/package-lock.json`
- Modify: `web_fullstack/scripts/prepare_frontend_runtime.ps1`
- Modify: `web_fullstack/scripts/run_frontend.ps1`
- Modify: `web_fullstack/scripts/verify.ps1`
- Modify: `web_fullstack/README.md`
- Modify: `fe/app/README.md`

**Interfaces:**
- `run_frontend.ps1` runs Flutter from `fe/app`.
- `prepare_frontend_runtime.ps1` installs ONNX Runtime Web under `fe/app/web_runtime/node_modules` and copies exact runtime files to `fe/app/web/vendor/ort`.
- `verify.ps1` treats changes inside `fe/app` as expected and validates both APK and web artifacts.

- [ ] **Step 1: Add a script assertion that currently fails**

Add this temporary assertion before changing the script paths:

```powershell
$runFrontend = Get-Content (Join-Path $PSScriptRoot "run_frontend.ps1") -Raw
if ($runFrontend -notmatch 'fe\\app') {
    throw "run_frontend.ps1 does not target the shared fe/app package."
}
```

Run: `powershell -ExecutionPolicy Bypass -File web_fullstack/scripts/verify.ps1`

Expected before script migration: FAIL with `run_frontend.ps1 does not target the shared fe/app package.`

- [ ] **Step 2: Move npm runtime metadata and update preparation paths**

Keep the existing locked `onnxruntime-web` version. Change source/target paths to `fe/app/web_runtime/node_modules/onnxruntime-web/dist` and `fe/app/web/vendor/ort`.

- [ ] **Step 3: Update run commands**

`run_frontend.ps1` must execute from `fe/app`:

```powershell
flutter run -d web-server --web-hostname 127.0.0.1 --web-port 8080 `
    --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

- [ ] **Step 4: Update verification artifacts**

Validate `fe/app/build/web/main.dart.js`, model, manifest, bridge, ONNX JS, and WASM. Add `flutter build apk --debug` before the web release build.

- [ ] **Step 5: Update README commands and source-of-truth statement**

Document that UI edits happen only in `fe/app/lib/presentation`, while backend/model tools remain in `web_fullstack`.

- [ ] **Step 6: Commit script migration**

```powershell
git add fe/app/README.md fe/app/web_runtime web_fullstack/scripts web_fullstack/README.md
git commit -m "build: run Android and web from the shared Flutter app"
```

---

### Task 7: Migrate Web Tests and Remove the Duplicate Frontend

**Files:**
- Move: `web_fullstack/frontend/test/services/web_inference_service_test.dart` to `fe/app/test/web/web_inference_data_source_test.dart`
- Move: `web_fullstack/frontend/test/services/sync_coordinator_test.dart` to `fe/app/test/web/platform_sync_web_test.dart`
- Move relevant report/send-mode tests into `fe/app/test/data/`
- Delete after successful verification: `web_fullstack/frontend/`
- Modify: `web_fullstack/DESIGN.md`

**Interfaces:**
- Consumes: all shared adapters and tests produced by Tasks 2–6.
- Produces: one Flutter package (`fe/app`) with no duplicate web UI source.

- [ ] **Step 1: Port web tests to shared domain types**

Replace `RescueReport` fixtures with `RescueRecord` plus `RescueImage`; replace `WebInferenceService` assertions with `InferenceWebDataSource`. Retain probability-length, finite-range, upload retry, and concurrent-sync assertions.

- [ ] **Step 2: Run migrated tests before deleting the old package**

Run: `cd fe/app; flutter test test/web test/data`

Expected: all migrated tests pass from `fe/app`.

- [ ] **Step 3: Run both runtime smoke checks**

Start an existing Android AVD and run `flutter run -d <device-id>` through splash/home/compose/history. Run `flutter run -d chrome` and traverse the same screens. Capture any platform capability difference as state, never as a separate screen tree.

- [ ] **Step 4: Delete the duplicate frontend only after parity passes**

Delete `web_fullstack/frontend/`. Search for stale references:

```powershell
rg -n "web_fullstack[/\\]frontend|flood_rescue_web" . --glob '!**/.git/**'
```

Expected: no runtime/script/documentation references remain.

- [ ] **Step 5: Commit consolidation**

```powershell
git add fe/app/test web_fullstack
git commit -m "refactor: remove duplicate Flutter web frontend"
```

---

### Task 8: Full Verification and Handoff

**Files:**
- Modify only if verification exposes a defect in files already owned by Tasks 1–7.

**Interfaces:**
- Consumes: the complete shared application and backend.
- Produces: evidence that Android and Chrome run the same UI source.

- [ ] **Step 1: Run source and unit verification**

```powershell
cd fe/app
flutter analyze
flutter test
```

Expected: zero analyzer issues and all tests pass.

- [ ] **Step 2: Run both production builds**

```powershell
flutter build apk --debug
flutter build web --release --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

Expected: both commands exit 0 and produce APK/web artifacts.

- [ ] **Step 3: Run backend and model verification**

```powershell
powershell -ExecutionPolicy Bypass -File web_fullstack/scripts/test_backend.ps1
powershell -ExecutionPolicy Bypass -File web_fullstack/scripts/export_web_model.ps1
```

Expected: pytest and model parity pass. If Python is still absent, install Python 3.11+ first rather than bypassing these checks.

- [ ] **Step 4: Run full-stack localhost smoke test**

Run `web_fullstack/scripts/run_all.ps1`, verify `/health`, select a real image, run ONNX inference, save offline, reconnect, and confirm the report appears through the backend API. Keep SMS disabled unless test credentials and a non-emergency recipient are explicitly provided.

- [ ] **Step 5: Check resource cleanup and Git diff**

Stop Flutter/Gradle/backend test processes. Run `git diff --check`, confirm no Java crash logs were created, and confirm only intended project files changed.

- [ ] **Step 6: Commit final verification fixes**

```powershell
git add fe/app web_fullstack docs
git commit -m "test: verify shared Flutter app on Android and Chrome"
```
