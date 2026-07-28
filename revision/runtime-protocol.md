# Runtime, memory, packet, and spatial-equivalence protocol

**Task:** F4  
**Status:** frozen before measured run  
**Executable:** `demo/experiments/exp22_runtime_repro.py`

## Inputs and repetitions

The benchmark reads only the first 1, 2, and 4 registered development datasets
from the Gate-1 frozen bundle, after matching that bundle manifest to
`revision/gate1-lock.json`. This gives three increasing input sizes without
exposing test data. Each size has one discarded warm-up and five measured
repeats. A measured repeat runs in a fresh process; stage durations use
`time.perf_counter`, and the summary reports the median and interquartile range
without dropping slow runs.

Every worker limits all discoverable native thread pools to one thread and
attempts to pin the process to one logical CPU. The artifact records the
thread-pool inspection and affinity outcome for every repeat. A one-core claim
is eligible only if all measured workers confirm both constraints.

Peak RSS is the operating-system `ru_maxrss` for the entire isolated worker,
including imports and simultaneous dense/spatial matrices. It is not presented
as a component-only memory attribution.

## Spatial comparison

The comparison is between:

1. the locked vectorized product matrix followed by the locked strict
   threshold/k-NN operation; and
2. a BallTree geographic candidate query using the finite product theorem,
   the same vectorized dense-reference numerical kernel on candidates, and
   the same locked sparsification operation.

Acceptance requires maximum matrix difference at most `1e-9`, identical edge
count, and Louvain partitions identical up to label permutation at the locked
random seed. Every repeat is retained. The spatial path still materializes a
dense compatibility matrix, so even a passing result supports exact candidate
pruning—not a fully sparse-memory scalability claim.

## Packet measurement

Packet size is measured on every report from the first development seed after
running the locked confidence computation. Compact, sorted UTF-8 JSON contains
ID, coordinates, UTC epoch, F/E/N/V, the actual computed C, image flag, source,
province, and missingness mask.

The reported min/median/max cover only this application payload. Transport
framing, HTTP/MQTT headers, TLS, authentication, retransmission, and link-layer
overhead are explicitly excluded, so the result is not an end-to-end network
packet claim.
