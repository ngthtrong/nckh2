---
name: ctu-slides
description: Create or revise editable research presentations using the bundled Can Tho University PowerPoint template. Use for CTU conference, thesis, project, and research slides, including diagrams, equations, figures, GIFs, speaker notes, and PDF previews.
---

# CTU research slides

Create an editable `.pptx` from the bundled CTU master, with a PDF preview and
speaker notes when requested. This skill is self-contained: resolve `assets/`,
`scripts/`, and `references/` relative to this file, never against another repo.

## Scope and content

Read the current paper/report, supplied outline, and reference deck before
adapting content. Retain the author's scientific scope, metadata, metric
definitions, evidence limits, and actual result values. Explain methods and
metrics before showing their results. Do not carry study-specific facts from
another deck into a new topic.

Honor the current task's stopping point. For an outline-only request, discuss the
outline without building files. For a request to build from an already settled
outline, proceed without another approval cycle. Do not assume that using this
skill authorizes experiments, manuscript edits, publication, or external uploads.

## Visual contract

- Use `assets/CTU_PowerPoint_Template_English.pptx` directly; preserve its CTU
  branding, footer artwork, and 16:9 canvas. Resolve layouts by name.
- Titles/headings use **K2D**; ordinary text uses **Readex Pro**. The template's
  explicit text styles override its generic Calibri theme fallback. Static
  Regular/Bold fonts and OFL licenses are bundled in `assets/fonts/`.
- Keep boxes simple: pale fill and a uniform thin outline. **No colored strip
  along a box's left edge. No added bottom footnotes or summary banners.** Put
  source locators and ancillary qualifications in speaker notes. Keep essential
  scientific conditions in the main explanation; preserve reference slides.
- Prefer a legible figure, comparison, equation, process, or short statement
  over repeated text boxes. Put Overview at slide 2 by default. Keep background,
  research gap, conclusion, and future work separate when requested. Slide count
  follows the topic and available speaking time; it is not fixed at 26.
- Mathematical symbols may require a math font inside rendered equations;
  ordinary figure labels must follow the CTU fonts. Do not shrink text until it
  becomes unreadable to force a dense slide to fit.

These are this template package's defaults; an explicit user change takes
precedence. Adapt `style` in a project specification for an authorized variation.

## Reusable implementation

Use `scripts/ctu_slides.py` with a project JSON, rather than editing a previous
topic's hard-coded generator. Read [references/spec.md](references/spec.md) for
layouts, paths, source records, figures, tables, and chart inputs.

```bash
python3 <skill>/scripts/ctu_slides.py init --project <new-project>
python3 <skill>/scripts/ctu_slides.py build --spec <new-project>/deck.json
python3 <skill>/scripts/ctu_slides.py render --project <new-project>
python3 <skill>/scripts/ctu_slides.py check --project <new-project>
```

Install `requirements.txt` in an environment appropriate to the workspace.
`render` requires a local LibreOffice installation, or an explicit
`--soffice /path/to/soffice` executable. It creates a private font configuration
that includes the bundled fonts. When no renderer is available, deliver the PPTX
and state that PDF/render inspection remains incomplete; do not label it passed.

`init` never overwrites an existing project specification. `build` detects edits
to a previously generated PPTX and stops before replacing it; inspect those edits
and preserve or incorporate them before deliberately using `--force`.

## Sources and animations

For quantitative charts, read a supplied CSV/artifact and retain source paths,
column names, units, directions, and confidence-interval meaning. Never infer
unreported values from decorative examples. Every catalog number is explicitly
illustrative; the catalog is a layout demonstration, not research evidence.

Use native shapes for editable diagrams. For animations, the `gif` command
assembles supplied PNG/JPEG frames with configurable durations. Identify whether
an animation is schematic, a replay, or measured data; scenario order must not
imply a real event timeline. Keep a static poster. PNG/GIF captions must not add
the bottom footnotes prohibited by the visual contract.

## Completion checks

Run the provided build/check commands and inspect actual rendered pages,
including image labels, equation glyphs, reference slides, and title wrapping.
The checker verifies canvas bounds, note coverage, template fonts, reference
links, file hashes, and GIF embedding; it does not prove semantic correctness or
detect every possible text overlap. Repair visible clipping before delivery.
After a relevant edit, refresh the PPTX, PDF, previews, and manifest together.

Report the PPTX/PDF locations, material rendering limitations, and how to open
animations in Slide Show mode. Do not equate a successful file build with
scientific acceptance, venue compliance, author approval, or field validity.
