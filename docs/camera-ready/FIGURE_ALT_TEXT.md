# Figure alt text for camera-ready delivery

Synchronized with `paper_6444_ALT_Text.xlsx` on 20 September 2026.
The workbook contains one row for each of the three figures in `paper/main.tex`.
Checked against the organizer example `paper_1122_ALT_Text.xlsx`: sheet `Alt-TextExcel`, columns `File Name`, `Thumbnail`, `Alt Text`, and numbered figure descriptions.
The author supplied all three thumbnails; their content and row order were checked against the manuscript figures. Images were converted to floating thumbnails, matching the organizer example, with the existing image bytes preserved. Each image also carries its row description as object alt text.
The File Name column identifies the PDF figures used in the LaTeX source; the thumbnails embedded in the workbook are PNG images.
The reviewed workbook is included at the root of the regenerated submission source ZIP. Local export is separate from external upload.

## Figure 1 — `pipeline_v2.pdf`

Fig. 1. Flowchart separating observable report processing from evaluator-only information. Reports missing location or event time enter a manual-review queue. Eligible reports pass through masked similarity and sparse graph construction using thresholding and k-nearest neighbours, predicted clustering, duplicate-family grouping and bounded priority ranking, then predicted-cluster scheduling. Dashed arrows carry the locked partition, ranking rule and locked schedule into separate evaluation paths: RQ1 evaluates clustering against incident truth; RQ2 evaluates ranking using oracle incident groups and independent benefit; RQ3 evaluates dispatch using the locked schedule and truth. The evaluator-only block holds incident identity, true need and vulnerability, deadlines, service demand, harm and independent benefit. This information does not feed back into observable inference.

## Figure 2 — `rq1_stress_delta_ari.pdf`

Fig. 2. Six-row, five-column heatmap of mean paired change in Adjusted Rand Index (ARI), computed on original incident-linked reports relative to each method's control over 40 held-out runs. Columns compare Product Louvain, Additive Louvain, matched-density Additive, Product Leiden and geo-time DBSCAN. Rows show GPS noise of 100 and 300 metres, timestamp noise of 15 and 60 minutes, and total copy multiplicities of two and five. All GPS and timestamp cells are negative. Twofold copies slightly increase ARI for the four graph methods; fivefold copies decrease it by 0.6057 to 0.6220. DBSCAN changes by zero under both copy conditions, with control ARI 0.4978. Cell values and control ARIs are printed numerically. Colours encode signed change; zero change does not imply high absolute accuracy.

## Figure 3 — `rq3_dispatch_conditions.pdf`

Fig. 3. Two-panel point chart showing mean simulated harm (left) and deadline-miss percentage (right) for Revised, Legacy and Nearest-first scheduling using the Product partition. The horizontal axis lists Lean Hue, Nominal dual depot and Regional surge resource conditions; each point averages 40 test seeds. Both outcomes decrease across these conditions for all policies. Nearest-first has the lowest harm (585.55, 230.00, 94.71) and deadline-miss rates (82.0%, 63.1%, 44.8%), respectively. Revised has lower mean deadline-miss rates than Legacy in all three conditions, but lower mean harm only in Regional surge. Blue circles, orange squares and green triangles identify Revised, Legacy and Nearest-first; all points have numeric labels. These are descriptive means; primary inference averages conditions within each seed and uses 40 seed-level pairs.
