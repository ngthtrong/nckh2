# Benchmark timeout and submitted summary wrap - 2026-10-24

## Completed

- Benchmark package downloads now use a 60-second receive timeout. The policy
  is set on the actual download request, including when a test Dio client is
  supplied. Connection timeout and redirect policy of the default client stay
  as configured previously.
- Download/preparation flags reset in a nested finally block even if partial-file
  cleanup fails. Timeout permits retry and releases the controller benchmark lock.
- Added an optional Dio constructor dependency to exercise the real native
  download and response-stream timeout without contacting a server.
- Submitted report summary labels and values have flexible widths, spacing and
  wrapping, with top alignment. Full priority-group and GPS values remain readable
  on narrow screens and with larger text. Receipt/status content is preserved.
- Updated the app README. Existing PTE, compose-image cleanup and user changes
  were preserved. No dependency, commit or push added.

## Verification

- The new download regression observed a missing receive timeout before the fix.
  The final test checks the production 60-second request policy, then shortens
  that request to 50 ms inside its adapter. The adapter emits one byte and stalls;
  real Dio timeout handling removes the partial file, resets locks, and permits
  a second attempt and resource cleanup. No external network is used.
- Submitted-screen user suite: **10 passed**, including 360 px / normal text
  and 320 px / double text with all four priority groups and long GPS accuracy.
- Admin download/auth/benchmark/submitted suites: **23 passed**.
- `dart analyze lib test`: **No issues found**. `git diff --check` passed.
- Commands from `products/fe/app`:

  ```powershell
  flutter test --no-pub --flavor user test/submitted_screen_test.dart --reporter expanded
  flutter test --no-pub --flavor admin test/benchmark_package_download_test.dart test/admin_model_access_test.dart test/model_benchmark_test.dart test/submitted_screen_test.dart --reporter expanded
  dart analyze lib test
  ```

## Remaining verification

No full-suite rerun, APK build/install, physical-device layout review or real
backend/network interruption test. The new package test is admin-only and skips
in the user flavor. Next device check: interrupt a package transfer, wait for its
receive timeout and retry; inspect submitted summary at large system text size.
