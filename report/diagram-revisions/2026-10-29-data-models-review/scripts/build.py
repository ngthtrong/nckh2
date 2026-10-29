#!/usr/bin/env python3
"""Build three review-only data diagrams; never writes into the report sources/assets.

Run from repository root with report/build/visual-env/bin/python <this script>.
The router and ER symbols are adapted from the user-supplied template.
"""
from __future__ import annotations

import ast
from collections import defaultdict
import hashlib
import html
import json
import math
from pathlib import Path
import sqlite3
import subprocess
import xml.etree.ElementTree as ET

import cairosvg
import erd_renderer as erd

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
ONE, OPT, MANY, SOME = ('one and only one', 'zero or one', 'zero or many', 'one or many')


def attr(name, dtype='', *, pk=False, nullable=False):
    return pk, name, dtype, nullable


def add(d, name, attrs):
    d.boxes[name] = erd.Box(name, attrs)


def rel(d, a, b, label, ca=ONE, cb=MANY, ident=False):
    d.rels.append(erd.Rel(a, b, label, ca, cb, ident))


def domain_relations(d, logical=False):
    rel(d, 'Report Source', 'Rescue Report', 'submits', OPT)
    rel(d, 'Rescue Team', 'Rescue Report', 'is assigned', OPT)
    rel(d, 'Rescue Report', 'Report Event', 'records')
    rel(d, 'Operator', 'Report Event', 'performs', OPT)
    rel(d, 'Algorithm Configuration', 'Analysis Run', 'is used by')
    rel(d, 'Analysis Run', 'Rescue Cluster', 'produces', ident=logical)
    rel(d, 'Rescue Cluster', 'Evidence Family', 'contains', cb=SOME, ident=logical)
    if logical:
        rel(d, 'Rescue Report', 'Analysis Member', 'is captured as', ident=True)
        rel(d, 'Analysis Run', 'Analysis Member', 'contains', ident=True)
        rel(d, 'Evidence Family', 'Analysis Member', 'contains', cb=SOME)
    else:
        rel(d, 'Rescue Report', 'Evidence Family', 'participates per run', SOME, MANY)


def cdm():
    d = erd.Diagram('CDM · Conceptual Data Model')
    boxes = {
        'Report Source': ['Mobile app / SMS / hotline', 'Synthetic sources marked'],
        'Rescue Report': ['Location L; observed time T', 'Flood F; urgency E', 'People N; vulnerability V', 'Image and source provenance'],
        'Rescue Team': ['Personnel and contact details', 'Current report assignment'],
        'Operator': ['Account and role', 'Auditable operator actions'],
        'Report Event': ['Intake / assignment / status', 'Time, channel and actor'],
        'Algorithm Configuration': ['Graph and confidence parameters', 'Near-duplicate and priority settings', 'Formula version and mapping rules'],
        'Analysis Run': ['Immutable input snapshot', 'Configuration and code version'],
        'Rescue Cluster': ['Family-wise E, F, N, V aggregates', 'Priority score P(c)'],
        'Evidence Family': ['Exact / near-duplicate evidence', 'Maxima reduce duplicate influence'],
    }
    for name, values in boxes.items():
        add(d, name, [attr(v) for v in values])
    domain_relations(d)
    grid = [
        ['Report Source', 'Rescue Report', 'Rescue Team'],
        ['Algorithm Configuration', 'Report Event', 'Operator'],
        ['Analysis Run', 'Rescue Cluster', 'Evidence Family'],
    ]
    d.layout(grid, colgap=150, rowgap=100)
    return d


def ldm():
    d = erd.Diagram('LDM · Logical Data Model')
    definitions = {
        'Report Source': [attr('Source ID', 'ID', pk=True), attr('Source type', 'Enum'), attr('Source family', 'Text', nullable=True)],
        'Rescue Report': [
            attr('Report ID', 'ID', pk=True), attr('Source ID; assigned team ID', 'ID', nullable=True),
            attr('Observed time T; location L', 'DateTime; Geo', nullable=True),
            attr('Flood F; urgency E', 'Real [0,1]', nullable=True),
            attr('People N; vulnerability V', 'Real ≥ 0', nullable=True),
            attr('LR score; five urgency flags', 'Real; Boolean[5]', nullable=True),
            attr('Image; model versions', 'Metadata', nullable=True),
            attr('Received time', 'DateTime'), attr('Status; status version', 'Enum; Integer'),
        ],
        'Rescue Team': [attr('Team ID', 'ID', pk=True), attr('Team name', 'Text (unique)'),
            attr('Member count; phone', 'Integer; Text', nullable=True), attr('Active', 'Boolean')],
        'Operator': [attr('Operator ID', 'ID', pk=True), attr('Username', 'Text (unique)'),
            attr('Display name', 'Text (unique)'), attr('Role; active', 'Enum; Boolean')],
        'Report Event': [attr('Event ID', 'ID', pk=True), attr('Report ID', 'ID'),
            attr('Operator ID', 'ID', nullable=True), attr('Kind; channel; time', 'Enum; Text; DateTime'),
            attr('Before; after; note', 'Text', nullable=True)],
        'Algorithm Configuration': [
            attr('Configuration ID', 'ID', pk=True), attr('Formula version', 'Text'),
            attr('Graph mode; community method', 'Enum; Enum'),
            attr('σ; τt; τF; τE', 'Real > 0'), attr('α; β; γ', 'Real ≥ 0'),
            attr('q; K; resolution; seed', 'Real; Int; Real; Int'),
            attr('b0; b1; b2 (Q)', 'Real'), attr('Corroboration radius; time window', 'Real ≥ 0'),
            attr('ωE; ωF; ωN', 'Real; sum = 1'), attr('μ; s; Nref; Ncap; Vcap', 'Real'),
            attr('Near: d; Δt; ΔF; ΔE', 'Real ≥ 0'),
            attr('Near: ΔN; ρN; ΔV; ΔQ', 'Real ≥ 0'),
            attr('Same source family; image state', 'Boolean'),
            attr('LR: ξ0; ξ1..ξ5; threshold', 'Real'),
            attr('Flag order; flood-label mapping', 'List; Map'),
        ],
        'Analysis Run': [attr('Run ID', 'ID', pk=True), attr('Configuration ID', 'ID'),
            attr('Input revision; code version', 'Integer; Text'), attr('Started time; state', 'DateTime; Enum'),
            attr('Completed time; threshold θ', 'DateTime; Real', nullable=True)],
        'Rescue Cluster': [attr('Run ID', 'ID', pk=True), attr('Cluster ID', 'Integer', pk=True),
            attr('Cluster key', 'Smallest member report ID'), attr('Ē; F̄; N̄', 'Real [0,1]'),
            attr('V̄; priority P(c)', 'Real ≥ 0; [0,μ]')],
        'Evidence Family': [attr('Run ID', 'ID', pk=True), attr('Cluster ID', 'Integer', pk=True),
            attr('Family ID', 'Integer', pk=True)],
        'Analysis Member': [
            attr('Run ID', 'ID', pk=True), attr('Report ID', 'ID', pk=True),
            attr('Cluster ID; family ID', 'Integer'), attr('Snapshot L; T', 'Geo; DateTime'),
            attr('Snapshot F; E', 'Real [0,1]'), attr('Snapshot N; V', 'Real ≥ 0'),
            attr('Image present; fingerprint', 'Boolean; Hash'), attr('Corroboration count; Q', 'Integer ≥ 0; [0,1]'),
            attr('Source family; provenance', 'Text; Real', nullable=True),
        ],
    }
    for name, values in definitions.items():
        add(d, name, values)
    domain_relations(d, logical=True)
    grid = [
        ['Report Source', 'Rescue Report', 'Rescue Team', 'Operator'],
        ['Algorithm Configuration', 'Analysis Member', 'Report Event', None],
        ['Analysis Run', 'Evidence Family', 'Rescue Cluster', None],
    ]
    d.layout(grid, colgap=136, rowgap=104)
    return d


def database():
    db = sqlite3.connect(':memory:')
    db.row_factory = sqlite3.Row
    db.executescript((HERE / 'schema.sql').read_text())
    return db


def validate_schema(db):
    """Audit original columns and exercise composite keys in an in-memory fixture."""
    original=sqlite3.connect(':memory:')
    for node in ast.walk(ast.parse((REPO/'products/be/storage.py').read_text())):
        if not (isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)
                and node.func.attr=='execute' and node.args):
            continue
        arg=node.args[0]
        if isinstance(arg,ast.Constant) and isinstance(arg.value,str):
            sql=arg.value
        elif isinstance(arg,ast.JoinedStr):
            sql=''.join(p.value if isinstance(p,ast.Constant) else 'reports' for p in arg.values)
        else:
            continue
        if sql.lstrip().upper().startswith('CREATE TABLE'):
            original.execute(sql)
    preserved={}
    for table, in original.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
        before={r[1]:r[2] for r in original.execute(f'PRAGMA table_info({table})')}
        after={r['name']:r['type'] for r in db.execute(f'PRAGMA table_info({table})')}
        assert all(after.get(c)==t for c,t in before.items()),table
        preserved[table]={'existing_columns':len(before),'proposed_columns':len(after)}
    assert len(preserved)==7
    original.close()

    # Values from the report's Product profile and the local policy/model files.
    # These are illustrative validation records, not an experiment or migration.
    lr=json.loads((REPO/'products/fe/app/assets/models/urgency_logistic.json').read_text())
    cfg={
        'id':'review-product-full-v1','label':'Illustrative full-input Product profile',
        'created_at':'2026-10-29T00:00:00Z','formula_version':'report-eq1-eq4',
        'graph_mode':'product','community_algorithm':'louvain','sigma_geo_m':700.0,
        'tau_t_min':60.0,'tau_f':0.25,'tau_e':0.35,'alpha':1.0,'beta':0.5,'gamma':0.5,
        'quantile_q':0.90,'top_k':8,'resolution':1.2,'random_seed':42,
        'q_b0':-0.2,'q_b1':1.4,'q_b2':0.9,'corrob_radius_m':400.0,'corrob_window_min':60.0,
        'omega_e':0.34,'omega_f':0.33,'omega_n':0.33,'mu':2.0,'v_scale':10.0,
        'n_ref':500.0,'n_claim_cap':500.0,'v_cap':50.0,'near_distance_m':100.0,
        'near_time_min':10.0,'near_f_abs':0.10,'near_e_abs':0.10,'near_n_floor':5.0,
        'near_n_relative':0.25,'near_v_abs':2.0,'near_q_abs':0.10,
        'require_same_source_family':0,'require_same_image_state':0,
        'lr_intercept':lr['intercept'],'lr_threshold':lr['threshold'],
        'lr_feature_order_json':json.dumps(lr['feature_order']),
        'flood_mapping_json':json.dumps({'non_flood':0.0,'low':0.33,'medium':0.66,'high':1.0}),
        **{'lr_coef_'+str(i+1):lr['coefficients'][name] for i,name in enumerate(lr['feature_order'])},
    }
    expected={r['name'] for r in db.execute('PRAGMA table_info(algorithm_configs)')}
    assert set(cfg)==expected
    keys=','.join(cfg)
    db.execute(f'INSERT INTO algorithm_configs ({keys}) VALUES ({",".join("?" for _ in cfg)})',list(cfg.values()))
    db.execute("INSERT INTO sources VALUES ('fixture-source','synthetic','fixture','2026-10-29T00:00:00Z')")
    db.execute("INSERT INTO reports(id,server_received_at,raw_payload,source_id) VALUES ('fixture-r1','2026-10-29T00:00:00Z','{}','fixture-source')")
    db.execute("INSERT INTO analysis_runs(id,config_id,input_revision,created_at,state,code_version) VALUES ('fixture-run',?,1,'2026-10-29T00:00:00Z','building','fixture')",(cfg['id'],))
    db.execute("INSERT INTO clusters VALUES ('fixture-run',1,'fixture-r1',0.5,0.7,0.4,2.0,0.6)")
    db.execute("INSERT INTO evidence_families VALUES ('fixture-run',1,1)")
    qi=1.0/(1.0+math.exp(-(-0.2+1.4)))
    values=('fixture-run','fixture-r1',1,1,10.0,105.0,'2026-10-29T00:00:00Z',0.7,0.8,5.0,2.0,1,'fixture',0.9,'fixture-fingerprint',0,qi)
    statement='INSERT INTO analysis_members VALUES ('+','.join('?' for _ in values)+')'
    db.execute(statement,values)
    checks=[]
    for label,sql,args in [
        ('one membership per report and run',statement,values),
        ('family must belong to the same run and cluster',"UPDATE analysis_members SET cluster_id=2",()),
        ('full-input snapshot rejects missing E',"UPDATE analysis_members SET urgency=NULL",()),
        ('Q domain is bounded',"UPDATE analysis_members SET q_score=1.1",()),
        ('priority weights sum to one',"UPDATE algorithm_configs SET omega_e=1.0",()),
    ]:
        try:
            db.execute(sql,args)
        except sqlite3.IntegrityError:
            checks.append(label)
        else:
            raise AssertionError('Expected constraint failure: '+label)
    assert not db.execute('PRAGMA foreign_key_check').fetchall()
    (HERE/'example-config.json').write_text(json.dumps({'purpose':'Illustrative design/constraint check only; not an executed experiment',
        'alpha_note':'Stored for the additive alternative; inactive in Product mode. This is not a reproduction of an optimized Additive run.',
        'parameters':cfg},ensure_ascii=False,indent=2)+'\n')
    db.rollback()  # The validation fixture is never saved as a database file.
    return {'preserved_current_columns':preserved,'constraint_checks':checks,
            'config_field_count':len(cfg),'fixture':'in-memory; rolled back'}


def pdm(db):
    d = erd.Diagram('PDM · Proposed SQLite Schema — All Columns')
    tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    for table in tables:
        columns = list(db.execute(f'PRAGMA table_info({table})'))
        fk_cols = {r['from'] for r in db.execute(f'PRAGMA foreign_key_list({table})')}
        unique_cols = set()
        for idx in db.execute(f'PRAGMA index_list({table})'):
            if idx['unique']:
                ic = list(db.execute(f'PRAGMA index_info({idx["name"]})'))
                if len(ic) == 1:
                    unique_cols.add(ic[0]['name'])
        attrs = []
        for row in columns:
            tags = []
            if row['name'] in fk_cols:
                tags.append('FK')
            if row['name'] in unique_cols and not row['pk']:
                tags.append('UQ')
            dtype = row['type'] + (' · ' + '/'.join(tags) if tags else '')
            attrs.append(attr(row['name'], dtype, pk=bool(row['pk']), nullable=not (row['notnull'] or row['pk'])))
        add(d, table, attrs)
        grouped = defaultdict(list)
        for f in db.execute(f'PRAGMA foreign_key_list({table})'):
            grouped[f['id']].append(f)
        pks = {c['name'] for c in columns if c['pk']}
        nullable = {c['name'] for c in columns if not c['notnull'] and not c['pk']}
        for group in grouped.values():
            fcols = {f['from'] for f in group}
            rel(d, group[0]['table'], table, '', OPT if fcols & nullable else ONE,
                MANY, ident=fcols <= pks)

    # Columns are groups; all physical columns are present, including the long
    # immutable configuration table. Natural-size PDF stays readable when zoomed.
    groups = [
        ('A · RESCUE OPERATIONS', ['sources', 'teams', 'reports']),
        ('B · CONTROL AND SYNC', ['operators', 'sessions', 'report_events', 'messages_dedup', 'server_meta']),
        ('C · METHOD CONFIGURATION', ['algorithm_configs']),
        ('D · ANALYSIS RESULTS', ['analysis_runs', 'clusters', 'evidence_families', 'analysis_members']),
    ]
    x = 64
    for label, names in groups:
        for name in names:
            d.boxes[name].measure()
        width = max(d.boxes[n].w for n in names)
        y = 80
        for name in names:
            b = d.boxes[name]
            b.x, b.y = x + erd.snap((width-b.w)/2), y
            y += b.h + 96
        x += width + 160
        d.panels.append((label, '#1F3864', '#F6F8FC', names))
    d.W = erd.snap(x-160+64)
    d.H = erd.snap(max(b.y+b.h for b in d.boxes.values())+72)
    return d


def validate_geometry(d):
    d.choose_sides()
    d.assign_ports()
    d.straighten()
    d.route()
    d.place_labels()
    errors = d.check()
    boxes = list(d.boxes.values())
    box_overlap = sum(erd.overlap(a.rect,b.rect) for i,a in enumerate(boxes) for b in boxes[i+1:])
    hits = []
    for r in d.rels:
        for p,q in zip(r.path,r.path[1:]):
            for b in boxes:
                if b.name not in (r.a,r.b) and erd.seg_hits(b.rect,p,q,shrink=2):
                    hits.append((r.a,r.b,b.name))
    if errors or box_overlap or hits or d.label_bad:
        raise ValueError({'line_errors':errors,'box_overlap':box_overlap,'box_hits':hits,'label_errors':d.label_bad})
    # Attribute widths are measured from the same font files used by all exports.
    for b in boxes:
        for pk,name,dtype,nullable in b.attrs:
            if b.col2 + erd.tw(dtype + ('  N' if nullable else ''),erd.FS) + erd.PADX > b.w + 1:
                raise ValueError('Attribute overflow: '+b.name+'.'+name)
    return {'box_count':len(boxes),'relationship_count':len(d.rels),'geometry_errors':0,
            'box_intersections':0,'line_box_hits':0,'attribute_overflows':0,**d.metrics()}


def drawio(d, stem, note):
    """Editable entity containers, one cell per attribute, fixed orthogonal edges."""
    root = ET.Element('mxfile', host='app.diagrams.net', version='26.0.0')
    page = ET.SubElement(root,'diagram',name=d.title,id=stem)
    model = ET.SubElement(page,'mxGraphModel',page='1',pageWidth=str(d.W),pageHeight=str(d.H),grid='1',gridSize='8')
    cells = ET.SubElement(model,'root')
    ET.SubElement(cells,'mxCell',id='0')
    ET.SubElement(cells,'mxCell',id='1',parent='0')
    def cell(id,value,x,y,w,h,style,parent='1'):
        c=ET.SubElement(cells,'mxCell',id=id,value=value,parent=parent,vertex='1',style=style)
        ET.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'})
    textstyle='text;html=1;whiteSpace=wrap;overflow=visible;spacing=0;fontFamily=DejaVu Serif;'
    for i,(label,color,fill,rect) in enumerate(d.panel_rects()):
        x,y,x1,y1=rect
        cell('panel'+str(i),'',x,y,x1-x,y1-y,f'rounded=1;fillColor={fill};strokeColor={color};')
        cell('panelname'+str(i),html.escape(label),x+8,y+2,x1-x-16,18,textstyle+'fontStyle=1;fontSize=10.5;align=left;')
    ids={n:'entity'+str(i) for i,n in enumerate(d.boxes)}
    arrows={ONE:'ERmandOne',OPT:'ERzeroToOne',MANY:'ERzeroToMany',SOME:'ERoneToMany'}
    for i,r in enumerate(d.rels):
        a,b=d.boxes[r.a],d.boxes[r.b]
        ax,ay=(r.pa[0]-a.x)/a.w,(r.pa[1]-a.y)/a.h
        bx,by=(r.pb[0]-b.x)/b.w,(r.pb[1]-b.y)/b.h
        style=(f'html=1;rounded=0;noEdgeStyle=1;startArrow={arrows[r.ca]};endArrow={arrows[r.cb]};'
               f'startFill=0;endFill=0;dashed={int(not r.ident)};strokeColor=#333333;jumpStyle=gap;jumpSize=8;'
               f'exitX={ax};exitY={ay};entryX={bx};entryY={by};exitPerimeter=0;entryPerimeter=0;')
        c=ET.SubElement(cells,'mxCell',id='edge'+str(i),parent='1',edge='1',source=ids[r.a],target=ids[r.b],style=style)
        g=ET.SubElement(c,'mxGeometry',relative='1',**{'as':'geometry'})
        arr=ET.SubElement(g,'Array',**{'as':'points'})
        for x,y in r.path[1:-1]:
            ET.SubElement(arr,'mxPoint',x=str(x),y=str(y))
        if r.lab:
            x,y,x1,y1=r.lab
            cell('label'+str(i),html.escape(r.label),x,y,x1-x,y1-y,textstyle+'fontSize=10.5;align=center;fillColor=#FFFFFF;')
    for n,b in d.boxes.items():
        eid=ids[n]
        cell(eid,'',b.x,b.y,b.w,b.h,'rounded=0;fillColor=#FFFFFF;strokeColor=#1F3864;container=1;collapsible=0;')
        cell(eid+'head',html.escape(n),0,0,b.w,erd.HEAD,
             textstyle+'fontSize=12.5;fontStyle=1;align=center;fillColor=#DCE6F2;strokeColor=#1F3864;',eid)
        for j,(pk,name,dtype,nullable) in enumerate(b.attrs):
            y=erd.HEAD+4+j*erd.ROW
            label=('<u>'+html.escape(name)+'</u>') if pk else html.escape(name)
            if pk:
                cell(eid+'key'+str(j),'PK',1,y,17,erd.ROW,textstyle+'fontSize=7;fontColor=#9C6500;',eid)
            cell(eid+'a'+str(j),label,b.col1,y,b.col2-b.col1-5,erd.ROW,textstyle+'fontSize=12;align=left;',eid)
            cell(eid+'t'+str(j),html.escape(dtype)+(' <font color="#9C0006">N</font>' if nullable else ''),
                 b.col2,y,b.w-b.col2-erd.PADX,erd.ROW,textstyle+'fontSize=12;align=left;fontColor=#444444;',eid)
    cell('title',html.escape(d.title),48,8,d.W-96,24,textstyle+'fontSize=17;fontStyle=1;align=center;')
    for i,ln in enumerate(note.splitlines()):
        cell('note'+str(i),html.escape(ln),48,d.H-12-18*(len(note.splitlines())-i),d.W-96,18,
             textstyle+'fontSize=11;fontStyle=2;align=left;')
    ET.indent(root)
    ET.ElementTree(root).write(HERE/(stem+'.drawio'),encoding='utf-8',xml_declaration=True)


def export(d, stem, note):
    # Leave room for the title and panel headers without changing routed geometry.
    for b in d.boxes.values():
        b.y += 32
    d.H += 32
    stats=validate_geometry(d)
    d.render(str(HERE/stem),note)
    svg=HERE/(stem+'.svg')
    content=svg.read_text()
    title=(f'<text x="{d.W/2}" y="23" text-anchor="middle" font-size="17" '
           f'font-weight="bold" fill="#1F3864">{html.escape(d.title)}</text>')
    content=content.replace('</svg>',title+'\n</svg>')
    svg.write_text(content)
    # Raster and PDF both derive from the final SVG, including title/diacritics.
    cairosvg.svg2pdf(bytestring=content.encode(),write_to=str(HERE/(stem+'.pdf')))
    cairosvg.svg2png(bytestring=content.encode(),write_to=str(HERE/(stem+'.png')),scale=3)
    drawio(d,stem,note)
    stats['size_px']=[d.W,d.H]
    return stats


def dictionary(db):
    lines=['# Từ điển PDM đề xuất','',
        'Sinh trực tiếp từ `schema.sql`; đây là thiết kế để review, chưa áp dụng vào backend.','',
        'PK: khóa chính; FK: khóa ngoại; N: cho phép NULL. Default, CHECK, UNIQUE và FK ghép xem SQL.','']
    for table, in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
        lines += ['## '+table,'','| Cột | Kiểu SQLite | PK | N | Mặc định |','|---|---|---|---|---|']
        for c in db.execute(f'PRAGMA table_info({table})'):
            lines.append(f'| `{c["name"]}` | {c["type"]} | {c["pk"] or ""} | {"N" if not(c["notnull"] or c["pk"]) else ""} | {c["dflt_value"] or ""} |')
        for fk in db.execute(f'PRAGMA foreign_key_list({table})'):
            lines += ['',f'- FK #{fk["id"]}: `{fk["from"]}` → `{fk["table"]}.{fk["to"]}`.']
        lines.append('')
    (HERE/'data-dictionary.md').write_text('\n'.join(lines)+'\n')


def main():
    db=database()
    schema_checks=validate_schema(db)
    assert not db.execute('PRAGMA foreign_key_check').fetchall()
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    legend='Underlined key = PK; N = nullable; crow foot = many; circle = zero; double bar = exactly one.'
    legends=[
        'Business relationships; a report can enter multiple runs. Crow foot = many; circle = zero; double bar = exactly one.\n'
        'Q and P(c) are derived values. Each evidence family belongs to one cluster within one analysis run.',
        legend+'\nSolid = identifying; dashed = non-identifying. Parameter groups are logical composite types.\n'
        'Analysis members retain complete L, T, F, E, N, V snapshots and Q; intake records may still have missing fields.',
        legend+'\nSolid = identifying; dashed = non-identifying. FK/UQ = foreign key/single-column unique key.\n'
        'Composite UNIQUE, CHECK, DEFAULT and indexes: see schema.sql. All columns are shown.\n'
        'Proposed 13-table schema: retains columns of seven existing tables and adds six tables. Not implemented in the backend.',
    ]
    stems=['01-cdm','02-ldm','03-pdm']
    results={}
    for stem,factory,note in zip(stems,[cdm,ldm,lambda:pdm(db)],legends):
        results[stem]=export(factory(),stem,note)
        print(stem,results[stem],flush=True)
    subprocess.run(['pdfunite',*[str(HERE/(s+'.pdf')) for s in stems],str(HERE/'review.pdf')],check=True)
    dictionary(db)
    (HERE/'validation.json').write_text(json.dumps({'diagrams':results,'schema_checks':schema_checks,'sqlite_integrity':'ok',
        'foreign_key_check':'ok','schema_scope':'proposed; in-memory only'},ensure_ascii=False,indent=2)+'\n')
    sources=['template-diagram-system/erd.py','template-diagram-system/README.md',
        'report/chapters/03-system/sections/architecture.tex','report/chapters/02-data-methods/sections/methods.tex',
        'products/be/storage.py','products/be/cluster_service.py','products/be/rescue_core/contracts.py',
        'products/be/rescue_core/dedup.py','products/be/rescue_core/priority.py',
        'products/be/rescue_core/clustering.py','products/fe/app/assets/models/urgency_logistic.json']
    (HERE/'sources.json').write_text(json.dumps({s:hashlib.sha256((REPO/s).read_bytes()).hexdigest() for s in sources},indent=2)+'\n')
    initial=json.loads((HERE/'initial-state.json').read_text())
    changed=[p for p,h in initial['protected_sha256'].items() if hashlib.sha256((REPO/p).read_bytes()).hexdigest()!=h]
    assert not changed, 'Protected originals changed: '+repr(changed)
    print('Protected report, existing dashboard edits, and supplied templates: unchanged.')


if __name__=='__main__':
    main()
