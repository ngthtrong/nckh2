# Mobile HTTP retry and summary SMS fixes — 2026-10-23

## Changes

- Permanent HTTP errors remain dead-letter and surface on the local report.
  Legacy HTTP 400/404 dead-letters are no longer recreated. Connection failures,
  HTTP 408/429/5xx retain retry/backoff behavior.
- HTTP 413 halves the batch size while retaining message IDs, sequences and
  payloads. A singleton rejected with 413 becomes `REQUEST_TOO_LARGE`; smaller
  neighbouring reports can still sync. Batch splitting shares the existing
  time budget.
- SMS fallback excludes free-text notes and retains report ID, location, people
  counts, vulnerable groups, mobility and severe signs. The full description
  remains local and syncs later through data. Feedback explains summary SMS.
- The backend still supports notes in SMS from older app versions. No backend
  production code, dependencies or native SMS sending logic changed.

## Verification

- Focused Flutter tests: **74 passed**.
- `flutter test --flavor user --reporter compact`: **198 passed**.
- `flutter analyze`: **No issues found**.
- Four backend SMS regression tests passed using a temporary database, including
  summary SMS followed by a full 2,000-character description through sync.
- Dart format check and `git diff --check`: passed.

## Not checked

No APK build, physical device, SIM/carrier, live backend or gateway test.
Structured emergency fields can still require multipart SMS and incur fees.
The sync time budget is checked between transport operations.
Changes are uncommitted; no files were deleted.
