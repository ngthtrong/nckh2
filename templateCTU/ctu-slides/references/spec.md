# Project JSON: `ctu-slides/1`

The configuration is data, not executable code. Write UTF-8 JSON. All input paths
are relative to the JSON file's own directory, so the project can move together
with its figures/CSVs. The bundled template/fonts resolve relative to the skill.
Output paths come from CLI arguments. No source files are edited by `build`.

```json
{
  "schema": "ctu-slides/1",
  "deck": {
    "slug": "my-topic",
    "title": "Research title",
    "authors": ["Author One", "Author Two"],
    "affiliation": "Can Tho University",
    "event": "Conference or defense",
    "language": "en",
    "target_minutes": 20
  },
  "style": {},
  "sources": [],
  "slides": [
    {"layout": "title", "title": "Research title", "notes": "Opening remarks."},
    {"layout": "overview", "title": "Presentation overview", "items": [
      {"heading": "Problem and gap", "body": "Why this work is needed."},
      {"heading": "Methods and evaluation", "body": "How the question is tested."}
    ], "notes": "Explain the structure."}
  ]
}
```

`slug` controls the output filename. It accepts letters, digits, dots, underscores
and hyphens. `title`/`authors`/`affiliation`/`event` supply cover metadata.
`target_minutes` is a planning field, not a measured rehearsal duration.
No slide count or topic is hard-coded. `init --language vi|en` creates an editable
13-heading starter; its empty bodies/notes are intentional and must be filled.

## Common slide fields

| Field | Meaning |
|---|---|
| `layout` | One of the layouts below. |
| `title` | Required title; shorten if rendered title wraps into the content. |
| `subtitle` | Optional brief line below the title; use it for an essential scope qualifier. |
| `notes` | Spoken explanation. Kept in PowerPoint Notes and exported to Markdown. |
| `source_ids` | String IDs referring to `sources`; details are added to Notes, not bottom footnotes. |
| `qualifications` | Ancillary evidence conditions for Notes. Essential conditions still belong in the main explanation. |

## Layouts

| Layout | Fields and intended size |
|---|---|
| `title` | CTU blue cover; `authors`, `affiliation`, `event` may override deck metadata. |
| `overview` | `items`: 1–6 objects with `heading`, optional `body`. Default position: slide 2. |
| `cards` | `items`: 1–4 parallel boxes, each with `heading`, `body`, optional `color`. |
| `bullets` | `items`: at most 5 strings or `{heading, body, color}` objects. Also suitable for conclusion/future work. |
| `flow` | `items`: 1–5 stages; editable boxes joined by arrows. |
| `equations` | `equations`: 1–3 `{label, latex}` objects; `glossary` explains symbols. Uses matplotlib mathtext, not a full TeX installation. |
| `metrics` | `items`: 1–3 `{name, direction, meaning, color}` objects. Include units and direction. |
| `table` | `headers`: up to 6; `rows`: up to 7; optional positive relative `widths` and `font_size`. |
| `figure` | `path`: PNG/JPEG/GIF; `alt`: meaningful description. Optional `body` creates a right-hand text column; optional `poster` records a GIF static poster. Pre-render SVG/PDF figures to PNG before embedding. |
| `chart` | `csv`, `label_column`, `value_column`, optional `low_column`, `high_column`, `xlabel`, `xlim`, `alt`. Draws an estimate/interval plot from 1–12 rows. |
| `references` | `source_ids`: at most 6 sources on one slide. Add another reference slide for more entries. |
| `closing` | CTU blue closing slide with `title`, `subtitle`, `body`. |

Named colors are `blue`, `teal`, `cyan`, `orange`, `ink`, `muted`, `pale`,
`outline`; an explicit RGB hex color is also accepted. Boxes have uniform
outlines and no left accent strip. There is no bottom-footnote/banner field.
`style` can override the named colors and `title_font`/`body_font` when explicitly
requested; custom fonts must be available to the renderer. Default fonts are
K2D and Readex Pro. Equations may use a separate mathematical symbol font.

## Source records

```json
{
  "id": "method-paper",
  "title": "Canonical source title",
  "citation": "Author(s). Year. Title. Venue, volume, pages.",
  "doi": "10.xxxx/example",
  "url": "https://publisher.example/source",
  "path": "evidence/source.pdf",
  "locator": "Section, page, figure or table supporting the claim"
}
```

Only `id` is structurally required; add the fields supported by the actual source.
IDs must be unique strings. A local `path` must exist and is hashed. Do not invent
DOIs or make a placeholder URL look like a verified reference. Numbered or
author-year IDs are both usable; IDs such as `1`, `2` should be JSON strings.
The engine records locators/URLs; it does not independently establish that a
reference exists or supports a claim. Verify primary sources during authoring.
Reference slides display an optional `label`, a numeric ID, or otherwise the
source's insertion-order number; a long symbolic ID stays in Notes.

`references` slides render `citation` (or title) and a linked URL/DOI. Footer
source notes are never added. If a source has multiple important passages, put
the relevant locator in the slide's `notes` or `qualifications`.

## Charts from CSV

```csv
label,value,low,high
Method A,0.60,0.54,0.66
Method B,0.72,0.66,0.78
```

These numbers are illustrative. Replace them with actual exported data. `low`
and `high` are optional; if intervals exist, both columns are required and each
must contain the estimate. State interval type, test unit, aggregation and metric
direction in Notes/the main explanation. The engine does not choose a confidence
level or invent error bars. It rejects non-finite estimates and invalid intervals.

## GIF assembly

```bash
python3 <skill>/scripts/ctu_slides.py gif \
  --frames assets/frame-1.png assets/frame-2.png assets/frame-3.png \
  --durations 1800 1800 3500 --kind schematic --output assets/process.gif
```

Frames must have equal dimensions. `--kind` is `schematic`, `replay` or
`measured`. The command writes GIF, first-frame PNG poster and a JSON hash record.
The classification is author-provided, not automatically verified. A scenario
sequence must not be described as a real-world timeline without evidence.

## Outputs and validation

`build --spec deck.json [--out output]` generates `<slug>.pptx`,
`speaker-notes.md`, `build-manifest.json`, and rendered equation/chart assets.
Output defaults to the JSON's directory. Unchanged generated PPTX files may be
rebuilt; manually changed PPTX files require preserving/merging edits before a
deliberate `--force` overwrite. Existing source files are never overwritten.

`render --project output [--soffice executable]` writes `<slug>.pdf`,
`checks/slides/*.png`, `checks/contact-sheet.png` and a render log. It includes
hidden slides. GIFs are static in PDF. Fonts are included in a private renderer
configuration, with Windows/macOS users advised to install the bundled fonts.

`check --project output` verifies structural hashes, shapes/canvas, native font
families, note coverage, reference identifiers/URL syntax, PDF count/font family
presence and animated-media embedding. Missing PDF is a failed/incomplete check;
no renderer or failed parsing is never labeled a visual PASS. Blank starter
notes fail note coverage by design until authored. The checks do not certify
research claims, reference existence, PowerPoint playback, or complete absence
of overlapping text. Inspect the rendered contact sheet and detailed pages.

Examples are in `examples/catalog.json`. Regenerate them with
`scripts/make_demo.py`; all figures and CSV values in that catalog are explicitly
illustrative. A copied skill can run without the original repo or its prior deck.
