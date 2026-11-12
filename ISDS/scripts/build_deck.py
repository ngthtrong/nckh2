#!/usr/bin/env python3
"""Build the editable CTU / ISDS-6444 conference presentation.

Run from the repository root. Quantitative assets are generated separately by
build_science_assets.py; this script never modifies research artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ISDS"
ASSETS = OUT / "assets"
SCIENCE = ASSETS / "science"
NATIVE = ASSETS / "native"
TEMPLATE = ROOT / "CTU_PowerPoint_Template_English.pptx"
if not TEMPLATE.exists():
    TEMPLATE = ROOT / "templateCTU/ctu-slides/assets/CTU_PowerPoint_Template_English.pptx"
BLUE, CYAN, TEAL = "0070C0", "00AFEF", "009988"
INK, MUTED, ORANGE, RED = "17212B", "526474", "C97724", "AD363C"
PALE, LINE, WHITE = "F0F6FA", "D6E3EC", "FFFFFF"
FONT = "Readex Pro"
TITLE_FONT = "K2D"


def rgb(c):
    return RGBColor.from_string(c)


def text(s, value, x, y, w, h, size=20, color=INK, bold=False,
         align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.TOP, name=None):
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        box.name = name
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(.01)
    tf.margin_top = tf.margin_bottom = Inches(.01)
    tf.vertical_anchor = valign
    for i, line in enumerate(value.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_before = Pt(0)
        p.space_after = Pt(3)
        p.line_spacing = 1.13
        # Readex Pro lacks directional-arrow glyphs; K2D supplies these while
        # keeping all editable audience text inside the template font families.
        for fragment in re.split(r"([↑↓→←↔])",line):
            if not fragment:
                continue
            run = p.add_run()
            run.text = fragment
            run.font.name = TITLE_FONT if bold or fragment in "↑↓→←↔" else FONT
            run.font.size = Pt(size)
            run.font.bold = bold
            run.font.color.rgb = rgb(color)
    return box


def box(s, x, y, w, h, fill=PALE, stroke=None, radius=False, name=None):
    sh = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
                            Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        sh.name = name
    sh.fill.solid()
    sh.fill.fore_color.rgb = rgb(fill)
    if stroke:
        sh.line.color.rgb = rgb(stroke)
        sh.line.width = Pt(.8)
    else:
        sh.line.fill.background()
    if radius:
        sh.adjustments[0] = .08
    return sh


def line(s, x1, y1, x2, y2, color=LINE, width=1.5, arrow=False, dash=False):
    sh = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    sh.line.color.rgb = rgb(color)
    sh.line.width = Pt(width)
    if arrow:
        el = OxmlElement("a:tailEnd")
        el.set("type", "triangle")
        sh.line._get_or_add_ln().append(el)
    if dash:
        sh.line.dash_style = 4
    return sh


def circle(s, x, y, r, fill=BLUE, stroke=None):
    sh = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x-r), Inches(y-r), Inches(2*r), Inches(2*r))
    sh.fill.solid()
    sh.fill.fore_color.rgb = rgb(fill)
    if stroke:
        sh.line.color.rgb = rgb(stroke)
    else:
        sh.line.fill.background()
    return sh


def label(s, value, x, y, w=2, color=BLUE, size=14):
    return text(s, value.upper(), x, y, w, .30, size, color, True)


def panel(s, x, y, w, h, heading, body, accent=BLUE, size=19):
    box(s, x, y, w, h, PALE, LINE, True)
    if h < 1.85:
        text(s, heading, x+.20, y+.16, w-.40, .43, 18, accent, True)
        text(s, body, x+.20, y+.69, w-.40, h-.77, size)
    else:
        text(s, heading, x+.22, y+.19, w-.44, .65, 20, accent, True)
        text(s, body, x+.22, y+.99, w-.44, h-1.10, size)


def number(s, value, x, y, color=BLUE):
    circle(s, x+.20, y+.20, .20, color)
    text(s, str(value), x, y+.01, .40, .39, 16, WHITE, True, PP_ALIGN.CENTER)



def source(s, value):
    # User preference: no added footnotes at the bottom of audience slides.
    # Keep source locators in the PowerPoint notes instead.
    s._source_note = value


def picture(s, name, x, y, w, h, alt=None):
    path = Path(name)
    if not path.is_absolute():
        path = SCIENCE / path
    if not path.exists():
        raise FileNotFoundError(path)
    with Image.open(path) as im:
        iw, ih = im.size
    scale = min(w / iw, h / ih)
    dw, dh = iw*scale, ih*scale
    sh = s.shapes.add_picture(str(path), Inches(x+(w-dw)/2), Inches(y+(h-dh)/2),
                              width=Inches(dw), height=Inches(dh))
    sh.name = "Asset: " + path.name
    nv = sh._element.find("{http://schemas.openxmlformats.org/presentationml/2006/main}nvPicPr")
    nv.find("{http://schemas.openxmlformats.org/presentationml/2006/main}cNvPr").set("descr", alt or path.stem)
    return sh


def equation(s, expr, name, x, y, w, h, color=INK):
    p = NATIVE / (name + ".png")
    fig = plt.figure(figsize=(10, 1.1), dpi=220)
    fig.text(.5, .50, "$"+expr+"$", ha="center", va="center", fontsize=30, color="#"+color)
    fig.savefig(p, transparent=True, bbox_inches="tight", pad_inches=.08)
    plt.close(fig)
    picture(s, p, x, y, w, h, expr)


def slide(prs, title, subtitle="", section="", n=0):
    s = prs.slides.add_slide(prs.slide_layouts[5])
    for sh in list(s.shapes):
        sh._element.getparent().remove(sh._element)
    text(s, title, .94, .35, 11.65, .66, 29, BLUE, True, valign=MSO_ANCHOR.MIDDLE, name="Slide title")
    if subtitle:
        text(s, subtitle, .95, 1.11, 11.52, .40, 13.5, MUTED)
    if section:
        label(s, section, 10.12, .08, 2.20, MUTED, 8.5)
    box(s, 12.60, 7.065, .47, .32, WHITE)
    text(s, f"{n:02d}", 12.65, 7.10, .30, .20, 9, MUTED, align=PP_ALIGN.RIGHT)
    return s


def map_sketch(s, x, y, w, h):
    """Pedagogical scene: report positions are explicitly schematic."""
    box(s, x, y, w, h, "F5F9FC", LINE)
    for v in (.22,.52,.78):
        line(s,x+w*v,y+.10,x+w*(v-.11),y+h-.10,"DBE6EC",1)
    for v in (.18,.49,.76):
        line(s,x+.10,y+h*v,x+w-.10,y+h*(v+.08),"DBE6EC",1)
    pts=[(.22,.45),(.27,.37),(.30,.49),(.38,.38),(.66,.45),(.70,.57),(.75,.49),(.80,.59)]
    for a,b in [(0,1),(1,2),(0,2),(2,3),(4,5),(5,6),(6,7),(4,6)]:
        line(s,x+w*pts[a][0],y+h*pts[a][1],x+w*pts[b][0],y+h*pts[b][1],CYAN,2)
    for i,(a,b) in enumerate(pts):
        circle(s,x+w*a,y+h*b,.075,BLUE if i<4 else TEAL)
    for a,b,t,c in [(.20,.72,"One incident / several reports",BLUE),(.69,.23,"Nearby distinct incident",TEAL)]:
        text(s,t,x+w*a-.6,y+h*b,w*.43,.48,13,c,True)
    circle(s,x+w*.50,y+h*.78,.09,ORANGE)
    text(s,"False report",x+w*.50+.14,y+h*.78-.12,1.75,.37,13,ORANGE,True)


def metrics_row(s, y, name, direction, definition, color=BLUE):
    box(s,.80,y,11.75,1.25,PALE,LINE,True)
    text(s,name,.99,y+.18,2.48,.47,22,color,True)
    text(s,direction,1.00,y+.79,2.4,.25,12,MUTED)
    text(s,definition,3.72,y+.25,8.43,.80,20)


def build():
    NATIVE.mkdir(parents=True, exist_ok=True)
    prs = Presentation(TEMPLATE)
    for sid in list(prs.slides._sldIdLst):
        prs.part.drop_rel(sid.rId)
        prs.slides._sldIdLst.remove(sid)
    titles=[]
    def add(title, sub="", sec=""):
        titles.append(title)
        return slide(prs,title,sub,sec,len(titles))

    # 01 — CTU cover, preserving the original institutional layout and artwork.
    s = prs.slides.add_slide(prs.slide_layouts[0]); titles.append("Title")
    for sh in list(s.shapes): sh._element.getparent().remove(sh._element)
    text(s,"Stress-Testing Product-Gated Clustering\nand Bounded Priority Ranking\nfor Flood-Rescue Reports: A Synthetic Study",
         .77,2.10,11.80,1.92,28,WHITE,True,PP_ALIGN.CENTER)
    text(s,"Thanh-Trong Nguyen · Ngoc-Anh Le · Nhu-Quynh Nguyen · Tuong-Hung Cao\nHung-Thinh Ngo · Xuan-Phuong Chau · Lan Phuong Phan · Thanh-Khoa Nguyen",
         .70,4.19,11.94,.70,14.4,WHITE,align=PP_ALIGN.CENTER)
    text(s,"College of Information and Communication Technology · Can Tho University\nISDS 2026  |  Paper 6444  |  Synthetic stress-testing study",
         .74,5.40,11.85,.80,17,WHITE,align=PP_ALIGN.CENTER)

    # 02 — Restored overview.
    s=add("Presentation overview","From noisy reports to measured scheduling consequences","OVERVIEW")
    items=[("01","Problem and research gap","Why consolidation errors matter"),
           ("02","Data and proposed pipeline","Two separate synthetic experimental suites"),
           ("03","Methods and evaluation","Product / Additive, Louvain, priority, reported metrics"),
           ("04","Results for RQ1–RQ3","Clustering → ranking → dispatch"),
           ("05","Conclusions and next validation","What the evidence supports and what remains open")]
    for i,(n,h,b) in enumerate(items):
        yy=1.76+i*.84
        text(s,n,.94,yy,.62,.40,23,CYAN,True)
        text(s,h,1.85,yy,9.9,.35,21,INK,True)
        text(s,b,1.86,yy+.37,9.9,.27,13.5,MUTED)
    source(s,"Source: paper/main.tex, Introduction and Related Work; presentation structure adapted from the supplied Paper 8253 deck.")

    # 03 — Background and an explicitly schematic report map.
    s=add("Many reports do not mean many incidents","Repeated, nearby and false reports create different operational risks","BACKGROUND")
    map_sketch(s,.80,1.78,7.0,4.18)
    for i,(h,b,c) in enumerate([("Repeated evidence","One event can generate many overlapping reports.",BLUE),
                              ("False merges / splits","Nearby events may be merged; one event may be split.",TEAL),
                              ("False destinations","Coordinated reports may create a destination with no genuine incident.",ORANGE)]):
        text(s,h,8.15,1.87+i*1.34,4.15,.45,21,c,True)
        text(s,b,8.15,2.40+i*1.34,4.15,.78,17)
    source(s,"[6] Sakaki et al. (2010). Study-specific failure modes: Paper 6444, Introduction and RQ1/RQ3. Map is schematic.")

    # 04 — Related work and gap kept separate from background.
    s=add("Related approaches and the study gap","Three research strands meet at the report-to-dispatch boundary","RESEARCH GAP")
    strands=[("Social sensing","Event detection and crisis-information extraction","[6–8]"),
             ("Report consolidation","Graph community detection and density-based clustering","[1]; Paper 6444 §1"),
             ("Humanitarian dispatch","Competing need, efficiency and equity objectives","[5]")]
    for i,(h,b,c) in enumerate(strands):
        panel(s,.80+i*4.02,1.86,3.76,2.45,h,b,size=18)
        text(s,c,1.02+i*4.02,3.93,3.25,.22,11,MUTED)
    label(s,"Gap examined in this study",.97,4.68,8,ORANGE)
    text(s,"How do predicted splits, merges and false destinations propagate\nthrough ranking into a scheduler that cannot consult incident truth?",
         .97,5.06,11.55,.95,23,INK,True)
    source(s,"[1] Blondel et al. (2008); [5] Gralla et al. (2014); [6] Sakaki et al. (2010); [7] CrisisMMD; [8] FloodNet.")

    # 05 — Editable pipeline, with an observable/evaluator boundary.
    s=add("Observable pipeline and contribution boundaries","Predictions are fixed before evaluator-only truth is joined","PIPELINE")
    steps=[("Reports","Location / time\nFlood / urgency\nClaims / support"),
           ("Sparse graph","Observable affinity\nThreshold + top-k"),
           ("Clusters","Louvain / Leiden\nPredicted groups"),
           ("Priority","Duplicate families\nBounded score"),
           ("Schedule","Predicted destinations\nResource constraints")]
    for i,(h,b) in enumerate(steps):
        xx=.77+i*2.52
        panel(s,xx,2.06,2.30,2.27,h,b,BLUE if i<3 else TEAL,size=15)
        if i<4:line(s,xx+2.31,3.16,xx+2.50,3.16,CYAN,2,True)
    box(s,.80,4.66,3.15,.93,"FCF2E7",None,True)
    text(s,"Missing location / time\n→ manual review",1.00,4.83,2.76,.65,17,ORANGE,True)
    box(s,4.34,4.66,8.18,1.15,PALE,LINE,True)
    text(s,"EVALUATOR ONLY",4.55,4.80,7.6,.30,14,MUTED,True)
    text(s,"Incident identity · independent benefit · deadline · harm",4.55,5.25,7.56,.35,17)
    line(s,11.95,4.34,11.95,4.62,MUTED,1.5,True,True)
    source(s,"Redrawn from Paper 6444, Figure 1 and Algorithms 1–2. The current RQ1 suite does not empirically exercise missingness.")

    # 06 — Semi-synthetic data construction.
    s=add("Generator 3.0: what is anchored, what is simulated?","RQ1 · 80 runs · 16 incidents per run · 26,288 reports","DATA / RQ1")
    for i,(h,b) in enumerate([("Copernicus EMSR848","Historical flood context\nCentral Viet Nam"),
                              ("OpenStreetMap","Geographic locations\nand anchor features"),
                              ("WorldPop 2025","Population reference\naround geographic anchors")]):
        panel(s,.80+i*4.02,1.79,3.76,1.60,h,b,size=16)
    label(s,"Controlled simulation",.97,3.72,5,ORANGE)
    nodes=[("Latent incidents","16 per run"),("Observable reports","Position / time / F / E / N / V"),("Copies + campaigns","Controlled duplication / attacks")]
    for i,(h,b) in enumerate(nodes):
        xx=.93+i*4.02
        box(s,xx,4.15,3.70,1.17,"FCF2E7",None,True)
        text(s,h,xx+.15,4.32,3.38,.35,18,ORANGE,True)
        text(s,b,xx+.15,4.81,3.38,.28,13.5)
        if i<2:line(s,xx+3.72,4.73,xx+3.99,4.73,ORANGE,1.5,True)
    text(s,"Separate exports: observable algorithm input  |  evaluator-only incident and report labels",.96,5.61,11.48,.38,17)
    source(s,"[9–11]; thucnghiem/data/README.md and gold/run_001/run_manifest.json. Raw source snapshots and row lineage remain unavailable.")

    # 07 — Separate fully synthetic suite.
    s=add("Candidate 4.1: a separate fully synthetic suite","RQ2 / RQ3 · 80 datasets · 30,229 reports · synthetic regional geometry","DATA / RQ2–RQ3")
    for i,(h,b) in enumerate([("1  Generate incidents","Geometry, start times, needs\nand vulnerability are simulated."),
                              ("2  Generate reports","Noisy observable evidence,\nexact / near copies and attacks."),
                              ("3  Reserve outcome truth","Benefit, deadlines, service\nand harm remain evaluator-only.")]):
        panel(s,.80+i*4.02,1.91,3.76,2.33,h,b,TEAL,size=17)
    panel(s,.80,4.57,5.75,1.26,"Why simulation?","Known linkage and controlled perturbations.",size=16)
    panel(s,6.80,4.57,5.75,1.26,"What it cannot establish","Field representativeness or policy validity.",ORANGE,size=16)
    source(s,"Paper 6444, Experimental Design / Table 1; Candidate-4.1 notebooks. No EMSR848 anchoring is claimed for Candidate 4.1.")

    # 08 — Product/Additive formulas and explicit glossary.
    s=add("Product and Additive: two edge-weight constructions","A node is a report; an edge weight expresses observable affinity","METHOD / GRAPH")
    box(s,.80,1.83,7.20,1.46,PALE,LINE,True)
    label(s,"Product",1.00,1.98,3)
    equation(s,r"w^{\times}_{ij}=a_i a_j G_{ij}(\beta T_{ij}+\gamma C_{ij})","product",1.05,2.40,6.62,.68)
    box(s,.80,3.49,7.20,1.46,PALE,LINE,True)
    label(s,"Additive",1.00,3.64,3)
    equation(s,r"w^{+}_{ij}=a_i a_j(\alpha G_{ij}+\beta T_{ij}+\gamma C_{ij})","additive",1.02,4.06,6.67,.68)
    text(s,"G  Spatial proximity\nT  Temporal proximity\nC  Flood / urgency similarity\na  Location-and-time admission",8.37,1.96,4.02,1.80,19)
    text(s,"alpha, beta, gamma:\nnonnegative weights",8.38,4.05,4.01,.72,16,MUTED)
    text(s,"Far apart, similar time/context: Product attenuates\nthe full time–context contribution.",1.00,5.31,11.15,.78,19,BLUE,True)
    source(s,"Paper 6444, Equation 3 and Theorem 1; [2] Tomasi & Manduchi (1998) supplies spatial–range-product precedent.")

    # 09 — Louvain GIF with static first-frame poster.
    s=add("Louvain: turn a weighted graph into communities","The graph construction and the community detector are distinct choices","METHOD / CLUSTERING")
    picture(s,"louvain_schematic.gif",.80,1.72,7.40,4.35,
            "Schematic Louvain animation: node moves and aggregation; not an experimental result.")
    for i,(h,b) in enumerate([("1  Local moves","Move a node when modularity increases."),
                              ("2  Aggregate","Replace each community with a super-node."),
                              ("3  Repeat","Continue until no further gain is obtained.")]):
        text(s,h,8.42,1.91+i*1.30,3.90,.36,20,BLUE,True)
        text(s,b,8.42,2.37+i*1.30,3.90,.69,17)
    source(s,"[1] Blondel et al. (2008). Modularity compares within-community edge concentration with a null network. Animation is schematic.")

    # 10 — Priority schematic.
    s=add("Duplicate-aware, bounded priority","Repeated transport copies should not count as independent evidence","METHOD / PRIORITY")
    for j in range(4):
        box(s,.97+j*.14,2.03+j*.19,2.13,.72,WHITE,LINE,True)
        text(s,"Same report payload",1.10+j*.14,2.23+j*.19,1.90,.30,14,BLUE)
    line(s,3.57,3.03,4.08,3.03,CYAN,2,True)
    panel(s,4.23,2.00,3.55,2.18,"Evidence families","Exact fingerprints and\nnear-duplicate grouping.",size=18)
    line(s,7.86,3.03,8.31,3.03,CYAN,2,True)
    panel(s,8.46,2.00,3.96,2.18,"Bounded score","Confidence gating, maxima,\nclipping and saturation.",TEAL,size=18)
    equation(s,r"0\leq P_k\leq\mu,\qquad 1\leq\mu\leq 2","priority_bound",4.48,4.66,7.75,.62)
    text(s,"Exact-copy invariance requires fixed evidence grouping and score inputs.",1.02,5.55,11.18,.38,18,INK,True)
    source(s,"Paper 6444, Equation 4 / Algorithm 2 and RQ2. Q is a confidence heuristic, not a calibrated truth probability.")

    # 11 — Formal RQs after definitions.
    s=add("Research questions and stage-specific contributions","Each question tests a different part of the pipeline","RESEARCH QUESTIONS")
    rows=[("RQ1","Clustering","Does the independently tuned Product pipeline improve clustering over Additive?","Conditional edge bound + composition / stress comparison."),
          ("RQ2","Ranking","Does duplicate-aware priority align with independent simulated benefit under report perturbations?","Exact-copy invariance + alignment and attack audit."),
          ("RQ3","Dispatch","How do predicted split, merge and noise errors affect dispatch outcomes?","Paired scheduling audit using predicted destinations.")]
    for i,(r,h,q,c) in enumerate(rows):
        yy=1.75+i*1.42
        label(s,r,.97,yy+.05,1.0)
        text(s,h,2.00,yy,2.3,.40,22,BLUE,True)
        text(s,q,4.30,yy,8.06,.72,19)
        text(s,c,4.30,yy+.84,8.06,.33,13.5,MUTED)
        if i<2:line(s,.97,yy+1.22,12.40,yy+1.22,LINE,.8)
    source(s,"Paper 6444, Introduction and Contributions.")

    # 12 — Evaluation protocol with visual split bars.
    s=add("Evaluation protocol and information boundaries","Select on calibration; hold configurations fixed for the test audit","EVALUATION")
    for yy,title in [(1.84,"Generator 3.0 / RQ1"),(3.16,"Candidate 4.1 / RQ2–RQ3")]:
        text(s,title,.98,yy,10.8,.35,20,BLUE,True)
        for xx,ww,tt,cc in [(1.00,2.82,"20 development",MUTED),(3.91,2.82,"20 calibration",CYAN),(6.82,5.50,"40 held-out test",BLUE)]:
            box(s,xx,yy+.51,ww,.50,cc)
            text(s,tt,xx,yy+.61,ww,.28,16,WHITE,True,PP_ALIGN.CENTER)
    panel(s,.97,4.58,5.52,1.39,"RQ2: oracle incident grouping","Isolate ranking from upstream clustering errors.",size=16)
    panel(s,6.80,4.58,5.52,1.39,"RQ3: predicted clusters","Average resource conditions within each seed: 40 pairs.",TEAL,size=16)
    source(s,"Paper 6444, Experimental Design. RQ1 fixed stresses receive no retuning; RQ3 primary inference uses 40 seed-level pairs.")

    # 13 — Clustering metrics.
    s=add("Reported metrics: clustering","Compare predicted groups with evaluator-only incident linkage","METRICS / RQ1")
    metrics_row(s,1.87,"ARI","HIGHER IS BETTER","Adjusted Rand Index: agreement between two partitions, corrected for chance.")
    metrics_row(s,3.34,"Pairwise F1","HIGHER IS BETTER","Treat each pair of reports as same-incident or different-incident; combine precision and recall.",TEAL)
    for xx,v,t in [(1.04,"1","Identical partitions"),(5.07,"≈ 0","Chance-level agreement"),(9.05,"< 0","Possible discordance")]:
        text(s,v,xx,5.02,2.98,.46,28,BLUE,True)
        text(s,t,xx,5.62,3.35,.31,14,MUTED)
    source(s,"[3] Hubert & Arabie (1985). Paper 6444: ARI is primary; pairwise F1 is complementary. NMI / diameter / runtime are secondary.")

    # 14 — NDCG with a miniature ranked list, linear-gain equation.
    s=add("Reported metrics: ranking and score stability","Normalized Discounted Cumulative Gain at five (NDCG@5) and score stability","METRICS / RQ2")
    label(s,"NDCG@5  ↑",.99,1.84,5)
    equation(s,r"\mathrm{DCG@5}=\sum_{r=1}^{5}\frac{b_{\pi_r}}{\log_2(r+1)}","dcg",.99,2.36,6.27,.83)
    equation(s,r"\mathrm{NDCG@5}=\frac{\mathrm{DCG@5}}{\mathrm{Ideal\ DCG@5}}","ndcg",1.03,3.44,6.21,.79)
    text(s,"b: independent simulated benefit\nπ: order induced by the priority score\n1: ideal ranking; larger is better",1.04,4.67,6.17,1.13,17)
    panel(s,7.80,1.88,4.52,1.69,"Priority drift  ↓","Absolute normalized score change after a perturbation.",size=17)
    panel(s,7.80,3.82,4.52,1.69,"Top-five churn  ↓","Change in membership of the five highest-ranked incidents.",TEAL,size=17)
    source(s,"[4] Järvelin & Kekäläinen (2002); RQ2 notebook uses sklearn.ndcg_score with linear benefit gains. Spearman / overlap are secondary.")

    # 15 — Dispatch metrics.
    s=add("Reported metrics: dispatch outcomes","Consequences are evaluated only after the schedule is fixed","METRICS / RQ3")
    metrics_row(s,1.88,"Simulated harm","LOWER IS BETTER","Mean incident harm from the synthetic lateness / service model, not measured real-world injury.")
    metrics_row(s,3.40,"Deadline misses","LOWER IS BETTER","Fraction of incidents whose simulated response time exceeds their own deadline.",TEAL)
    text(s,"Travel / service constraints",1.02,5.17,3.74,.40,19,BLUE,True)
    line(s,4.73,5.39,5.20,5.39,CYAN,2,True)
    text(s,"Locked schedule",5.39,5.17,3.09,.40,19,BLUE,True)
    line(s,8.32,5.39,8.79,5.39,CYAN,2,True)
    text(s,"Evaluator-only outcomes",8.97,5.17,3.47,.65,19,TEAL,True)
    source(s,"Paper 6444, RQ3; RQ3_EndToEnd_Dispatch_Colab.ipynb, outcomes and metrics. Other operational endpoints remain complementary.")

    # 16–20 — Exported results, never a new benchmark.
    s=add("RQ1: no Product composition advantage is established","Held-out Generator-3.0 test split · 40 paired runs","RESULTS / RQ1")
    picture(s,"rq1_ari_ci.png",.80,1.72,8.02,4.38)
    text(s,"Additive Louvain",9.04,2.00,3.35,.37,19,TEAL,True)
    text(s,"0.9191",9.04,2.48,3.35,.60,36,TEAL,True)
    text(s,"Product Louvain",9.04,3.42,3.35,.37,19,BLUE,True)
    text(s,"0.9072",9.04,3.90,3.35,.60,36,BLUE,True)
    text(s,"Holm-adjusted p = .2560\nfor the paired contrast",9.04,5.05,3.35,.72,16,MUTED)
    source(s,"Paper 6444, Table 2 and §4.1; RQ1 exported benchmark summary. Error bars: unadjusted bootstrap 95% CIs.")

    s=add("RQ1: graph structure changes under fixed stresses","Same run and locked configurations · separate perturbations of the control batch","RESULTS / RQ1 STRESS")
    picture(s,"graph_stress.gif",.78,1.68,11.76,4.49,
            "Actual held-out run graph reproduction under seven fixed stress conditions; not a streaming experiment.")
    source(s,"Paper 6444, Figure 2; exported RQ1 stress checkpoints / summaries. Animation: one-run reproduction; heatmap: 40-run means.")

    s=add("RQ2: exact-copy stability has a narrow scope","Oracle incident groups and fixed score inputs","RESULTS / RQ2 STRESS")
    picture(s,"rq2_priority_drift.png",.85,1.76,8.19,4.32)
    panel(s,9.24,1.97,3.12,1.78,"Exact copies","2× / 5× / 10×:\nzero revised score drift.",TEAL,size=16)
    panel(s,9.24,4.02,3.12,1.78,"Coordinated attack","High-confidence payloads\nstill distort priority.",ORANGE,size=16)
    source(s,"Paper 6444, Table 3 / §4.2; exported RQ2 robustness summaries. Revised campaign drift .1688; legacy .0309.")

    s=add("RQ2: alignment with simulated benefit remains weak","Even oracle grouping does not establish a general ranking advantage","RESULTS / RQ2 ALIGNMENT")
    picture(s,"rq2_ndcg_ci.png",.80,1.74,8.23,4.31)
    text(s,"Revised NDCG@5",9.30,2.16,3.11,.40,19,BLUE,True)
    text(s,"0.6669",9.30,2.78,3.11,.68,36,BLUE,True)
    text(s,"Random comparator",9.30,4.00,3.11,.40,19,MUTED,True)
    text(s,"0.6763",9.30,4.59,3.11,.68,32,MUTED,True)
    source(s,"Paper 6444, §4.2; exported RQ2 alignment summaries. Intervals: bootstrap 95%; linear independent-benefit gains.")

    s=add("RQ3: safeguards do not ensure better dispatch","Product partition · three resource conditions · 40 test seeds","RESULTS / RQ3")
    picture(s,"rq3_dispatch.png",.78,1.78,11.76,4.20)
    source(s,"Paper 6444, Figure 3 / §4.3; descriptive condition means. Primary tests average conditions within seed, retaining 40 pairs.")

    # 21 — Discussion / evidence ladder.
    s=add("Discussion: three different levels of evidence","A guarantee at one stage does not validate the next stage","DISCUSSION")
    cols=[("Mathematical safeguards","Conditional edge localization.\nExact-copy score invariance\nunder fixed grouping / inputs.",BLUE),
          ("Observed synthetic results","Noise and 5× copies degrade\nclustering; alignment is weak;\ndispatch benefit is unestablished.",TEAL),
          ("External validity","Two synthetic suites.\nNo expert-endorsed policy.\nNo field-outcome validation.",ORANGE)]
    for i,(h,b,c) in enumerate(cols):panel(s,.80+i*4.02,1.94,3.76,3.36,h,b,c,size=18)
    source(s,"Paper 6444, §4.4, Discussion and Threats to Validity. Missingness / extraction / source authenticity / deployment costs remain gaps.")

    # 22 — Separate conclusion.
    s=add("Conclusion","What this study establishes within its tested scope","CONCLUSION")
    conclusions=[("1","Product gating","Provides a conditional geographic edge bound; empirical composition superiority is not established."),
                 ("2","Family-wise priority","Is invariant to exact copies under fixed grouping and inputs; benefit alignment remains unestablished."),
                 ("3","Downstream audit","Reveals that clustering and ranking safeguards do not ensure improved simulated dispatch.")]
    for i,(n,h,b) in enumerate(conclusions):
        yy=1.93+i*1.37
        number(s,n,1.02,yy)
        text(s,h,1.73,yy,10.42,.43,23,BLUE,True)
        text(s,b,1.73,yy+.56,10.42,.68,19)
    source(s,"Paper 6444, Conclusion. Results are synthetic diagnostics, without establishing policy validity or field readiness.")

    # 23 — Separate future work.
    s=add("Future work: close the evidence gaps","Proposed validation steps, not results already obtained","NEXT VALIDATION")
    future=[("01","Real report linkage","Acquire traceable report snapshots and independently annotate same-incident links."),
            ("02","Expert priority validation","Define and assess rescue priorities with domain experts and operational stakeholders."),
            ("03","Transfer and stress coverage","Freeze the pipeline and test new event contexts, missingness and source-quality mechanisms."),
            ("04","Scheduling objectives","Evaluate need-based priorities together with travel, service capacity and resource constraints.")]
    for i,(n,h,b) in enumerate(future):
        xx=.93+(i%2)*6.08; yy=1.91+(i//2)*2.08
        text(s,n,xx,yy,.55,.43,24,CYAN,True)
        text(s,h,xx+.78,yy,4.87,.57,21,BLUE,True)
        text(s,b,xx+.78,yy+.76,4.87,1.06,18)
    source(s,"Author-facing proposals derived from Paper 6444, Discussion and Threats to Validity; not completed field validation.")

    # 24–25 — References, numbered consistently with citations in the notes.
    refs=json.loads((OUT/"research/references.json").read_text())
    if isinstance(refs,dict):refs=refs.get("references",refs.get("items",[]))
    for page in range(2):
        s=add(f"References ({page+1} of 2)","Methods and evaluation" if page==0 else "Data and application context","REFERENCES")
        for i,r in enumerate(refs[page*6:(page+1)*6]):
            yy=1.76+i*.735
            rid=r.get("id",page*6+i+1)
            text(s,f"[{rid}]",.92,yy,.62,.30,15,BLUE,True)
            entry=r.get("slide_text") or r.get("formatted") or r.get("full_citation")
            if not entry:raise ValueError(f"Missing slide_text for ref {rid}")
            if int(rid)==12:
                entry="Nguyen, T.-T., et al. (2026). Research artifact for stress-testing flood-rescue report clustering and ranking. GitHub Release v1.0.1."
            text(s,entry,1.72,yy,10.56,.44,13.1)
            url=r.get("url") if int(rid)==12 else (r.get("doi_url") or r.get("doi") or r.get("url") or r.get("primary_url"))
            if url and not url.startswith("http"):url="https://doi.org/"+url
            sh=text(s,url or "",1.72,yy+.44,10.56,.22,9.5,MUTED)
            if url:
                sh.text_frame.paragraphs[0].runs[0].hyperlink.address=url
        source(s,"Full bibliographic metadata and verification links: ISDS/research/references.json. Project artifact [12] is cited on the final slide.")

    # 26 — CTU closing layout.
    s=prs.slides.add_slide(prs.slide_layouts[0]);titles.append("Thank you — Questions and discussion")
    for sh in list(s.shapes):sh._element.getparent().remove(sh._element)
    text(s,"THANK YOU",.95,2.35,11.45,.85,44,WHITE,True,PP_ALIGN.CENTER)
    text(s,"Questions and discussion",.95,3.51,11.45,.65,26,WHITE,align=PP_ALIGN.CENTER)
    text(s,"Clustering safeguards, ranking stability and dispatch benefit\nrequire separate evaluation.",.95,4.39,11.45,.66,19,WHITE,align=PP_ALIGN.CENTER)
    text(s,"Paper 6444 · Can Tho University\nResearch artifact [12]: github.com/ngthtrong/nckh2/releases/tag/v1.0.1\nFunded by Can Tho University · THS2026-68",.95,5.53,11.45,.96,14,WHITE,align=PP_ALIGN.CENTER)

    # Notes and source provenance, embedded in the editable deck.
    notes=json.loads((OUT/"research/speaker-notes.json").read_text())
    if isinstance(notes,dict):notes=notes.get("slides",notes.get("notes",[]))
    by_num={int(r["slide"]):r for r in notes}
    for i,s in enumerate(prs.slides,1):
        if i not in by_num:raise ValueError(f"Missing notes for slide {i}")
        content=by_num[i]["notes"]
        if isinstance(content,list):content="\n\n".join(content)
        if getattr(s,"_source_note",None):
            content += "\n\nSource notes: " + s._source_note
        s.notes_slide.notes_text_frame.text=content
        for p in s.notes_slide.notes_text_frame.paragraphs:
            for r in p.runs:
                r.font.name=FONT
                r.font.size=Pt(12)
    prs.core_properties.title="Paper 6444 — Stress-Testing Flood-Rescue Report Clustering and Ranking"
    prs.core_properties.subject="ISDS 2026 conference presentation; synthetic study"
    prs.core_properties.author="Paper 6444 research team"
    prs.core_properties.keywords="ISDS 2026, flood rescue, clustering, Product, Additive, bounded priority, synthetic stress test"
    prs.core_properties.comments="Prepared with AI assistance using academic-research-suite; based on repository paper and exported results. Scientific claims require author review."
    dest=OUT/"ISDS2026_Paper_6444_Conference_Deck.pptx"
    prs.save(dest)
    (OUT/"slide-index.json").write_text(json.dumps([{"slide":i,"title":t} for i,t in enumerate(titles,1)],indent=2,ensure_ascii=False)+"\n")
    style_reference=ROOT/"ID_8253_Chromatic_Anchoring_ISDS2026_Conference_Deck.pptx"
    if not style_reference.exists():
        style_reference=OUT/"checks/reference/ID_8253_Chromatic_Anchoring_ISDS2026_Conference_Deck.pdf"
    source_files=[TEMPLATE,style_reference,ROOT/"paper/main.tex",ROOT/"paper/main.pdf",ROOT/"paper/references.bib"]
    manifest={"slides":len(prs.slides),"overview_slide":2,"language":"English","target_duration_minutes":20,
              "inputs":{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files},
              "deck_sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
              "template_layouts_used":["Title Slide","Title and Content"],
              "fonts":{"titles":"K2D","body":"Readex Pro","source":"Original template layout and master text styles"},
              "audience_footnotes":False,
              "bottom_summary_banners":False,
              "colored_box_left_borders":False,
              "generation":"Native editable text/shapes; equations and source-backed charts/GIFs as embedded images.",
              "ai_assistance":"Academic-research-suite-guided content adaptation, diagrams, animation, and formatting; not an author approval or scientific validation."}
    (OUT/"build-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(dest)
    print(f"{len(prs.slides)} slides; {len(by_num)} speaker-note records")


if __name__=="__main__":
    # The checked-in editable deck is the source for current author edits.
    if not (OUT/"ISDS2026_Paper_6444_Conference_Deck.pptx").exists():
        raise SystemExit('Restore the canonical editable PPTX before rebuilding.')
    from compact_deck import compact
    compact()
