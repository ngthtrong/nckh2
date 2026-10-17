# Checkpoint: mobile audit fixes 1–9

Date: 2026-10-16

## Scope

- SOS feedback distinguishes server acceptance, queued reports, successful SMS and failure.
- Model runtime and comparison controls are locked during a dataset benchmark; runner checks the selected runtime and result model for every warmup and sample.
- Picked images are copied into durable app storage before queueing; unreadable/empty attachments remain pending and are reported. Metadata ACK is persisted separately so image retries do not recreate report messages.
- Local logout clears only signed-in state; existing profiles migrate and remain available for later login.
- Foreground/background Hive access uses an atomic owner mapping. Delegated sync is acknowledged after completion; background Hive closes before releasing ownership. Timeout never steals an active owner's mapping.
- Production server connections require configured HTTPS. HTTP private-LAN mode is explicit at build time; Android cleartext defaults off and API clients do not follow redirects.
- Benchmark JSON schema 2 records checkpoint/artifact hashes, split CSV hash, runtime, run ID, UTC timestamps, app and Android device metadata.
- Deleted nine confirmed-unused legacy source files. Kept the `send_mode.dart` compatibility export.
- Outbox uses a per-record message index that handles duplicate records from old data and removes individual IDs on ACK.

## Evidence

- `flutter analyze --no-pub`: no issues found.
- Background sync guard focused tests: 9/9 passed, including a simulated long upload/close and retained ownership on timeout.
- Local-data focused run reported 24 passing cases; one locator assertion was then updated for HTTPS test configuration. The final full test suite was not run.
- No APK build or physical-device run, at the user's request. Release packaging and runtime behavior on hardware remain for the user's build/install pass.
- No commit created; preserve existing report/model/backend changes.

## Build

- One shared APK serves normal users and backend-authenticated admins. For the current trusted-LAN Docker HTTP demo, build with `ALLOW_INSECURE_LAN=true`; for deployment, configure a real HTTPS `SERVER_URL` and leave insecure LAN disabled.
- The HTTP demo build exposes admin credentials and report traffic to other devices on that Wi-Fi; use only on a trusted private network.

## Limits

- A stale IsolateNameServer owner after an isolate dies cannot safely be distinguished from a slow live owner; the app asks to retry or restart instead of allowing concurrent Hive writers.
- Physical-device and full integration tests remain unverified.
