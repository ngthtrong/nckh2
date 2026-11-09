#!/usr/bin/env python3
"""Portable CTU slide authoring: init, build, render, check and assemble GIFs."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from xml.sax.saxutils import escape
from zipfile import ZipFile

SKILL = Path(__file__).resolve().parents[1]
ASSETS = SKILL / "assets"
FONT_DIR = ASSETS / "fonts"
DEFAULT_STYLE = {
    "title_font": "K2D", "body_font": "Readex Pro",
    "blue": "0070C0", "cyan": "00AFEF", "teal": "009988",
    "orange": "C97724", "ink": "17212B", "muted": "526474",
    "pale": "F0F6FA", "outline": "D6E3EC",
}
LAYOUTS = {"title", "overview", "cards", "bullets", "flow", "equations",
           "metrics", "table", "figure", "chart", "references", "closing"}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def load_spec(path):
    path = Path(path).resolve()
    spec = read_json(path)
    if spec.get("schema") != "ctu-slides/1":
        raise ValueError("Expected schema 'ctu-slides/1'.")
    slug = spec.get("deck", {}).get("slug", "ctu-presentation")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", slug):
        raise ValueError("deck.slug must be a safe filename stem.")
    slides = spec.get("slides")
    if not isinstance(slides, list) or not slides:
        raise ValueError("slides must be a non-empty array.")
    for i, slide in enumerate(slides, 1):
        if slide.get("layout") not in LAYOUTS:
            raise ValueError(f"Slide {i}: unknown layout {slide.get('layout')!r}.")
        if not isinstance(slide.get("title"), str) or not slide["title"].strip():
            raise ValueError(f"Slide {i}: title is required.")
    return path, spec, slug


def project_file(project):
    p = Path(project).resolve() / "build-manifest.json"
    if not p.exists():
        raise ValueError(f"Build the project before rendering/checking: {p}")
    return p, read_json(p)


def starter(language="vi"):
    vi = language == "vi"
    names = (["Tên đề tài", "Nội dung trình bày", "Bối cảnh và bài toán",
              "Nghiên cứu liên quan và khoảng trống", "Dữ liệu và phạm vi",
              "Phương pháp", "Chỉ số và thiết kế đánh giá", "Kết quả",
              "Thảo luận và giới hạn", "Kết luận", "Hướng phát triển",
              "Tài liệu tham khảo", "Cảm ơn"] if vi else
             ["Research title", "Presentation overview", "Background and problem",
              "Related work and research gap", "Data and scope", "Methods",
              "Metrics and evaluation design", "Results", "Discussion and limits",
              "Conclusion", "Future work", "References", "Thank you"])
    slides=[]
    for i, title in enumerate(names):
        layout = "title" if i == 0 else "overview" if i == 1 else "closing" if i == 12 else "references" if i == 11 else "bullets"
        s={"layout":layout,"title":title,"notes":"","source_ids":[]}
        if layout=="overview":
            s["items"]=[{"heading":x,"body":""} for x in
                        (["Bài toán và khoảng trống","Dữ liệu và phương pháp","Đánh giá và kết quả","Kết luận và hướng phát triển"] if vi else
                         ["Problem and gap","Data and methods","Evaluation and results","Conclusion and next steps"])]
        elif layout=="bullets": s["items"]=[]
        elif layout=="references":s["source_ids"]=[]
        slides.append(s)
    return {"schema":"ctu-slides/1","deck":{"slug":"ctu-presentation","title":names[0],
            "authors":[],"affiliation":"Can Tho University","event":"","language":language,
            "target_minutes":20},"style":{},"sources":[],"slides":slides}


def initialize(args):
    p=Path(args.project).resolve();p.mkdir(parents=True,exist_ok=True)
    target=p/"deck.json"
    if target.exists():raise ValueError(f"Refusing to replace an existing specification: {target}")
    write_json(target,starter(args.language))
    (p/"assets").mkdir(exist_ok=True)
    print(target)


class Deck:
    def __init__(self, spec_path, out):
        from pptx import Presentation
        self.path,self.spec,self.slug=load_spec(spec_path)
        self.out=Path(out).resolve();self.out.mkdir(parents=True,exist_ok=True)
        self.style={**DEFAULT_STYLE,**self.spec.get("style",{})}
        self.inputs={str(self.path):digest(self.path)}
        self.input_roles={str(self.path):"project specification"}
        self.warnings=[];self.media=[];self.picture_count=0;self.count=0
        self.sources={}
        for s in self.spec.get("sources",[]):
            if not isinstance(s.get("id"),str) or not s["id"] or s["id"] in self.sources:
                raise ValueError("Each source needs a unique non-empty string id.")
            self.sources[s["id"]]=s
            if s.get("path"): self.asset(s["path"],"declared source")
        template=self.asset(self.spec.get("template") or ASSETS/"CTU_PowerPoint_Template_English.pptx","CTU template")
        self.prs=Presentation(template)
        for sid in list(self.prs.slides._sldIdLst):
            self.prs.part.drop_rel(sid.rId);self.prs.slides._sldIdLst.remove(sid)
        self.layouts={l.name:l for l in self.prs.slide_layouts}
        for name in ("Title Slide","Title and Content"):
            if name not in self.layouts:raise ValueError(f"Template layout missing: {name}")
        if abs(self.prs.slide_width/self.prs.slide_height-16/9)>.001:
            raise ValueError("Expected a 16:9 CTU template.")
        for f in FONT_DIR.rglob("*.ttf"):self.inputs[str(f)]=digest(f);self.input_roles[str(f)]="bundled font"

    def asset(self,value,role="figure"):
        p=Path(value)
        if not p.is_absolute():p=self.path.parent/p
        p=p.resolve()
        if not p.is_file():raise ValueError(f"Missing {role}: {p}")
        self.inputs[str(p)]=digest(p);self.input_roles[str(p)]=role
        return p

    def color(self,value):
        from pptx.dml.color import RGBColor
        return RGBColor.from_string(self.style.get(value,value).lstrip("#"))

    def text(self,s,value,x,y,w,h,size=20,color="ink",bold=False,align="left",name=None):
        from pptx.util import Inches,Pt
        from pptx.enum.text import PP_ALIGN
        sh=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h))
        sh.name=name or "CTU text"
        tf=sh.text_frame;tf.clear();tf.word_wrap=True
        tf.margin_top=tf.margin_bottom=Inches(.01)
        tf.margin_left=tf.margin_right=Inches(.01)
        for i,line in enumerate(str(value).split("\n")):
            p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
            p.alignment={"left":PP_ALIGN.LEFT,"center":PP_ALIGN.CENTER,"right":PP_ALIGN.RIGHT}[align]
            p.space_before=Pt(0);p.space_after=Pt(3);p.line_spacing=1.13
            for part in re.split(r"([↑↓→←↔])",line):
                if not part:continue
                r=p.add_run();r.text=part;r.font.size=Pt(size);r.font.bold=bold
                r.font.name=self.style["title_font"] if bold or part in "↑↓→←↔" else self.style["body_font"]
                r.font.color.rgb=self.color(color)
        return sh

    def box(self,s,x,y,w,h,fill="pale",stroke="outline"):
        from pptx.util import Inches,Pt
        from pptx.enum.shapes import MSO_SHAPE
        sh=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h))
        sh.name="CTU plain box";sh.adjustments[0]=.08
        sh.fill.solid();sh.fill.fore_color.rgb=self.color(fill)
        if stroke:sh.line.color.rgb=self.color(stroke);sh.line.width=Pt(.8)
        else:sh.line.fill.background()
        return sh

    def arrow(self,s,x1,y1,x2,y2):
        from pptx.enum.shapes import MSO_CONNECTOR
        from pptx.util import Inches,Pt
        from pptx.oxml.xmlchemy import OxmlElement
        sh=s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Inches(x1),Inches(y1),Inches(x2),Inches(y2))
        sh.line.color.rgb=self.color("cyan");sh.line.width=Pt(1.5)
        el=OxmlElement("a:tailEnd");el.set("type","triangle");sh.line._get_or_add_ln().append(el)

    def picture(self,s,path,x,y,w,h,alt=""):
        from PIL import Image
        from pptx.util import Inches
        p=self.asset(path)
        with Image.open(p) as im:
            iw,ih=im.size;n=getattr(im,"n_frames",1)
            duration=0
            for k in range(n):im.seek(k);duration+=im.info.get("duration",0)
        scale=min(w/iw,h/ih);dw,dh=iw*scale,ih*scale
        sh=s.shapes.add_picture(str(p),Inches(x+(w-dw)/2),Inches(y+(h-dh)/2),width=Inches(dw),height=Inches(dh))
        sh.name="CTU figure: "+p.name
        ns="{http://schemas.openxmlformats.org/presentationml/2006/main}"
        sh._element.find(ns+"nvPicPr").find(ns+"cNvPr").set("descr",alt or p.stem)
        self.media.append({"path":str(p),"sha256":digest(p),"frames":n,"duration_ms":duration,"slide":self.count})
        self.picture_count+=1

    def matplotlib(self):
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib import pyplot as plt,font_manager
        for f in FONT_DIR.rglob("*.ttf"):font_manager.fontManager.addfont(str(f))
        plt.rcParams.update({"font.family":[self.style["body_font"],self.style["title_font"],"DejaVu Sans"],
                             "font.size":14,"axes.labelsize":14,"text.color":"#"+self.style["ink"]})
        return plt

    def frame(self,title,subtitle="",cover=False):
        self.count+=1
        s=self.prs.slides.add_slide(self.layouts["Title Slide" if cover else "Title and Content"])
        for sh in list(s.shapes):sh._element.getparent().remove(sh._element)
        if not cover:
            self.text(s,title,.94,.35,11.65,.82,28,"blue",True,name="CTU slide title")
            if subtitle:self.text(s,subtitle,.95,1.24,11.55,.48,14,"muted")
            # Mask the template's automatic number only; keep its branding artwork.
            from pptx.util import Inches
            from pptx.enum.shapes import MSO_SHAPE
            sh=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(12.60),Inches(7.065),Inches(.47),Inches(.32))
            sh.name="CTU page number mask";sh.fill.solid();sh.fill.fore_color.rgb=self.color("FFFFFF");sh.line.fill.background()
            self.text(s,str(self.count).zfill(2),12.65,7.10,.30,.20,9,"muted",align="right")
        return s

    def cover(self,s,d,closing=False):
        meta=self.spec["deck"]
        self.text(s,d["title"],.78,2.18,11.77,1.72,32,"FFFFFF",True,"center")
        if closing:
            self.text(s,d.get("subtitle",""),.85,4.06,11.65,.78,23,"FFFFFF",align="center")
            self.text(s,d.get("body",""),.85,5.48,11.65,.76,16,"FFFFFF",align="center")
        else:
            authors=d.get("authors",meta.get("authors",[]))
            if isinstance(authors,list):authors=" · ".join(authors)
            self.text(s,authors,.80,4.13,11.72,.76,16,"FFFFFF",align="center")
            bottom="\n".join(x for x in [d.get("affiliation",meta.get("affiliation","")),d.get("event",meta.get("event",""))] if x)
            self.text(s,bottom,.80,5.45,11.72,.83,17,"FFFFFF",align="center")

    def cards(self,s,items,flow=False):
        n=len(items)
        if not 1<=n<=(5 if flow else 4):raise ValueError("cards: 1–4 items; flow: 1–5 stages.")
        gap=.24;w=(11.76-gap*(n-1))/n;y=2.15 if flow else 1.98;h=3.20 if flow else 3.92
        for i,item in enumerate(items):
            x=.80+i*(w+gap);self.box(s,x,y,w,h)
            color=item.get("color","blue")
            self.text(s,item.get("heading",""),x+.20,y+.20,w-.40,.88,20 if n<4 else 18,color,True)
            self.text(s,item.get("body",""),x+.20,y+1.18,w-.40,h-1.34,19 if n<4 else 17)
            if flow and i<n-1:self.arrow(s,x+w+.015,y+h/2,x+w+gap-.015,y+h/2)

    def bullets(self,s,items):
        if not items:return
        if len(items)>5:raise ValueError("Use at most five bullet groups per slide, or split the slide.")
        step=4.36/len(items)
        for i,item in enumerate(items):
            if isinstance(item,str):item={"body":item}
            y=1.99+i*step
            if item.get("heading"):
                self.text(s,item["heading"],.97,y,11.42,.48,22,item.get("color","blue"),True)
                self.text(s,item.get("body",""),.98,y+.57,11.39,step-.66,19)
            else:self.text(s,"•  "+item.get("body",""),.97,y,11.42,step-.13,20)

    def overview(self,s,items):
        if not 1<=len(items)<=6:raise ValueError("overview requires 1–6 items.")
        step=4.43/len(items)
        for i,it in enumerate(items):
            if isinstance(it,str):it={"heading":it}
            y=1.98+i*step;self.text(s,f"{i+1:02d}",.97,y,.60,.40,22,"cyan",True)
            self.text(s,it.get("heading",""),1.86,y,10.46,.41,21,"ink",True)
            if it.get("body"):self.text(s,it["body"],1.87,y+.46,10.40,.34,14,"muted")

    def equations(self,s,d):
        equations=d.get("equations",[])
        if not 1<=len(equations)<=3:raise ValueError("equations requires 1–3 entries.")
        plt=self.matplotlib();fdir=self.out/"assets";fdir.mkdir(exist_ok=True)
        step=4.40/len(equations)
        for i,e in enumerate(equations):
            y=1.98+i*step;self.box(s,.80,y,7.30,step-.25)
            self.text(s,e.get("label",""),1.00,y+.17,6.85,.39,18,"blue",True)
            path=fdir/f'equation-{self.count:02d}-{i+1}.png'
            fig=plt.figure(figsize=(10,1.1),dpi=180)
            fig.text(.5,.5,"$"+e["latex"]+"$",ha="center",va="center",fontsize=30,color="#"+self.style["ink"])
            fig.savefig(path,transparent=True,bbox_inches="tight",pad_inches=.08);plt.close(fig)
            self.picture(s,path,1.02,y+.69,6.84,max(.35,step-1.10),e["latex"])
        self.text(s,d.get("glossary",""),8.43,2.01,3.90,4.15,19)

    def metrics(self,s,items):
        if not 1<=len(items)<=3:raise ValueError("metrics requires 1–3 entries.")
        step=4.43/len(items)
        for i,m in enumerate(items):
            y=1.98+i*step;h=step-.22;self.box(s,.80,y,11.76,h)
            self.text(s,m["name"],1.00,y+.18,2.45,.72,21,m.get("color","blue"),True)
            self.text(s,m.get("direction",""),1.00,y+min(.98,h-.34),2.45,.24,11,"muted")
            self.text(s,m.get("meaning",""),3.77,y+.26,8.30,h-.42,19)

    def table(self,s,d):
        from pptx.util import Inches,Pt
        headers=d.get("headers",[]);rows=d.get("rows",[])
        if not headers or len(headers)>6 or len(rows)>7:raise ValueError("table supports 1–6 columns and at most seven rows.")
        if any(len(r)!=len(headers) for r in rows):raise ValueError("Every table row must match headers.")
        t=s.shapes.add_table(len(rows)+1,len(headers),Inches(.82),Inches(2.02),Inches(11.72),Inches(min(4.25,(len(rows)+1)*.60))).table
        widths=d.get("widths")
        if widths:
            if len(widths)!=len(headers) or min(widths)<=0:raise ValueError("table.widths must be positive per-column weights.")
            for col,w in zip(t.columns,widths):col.width=Inches(11.72*w/sum(widths))
        for i,row in enumerate([headers]+rows):
            for j,value in enumerate(row):
                c=t.cell(i,j);c.text=str(value);c.margin_top=c.margin_bottom=Inches(.09)
                c.fill.solid();c.fill.fore_color.rgb=self.color("blue" if i==0 else "pale" if i%2 else "FFFFFF")
                for p in c.text_frame.paragraphs:
                    for r in p.runs:
                        r.font.name=self.style["title_font"] if i==0 else self.style["body_font"]
                        r.font.size=Pt(d.get("font_size",17));r.font.bold=i==0
                        r.font.color.rgb=self.color("FFFFFF" if i==0 else "ink")

    def figure(self,s,d):
        if d.get("body"):
            self.picture(s,d["path"],.80,1.95,7.70,4.50,d.get("alt",""))
            self.text(s,d["body"],8.78,2.04,3.54,4.22,19)
        else:self.picture(s,d["path"],.80,1.95,11.76,4.53,d.get("alt",""))
        if d.get("poster"):self.asset(d["poster"],"GIF poster")

    def chart(self,s,d):
        path=self.asset(d["csv"],"quantitative CSV")
        with path.open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
        if not rows or len(rows)>12:raise ValueError("chart requires 1–12 CSV rows; aggregate/split larger inputs explicitly.")
        labelcol=d.get("label_column","label");valuecol=d.get("value_column","value")
        labels=[r[labelcol] for r in rows];vals=[float(r[valuecol]) for r in rows]
        if not all(math.isfinite(x) for x in vals):raise ValueError("Non-finite chart values.")
        plt=self.matplotlib();fig,ax=plt.subplots(figsize=(11.5,4.55),dpi=160)
        fig.subplots_adjust(left=.24,right=.97,top=.95,bottom=.20)
        for i,(r,v) in enumerate(zip(rows,vals)):
            lo=r.get(d.get("low_column","low"));hi=r.get(d.get("high_column","high"));err=None
            if (lo is None)!=(hi is None):raise ValueError("Both low and high columns are required for intervals.")
            if lo is not None and hi is not None:
                lo=float(lo);hi=float(hi)
                if not lo<=v<=hi:raise ValueError("Chart interval must contain its estimate.")
                err=[[v-lo],[hi-v]]
            color="#"+self.style["blue" if i%2==0 else "teal"]
            ax.errorbar(v,i,xerr=err,fmt="o",capsize=5,markersize=9,color=color,elinewidth=2)
        ax.set_yticks(range(len(rows)),labels);ax.invert_yaxis()
        ax.set_xlabel(d.get("xlabel",valuecol));ax.grid(axis="x",color="#E1E7EC")
        ax.set_axisbelow(True);ax.spines[["top","right"]].set_visible(False)
        if d.get("xlim"):ax.set_xlim(*d["xlim"])
        p=self.out/"assets"/f'chart-{self.count:02d}.png';p.parent.mkdir(exist_ok=True)
        fig.savefig(p);plt.close(fig)
        self.picture(s,p,.80,1.95,11.76,4.53,d.get("alt","Source-backed chart"))

    def references(self,s,d):
        ids=d.get("source_ids",[])
        if len(ids)>6:raise ValueError("Split references across slides: at most six per slide.")
        for i,rid in enumerate(ids):
            if rid not in self.sources:raise ValueError(f"Unknown source id {rid!r}")
            r=self.sources[rid];y=1.98+i*.74
            display=r.get("label",rid if rid.isdigit() else str(list(self.sources).index(rid)+1))
            self.text(s,f"[{display}]",.95,y,.63,.34,15,"blue",True)
            self.text(s,r.get("citation",r.get("title",rid)),1.76,y,10.55,.47,14)
            url=r.get("url") or ("https://doi.org/"+r["doi"] if r.get("doi") else "")
            if url:
                sh=self.text(s,url,1.77,y+.48,10.51,.21,9.5,"muted")
                for p in sh.text_frame.paragraphs:
                    for run in p.runs:run.hyperlink.address=url

    def notes(self,s,d):
        from pptx.util import Pt
        parts=[d.get("notes","")]
        for rid in d.get("source_ids",[]):
            if rid not in self.sources:raise ValueError(f"Unknown source id {rid!r}")
            parts.append("Source: "+json.dumps(self.sources[rid],ensure_ascii=False))
        if d.get("qualifications"):parts.append("Qualifications: "+d["qualifications"])
        content="\n\n".join(x for x in parts if x)
        if not content:self.warnings.append(f"Slide {self.count}: no speaker notes yet.")
        s.notes_slide.notes_text_frame.text=content
        for p in s.notes_slide.notes_text_frame.paragraphs:
            for r in p.runs:r.font.name=self.style["body_font"];r.font.size=Pt(12)

    def build(self,force=False):
        dest=self.out/(self.slug+".pptx");mp=self.out/"build-manifest.json"
        if dest.exists() and not force:
            old=read_json(mp) if mp.exists() else {}
            if old.get("deck_sha256")!=digest(dest):
                raise ValueError("Existing PPTX differs from the last generated output. Preserve/incorporate manual edits, or deliberately pass --force.")
        for d in self.spec["slides"]:
            layout=d["layout"];cover=layout in ("title","closing")
            s=self.frame(d["title"],d.get("subtitle",""),cover)
            if cover:self.cover(s,d,layout=="closing")
            elif layout=="overview":self.overview(s,d.get("items",[]))
            elif layout in ("cards","flow"):self.cards(s,d.get("items",[]),layout=="flow")
            elif layout=="bullets":self.bullets(s,d.get("items",[]))
            elif layout=="equations":self.equations(s,d)
            elif layout=="metrics":self.metrics(s,d.get("items",[]))
            elif layout=="table":self.table(s,d)
            elif layout=="figure":self.figure(s,d)
            elif layout=="chart":self.chart(s,d)
            elif layout=="references":self.references(s,d)
            self.notes(s,d)
        m=self.spec["deck"];self.prs.core_properties.title=m.get("title",self.slug)
        self.prs.core_properties.author="; ".join(m.get("authors",[]))
        self.prs.core_properties.subject=m.get("event","")
        self.prs.core_properties.comments="Created with the portable CTU slides skill. Source evidence remains project-specific."
        self.prs.save(dest)
        md=["# "+m.get("title",self.slug)]
        for i,d in enumerate(self.spec["slides"],1):
            md.extend([f"\n## {i:02d}. {d['title']}","",d.get("notes","")])
            if d.get("source_ids"):md.extend(["","Sources: "+", ".join(d["source_ids"])])
        (self.out/"speaker-notes.md").write_text("\n".join(md)+"\n",encoding="utf-8")
        manifest={"schema":"ctu-build/1","spec":str(self.path),"deck":dest.name,
                  "deck_sha256":digest(dest),"slides":len(self.prs.slides),"style":self.style,
                  "inputs":self.inputs,"input_roles":self.input_roles,"media":self.media,
                  "warnings":self.warnings,"generator_sha256":digest(__file__),
                  "visual_defaults":{"bottom_footnotes":False,"bottom_summary_banners":False,"colored_left_box_strips":False}}
        write_json(mp,manifest)
        print(json.dumps({"pptx":str(dest),"slides":len(self.prs.slides),"warnings":self.warnings},ensure_ascii=False))


def render(args):
    import pymupdf
    from PIL import Image,ImageDraw,ImageFont
    mp,m=project_file(args.project);project=mp.parent
    soffice=args.soffice or shutil.which("libreoffice") or shutil.which("soffice")
    if not soffice:raise ValueError("LibreOffice not found. Install it or provide --soffice; PDF inspection is not complete.")
    checks=project/"checks";checks.mkdir(exist_ok=True)
    cfg=checks/"fontconfig.xml";cache=checks/"font-cache";cache.mkdir(exist_ok=True)
    includes="".join(f"<dir>{escape(str(p.resolve()))}</dir>" for p in sorted(FONT_DIR.iterdir()) if p.is_dir())
    cfg.write_text('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig><include ignore_missing="yes">/etc/fonts/fonts.conf</include>'+includes+f'<cachedir>{escape(str(cache))}</cachedir></fontconfig>',encoding="utf-8")
    env=os.environ.copy();env["FONTCONFIG_FILE"]=str(cfg)
    deck=project/m["deck"]
    pdf=deck.with_suffix(".pdf")
    # Export into a new directory so an old PDF cannot masquerade as success.
    with tempfile.TemporaryDirectory(prefix="ctu-export-",dir=checks) as stage:
        command=[soffice,'-env:UserInstallation='+ (checks/"lo-profile").as_uri(),"--headless","--convert-to",
                 'pdf:impress_pdf_Export:{"ExportHiddenSlides":{"type":"boolean","value":"true"}}',"--outdir",stage,str(deck)]
        result=subprocess.run(command,env=env,capture_output=True,text=True,timeout=180)
        (checks/"render.log").write_text(result.stdout+result.stderr,encoding="utf-8")
        fresh=Path(stage)/pdf.name
        if result.returncode or not fresh.exists():raise ValueError("PDF export failed; inspect checks/render.log.")
        os.replace(fresh,pdf)
    doc=pymupdf.open(pdf)
    folder=checks/"slides";folder.mkdir(exist_ok=True)
    cols,tw,th,pad,lab=4,480,270,16,28
    rows=math.ceil(len(doc)/cols);sheet=Image.new("RGB",(pad+cols*(tw+pad),pad+rows*(th+pad+lab)),"#DCE5EC")
    draw=ImageDraw.Draw(sheet);font=ImageFont.truetype(str(FONT_DIR/"k2d/K2D-Regular.ttf"),18)
    for i,page in enumerate(doc):
        path=folder/f"slide-{i+1:02d}.png"
        page.get_pixmap(matrix=pymupdf.Matrix(1280/page.rect.width,720/page.rect.height),alpha=False).save(path)
        im=Image.open(path);im.thumbnail((tw,th));x=pad+i%cols*(tw+pad);y=pad+i//cols*(th+lab+pad)
        draw.text((x,y),f"{i+1:02d}",font=font,fill="#17212B");sheet.paste(im,(x,y+lab))
    sheet.save(checks/"contact-sheet.png")
    m["pdf_sha256"]=digest(pdf);write_json(mp,m)
    print(json.dumps({"pdf":str(pdf),"pages":len(doc),"preview":str(checks/"contact-sheet.png")}))


def check(args):
    from pptx import Presentation
    from PIL import Image
    mp,m=project_file(args.project);project=mp.parent;deck=project/m["deck"]
    prs=Presentation(deck);checks=[]
    def record(name,ok,detail=None):checks.append({"check":name,"passed":bool(ok),"detail":detail})
    record("deck_hash",digest(deck)==m["deck_sha256"])
    record("slide_count",len(prs.slides)==m["slides"],len(prs.slides))
    record("canvas_16_by_9",abs(prs.slide_width/prs.slide_height-16/9)<.001)
    overflow=[];bars=[];foot=[];fonts=set();notes=[]
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    for i,s in enumerate(prs.slides,1):
        notes.append(bool(s.notes_slide.notes_text_frame.text.strip()))
        for sh in s.shapes:
            if sh.left<0 or sh.top<0 or sh.left+sh.width>prs.slide_width+100 or sh.top+sh.height>prs.slide_height+100:overflow.append([i,sh.name])
            if sh.shape_type==MSO_SHAPE_TYPE.AUTO_SHAPE and 0<sh.width<.06*914400 and sh.height>914400:bars.append([i,sh.name])
            if 6.60*914400<sh.top<7.03*914400 and sh.has_text_frame and sh.text.strip():foot.append([i,sh.text])
            if sh.has_text_frame:
                for p in sh.text_frame.paragraphs:
                    for r in p.runs:
                        if r.font.name:fonts.add(r.font.name)
            if sh.has_table:
                for row in sh.table.rows:
                    for cell in row.cells:
                        for p in cell.text_frame.paragraphs:
                            for r in p.runs:
                                if r.font.name:fonts.add(r.font.name)
    record("canvas_bounds",not overflow,overflow)
    record("no_left_box_strips",not bars,bars);record("no_added_bottom_footnotes",not foot,foot)
    record("native_template_fonts",fonts<={m["style"]["title_font"],m["style"]["body_font"]},sorted(fonts))
    record("speaker_notes_present",all(notes),[i+1 for i,ok in enumerate(notes) if not ok])
    _,spec,_=load_spec(m["spec"])
    sources={s["id"]:s for s in spec.get("sources",[])}
    unresolved=[rid for slide in spec["slides"] for rid in slide.get("source_ids",[]) if rid not in sources]
    record("reference_ids_resolve",not unresolved,unresolved)
    invalid_urls=[rid for rid,s in sources.items() if s.get("url") and not re.match(r"^https?://[^\s/]+(?:/[^\s]*)?$",s["url"])]
    record("reference_url_syntax",not invalid_urls,invalid_urls)
    changed=[p for p,h in m["inputs"].items() if not Path(p).exists() or digest(p)!=h]
    record("input_hashes",not changed,changed)
    with ZipFile(deck) as z:
        record("zip_integrity",z.testzip() is None)
        embedded={hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith("ppt/media/")}
        gifs=[x for x in m["media"] if x["frames"]>1]
        record("animated_gifs_embedded",all(x["sha256"] in embedded for x in gifs),len(gifs))
    pdf=deck.with_suffix(".pdf")
    if pdf.exists():
        import pymupdf
        doc=pymupdf.open(pdf);record("pdf_pages",len(doc)==len(prs.slides),len(doc))
        record("pdf_hash",m.get("pdf_sha256")==digest(pdf))
        names=sorted({f[3] for p in doc for f in p.get_fonts()})
        normalized=lambda s:re.sub(r"[^a-z]","",s.lower())
        record("pdf_font_families",all(any(normalized(font) in normalized(n) for n in names) for font in (m["style"]["title_font"],m["style"]["body_font"])),names)
    else:record("pdf_rendered",False,"No PDF: render inspection is incomplete.")
    result={"passed":all(c["passed"] for c in checks),"checks":checks,"deck_sha256":digest(deck),
            "scope":"Artifact checks only. Visual inspection and scientific review remain separate."}
    write_json(project/"checks/validation.json",result)
    print(json.dumps({"passed":result["passed"],"checks":len(checks),"failures":[c for c in checks if not c["passed"]]},ensure_ascii=False,indent=2))
    return 0 if result["passed"] else 1


def gif(args):
    from PIL import Image
    paths=[Path(x).resolve() for x in args.frames]
    frames=[Image.open(p).convert("RGB") for p in paths]
    if len(frames)<2 or len({f.size for f in frames})!=1:raise ValueError("Provide at least two equal-size image frames.")
    durations=args.durations or [args.duration]*len(frames)
    if len(durations)!=len(frames) or min(durations)<20:raise ValueError("Provide one duration >=20 ms per frame.")
    dest=Path(args.output).resolve();dest.parent.mkdir(parents=True,exist_ok=True)
    frames[0].save(dest,save_all=True,append_images=frames[1:],duration=durations,loop=0,disposal=2,optimize=True)
    poster=dest.with_suffix(".png");frames[0].save(poster)
    write_json(dest.with_suffix(".json"),{"kind":args.kind,"frames":len(frames),"durations_ms":durations,
               "inputs":{os.path.relpath(p,dest.parent):digest(p) for p in paths},"gif_sha256":digest(dest),"poster":poster.name})
    print(dest)


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest="command",required=True)
    a=sub.add_parser("init");a.add_argument("--project",required=True);a.add_argument("--language",choices=["vi","en"],default="vi")
    a=sub.add_parser("build");a.add_argument("--spec",required=True);a.add_argument("--out");a.add_argument("--force",action="store_true")
    a=sub.add_parser("render");a.add_argument("--project",required=True);a.add_argument("--soffice")
    a=sub.add_parser("check");a.add_argument("--project",required=True)
    a=sub.add_parser("gif");a.add_argument("--frames",nargs="+",required=True);a.add_argument("--output",required=True)
    a.add_argument("--duration",type=int,default=1800);a.add_argument("--durations",nargs="+",type=int)
    a.add_argument("--kind",choices=["schematic","replay","measured"],required=True)
    args=p.parse_args()
    try:
        if args.command=="init":initialize(args)
        elif args.command=="build":Deck(args.spec,args.out or Path(args.spec).resolve().parent).build(args.force)
        elif args.command=="render":render(args)
        elif args.command=="gif":gif(args)
        else:return check(args)
    except (ValueError,KeyError,OSError) as e:
        print(f"CTU slides: {e}",file=sys.stderr);return 2
    return 0


if __name__=="__main__":raise SystemExit(main())
