# EasyChair camera-ready checklist

Source: `remind_for_camera_ready.md`, Springer LNCS/CCIS author instructions,
and the local LTP. Deadline recorded by the organizers: **16 September 2026**;
the exact time and time zone still require confirmation. Internal target:
15 September 2026.

## EasyChair fields

| Field | Prepared value/file |
|---|---|
| Zip file | `paper-6444-camera-ready-source.zip` |
| PDF file | `paper-6444-camera-ready.pdf` |
| Signed copyright form | LTP metadata completed; handwritten signature/date and scanned PDF pending |
| Name of the main LaTeX file | `main.tex` |
| Program to process the main file | `xelatex` |
| Program to process the bibliography | `bibtex` |

## Source package contract

- `main.tex` is at ZIP root and has no prohibited character.
- Include `references.bib`, generated `main.bbl`, `llncs.cls`,
  `splncs04.bst`, `figures/pipeline_v2.pdf`, and
  `figures/rq1_stress_delta_ari.pdf`.
- Exclude caches, logs, old figures, notebooks, experimental results, audit,
  checkpoints, response draft, and other internal documents.
- From a fresh extraction, run:

```bash
xelatex main.tex
bibtex main
xelatex main.tex
xelatex main.tex
```

- Reject the package for TeX errors, undefined references/citations, overfull
  boxes, missing fonts/files, or a page count outside 12–15.
- Compare the clean-build PDF with the upload PDF for text, figures, layout,
  references, and page count. Byte-identical hashes are not required when only
  build metadata differs.

Generate the minimal package after a successful manuscript build:

```bash
python3 scripts/package_camera_ready.py
```

## Metadata and rights

- Title and eight-author order must match PDF, EasyChair, and LTP.
- Thanh-Trong Nguyen is the only corresponding author, proof contact, and the
  Corresponding Author Name to enter on the LTP. His header email is
  `trongb2305615@student.ctu.edu.vn`.
- Retain the organizer's written approval for the eight-author list.
- Confirm acknowledgment `THS2026-68`, affiliations, ORCIDs, email, and
  competing-interest statement.
- One author may sign the LTP for all authors after group agreement. Print,
  sign by hand, date, scan clearly, and do not alter authors/title afterward
  without renewed authorization.
- Springer requests one corresponding author for LNCS/CCIS proceedings; that
  author must be marked in the paper header, have an email in the header, and
  match the LTP. Monitor the corresponding email for the proof request; the
  response window is usually 72 hours and the actual message controls. See
  Springer's [Instructions for Authors of Computer Science Proceedings](https://cms-resources.apps.public.k8s.springernature.io/springer-cms/rest/v1/content/27852130/data/Instructions%20for%20Authors%20PDF),
  Sections 4.1, 5.1, and 6.2.
- The LTP governs only its defined Contribution. Code remains MIT; other
  current non-code material is not newly offered under CC BY; earlier
  `v1.0.1` permissions remain untouched.

## Final external gates

- Confirm deadline time/time zone and how alt text must be delivered.
- Group approves PDF, ZIP, metadata, alt text, and LTP scan.
- Submission owner uploads the three EasyChair files and retains receipts.
- Commit, push, registration, public release, and new archive are separate
  authorized actions.
