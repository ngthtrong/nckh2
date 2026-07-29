# X0 post-run validator incident

- Detected at: Gate 3 promotion of
  `20260728T213934Z-85f2a6686a1b-9797f31f-x0-exp23-heldout`.
- Scope: independent Gate-3 verifier only.
- Symptom: the verifier compared the in-memory selected-config registry with
  the canonical JSON registry using Python container identity. The frozen
  loader represents `simplex_weights` as a tuple; canonical JSON represents
  the same sequence as a list.
- Evidence: the candidate completed with exit code 0, self-validation passed,
  the run manifest sealed the result, and the Gate-3 verifier stopped before
  creating a lock. No result, selector, protocol, selected configuration, test
  row, or candidate manifest was changed.
- Resolution: normalize the independently reloaded selected-config bundle
  through finite canonical JSON before structural comparison.
- Scientific impact: none. Values, order, configuration hashes, predictions,
  metrics, inference, and checksums are unchanged.
- Rerun policy: no test rerun. The fix changes only the verifier's
  tuple-versus-list representation handling and is applied to the complete
  immutable candidate artifact.

