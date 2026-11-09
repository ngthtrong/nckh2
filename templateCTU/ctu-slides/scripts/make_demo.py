#!/usr/bin/env python3
"""Regenerate the topic-neutral layout catalog and explicitly illustrative media."""
from pathlib import Path
import importlib.util
import json

from PIL import Image,ImageDraw,ImageFont

BASE=Path(__file__).resolve().parents[1]
EX=BASE/"examples"


def main():
    EX.mkdir(exist_ok=True);media=EX/"media";media.mkdir(exist_ok=True)
    heading=ImageFont.truetype(str(BASE/"assets/fonts/k2d/K2D-Bold.ttf"),40)
    body=ImageFont.truetype(str(BASE/"assets/fonts/readexpro/ReadexPro-Regular.ttf"),27)
    frames=[]
    for active in range(3):
        im=Image.new("RGB",(1600,720),"white");draw=ImageDraw.Draw(im)
        draw.text((70,45),"Schematic process — layout example",font=heading,fill="#17212B")
        draw.text((70,115),"Illustration only; no research observations or measured timing.",font=body,fill="#526474")
        for i,(name,desc) in enumerate([("Input","Describe observable inputs"),("Method","Explain the operation"),("Output","Show the expected artifact")]):
            x=70+i*510;c="#0070C0" if i==active else "#D6E3EC"
            draw.rounded_rectangle((x,255,x+430,520),radius=18,fill="#F0F6FA",outline=c,width=5 if i==active else 2)
            draw.text((x+28,295),name,font=heading,fill="#0070C0")
            draw.text((x+28,390),desc,font=body,fill="#17212B")
            if i<2:
                draw.line((x+447,385,x+492,385),fill="#00AFEF",width=4)
                draw.polygon([(x+492,385),(x+478,377),(x+478,393)],fill="#00AFEF")
        p=media/f"frame-{active+1}.png";im.save(p);frames.append(p)
    spec=importlib.util.spec_from_file_location("ctu_slides",BASE/"scripts/ctu_slides.py")
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    from argparse import Namespace
    module.gif(Namespace(frames=[str(p) for p in frames],output=str(media/"process.gif"),duration=1800,durations=None,kind="schematic"))
    (EX/"illustrative.csv").write_text("label,value,low,high\nExample A,0.60,0.54,0.66\nExample B,0.72,0.66,0.78\nExample C,0.79,0.74,0.84\n",encoding="utf-8")
    common={"notes":"This is a reusable layout example. Replace its content with the new topic's verified evidence before presenting it as research.","source_ids":["template"]}
    def s(layout,title,**kw):return {**common,"layout":layout,"title":title,**kw}
    slides=[
        s("title","CTU research presentation\nReusable layout catalog",authors=["Your research team"],event="Layout demonstration · illustrative content"),
        s("overview","Presentation overview",items=[{"heading":"Problem and research gap","body":"Explain why the work is needed."},{"heading":"Data and methods","body":"Define the inputs and core concepts."},{"heading":"Evaluation and results","body":"Define metrics before interpreting results."},{"heading":"Conclusion and next steps","body":"State evidence limits and proposed validation."}]),
        s("bullets","Build a clear research narrative",subtitle="Example structure; adjust it to the topic and audience",items=[{"heading":"Start with the problem","body":"Use one concrete situation to motivate the research question."},{"heading":"Explain unfamiliar concepts","body":"Introduce algorithms, symbols and metrics before reporting values."},{"heading":"Keep claim and evidence together","body":"Distinguish observed results, mathematical conditions and proposed work."}]),
        s("cards","Compare three parallel ideas",subtitle="Plain boxes with a uniform outline and no colored left strip",items=[{"heading":"Context","body":"What is the practical problem?\nWhich audience needs the answer?"},{"heading":"Contribution","body":"What does the work introduce?\nWhat comparison tests it?","color":"teal"},{"heading":"Evidence limits","body":"Which conditions were tested?\nWhat remains unknown?","color":"orange"}]),
        s("flow","An editable process diagram",subtitle="Native PowerPoint shapes; adapt the stages to the actual workflow",items=[{"heading":"Input","body":"Name the data and the observable fields."},{"heading":"Preparation","body":"Describe transformations and exclusions."},{"heading":"Method","body":"Explain the decision or computation."},{"heading":"Evaluation","body":"Compare outputs with independent evidence."}]),
        s("equations","Explain formulas before presenting results",subtitle="Generic weighted score shown only as a notation example",equations=[{"label":"Weighted combination","latex":r"S=\sum_{j=1}^{m}w_jx_j"},{"label":"Example constraints","latex":r"w_j\geq0,\qquad\sum_{j=1}^{m}w_j=1"}],glossary="S: a generic score\nx: input components\nw: component weights\nm: number of components\n\nReplace this illustration with the actual method."),
        s("metrics","Define reported metrics",subtitle="Give meaning, unit and direction before showing a result",items=[{"name":"Error","direction":"LOWER IS BETTER","meaning":"Describe the error endpoint and its unit. State what it does not measure."},{"name":"Agreement","direction":"HIGHER IS BETTER","meaning":"Explain what is being compared and the interpretation of the scale."},{"name":"Latency","direction":"LOWER IS BETTER","meaning":"Specify hardware, batch size and measurement boundary."}]),
        s("table","A compact comparison table",subtitle="Illustrative descriptions; no measured performance is claimed",headers=["Aspect","Candidate A","Candidate B"],rows=[["Input","Describe A","Describe B"],["Assumption","State assumption","State assumption"],["Evaluation","Name endpoint","Name endpoint"]],widths=[1,2,2]),
        s("chart","Plot verified data with uncertainty",subtitle="Layout demonstration — ALL numbers and intervals here are illustrative",csv="illustrative.csv",xlabel="Illustrative score (higher is better)",xlim=[0,1],alt="Three illustrative scores and illustrative intervals; not experimental results.",notes="These values are invented for layout demonstration. Replace illustrative.csv with an actual exported result table, record units and the meaning of the intervals, then edit this interpretation."),
        s("figure","Use a large figure with a short explanation",subtitle="Schematic image; replace it with a relevant source-backed visual",path="media/process.png",alt="Schematic input-method-output process",body="The figure supports one main point.\n\nKeep labels large enough to read.\n\nPut detailed source locators in speaker notes."),
        s("figure","Animate only when it explains a change",subtitle="Schematic GIF assembled from three supplied image frames",path="media/process.gif",poster="media/process.png",alt="A schematic highlighting Input, Method and Output in sequence",notes="This GIF is an instructional schematic. Its frame sequence is not an event timeline or a measured experimental result. PowerPoint Slide Show plays the animation; the PDF shows a static frame."),
        s("bullets","Conclusion",items=[{"heading":"State the supported outcome","body":"Tie each conclusion to the evidence actually available."},{"heading":"Retain essential conditions","body":"Keep assumptions and tested scope explicit in the spoken explanation."}]),
        s("bullets","Future work",items=[{"heading":"Close a named evidence gap","body":"State a concrete next validation step instead of implying it has been completed."},{"heading":"Keep the scope appropriate","body":"Choose new data, comparisons or deployment checks only when they answer the remaining question."}]),
        s("references","References",source_ids=["template","fonts"],notes="The catalog's references document the bundled visual template and font license only. A research presentation must replace or supplement them with the actual cited sources."),
        s("closing","Thank you",subtitle="Questions and discussion",body="Can Tho University · reusable research slide template")
    ]
    catalog={"schema":"ctu-slides/1","deck":{"slug":"ctu-layout-catalog","title":"CTU reusable layout catalog","authors":["Your research team"],"affiliation":"Can Tho University","event":"Layout demonstration","language":"en","target_minutes":15},"style":{},
             "sources":[{"id":"template","title":"Supplied CTU PowerPoint template","citation":"Can Tho University. Supplied English PowerPoint template. Local visual source.","path":"../assets/CTU_PowerPoint_Template_English.pptx"},{"id":"fonts","title":"Bundled font license","citation":"K2D / Readex Pro / Barlow. SIL Open Font License 1.1; bundled font files retain their licenses.","path":"../assets/fonts/k2d/OFL.txt","url":"https://openfontlicense.org/"}],"slides":slides}
    module.write_json(EX/"catalog.json",catalog)
    print(EX/"catalog.json")


if __name__=="__main__":main()
