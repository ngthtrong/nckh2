# ISDS 2026 · Paper 6444 · Problem-first 15-minute talk

- [PowerPoint](ISDS2026_Paper_6444_15min.pptx)
- [PDF](ISDS2026_Paper_6444_15min.pdf)
- [English and Vietnamese script](speaker-notes.md)
- [Slide-by-slide content allocation](content-plan.md)
- [Q&A preparation (Vietnamese)](qa-prep.md)
- [Generated illustration prompts](assets/imagegen/prompts.md)
- [Visual overview](checks/contact-sheet.png)

The current variant is reauthored from the paper, with a new purpose, audience content, and talk track for every body slide. The source deck supplies the CTU template scaffold only. The cover, two reference pages, and thank-you artwork are preserved as requested; reference page numbers are updated. The original conference PPTX remains unchanged.

There are **17 visible slides and two hidden backups**:

| Section | Slides | Planned time |
|---|---|---:|
| Title + Introduction | 1, 3–4 | 3:15 |
| Overview | 2 | 0:15 |
| Related work | 5 | 1:00 |
| Dataset: synthesis and information boundary | 6–7 | 2:50 |
| Method: report graph, evidence and dispatch | 8–9 | 2:25 |
| Results: clustering accuracy, clustering under stress, ranking, dispatch | 10–13 | 4:00 |
| Conclusion & Future work | 14 | 0:50 |
| References and Thank you | 15–17 | 0:15 |
| **Total** | **1–17** | **14:50** |

This is a speaking budget, not a measured rehearsal; 10 seconds remain for transitions or slower delivery. The English script contains approximately 1,640 words. The script places all English slides before all Vietnamese slides. Both languages are embedded in every slide's Notes. The English script uses B2-oriented wording and short spoken sentences; required technical terms are explained. Slides 18 and 19 contain protocol details and answers to anticipated questions (interval vs. test, Leiden, constant sensitivity, why synthetic data); both are hidden during the PPTX slide show. The PDF includes them for reference.

## Illustrations and quantitative evidence

Three conceptual illustrations were created with the **built-in imagegen tool**, not manual scene drawing. Each PNG is stored in `assets/imagegen/` beside its exact `.prompt.txt`; `prompts.json`, `prompts.md` and `manifest.json` record prompts, slide mappings, source files and SHA-256 hashes. The PNG outputs are used as generated; no local image editing substitutes for imagegen.

| Slide | Generated asset | Purpose |
|---|---|---|
| 3 | `01-rescue-context.png` | Fictional neighborhood and a coordinator with limited crews |
| 4 | `02-report-ambiguity.png` | Repeated, distinct-nearby and false-destination cases |
| 6 | `03-synthetic-construction.png` | Scenario → incidents → reports → perturbations |

Images are explanatory illustrations, not field records, generated training data, observed results, or claims of successful rescue. Editable text remains in the template fonts. Slide 7 uses an information-boundary diagram (observed fields → group → rank → schedule above the line; hidden truth joined only after predictions are fixed below it; 80-run split bar). The method slides 8–9 use diagrams drawn by `scripts/figures_15min.py` from the manuscript equations (Eq. 3 and Eq. 4) instead of generated images; `04-*.png` and `05-*.png` remain on disk but are unused. Quantitative charts on slides 10–13 (ARI of all ten methods with 95% CI, stress heatmap, ranking, dispatch) are rendered with matplotlib from the result CSVs; they are not AI-generated charts or reused figure images. Slides carry no footnotes; provenance and the AI-illustration disclosure live in the Notes, alt text and this README. Exact values and provenance are in `assets/charts/plot-data.json`. The dispatch chart and the deadline-miss contrasts on slide 13 read candidate-minus-comparator values directly from the paired CSV, with positive values meaning worse simulated harm; the builder asserts that they match the manuscript's rounded values. The ranking chart adds the population-only comparator (.6709) quoted in the manuscript. Slide 13's third card (Product vs matched-density Additive under revised priority, harm +18.34, Holm p = .000168) is read from the same CSV's partition rows and asserted against the manuscript. Slide 6 labels EMSR848 · OSM · WorldPop as the clustering-test context; ranking/dispatch use synthetic geometry, as in the paper. Citations [2], [3], [4] appear on slides 8, 10 and 12.

Dataset is taught as one synthetic construction narrative. Its experimental configurations remain independently generated; geographic clustering and fully synthetic ranking/dispatch have separate samples. Counts are not pooled and results are not represented as a common-sample end-to-end test. No experiments are rerun.

## Rebuild and inspect

From the repository root, using Python with python-pptx, Pillow, matplotlib, numpy and PyMuPDF:

LibreOffice loads its own libraries first; with an unpacked (non-system) LibreOffice, put its `program` directory before other library paths in `LD_LIBRARY_PATH`.

```sh
python3 ISDS/scripts/build_15min.py
python3 ISDS/scripts/render_15min.py --soffice /path/to/soffice
python3 ISDS/scripts/validate_15min.py
```

The builder reads `content-plan.json`, the source conference PPTX, generated PNG assets, and the paired results CSV. The renderer uses the bundled static K2D and Readex Pro fonts. Validation covers original-deck preservation, template parts, protected slides, bilingual Notes, illustration provenance, PDF text and fonts.

For PowerPoint presentation, install the bundled static K2D and Readex Pro fonts before opening the deck, or use the checked PDF. Font licenses are in `ISDS/fonts/`. Native PowerPoint on this machine initially substituted fonts; the delivered PDF uses the checked LibreOffice export with the correct bundled fonts.
