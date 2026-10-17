# Checkpoint: admin-only model comparison and download

Date: 2026-10-16

## Implemented

- PTE remains bundled and is the default mobile inference runtime for offline users.
- ONNX is removed from Flutter's bundled assets. A signed-in backend `admin` can download it; the app verifies file size, SHA-256 and manifest pairing with the bundled PTE before atomically activating it.
- Backend protects the model catalog, model downloads and benchmark package with its existing `require_admin` dependency. The old `rhna` username special case is removed.
- Model comparison and benchmark UI is only built for a currently verified admin session. A local profile named `admin` grants no privileges. Logout, role change, server change or expiry closes the UI, cancels downloads and returns inference to PTE; active ONNX inference completes before its session is released.
- Docker image copies the ONNX/PTE model pair and manifest to `/app/model_exports`; native backend defaults to the repository export directory. Both use `RESCUE_MODEL_EXPORT_DIR` when configured.

## Evidence

- Backend role/download API test passed: anonymous receives 401, an operator named `rhna` receives 403, admin can download a matching model package, manifest mismatch receives 503, and logout revokes access.
- Flutter targeted analysis found and fixed the Dio cancellation API mismatch. The focused Flutter test command was not rerun after that fix.
- Release APK built at `products/fe/app/build/app/outputs/flutter-apk/app-release.apk` (121,178,446 bytes, SHA-256 `449a968a31b970089fb29626394fe07297c314aa65568a80b19f8d70aa6e0c0b`). APK manifest contains PTE and no ONNX model asset.
- Physical Android device checks and a Docker image rebuild remain to be done.

## Files remain uncommitted

- Backend `model_assets.py`, `main.py`, `test_dashboard_api.py`.
- Docker backend image configuration.
- Mobile admin session, model downloader, PTE-first inference state, admin-gated UI, tests and updated docs.
- Preserve all other in-progress seed-1024 report, benchmark and mobile JSON download work.
