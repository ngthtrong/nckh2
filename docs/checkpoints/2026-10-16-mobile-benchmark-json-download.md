# Android benchmark JSON download

## Change

- Added a `Tải JSON` button beside each ONNX/PTE result after the benchmark runner returns.
- The button sends the entire existing `ModelBenchmarkReport.toJson()` through `rescue/benchmark_export`, then Android `ACTION_CREATE_DOCUMENT` lets the user choose a location/name. The selected document is written as UTF-8 on a separate executor. No new package, storage permission, model export, or inference-path change was introduced.
- Suggested filenames include runtime and UTC export time. The existing copy button remains. Cancellation does not report success, duplicate saves are guarded, write errors allow retry, and failed partial documents are deleted when the provider permits it.
- Updated the app README and benchmark runbook to transfer original JSON files rather than paste long clipboard text.

## Proof

- Three Flutter widget tests pass on the final code: full 256-prediction JSON larger than 20,000 bytes, cancel/retry, and save-error/retry.
- Targeted Dart analysis of the two benchmark widgets and regression test: no issues.
- Full app analysis reports 22 existing errors in legacy files that import missing `models/rescue_record.dart`; these files were not changed.
- Read-only review found no blocker; changed the success message to avoid claiming the suggested filename when the user renames it in the system picker.
- App model assets still match the seed-1024 export; checkpoint SHA-256 is `6d4ef6fff1b59e8ac5d3165f935f28214b935ee377e21ecf16e3b0627be3d9ae`.

## Build and next step

- Release APK build passed (477.5 seconds). Initial attempts failed in an existing Gradle daemon reporting cached Pub plugin paths as missing. Regenerated ignored Flutter plugin metadata, normalized its paths, and built with `GRADLE_OPTS=-Dorg.gradle.daemon=false` in that build process only. Source dependency versions are unchanged.
- APK: `products/fe/app/build/app/outputs/flutter-apk/app-release.apk`, 136,723,382 bytes; SHA-256 `1af89ee19ba1b351d83bb5c7c8b3e158dd415e92d78bb15899b5312aa4f0006b`. Verified the new native export channel is present in DEX and all four packaged model/manifest files are byte-identical to the current seed-1024 app assets.
- Not installed on or exercised against a physical phone. After installing the new APK, rerun mobile benchmark and save one complete JSON file for each runtime/device. The report update is still waiting for the three previously truncated Redmi mobile files; do not relabel the historical mobile evidence as seed 1024 before validating the replacements.
- No commit was created; preserve unrelated model/report/database edits in the working tree.
