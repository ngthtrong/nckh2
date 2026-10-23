# Mobile history status and layout fixes — 2026-10-23

- History cards show pending delivery until metadata ACK/full sync. SMS alone
  does not imply server receipt. Permanent rejection displays an error badge,
  error code and guidance to call 112. Server dispatch/final states remain.
- Location, timestamp and report ID text fit available width and wrap, including
  long GPS accuracy warnings on a 320 px screen with 2x text scaling.
- Regression tests reproduced both bugs before the fix. Afterwards, **27 tests**
  covering history, submitted feedback and SOS feedback passed.
- `flutter analyze --no-pub`: **No issues found**; `git diff --check`: passed.
- No APK build, physical-device test, commit or push. Existing pending changes
  are preserved; no files were deleted.
