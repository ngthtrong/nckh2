# Checkpoint: clean downloaded mobile benchmark resources

Date: 2026-10-16

## Scope

- Automatically remove the legacy `model.onnx`, its version/temp files, old hash-named ONNX files and interrupted ONNX downloads at startup. Keep the currently pinned ONNX hash, PTE and user records.
- Provide an admin-only button to delete downloaded ONNX and benchmark images, including partial downloads. Keep exported JSON and in-memory benchmark results; show reclaimed bytes in MB.
- Return to PTE and wait for any active ONNX call to finish before deleting its model. Block new model downloads/benchmark while deleting; block deletion during downloads/benchmark.
- Move `integration_test` to dev dependencies so Flutter's release plugin filter excludes it.

## Evidence

- Final focused run: all 17 tests passed (cleanup, admin access, default PTE, deletion-button locking and full JSON export).
- Targeted analysis of the 11 changed implementation/test files passed with no issues; `git diff --check` passed.
- Subsequent audit ran the full existing test suite: 64 tests passed. Full analysis reports 22 errors in unused legacy files plus 2 formatting notices in `admin_session.dart`.
- User requested no more builds and will build locally. The running release build was interrupted; a new APK size and release DEX exclusion were not verified. Flutter plugin metadata correctly marks `integration_test` as dev-only.
- Previous ARM64 APK baseline: 61,327,087 bytes, SHA-256 `4c5e246c7bf98227198ea712e9febfc198cde87f4cb9c484924109024eabbffc`.

## Limits

- Phone storage cannot be reclaimed until the updated app is installed and launched. Benchmark downloads stay until the admin uses the delete button.
- The bundled PTE and its extracted runtime copy remain necessary for the current native bridge. ONNX Runtime remains included for admin use.
- No changes committed; preserve other report/model work.
