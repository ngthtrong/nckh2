# Mobile: battery scheduling and APK size

Date: 2026-10-22

## Implemented

- Android `user` (default) and `admin` flavors. User keeps package `com.example.app`,
  excludes `libonnxruntime.so`, blocks ONNX activation and hides model admin tools.
  Admin uses `com.example.app.admin` and retains comparison/benchmark features.
- PTE loads once on demand when the report form opens, asynchronously; image
  analysis shares the pending load. Sending SOS/reports does not await AI.
- Status polling waits 15 seconds while history/submitted status is visible,
  60 seconds elsewhere, and stops without tracked reports, network, or foreground.
  Resume checks outstanding work immediately.
- The unique WorkManager schedule is kept while messages/images await sync OR
  any non-rejected report is non-final. It is cancelled when idle and rearmed
  when a new report is saved. Existing periodic work is kept, not replaced.
- Failed automatic LAN scans back off 1/2/5 minutes; known URLs remain preferred.
  Explicit reconnect/new sends can bypass the delay. Worker LAN scans stay disabled.
- An overdue message whose server is unreachable no longer creates a zero-delay
  retry loop: wait 30 seconds, stop retry timers when offline or in background.
- Settings cleanup is available without admin login. It removes owned ONNX and
  benchmark downloads, preserving PTE, rescue reports/attachments, and JSON exports.
  Cleanup is locked while resources are read/downloaded or benchmarks run.
- Splash/logo use lossless WebP: combined bytes 1,729,449 -> 1,281,166
  (448,283 bytes saved in source assets, not a measured APK-size result).
- Fixed emergency phone cards overflowing on narrow screens/large text, and
  late AI results attaching to a replaced/deleted image or updating a closed form.

## Evidence

- `dart analyze lib test`: no issues.
- `flutter test --no-pub --flavor user`: 117 tests passed.
- `flutter test --no-pub --flavor admin test/admin_model_access_test.dart test/ai_model_test.dart test/model_benchmark_test.dart test/model_download_cleanup_test.dart`: 18 tests passed.
- `git diff --check`: passed.
- Flutter tests required permission to access the SDK lockfile outside workspace.

## Pending

- User explicitly requested source changes only; no APK build/install was run.
- After building, inspect the user APK to confirm no `libonnxruntime.so`, verify
  PTE inference on Android and user upgrade compatibility with the old signing key.
- Measure actual APK/install size, cold model load time, RAM and battery on device.
- Verify background delivery with pending images and non-final reports, idle
  cancellation, resume/network restoration and manufacturer battery restrictions.
- WorkManager is opportunistic; force-stop may suspend it until app is reopened.

Build/install commands and flavor details are in `products/fe/app/README.md`.
Changes are not committed by this task; preserve other concurrent repository work.
