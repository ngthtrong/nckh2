# Figure alt text for camera-ready delivery

## Figure 1 — Observable pipeline

Flow diagram of an observable-only flood-report pipeline. Reports with
location and event time proceed through similarity graph construction,
clustering, duplicate-family priority scoring, and scheduling; incomplete
reports take a manual-review branch. Incident identity, benefit, deadlines,
and harm are kept on a separate evaluator-only path that joins only after the
schedule is fixed.

## RQ1 stress heatmap

Six-by-five annotated heatmap of mean paired change in original-report ARI
relative to each method's control over 40 held-out runs. Columns are Product
Louvain, Additive Louvain, matched-density Additive, Product Leiden, and
geo-time DBSCAN. Rows are GPS noise at 100 and 300 metres, timestamp noise at
15 and 60 minutes, and exact copies at total multiplicity two and five. All
GPS/time cells are negative. Twofold-copy graph cells are slightly positive,
while fivefold-copy graph cells are approximately minus 0.61; both DBSCAN copy
cells are zero. Every cell is printed numerically so color is not required.

