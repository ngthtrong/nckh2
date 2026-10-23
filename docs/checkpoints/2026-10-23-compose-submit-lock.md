# Compose input lock — 2026-10-23

- Locked pointer input and keyboard focus while a report submission is pending.
  Failed submissions unlock the same form and preserve its input.
- Regression test reproduced the old behavior: a person count changed from 0
  to 1 during submission. It now verifies blocked count/photo interactions,
  blocked editor focus, and restored editing after failure.
- Focused form and input-validation tests: **9 passed**.
- `flutter analyze --no-pub`: **No issues found**.
- `git diff --check`: passed.
- No APK build, device/SIM test, commit or push performed.
