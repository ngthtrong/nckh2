---
name: rtk
description: >
  RTK = Rust Token Killer, a token-optimized CLI proxy for shell commands used in this
  project (see RTK.md). Prefix shell commands with `rtk` to filter/compress output and
  cut token usage while running git, cargo, npm, pytest, and other tooling.
  Use when user says "use rtk", "run with rtk", "rtk mode", asks about token savings on
  shell output, or invokes /rtk. NOTE: this project has no Redux Toolkit — "RTK" here
  means the Rust Token Killer CLI, not the JS state library.
---

RTK (Rust Token Killer) = token-optimized CLI proxy. Wraps shell commands, filters noisy
output, reports token savings. Source of truth: [RTK.md](../../../RTK.md).

## Rule

Prefix shell commands with `rtk` when running project tooling:

```bash
rtk git status
rtk cargo test
rtk npm run build
rtk pytest -q
```

`rtk` runs the command and trims low-signal output (progress bars, repeated lines) to save
tokens. Command semantics unchanged — same exit codes, same real work.

## Meta commands

```bash
rtk gain            # token savings analytics
rtk gain --history  # recent command savings history
rtk proxy <cmd>     # run raw command, no filtering (use when you need full raw output)
```

## Verification

```bash
rtk --version
rtk gain
which rtk
```

If `which rtk` finds nothing, rtk is not installed on PATH — fall back to plain commands
and tell the user rtk is unavailable.

## Boundaries

- Only wraps shell invocations. Does not change code, config, or business logic.
- Use `rtk proxy <cmd>` when filtered output would hide something you need (full logs,
  exact byte-for-byte output).
- Do not prefix `rtk` on commands where the user needs unfiltered output verbatim.

## NEEDS USER CONFIRMATION

This skill assumes `RTK` = Rust Token Killer per [RTK.md](../../../RTK.md). The original task
mentioned Redux Toolkit / RTK Query as a possibility, but this project has NO frontend using
Redux Toolkit (grep for `@reduxjs/toolkit`, `createApi`, `createSlice` → no matches).

Confirm which RTK you want:
1. Rust Token Killer CLI (current content) — keep as is.
2. Redux Toolkit / RTK Query workflow — needs a frontend that uses it; not present now.
   If you plan to add one, tell me the stack and I'll rewrite this skill accordingly.
