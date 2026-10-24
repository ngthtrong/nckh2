# Camera recovery snapshot scope

- User clarified that unfinished forms need no general draft persistence.
- Persist a snapshot before launching camera/gallery; discard it when the picker returns, when leaving the form, and before report persistence.
- Startup restores a snapshot only when Android image_picker returns interrupted picker data; ordinary startup discards it. Submitted reports retain their existing durable storage and sync behavior.
- Each copied picker image has a unique filename, preventing stale FileImage cache reuse.
- Validation: 19 focused Flutter recovery/form tests passed. Includes ordinary restart discard, Android lost-data recovery, cancellation, leaving the form, deletion before submission, and consecutive image bytes/paths.
- Flutter analyze passed with no issues; git diff --check passed.
- Physical Android process death, force-stop and camera/gallery behavior remain unverified. Force-stop is not guaranteed to yield recoverable picker data.
- Existing uncommitted changes were preserved; no commit/push.
