#!/usr/bin/env python3
"""Apply the source-bound 2026-11-11 revision to the existing editable deck.

Unchanged slides and the author's cover/overview geometry are retained. Native
shapes illustrate concepts; only the static cohort heatmap reads result data.
No model fitting or benchmark replay takes place in this build.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from build_deck import (ROOT, OUT, SCIENCE, BLUE, CYAN, TEAL, INK, MUTED,
                        ORANGE, PALE, LINE, WHITE, FONT, TITLE_FONT,
                        text, box, line, circle, label, picture, equation,
                        rgb, source)

DECK = OUT / "ISDS2026_Paper_6444_Conference_Deck.pptx"
REVISION = OUT / "research/revision-content.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def replace_text(shape, value):
    """Keep manual position, geometry, paragraph style and first-run style."""
    p = shape.text_frame.paragraphs[0]
    if p.runs:
        p.runs[0].text = value
        for run in list(p.runs)[1:]:
            p._p.remove(run._r)
    else:
        p.add_run().text = value
    for para in list(shape.text_frame.paragraphs)[1:]:
        shape.text_frame._txBody.remove(para._p)


def prepare(s, title, subtitle, section):
    """Retain the master, title, subtitle, section and page-number scaffold."""
    shapes = list(s.shapes)
    for sh in shapes[5:]:
        sh._element.getparent().remove(sh._element)
    replace_text(shapes[0], title)
    replace_text(shapes[1], subtitle)
    replace_text(shapes[2], section)


def report_icon(s, x, y, color=BLUE, scale=1):
    box(s, x, y, .40*scale, .50*scale, WHITE, color, True)
    for dy, width in [(.14, .24), (.23, .24), (.32, .17)]:
        line(s, x+.08*scale, y+dy*scale, x+(.08+width)*scale,
             y+dy*scale, color, 1)


def mini_partition(s, x, y, groups):
    colors = [BLUE, TEAL, ORANGE]
    offset = 0
    for k, group in enumerate(groups):
        w = len(group)*.39+.22
        box(s, x+offset, y, w, .55, "F0F6FA", LINE, True)
        for j, value in enumerate(group):
            circle(s, x+offset+.27+j*.39, y+.28, .14, colors[k])
            text(s, str(value), x+offset+.13+j*.39, y+.15, .28, .25,
                 10, WHITE, True, PP_ALIGN.CENTER)
        offset += w+.16


def house_icon(s, x, y, color=BLUE, scale=1):
    """Editable house, person and water glyphs for a schematic flood scene."""
    roof=s.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE, Inches(x), Inches(y),
                            Inches(.92*scale), Inches(.51*scale))
    roof.fill.solid();roof.fill.fore_color.rgb=rgb(color);roof.line.fill.background()
    box(s,x+.12*scale,y+.40*scale,.68*scale,.64*scale,WHITE,color,True)
    circle(s,x+.46*scale,y+.64*scale,.075*scale,color)
    box(s,x+.38*scale,y+.75*scale,.16*scale,.20*scale,color)
    for j in range(3):
        line(s,x-.11*scale+j*.06*scale,y+(1.02+j*.10)*scale,
             x+(.99-j*.06)*scale,y+(1.02+j*.10)*scale,CYAN,2)


def reports_scene(s):
    prepare(s,"Many reports do not mean many incidents",
            "Schematic flood scenarios: repeated reports, nearby incidents and false destinations", "BACKGROUND")
    scenes=[(.88,"Repeated reports",BLUE,"Many reports,\none physical incident","Risk: repeated trips"),
            (4.91,"Nearby incidents",TEAL,"Close in space,\ndifferent incidents","Risk: a missed incident"),
            (8.94,"False reports",ORANGE,"Several reports,\nno genuine incident","Risk: a false destination")]
    for x,title,color,meaning,risk in scenes:
        box(s,x,1.87,3.63,4.32,PALE,LINE,True)
        text(s,title,x+.18,2.06,3.27,.43,22,color,True)
        # A street and water convey a scene rather than a generic graph.
        box(s,x+.16,3.88,3.31,.54,"E2F2FA",None,True)
        line(s,x+.20,4.14,x+3.42,4.14,WHITE,2,dash=True)
        text(s,meaning,x+.18,4.75,3.27,.85,20,INK,True)
        text(s,risk,x+.18,5.77,3.27,.30,14.5,color)
    # One physical incident receives three overlapping messages.
    x=.88
    house_icon(s,x+1.37,3.00,BLUE,.95)
    for dx,dy in [(.35,2.84),(2.61,2.89),(2.55,3.62)]:
        report_icon(s,x+dx,dy,BLUE,1.12)
        line(s,x+dx+.21,dy+.56,x+1.83,3.60,CYAN,1.3)
    # Distinct physical incidents remain distinct, despite nearby reports.
    x=4.91
    house_icon(s,x+.47,3.04,BLUE,.85)
    house_icon(s,x+2.00,3.04,TEAL,.85)
    report_icon(s,x+.76,2.66,BLUE,.80)
    report_icon(s,x+2.27,2.66,TEAL,.80)
    # A coordinated report cluster has no corresponding house or person.
    x=8.94
    for dx,dy in [(.56,2.99),(1.58,2.77),(2.47,3.15)]:
        report_icon(s,x+dx,dy,ORANGE,1.10)
    for a,b,c,d in [(1.00,3.25,1.61,3.06),(1.99,3.10,2.49,3.40),(.98,3.47,2.49,3.55)]:
        line(s,x+a,b,x+c,d,ORANGE,1.4,dash=True)
    circle(s,x+1.81,4.08,.25,ORANGE)
    text(s,"?",x+1.56,3.85,.50,.47,25,WHITE,True,PP_ALIGN.CENTER)
    source(s,"Redrawn schematic: repeated reports, nearby distinct incidents and a false-only report cluster. No actual report locations or field imagery. Paper 6444, Introduction / RQ1 / RQ3.")


def stage_icon(s, kind, x, y, color=BLUE):
    if kind==0:
        for j in range(3):report_icon(s,x+j*.20,y+j*.04,color,.75)
    elif kind in (1,2):
        pts=[(.05,.12),(.47,.02),(.80,.35),(.34,.55)]
        for a,b in [(0,1),(1,2),(2,3),(3,0),(1,3)]:
            line(s,x+pts[a][0],y+pts[a][1],x+pts[b][0],y+pts[b][1],LINE,1.3)
        for j,(dx,dy) in enumerate(pts):
            circle(s,x+dx,y+dy,.075,color if kind==1 or j<2 else TEAL)
    elif kind==3:
        for j,w in enumerate([.78,.58,.38]):
            box(s,x,y+j*.20,w,.10,color)
    else:
        for j in range(3):
            circle(s,x+j*.32,y+(.23 if j==1 else .05),.065,color)
        line(s,x+.08,y+.06,x+.26,y+.20,color,1.5,True)
        line(s,x+.39,y+.20,x+.58,y+.06,color,1.5,True)


def observable_pipeline(s):
    prepare(s,"Observable pipeline: reports to a fixed schedule",
            "Algorithm inputs and evaluator-only truth stay separate", "PIPELINE")
    label(s,"Algorithm · observable inputs only",.95,1.79,10,BLUE,15)
    stages=[("Reports","Location / time\nEvidence / claims"),
            ("Sparse graph","Affinity weights\nThreshold + top-k"),
            ("Clusters","Louvain / Leiden\nPredicted groups"),
            ("Priority","Evidence families\nBounded score"),
            ("Schedule","Predicted destinations\nResource constraints")]
    for j,(heading,body) in enumerate(stages):
        x=.88+j*2.45;color=BLUE if j<3 else TEAL
        box(s,x,2.31,2.19,1.91,PALE,LINE,True)
        stage_icon(s,j,x+.68,2.51,color)
        text(s,heading,x+.13,3.19,1.93,.36,19.5,color,True,PP_ALIGN.CENTER)
        text(s,body,x+.13,3.57,1.93,.58,12.5,INK,align=PP_ALIGN.CENTER)
        if j<4:line(s,x+2.21,3.22,x+2.43,3.22,CYAN,2,True)
    # Missing observations have an explicit side branch, outside evaluation.
    line(s,1.98,4.24,1.98,4.66,ORANGE,1.6,True)
    box(s,.90,4.74,2.18,1.20,"FCF2E7",None,True)
    text(s,"Missing location\nor time",1.03,4.88,1.92,.51,13.5,ORANGE,True)
    text(s,"Manual review",1.03,5.51,1.92,.32,15,ORANGE,True)
    # Truth enters only the evaluator, after algorithm outputs are frozen.
    line(s,3.80,4.61,12.64,4.61,LINE,1,dash=True)
    label(s,"Offline evaluation",3.96,4.79,6,ORANGE,14)
    text(s,"Fixed outputs",9.15,4.35,1.90,.25,12.5,MUTED)
    line(s,11.77,4.24,11.77,5.16,TEAL,1.7,True,dash=True)
    box(s,3.94,5.21,4.11,.94,"FCF2E7",None,True)
    text(s,"Withheld incident truth",4.11,5.32,3.77,.33,18,ORANGE,True)
    text(s,"Links · benefit · deadlines · harm",4.11,5.81,3.77,.25,13.5)
    line(s,8.08,5.68,8.83,5.68,ORANGE,1.8,True)
    box(s,8.88,5.21,3.82,.94,PALE,LINE,True)
    text(s,"Evaluate fixed outputs",9.05,5.32,3.48,.33,18,TEAL,True)
    text(s,"Clustering · ranking · dispatch",9.05,5.81,3.48,.25,13.5)
    source(s,"Paper 6444, Figure 1 / Algorithms 1–2. Schematic observable-only inference and frozen-output evaluation. Missingness path is specified but not an empirically validated RQ1 result.")


def louvain_network(s,x,y,colored=False):
    pts=[(.42,.47),(.57,1.20),(1.12,.64),(1.28,1.42),
         (2.06,.47),(2.20,1.20),(2.76,.64),(2.92,1.42)]
    edges=[(i,j) for start in (0,4) for i in range(start,start+4)
           for j in range(i+1,start+4)]
    for a,b in edges+[(2,4),(3,5)]:
        internal=(a<4)==(b<4)
        line(s,x+pts[a][0],y+pts[a][1],x+pts[b][0],y+pts[b][1],
             "A7C8DD" if internal else "D8E1E8",2 if internal else .8)
    palette=[BLUE,TEAL,ORANGE,"8A65A0","668539","7D6B56","3A7795","BC5A68"]
    for j,(dx,dy) in enumerate(pts):
        color=(BLUE if j<4 else TEAL) if colored else palette[j]
        circle(s,x+dx,y+dy,.145,color)
        text(s,str(j+1),x+dx-.145,y+dy-.125,.29,.26,11,WHITE,True,PP_ALIGN.CENTER)


def louvain_diagram(s):
    prepare(s,"Louvain: local moves and graph aggregation",
            "Schematic weighted network · modularity is an objective, not incident-label accuracy", "METHOD / CLUSTERING")
    headings=["1  Weighted graph","2  Local moves","3  Aggregate"]
    captions=["Start with one community\nfor each report node.",
              "Move nodes when\nmodularity increases.",
              "Communities become\nweighted super-nodes."]
    for j in range(3):
        x=.88+j*4.03
        box(s,x,1.85,3.64,3.83,PALE,LINE,True)
        text(s,headings[j],x+.16,2.04,3.32,.45,22,BLUE,True)
        text(s,captions[j],x+.19,4.78,3.26,.70,17)
        if j<2:line(s,x+3.68,3.64,x+3.99,3.64,CYAN,2,True)
    louvain_network(s,.91,2.66,False)
    louvain_network(s,4.94,2.66,True)
    # Aggregated vertices retain internal weight as self-loops.
    for x,color,value in [(9.76,BLUE,"C1"),(11.38,TEAL,"C2")]:
        loop=s.shapes.add_shape(MSO_SHAPE.OVAL,Inches(x-.37),Inches(2.83),Inches(.74),Inches(.74))
        loop.fill.background();loop.line.color.rgb=rgb(color);loop.line.width=Pt(2)
        circle(s,x,3.73,.40,color)
        text(s,value,x-.40,3.48,.80,.49,24,WHITE,True,PP_ALIGN.CENTER)
    line(s,10.18,3.73,10.95,3.73,MUTED,1.6)
    text(s,"Between-group weight",9.35,4.30,2.52,.26,11.5,MUTED,align=PP_ALIGN.CENTER)
    text(s,"Repeat on the smaller graph until no further modularity gain is obtained.",
         1.00,6.04,11.40,.40,18,BLUE,True)
    source(s,"Original editable schematic of Louvain local movement and graph aggregation; Blondel et al. (2008). Node positions and colors are pedagogical, not measured rescue data. Self-loops represent aggregate internal weights; detection approximates modularity optimization.")


def stress_heatmap():
    src = ROOT / "thucnghiem/results/rq1_results/aggregate/rq1_stress_paired_effects.csv"
    with src.open() as f:
        rows = list(csv.DictReader(f))
    methods = ["product_cij_louvain", "additive_cij_louvain",
               "additive_cij_louvain_matched_density", "product_cij_leiden", "geo_time_dbscan"]
    scenarios = ["gps_noise_100m", "gps_noise_300m", "time_noise_15min",
                 "time_noise_60min", "exact_transport_copy_2x", "exact_transport_copy_5x"]
    values = np.array([[float(next(r["mean_stress_minus_baseline"] for r in rows
                         if r["metric"] == "ari_original" and r["method"] == m
                         and r["scenario"] == scenario)) for scenario in scenarios]
                       for m in methods])
    for p in (OUT/"fonts").rglob("*.ttf"):
        if "[" not in p.name:
            font_manager.fontManager.addfont(str(p))
    with plt.rc_context({"font.family": [FONT, TITLE_FONT, "DejaVu Sans"]}):
        fig, ax = plt.subplots(figsize=(8.1, 4.25), dpi=190)
        fig.subplots_adjust(left=.27, right=.99, top=.76, bottom=.18)
        fig.text(.55, .95, "Mean paired change in ARI", ha="center", fontsize=18,
                 fontweight="bold", color="#"+BLUE)
        fig.text(.55, .855, "40 held-out runs · negative = degradation", ha="center",
                 fontsize=12, color="#"+MUTED)
        cmap = LinearSegmentedColormap.from_list("stress", ["#EAB575", "#FFF8EB", "#D7EBF6"])
        ax.imshow(values, cmap=cmap, vmin=-.65, vmax=.05, aspect="auto")
        ax.set_yticks(range(5), ["Product Louvain", "Additive Louvain", "MD Additive",
                               "Product Leiden", "Geo-time DBSCAN"], fontsize=12.5)
        ax.set_xticks(range(6), ["GPS\n100 m", "GPS\n300 m", "Time\n15 min",
                               "Time\n60 min", "Copies\n2×", "Copies\n5×"], fontsize=12)
        ax.tick_params(length=0, pad=9, colors="#"+INK)
        for i in range(5):
            for j in range(6):
                ax.text(j, i, f"{values[i,j]:+.3f}", ha="center", va="center",
                        fontsize=13, fontweight="bold", color="#"+INK)
        ax.set_xticks(np.arange(-.5, 6), minor=True)
        ax.set_yticks(np.arange(-.5, 5), minor=True)
        ax.grid(which="minor", color="white", linewidth=3)
        ax.tick_params(which="minor", bottom=False, left=False)
        for sp in ax.spines.values():
            sp.set_visible(False)
        path = SCIENCE/"rq1_stress_static.png"
        fig.savefig(path, facecolor="white")
        plt.close(fig)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path),
            "kind": "Existing exported cohort results, statically replotted; no fitting",
            "input": str(src.relative_to(ROOT)), "input_sha256": sha(src),
            "methods": methods, "scenarios": scenarios, "mean_delta_ari": values.tolist()}


def revise():
    revision = json.loads(REVISION.read_text())
    before_hash = sha(DECK)
    prs = Presentation(DECK)
    if len(prs.slides) != 26:
        raise ValueError("Expected the existing 26-slide presentation")
    # Persist the original logical index on the slide, independent of ordering.
    by_old = {}
    for current, s in enumerate(prs.slides, 1):
        name = s._element.cSld.get("name", "")
        original = int(name.rsplit("-", 1)[1]) if name.startswith("ISDS6444-source-") else current
        by_old[original] = s
        s._element.cSld.set("name", f"ISDS6444-source-{original}")
    if sorted(by_old) != list(range(1, 27)):
        raise ValueError("Logical slide identities are incomplete")
    original_sources = {}
    sources_path=OUT/"research/slide-sources.json"
    previous_sources={r['original_slide']:r['source_notes'] for r in
                      json.loads(sources_path.read_text())} if sources_path.exists() else {}
    for i, s in by_old.items():
        note = s.notes_slide.notes_text_frame.text
        original_sources[i] = note.split("\n\nSource notes: ", 1)[1] if "\n\nSource notes: " in note else previous_sources.get(i,"")

    # Keep the author's shifted overview list and cover edits.
    overview = {
        "Problem and research gap": "Problem and research questions",
        "Why consolidation errors matter": "Why stage-level safeguards need an outcome audit",
        "Data and proposed pipeline": "Methods and observable pipeline",
        "Two separate synthetic experimental suites": "Graph construction, clustering and bounded priority",
        "Methods and evaluation": "Experimental design and metrics",
        "Product / Additive, Louvain, priority, reported metrics": "Two separate suites; run-level evaluation",
        "Conclusions and next validation": "Contributions, limits and conclusion",
        "Contributions, limits and conclusion": "Contributions and conclusions",
        "What the evidence supports and what remains open": "Proved properties, simulated findings, open validation"
    }
    for sh in by_old[2].shapes:
        if sh.has_text_frame and sh.text in overview:
            replace_text(sh, overview[sh.text])
    # These deliberately short descriptions fit the manually narrowed text boxes.
    short_overview = {
        "Why stage-level safeguards need an outcome audit": "Why consolidation errors matter",
        "Graph construction, clustering and bounded priority": "Graph, clustering and bounded priority",
        "Proved properties, simulated findings, open validation": "What is proved, observed and still open"
    }
    for sh in by_old[2].shapes:
        if sh.has_text_frame and sh.text in short_overview:
            replace_text(sh, short_overview[sh.text])
        if sh.has_text_frame and sh.text == "Contributions, limits and conclusion":
            replace_text(sh, "Contributions and conclusions")

    reports_scene(by_old[3])
    observable_pipeline(by_old[5])
    louvain_diagram(by_old[9])

    s = by_old[11]
    prepare(s, "Research questions: do safeguards improve dispatch?",
            "Three stage-specific questions guide the methods, data and evaluation", "RESEARCH QUESTIONS")
    text(s, "A safeguard at one stage does not establish benefit at the next.",
         .98, 1.82, 11.35, .58, 23, BLUE, True)
    rqs = [("RQ1", "Clustering", "Does the tuned Product pipeline improve clustering over Additive?"),
           ("RQ2", "Ranking", "Does duplicate-aware priority align with independent simulated benefit?"),
           ("RQ3", "Dispatch", "How do predicted splits, merges and noise affect dispatch outcomes?")]
    for j, (rq, stage, question) in enumerate(rqs):
        y = 2.77+j*1.05
        label(s, rq, .99, y+.03, 1.0, BLUE, 20)
        text(s, stage, 2.15, y, 2.2, .45, 22, TEAL, True)
        text(s, question, 4.45, y, 7.78, .72, 20)
        if j < 2:
            line(s, .99, y+.84, 12.30, y+.84)
    source(s, "paper/main.tex:150–168, 486–543; RQs moved ahead of technical definitions.")

    s = by_old[6]
    prepare(s, "Generator 3.0: what does one run contain?",
            "RQ1 · geographically anchored, semi-synthetic · 80 runs · 26,288 reports", "DATA / RQ1")
    for j, (h, b) in enumerate([("Copernicus EMSR848", "Historical flood context"),
                               ("OpenStreetMap", "Geographic anchors"),
                               ("WorldPop 2025", "Population reference")]):
        x = .84+j*4.02
        box(s, x, 1.82, 3.76, .99, PALE, LINE, True)
        text(s, h, x+.17, 1.98, 3.42, .34, 18, BLUE, True)
        text(s, b, x+.17, 2.43, 3.42, .25, 13.5, MUTED)
    label(s, "1 run = one generated scenario", .99, 3.08, 10, ORANGE, 17)
    for x in (.84, 4.86, 8.88):
        box(s, x, 3.58, 3.76, 2.36, PALE, LINE, True)
    text(s, "16 latent incidents", 1.02, 3.77, 3.42, .43, 21, BLUE, True)
    for r in range(4):
        for c in range(4):
            circle(s, 1.34+c*.40, 4.54+r*.29, .075, BLUE if c < 2 else TEAL)
    text(s, "Simulated truth", 2.92, 4.70, 1.44, .77, 14, MUTED)
    text(s, "288–370 reports", 5.04, 3.77, 3.40, .43, 21, BLUE, True)
    for j in range(5):
        report_icon(s, 5.13+j*.52, 4.49, TEAL if j == 4 else BLUE)
    text(s, "Genuine + copies + campaigns", 5.04, 5.30, 3.4, .44, 14.5)
    text(s, "Two separate exports", 9.06, 3.77, 3.4, .43, 21, BLUE, True)
    text(s, "Inference: observable reports", 9.06, 4.49, 3.4, .58, 16)
    text(s, "Evaluation: withheld labels", 9.06, 5.22, 3.4, .58, 16, TEAL)
    line(s, 4.61, 4.75, 4.83, 4.75, CYAN, 2, True)
    line(s, 8.63, 4.75, 8.85, 4.75, CYAN, 2, True)
    source(s, "paper/main.tex:441–454; thucnghiem/data/README.md; gold/run_001/run_manifest.json. [9–11]. Icons are schematic, not report images.")

    s = by_old[7]
    prepare(s, "Why two generators? Different questions need different truth",
            "Candidate 4.1 is fully synthetic and independent of the Generator-3.0 sample", "DATA / RQ2–RQ3")
    lanes = [(1.94, BLUE, "Generator 3.0", "80 runs · 16 incidents/run\n26,288 reports", "Incident linkage +\ncontrolled graph stresses", "RQ1", "Clustering"),
             (3.92, TEAL, "Candidate 4.1", "80 datasets · 16 incidents each\n30,229 reports", "Independent benefit,\ndeadlines, service + harm", "RQ2 / RQ3", "Ranking / dispatch")]
    for y, color, h, count, truth, rq, endpoint in lanes:
        box(s, .85, y, 3.64, 1.57, PALE, LINE, True)
        text(s, h, 1.02, y+.17, 3.31, .40, 22, color, True)
        text(s, count, 1.02, y+.79, 3.31, .61, 15)
        line(s, 4.52, y+.79, 4.96, y+.79, color, 2, True)
        box(s, 5.00, y, 3.76, 1.57, PALE, LINE, True)
        text(s, "Required evaluator truth", 5.17, y+.17, 3.42, .39, 17, color, True)
        text(s, truth, 5.17, y+.77, 3.42, .66, 16)
        line(s, 8.80, y+.79, 9.24, y+.79, color, 2, True)
        text(s, rq, 9.50, y+.19, 2.85, .45, 25, color, True)
        text(s, endpoint, 9.50, y+.88, 2.85, .40, 19)
    text(s, "Separate samples: complementary stage tests, not one common-sample validation chain.",
         .98, 5.83, 11.50, .46, 17.5, INK, True)
    source(s, "paper/main.tex:441–469, 486–543. Candidate 4.1: 339–424 reports/dataset. Its outcomes are not inferred from the priority formula.")

    s = by_old[8]
    prepare(s, "Why test Product? Geography gates the whole affinity",
            "A plausible mechanism to test; a geographic edge bound alone does not ensure better clusters", "METHOD / GRAPH")
    for y, h, expr, name in [(1.80, "Product", r"w^{\times}_{ij}=a_i a_jG_{ij}(\beta T_{ij}+\gamma C_{ij})", "product"),
                             (3.00, "Additive", r"w^{+}_{ij}=a_i a_j(\alpha G_{ij}+\beta T_{ij}+\gamma C_{ij})", "additive")]:
        box(s, .84, y, 7.16, 1.07, PALE, LINE, True)
        label(s, h, 1.01, y+.11, 3, BLUE, 14)
        equation(s, expr, name, 1.04, y+.49, 6.72, .43)
    text(s, "G  Geographic proximity\nT  Temporal proximity\nC  Context similarity\na  Location/time admission", 8.32, 1.92, 4.0, 1.87, 18)
    text(s, "alpha, beta, gamma: nonnegative weights", 8.32, 3.91, 4.0, .33, 12, MUTED)
    label(s, "Illustrative pair · same time and context, far apart", .99, 4.42, 11.4, ORANGE, 14)
    box(s, .94, 4.98, 3.40, 1.18, PALE, LINE, True)
    circle(s, 1.32, 5.41, .13, BLUE)
    circle(s, 3.93, 5.41, .13, TEAL)
    line(s, 1.55, 5.41, 3.71, 5.41, MUTED, 1.3, dash=True)
    text(s, "Report A", 1.00, 5.78, 1.08, .27, 12.5)
    text(s, "Report B", 3.20, 5.78, 1.08, .27, 12.5, align=PP_ALIGN.RIGHT)
    text(s, "G = .02; T = C = .90; a = 1; all weights = 1", 4.72, 4.99, 7.61, .37, 15)
    text(s, "Product  .036", 4.72, 5.51, 3.35, .49, 26, BLUE, True)
    text(s, "Additive  1.820", 8.66, 5.51, 3.73, .49, 26, TEAL, True)
    source(s, "paper/main.tex:250–325; [2] spatial–range product precedent. Pair values are invented teaching inputs, not benchmark results or tuned parameters. Retention thresholds and actual pipeline settings are not compared by this example.")

    s = by_old[10]
    prepare(s, "Bounded priority limits copies, not dishonest claims",
            "Duplicate handling and information verification are different tasks", "METHOD / PRIORITY")
    for j in range(3):
        report_icon(s, 1.15+j*.29, 2.03+j*.15, BLUE, 1.7)
    text(s, "Repeated payload", .99, 3.22, 2.74, .39, 18, BLUE, True)
    line(s, 3.30, 2.76, 3.95, 2.76, CYAN, 2, True)
    box(s, 4.09, 1.99, 3.78, 1.72, PALE, LINE, True)
    text(s, "Evidence families", 4.29, 2.18, 3.40, .42, 21, BLUE, True)
    text(s, "Exact / near-copy grouping\nFamily maxima", 4.29, 2.91, 3.40, .68, 17)
    line(s, 7.91, 2.76, 8.40, 2.76, CYAN, 2, True)
    box(s, 8.53, 1.99, 3.91, 1.72, PALE, LINE, True)
    text(s, "Bounded score", 8.73, 2.18, 3.51, .42, 21, TEAL, True)
    text(s, "Confidence, clipping\nand saturation", 8.73, 2.91, 3.51, .68, 17)
    equation(s, r"0\leq P_k\leq\mu,\qquad 1\leq\mu\leq2", "priority_bound", 3.72, 4.01, 6.09, .51)
    for x, h, b, color in [(1.00, "Exact-copy invariance", "Requires fixed families and score inputs.", BLUE),
                           (6.93, "Inflated headcounts remain unverified", "Clipping caps influence; it does not verify a claim.", ORANGE)]:
        text(s, h, x, 4.99, 5.42, .57, 19, color, True)
        text(s, b, x, 5.70, 5.42, .56, 16)
    source(s, "paper/main.tex:380–421, 620–677. The confidence Q is a heuristic, not a calibrated probability of truth. Fixed-family exact copies differ from changed or coordinated payloads.")

    s = by_old[13]
    prepare(s, "One held-out run: compare groups with withheld truth",
            "ARI measures partition agreement, corrected for chance · schematic partition example", "METRICS / RQ1")
    box(s, .92, 2.55, 2.30, 1.47, PALE, LINE, True)
    text(s, "Report inputs", 1.08, 2.75, 1.99, .43, 18, BLUE, True)
    for j in range(3):
        report_icon(s, 1.15+j*.52, 3.39, BLUE, .8)
    line(s, 3.24, 3.00, 3.71, 2.53, CYAN, 2, True)
    box(s, 3.80, 1.96, 4.10, 1.45, PALE, LINE, True)
    text(s, "Clustering → predicted groups", 3.98, 2.10, 3.75, .40, 18, BLUE, True)
    mini_partition(s, 4.02, 2.70, [[1, 2], [3], [4, 5, 6]])
    box(s, 3.80, 4.01, 4.10, 1.45, "FCF2E7", None, True)
    text(s, "Withheld truth · evaluator only", 3.98, 4.15, 3.75, .40, 17, ORANGE, True)
    mini_partition(s, 4.02, 4.77, [[1, 2, 3], [4, 5, 6]])
    line(s, 7.95, 2.72, 8.64, 3.35, CYAN, 2, True)
    line(s, 7.95, 4.74, 8.64, 4.07, ORANGE, 2, True)
    box(s, 8.78, 2.86, 3.59, 1.87, PALE, LINE, True)
    text(s, "ARI", 9.00, 3.02, 3.15, .70, 38, BLUE, True)
    text(s, "Compare partitions after\npredictions are fixed", 9.00, 3.95, 3.15, .65, 17)
    text(s, "ARI: 1 = identical; ≈ 0 = chance; negative values are possible. Higher is better.",
         .99, 5.75, 11.50, .38, 16)
    text(s, "Pairwise F1 complements ARI by balancing false merges and false splits.",
         .99, 6.16, 11.50, .31, 14, MUTED)
    source(s, "[3] Hubert & Arabie (1985); paper/main.tex:522–543. Six-dot partitions are schematic and have no displayed measured ARI. ARI is not percent correctly classified. Independent units are runs, not individual report pairs.")

    s = by_old[16]
    prepare(s, "RQ1: no Product composition advantage is established",
            "Held-out Generator-3.0 test split · 40 paired runs", "RESULTS / RQ1")
    picture(s, "rq1_ari_ci.png", .80, 1.82, 8.02, 4.18)
    for y, h, v, color in [(1.98, "Additive Louvain", "0.9191", TEAL),
                            (3.27, "Product Louvain", "0.9072", BLUE)]:
        text(s, h, 9.04, y, 3.35, .35, 18, color, True)
        text(s, v, 9.04, y+.43, 3.35, .58, 33, color, True)
    text(s, "Paired Holm p = .2560", 9.04, 4.53, 3.35, .36, 15, MUTED)
    text(s, "16.49%", 9.04, 5.05, 3.35, .58, 32, ORANGE, True)
    text(s, "Product false destinations", 9.04, 5.75, 3.35, .47, 15, ORANGE, True)
    source(s, "paper/main.tex:548–591; benchmark_summary.csv. 16.49% is the fraction of predicted destinations that are false, not the fraction of fake reports. Zero fake absorption does not imply fake rejection. CIs are unadjusted bootstrap intervals.")

    heatmap = stress_heatmap()
    s = by_old[17]
    prepare(s, "RQ1: fivefold copies expose a major failure case",
            "Static 40-run result plus one-run illustration · separate fixed batch stresses", "RESULTS / RQ1 STRESS")
    label(s, "One-run illustration", .99, 1.93, 4.0, BLUE, 14)
    picture(s, "graph_stress.gif", .87, 2.48, 4.34, 1.96,
            "One-run graph reproduction under separate fixed conditions; not a time series. The static cohort result is always visible alongside it.")
    text(s, "5× copies · Product ΔARI", .99, 4.72, 4.15, .43, 18, ORANGE, True)
    text(s, "−0.6108", .99, 5.21, 4.15, .69, 36, ORANGE, True)
    text(s, "95% CI [−.6318, −.5881]", .99, 6.01, 4.15, .29, 13.5, MUTED)
    picture(s, "rq1_stress_static.png", 5.24, 1.92, 7.23, 4.29,
            "Static mean paired ARI change over 40 held-out runs, five methods and six perturbations. Negative means degradation; cells come from the existing paired-effects CSV.")
    source(s, "paper/main.tex:593–618; rq1_stress_paired_effects.csv. Displayed interval is the unadjusted paired-bootstrap 95% CI. MD = matched-density. Zero change for DBSCAN does not mean high absolute accuracy; two copy levels do not identify a collapse threshold.")

    s = by_old[21]
    prepare(s, "Three contributions, with explicit evidence limits",
            "Mathematical guarantees, simulated findings and unresolved validation are different claims", "CONTRIBUTIONS / LIMITS")
    columns = [(1.00, 2.24, "CONTRIBUTION", INK), (3.45, 2.67, "MATHEMATICALLY\nPROVED", BLUE),
               (6.40, 2.72, "OBSERVED IN\nSIMULATION", TEAL), (9.42, 2.96, "NOT YET\nESTABLISHED", ORANGE)]
    for x, w, h, color in columns:
        text(s, h, x, 1.87, w, .67, 15.5, color, True)
    cells = [
        ("1  Product graph", "Conditional retained-\nedge localization", "No composition\nadvantage established", "Cluster compactness\nor transfer advantage"),
        ("2  Family-wise\npriority", "Copy invariance with\nfixed families / inputs", "Zero copy drift;\nweak benefit alignment", "Claim authenticity or\ntrue headcounts"),
        ("3  Downstream\naudit", "No dispatch-policy\nguarantee", "Paired audit exposes\nadverse outcomes", "Expert priorities or\nfield effectiveness")
    ]
    for j, row in enumerate(cells):
        y = 2.78+j*1.13
        box(s, .86, y-.09, 11.63, 1.04, PALE if j != 1 else "F6F8FA", None, True)
        for (x, w, _, color), content in zip(columns, row):
            text(s, content, x, y+.08, w, .79, 17 if x > 3 else 18, color, x < 3)
    source(s, "paper/main.tex:150–188, 250–325, 380–421, 756–800. Three contributions are conditional theory, invariant scoring and a staged downstream audit; simulated evidence does not validate source authenticity or field policy.")

    s = by_old[22]
    prepare(s, "Conclusion: stage safeguards do not establish dispatch benefit",
            "Conditional theory and a synthetic audit identify what still needs validation", "CONCLUSION")
    text(s, "A valid local guarantee is only one part\nof the report-to-dispatch problem.",
         1.02, 1.92, 11.10, 1.00, 27, BLUE, True)
    for j, (h, b, color) in enumerate([
        ("Clustering", "Conditional edge bound;\nno Product advantage\nestablished.", BLUE),
        ("Ranking", "Exact-copy stability;\nbenefit alignment\nremains weak.", TEAL),
        ("Dispatch", "Stage safeguards do not\nensure improved\nsimulated outcomes.", ORANGE)]):
        x = .93+j*4.02
        box(s, x, 3.58, 3.63, 2.30, PALE, LINE, True)
        text(s, h, x+.19, 3.79, 3.25, .49, 25, color, True)
        text(s, b, x+.19, 4.55, 3.25, 1.10, 18)
        if j < 2:
            line(s, x+3.67, 4.64, x+3.98, 4.64, CYAN, 2, True)
    source(s, "paper/main.tex:756–800. Proved properties, within-generator results and deployment claims remain separate evidence layers.")

    # Preserve the future-work layout, while making authenticity an explicit gap.
    for sh in by_old[23].shapes:
        if sh.has_text_frame and sh.text == "Expert priority validation":
            replace_text(sh, "Expert and source validation")
        elif sh.has_text_frame and sh.text == "Define and assess rescue priorities with domain experts and operational stakeholders.":
            replace_text(sh, "Verify headcounts and source credibility; assess priorities with rescue experts.")

    # Reorder slide relationships, preserving every original slide and layout.
    elements = {int(e.id): e for e in prs.slides._sldIdLst}
    for original in revision["order"]:
        prs.slides._sldIdLst.append(elements[by_old[original].slide_id])
    for new_number, s in enumerate(prs.slides, 1):
        if new_number in (1, 26):
            continue
        # The final two-digit frame number is deliberately changed after moving RQs.
        page_shape = list(s.shapes)[4]
        replace_text(page_shape, f"{new_number:02d}")

    titles = []
    provenance = []
    for i, (s, original) in enumerate(zip(prs.slides,revision['order']), 1):
        title = next((sh.text for sh in s.shapes if sh.name == "Slide title"),
                     "Title" if i == 1 else "Thank you — Questions and discussion")
        titles.append({"slide": i, "original_slide": original, "title": title})
        provenance.append({"slide":i,"original_slide":original,"title":title,
                           "source_notes":getattr(s,"_source_note",None) or original_sources[original]})
        # Remove picture relationships belonging only to the replaced visuals.
        embeds=set(s._element.xpath('//@r:embed'))
        for rel in list(s.part.rels.values()):
            if rel.reltype.endswith('/image') and rel.rId not in embeds:
                s.part.drop_rel(rel.rId)
    (OUT/"slide-index.json").write_text(json.dumps(titles, ensure_ascii=False, indent=2)+"\n")
    sources_path.write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+"\n")
    subprocess.run([sys.executable,str(OUT/"research/write_notes.py")],check=True)
    notes=json.loads((OUT/"research/speaker-notes.json").read_text())
    for s,row in zip(prs.slides,notes):
        # Presenter-facing notes contain spoken English followed by Vietnamese.
        # Provenance remains in slide-sources.json, outside the requested script.
        s.notes_slide.notes_text_frame.text = row["notes"]
        for p in s.notes_slide.notes_text_frame.paragraphs:
            for r in p.runs:
                r.font.name = FONT
                r.font.size = Pt(12)
    prs.save(DECK)
    manifest_path = OUT/"build-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest.pop("pdf_sha256", None)
    old_template = "CTU_PowerPoint_Template_English.pptx"
    new_template = "templateCTU/ctu-slides/assets/CTU_PowerPoint_Template_English.pptx"
    if old_template in manifest["inputs"] and not (ROOT/old_template).exists():
        if sha(ROOT/new_template) != manifest["inputs"][old_template]:
            raise ValueError("Tracked CTU template differs from the original template hash")
        manifest["inputs"][new_template] = manifest["inputs"].pop(old_template)
    old_reference = "ID_8253_Chromatic_Anchoring_ISDS2026_Conference_Deck.pptx"
    if old_reference in manifest["inputs"] and not (ROOT/old_reference).exists():
        manifest.setdefault("historical_reference_inputs", {})[old_reference] = {
            "sha256": manifest["inputs"].pop(old_reference),
            "status": "Original style-reference PPTX unavailable; not an input to this in-place revision",
            "available_preview": "ISDS/checks/reference/ID_8253_Chromatic_Anchoring_ISDS2026_Conference_Deck.pdf"}
    reference_pdf = ROOT/"ISDS/checks/reference/ID_8253_Chromatic_Anchoring_ISDS2026_Conference_Deck.pdf"
    manifest["inputs"][str(reference_pdf.relative_to(ROOT))] = sha(reference_pdf)
    previous = manifest.get("revision", {})
    manifest.update({"deck_sha256": sha(DECK), "research_questions_slide": 5,
                     "scripts": {str(p.relative_to(ROOT)): sha(p) for p in sorted((OUT/"scripts").glob("*.py"))},
                     "notes_sha256": sha(OUT/"research/speaker-notes.json"),
                     "talk_track_sha256":sha(OUT/"research/talk-track.json"),
                     "speaker_script_sha256":sha(OUT/"speaker-notes.md"),
                     "notes_generator_sha256":sha(OUT/"research/write_notes.py"),
                     "slide_sources_sha256":sha(sources_path),
                     "speaker_script_languages":["English","Vietnamese"],
                     "speaker_script_order":"All 26 English slides, then all 26 Vietnamese slides; content only; no citations",
                     "references_sha256": sha(OUT/"research/references.json"),
                     "revision": {"date": revision["revision"],
                        "input_deck_sha256": previous.get("input_deck_sha256", before_hash),
                        "original_slide_order": revision["order"],
                        "preserved": "Existing cover edits, overview geometry, masters, fonts, reference slides, unchanged scientific charts and the graph-stress GIF",
                        "content_sha256": sha(REVISION), "new_static_heatmap": heatmap,
                        "new_editable_schematics": ["three flood-report scenarios", "observable-to-evaluator pipeline", "static Louvain phases with aggregate self-loops", "one generated run", "separate data suites", "far-apart report pair", "copy handling versus claim verification", "run-to-ARI evaluation", "contribution/evidence matrix", "stage-to-outcome conclusion"],
                        "benchmark_execution": False,
                        "external_images": False,
                        "visual_provenance": "Original editable schematics; invented teaching values explicitly labeled; result heatmap reads existing exports."}})
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n")
    print(f"Revised {DECK}: 26 slides; RQs at slide 5; static stress results at slide 17")


if __name__ == "__main__":
    revise()
