# Mobile network and GPS fixes — 2026-10-23

## Changes

- Settings > Vị trí can request permission again, open app settings after a
  permanent denial (including Android reporting it only after a request), or
  open location service settings. GPS failures clear previous coordinates and
  accuracy; SOS can still send without GPS. Recovery cannot interrupt an active
  submission.
- Bluetooth, VPN, satellite/other connection results are treated as potential
  data connections rather than offline. Actual server requests determine delivery.
- A foreground send with a priority report bypasses LAN discovery backoff.
  Automatic sync retains backoff and background workers retain their existing
  no-LAN-scan policy.
- Location accuracy is stored with the report, copied through delivery, shown
  in location text, and included in data payloads and optional SMS `acc` fields.
  Accuracy over 100 m displays a nearby-position warning. The backend validates
  positive finite accuracy with coordinates and preserves it in raw payloads.
  Existing records and SMS without accuracy remain supported; no DB migration.

## Verification

- Full user Flutter suite: **213 passed**.
- After the final Android permission adjustment, GPS/settings tests: **11 passed**.
- `flutter analyze --no-pub`: **No issues found** on the final source.
- Full backend dashboard API suite: **48 passed**, using a temporary database.
- `git diff --check`: passed.
- Regression cases cover denied/permanently denied permission, disabled GPS,
  no-GPS SOS, 2,000 m accuracy through SMS/data, local accuracy persistence,
  all connectivity enum values and LAN recovery before backoff expires.

## Remaining verification

No APK build/install, physical GPS, Bluetooth/VPN, carrier/SIM or live gateway
test. Deploy updated backend SMS intake to retain `acc` from summary SMS.
No files were deleted, no dependencies added, and no commit/push performed.
The earlier uncommitted Compose input-lock change is preserved.
