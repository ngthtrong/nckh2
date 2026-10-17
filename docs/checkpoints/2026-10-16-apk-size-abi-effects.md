# Checkpoint: mobile APK size and decorative effects

Date: 2026-10-16

- Replaced custom splash fade/page transition with an immediate transition and canceled its startup timer on dispose.
- Removed the repeating SOS pulse and animated color interpolation; SOS state colors and tap behavior remain.
- Replaced app `InkWell` tap surfaces with `GestureDetector` and disabled Material hover/splash/highlight overlays.
- Built per-ABI release APKs. ARM64 phone APK: 61,327,087 bytes, SHA-256 `4c5e246c7bf98227198ea712e9febfc198cde87f4cb9c484924109024eabbffc`. Contains only `arm64-v8a`; PTE and manifest remain bundled, ONNX weights are absent.
- Build outputs: arm64 58.5 MiB, armv7 43.1 MiB, x86_64 49.1 MiB. ARM64 artifact is about half the previous 121,178,446-byte universal APK.
- The installed app still includes PTE (16.8 MB), ONNX Runtime native library (14.2 MB for arm64, used by admin), Flutter (11.6 MB), and ExecuTorch (8.9 MB). Removing these runtimes requires changing delivery architecture; deleting hover/animation code has little effect on APK size.
- `git diff --check` passed. Release APK built successfully; no physical-device install or Flutter unit test run was performed.
