# PTE Activity teardown fix - 2026-10-24

## Completed

- Android teardown queues PTE disposal after all accepted load/inference work,
  then shuts down the single PTE executor without interrupting native execution
  or waiting on the UI thread. Disposal exceptions are logged and the module
  reference is cleared.
- Native PTE calls received after shutdown return a channel error. Inference
  reads the current module on its executor; a failed reload no longer retains
  a successfully closed previous module.
- Added two JVM regression tests for teardown during inference with queued work,
  and teardown during a model load. No dependency or Dart API changes.

## Verification

- The inference regression failed with the original immediate-close behavior:
  `IllegalStateException: Cannot destroy module while method is executing`.
- After the fix, Gradle reported `BUILD SUCCESSFUL` for both native unit suites.
  XML results confirm **8 user tests and 8 admin tests**, with zero failures,
  errors or skipped tests. Each suite includes 2 PTE and 6 existing SMS tests.
- `git diff --check` passed. Read-only diff review found no further issue.
- Run from `products/fe/app/android` with `JAVA_HOME` set to an installed JDK 21:

  ```powershell
  .\gradlew.bat :app:testUserDebugUnitTest :app:testAdminDebugUnitTest -Ptarget-platform=android-arm64 --console=plain --no-daemon --offline
  ```

## Remaining verification

No APK assembly/install or physical Android Activity lifecycle reproduction.
JVM tests use controlled tasks and fake resources; they do not run native PTE.
Next device check: finish/recreate the Activity during model load, image
classification and benchmark, then reopen the app and verify PTE loads again.
Existing uncommitted changes were preserved. No commit, push or file deletion.
