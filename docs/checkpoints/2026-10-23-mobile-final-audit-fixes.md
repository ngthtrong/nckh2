# Mobile: final audit fixes — 2026-10-23

## Scope

Implemented the eight findings from the final audit of `products/fe/app`.
No files were deleted, no dependencies added, and no commit/push or APK
build/install was performed. The existing staged change to
`report/build/content/content.pdf` is preserved.

| Finding | Final behavior | Regression evidence |
| --- | --- | --- |
| SOS blocked by old image upload | Only metadata/outbox mutations and sends share the serial queue; image and status network work release it. Same-record image work is coalesced. | SOS metadata and SMS complete while an older upload remains held; slow status response also does not block SOS; concurrent sends upload one image once. |
| Slow healthy server rejected | Configured/saved endpoint probes allow 5 seconds for connect and receive; LAN scans retain 400/700 ms limits. Concurrent probes share one attempt. | Local HTTP health response delayed 900 ms succeeds; known endpoint timeout remains finite; LAN timeout stays short. |
| One failed image starves older images | The last attachment attempt ID is saved in the existing outbox before upload. Later sync starts after it, including after Hive/repository reopen. | A failed upload exceeding the 20-second pass budget is followed by the older image first on the next worker instance. |
| False server receipt | Submitted screen shows the server progress tracker only after metadata ACK or full sync. | Offline, rejection, SMS-only, pending image after ACK, processing/dispatched/resolved/cancelled widget cases. |
| Leaving form loses pending send feedback | Close and system Back cannot leave Compose while submitting; idle system Back returns to tabs. | Pending-submit failure keeps input and displays its error; idle Back returns normally. |
| Invalid profile phone | Registration and profile edit share the existing 9–11-digit rule, stripping spaces before save. | Invalid letters/short numbers rejected in both forms; valid spaced phone normalized. |
| Unsupported ARM32 build | Gradle accepts only ARM64/x86_64 targets, filters non-split builds, and avoids conflicting NDK filters for split APKs. README requires explicit supported target flags. | ABI policy test compares the real ExecuTorch AAR runtimes to configured targets and split-filter policy. |
| Offline benchmark promise | README states that each run needs online `/api/auth/me` validation; the authentication policy is unchanged. | Source/caller review. |

The existing limits remain: each people count 0–10,000; description at most
300 whitespace-separated words and 2,000 Unicode code points. Record IDs,
stored reports/images, ACK/status/SMS merge behavior and model assets are kept.

## Verification

- `flutter test --no-pub --flavor user --reporter expanded`: **184 passed**.
- Admin/model/cleanup plus locator tests: **29 passed**.
- `flutter analyze --no-pub`: **No issues found**.
- `git diff --check`: passed.
- Offline Gradle `help` configuration passed for ARM64 with ABI splits enabled.
- Offline Gradle `help` with splits disabled and a generated assertion in
  `products/fe/app/build/` verified the actual final NDK filters are exactly
  `[arm64-v8a]`. Neither Gradle check assembled an APK.
- Independent read-only review of repository/outbox concurrency: no actionable
  issues found in the final patch.

## Remaining device/deployment verification

- Build a new APK with an explicit supported target, then check the packaged
  native libraries and perform an on-device PTE smoke test.
- Check real SMS/SIM callbacks and fees, Android Back/predictive Back, GPS,
  weak-network delivery, background execution and vendor battery restrictions.
- No real rescue server, SMS gateway or phone was used for these tests.
- Gradle reports existing Kotlin/old Android DSL deprecation warnings. A future
  Gradle/AGP migration is outside these eight fixes; the current configuration
  checks succeeded.
- The 20-second sync budget is checked between operations; individual requests
  still follow their transport timeouts. Slow image/status requests do not hold
  the SOS/outbox queue.

Changes are left uncommitted for review.
