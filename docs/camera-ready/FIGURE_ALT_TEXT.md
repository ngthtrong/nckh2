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
cells are zero. A symmetric color scale spans minus 0.65 to plus 0.65, and each
column label gives the method's control ARI. Every cell is printed numerically
so color is not required; zero change is not presented as high absolute ARI.

## RQ3 dispatch conditions

Two-panel point chart of descriptive means for the Product partition over 40
test seeds per resource condition. The left panel shows simulated harm and the
right shows deadline-miss rate as a percentage. Each panel compares revised,
legacy, and nearest-first policies in lean Hue, nominal dual-depot, and regional
surge conditions. Colors and marker shapes distinguish policies, and every
point is labeled numerically. Nearest-first is lower on both outcomes in all
three tested conditions. The points are descriptive condition means; primary
inference averages conditions within each seed and uses 40 seed-level pairs.
