# Compose image cleanup - 2026-10-24

## Completed

- Replaced, removed and abandoned form photos are reclaimed by exact path.
  A successful report submission releases its compose source only after the
  use case finishes; the separate report-owned copy remains available offline.
  Cancelled/failed picking and failed submission keep an open form's photo.
- Form disposal defers cleanup while a picker or submission is pending. Late
  results clean their abandoned sources after completing. Snapshot clearing
  remains separate from image deletion and completes before idle disposal.
- A picker snapshot write that fails after storing its new image path releases
  that failed snapshot before reclaiming the copied image.
- Startup first handles interrupted-picker recovery, then sweeps abandoned
  compose copies. Snapshot images and both image fields of every saved report
  are retained, even when a legacy report references a compose-prefixed file.
- Cleanup only scans direct regular files in the app's attachment directory
  with generated compose-image names. It skips links, a linked root, nested
  files, report copies and camera/gallery originals. Live cleanup targets only
  the discarded file, avoiding deletion of a newer picker result. Web/stub
  implementations do not remove data URI storage.
- Cleanup errors are logged and can be retried by the next startup sweep;
  they do not turn an already persisted report into a failed submission.
- Updated the app README. Existing PTE fix and other uncommitted work preserved.

## Verification

- Full Flutter user suite: **257 passed**, using:

  ```powershell
  cd products/fe/app
  flutter test --no-pub --flavor user --reporter expanded
  dart analyze lib test
  ```

- Dart analysis: **No issues found**. `git diff --check` passed.
- New regression cases cover generated-file scope, exact target cleanup,
  external/report/nested/link preservation, startup and interrupted recovery,
  post-write snapshot failure, replacement/removal, cancellation, abandonment,
  successful/failed submission and late picker/submit completion after disposal.
- Tests use temporary fixtures. No cleanup was run against an installed app's
  data. No APK build/install, physical camera process-death verification, commit
  or push was performed.

## Next device check

Build/install an updated APK. Select/replace/remove photos, close an unfinished
form, and submit an offline photo report. Verify temporary copies are reclaimed
while the report image remains readable after restart. Repeat interrupted-camera
recovery and confirm its active photo remains available.
