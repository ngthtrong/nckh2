# Android picker, restored outbox and native tests — 2026-10-23

## Completed

- Compose flushes a form snapshot to a separate Hive box before opening the
  camera/gallery. Android startup calls `retrieveLostData`, preserves a recovered
  image outside cache and reopens the draft form after authentication or guest
  entry. Selected images are persisted before a form can leave the picker flow.
  Drafts are not sync reports and never send automatically. Successful form
  submission clears the draft; missing/unrecoverable images keep text and show
  an actionable warning. The picker cancel path keeps the draft.
- The backend includes an optional next-sequence hint on `SEQUENCE_REUSED`.
  App persists the raised counter before recreating rejected messages. Sender
  identity, report IDs, queued payloads and old attachment ownership are retained.
  Old backend replies remain compatible, but fast recovery needs updated backend.
- Replaced the Kotlin SMS aggregation main function with six JUnit tests run by
  Gradle. Covers all/partial/missing callbacks, ordering, duplicates and indexes.
- Removed the two unused storage/image read permissions from the app manifest.
  Added Gradle test commands and recovery behavior to the app README/contract.

## Verification

- Full Flutter user suite: **233 passed**.
- After final guest-navigation and formatting adjustments: **16 draft/form tests
  passed**; `flutter analyze --no-pub`: **No issues found**.
- Backend dashboard API and contract suites: **57 passed**, temporary DBs only.
- Gradle `:app:testUserDebugUnitTest -Ptarget-platform=android-arm64
  --tests com.example.app.SmsPartResultsCheck --console=plain --no-daemon`:
  **BUILD SUCCESSFUL**; XML confirms **6 tests, 0 failures/errors/skipped**.
  Kotlin app and Android manifest compiled in this task graph.
- `git diff --check`: passed. Dependency lock versions unchanged; JUnit is a
  test-only dependency. No production dependency added.

## Remaining verification

No APK assembly/install or physical camera process-death, Android backup/restore,
SIM/carrier test. Actual Android receiver/Handler timeout integration is not
covered by the pure JVM SMS aggregation tests. Update backend for fast sequence
recovery before deployment. No commit/push or filesystem cleanup performed.
