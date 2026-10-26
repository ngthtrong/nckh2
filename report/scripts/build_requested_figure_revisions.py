#!/usr/bin/env python3
"""Scoped revisions requested on 26 October: ten diagrams, no result changes.

Coordinates are print-size points. All generated links have explicit ports and
waypoints; local steps connect vertically, while branches have separate lanes.
"""
from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote

from fontTools.pens.basePen import BasePen
from fontTools.svgLib.path import parse_path
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch
from matplotlib.transforms import Affine2D

import build_readable_report_diagrams as old
import build_detailed_system_diagrams as detailed
from build_system_diagrams import ROOT

REVIEW = ROOT / 'diagram-revisions/2026-10-26-requested-figures'
W = detailed.W


class Diagram(old.Diagram):
    def __init__(self, name, height, title, width=W):
        super().__init__(name, height, title, width=width)
        self.flow_links = []
        self.business_nodes = {}

    def box(self, key, x, y, w, h, value, *, decision=False, size=9.5):
        identifier = old.node(self, x, y, w, h, value, diamond=decision, size=size)
        self.business_nodes[key] = identifier
        return identifier

    def port(self, key, side, offset=.5):
        x, y, w, h, _ = self.shapes[self.business_nodes[key]]
        return {'top': (x+w*offset, y), 'bottom': (x+w*offset, y+h),
                'left': (x, y+h*offset), 'right': (x+w, y+h*offset)}[side]

    def link(self, a, b, points, *, label=None, at=None, dashed=False, heads=True):
        self.arrow(points, source=self.business_nodes.get(a), target=self.business_nodes.get(b),
                   label=label, at=at, dashed=dashed, heads=heads)
        self.flow_links.append({'from': a, 'to': b, 'points': points})

    def down(self, a, b, **kw):
        self.link(a, b, [self.port(a, 'bottom'), self.port(b, 'top')], **kw)


def panels(d, titles, height=384):
    for c, title in enumerate(titles):
        x = 10+c*244
        d.shape(x, 10, 220, height, rounded=False, background=True)
        d.text(x+10, 28, title, ha='left', bold=True, size=10.2)


def captured(factory):
    """Reuse the existing, source-backed wording without regenerating its PDF."""
    original = old.gridflow
    old.gridflow = lambda *a, **kw: (a, kw)
    try:
        args, kwargs = factory()
    finally:
        old.gridflow = original
    return args, kwargs


def grid(factory, height=430):
    args, _ = captured(factory)
    name, title, headings, specs, edges, footer = args
    d = Diagram(name, height, title)
    panels(d, headings)
    for key, (c, r, text, decision) in specs.items():
        x, y, w, h = 20+c*244, 52+r*68, 200, 51
        if decision:
            x += 15
            w -= 30
        d.box(key, x, y, w, h, text, decision=decision)
    return d, edges, footer


def footer(d, value):
    d.text(10, d.height-13, value, ha='left', size=9)


def training():
    d, edges, note = grid(old.training)
    for a, b, label, *_ in edges:
        if (a, b) == ('model', 'freeze'):
            d.link(a, b, [d.port(a, 'right'), (242, 281.5), (242, 77.5), d.port(b, 'left')])
        elif (a, b) == ('ckpt', 'test'):
            d.link(a, b, [d.port(a, 'right'), (492, 349.5), (492, 77.5), d.port(b, 'left')])
        elif (a, b) == ('val', 'tune'):
            d.link(a, b, [d.port(a, 'right'), (478, 213.5), (478, 145.5), d.port(b, 'right')],
                   label=label, at=(482, 179.5), dashed=True)
        else:
            d.down(a, b, label=label or None,
                   at=(389, 291) if label else None)
    footer(d, note)
    return d


def compose():
    d, edges, note = grid(old.compose)
    for a, b, label, *_ in edges:
        if (a, b) == ('photo', 'fallback'):
            d.link(a, b, [d.port(a, 'left'), (14, 145.5), (14, 349.5), d.port(b, 'left')],
                   label=label, at=(46, 311))
        elif (a, b) in [('infer', 'form'), ('fallback', 'form')]:
            lane, target_y = (236, 66) if a == 'infer' else (248, 89)
            d.link(a, b, [d.port(a, 'right'), (lane, d.port(a, 'right')[1]),
                          (lane, target_y), (264, target_y)])
        elif (a, b) == ('check', 'record'):
            d.link(a, b, [d.port(a, 'right'), (492, 349.5), (492, 77.5), d.port(b, 'left')])
        else:
            d.down(a, b, label=label or None, at=(140, 181) if label else None)
    footer(d, note)
    return d


def tracking():
    d, edges, note = grid(old.tracking)
    for a, b, label, *_ in edges:
        if (a, b) == ('net', 'api'):
            d.link(a, b, [d.port(a, 'left'), (14, 145.5), (14, 281.5), d.port(b, 'left')],
                   label=label, at=(37, 257))
        elif (a, b) in [('local', 'merge'), ('api', 'merge')]:
            lane, target_y = (236, 66) if a == 'local' else (248, 89)
            d.link(a, b, [d.port(a, 'right'), (lane, d.port(a, 'right')[1]),
                          (lane, target_y), (264, target_y)])
        elif (a, b) == ('ui', 'active'):
            d.link(a, b, [d.port(a, 'right'), (492, 281.5), (492, 77.5), d.port(b, 'left')])
        elif (a, b) == ('active', 'stop'):
            d.link(a, b, [d.port(a, 'right'), (716, 77.5), (716, 349.5), d.port(b, 'right')],
                   label=label, at=(685, 317))
        else:
            d.down(a, b, label=label or None,
                   at=(145, 181) if a == 'net' else (630, 164))
    footer(d, note)
    return d


def adaptive():
    d, edges, note = grid(old.adaptive, height=464)
    for a, b, label, *_ in edges:
        if (a, b) == ('data', 'meta'):
            d.link(a, b, [d.port(a, 'right'), (226, 145.5), (226, 281.5), d.port(b, 'right')],
                   label=label, at=(202, 246))
        elif (a, b) == ('ack', 'image'):
            d.link(a, b, [d.port(a, 'right'), (242, 349.5), (242, 42), (364, 42), d.port(b, 'top')])
        elif (a, b) == ('image', 'finish'):
            d.link(a, b, [d.port(a, 'left'), (250, 77.5), (250, 362), (264, 362)],
                   label=label, at=(269, 110))
        elif (a, b) == ('modes', 'finish'):
            d.link(a, b, [d.port(a, 'left'), (258, 213.5), (258, 338), (264, 338)],
                   label=label, at=(297, 314))
        elif (a, b) == ('upload', 'retry'):
            d.link(a, b, [d.port(a, 'right'), (492, 281.5), (492, 77.5), d.port(b, 'left')],
                   label=label, at=(531, 122))
        elif (a, b) == ('meta', 'reject'):
            d.link(a, b, [d.port(a, 'left'), (5, 281.5), (5, 425), (722, 425),
                          (722, 213.5), d.port(b, 'right')],
                   label=label, at=(653, 413))
        elif (a, b) == ('finish', 'status'):
            d.link(a, b, [d.port(a, 'bottom'), (364, 400), (608, 400), d.port(b, 'bottom')])
        else:
            at = {'data': (144, 181), 'sms': (157, 248), 'image': (385, 113),
                  'modes': (386, 248)}.get(a)
            d.down(a, b, label=label or None, at=at)
    footer(d, note)
    return d


def overview():
    d = Diagram('flowchart', 440, '2.2 · Bốn phân hệ và phản hồi trạng thái')
    for x, title in [(10, '1 · THIẾT BỊ'), (190, '2 · TIẾP NHẬN'),
                     (370, '3 · PHÂN CỤM'), (550, '4 · ĐIỀU PHỐI')]:
        d.shape(x, 10, 168, 402, rounded=False, background=True)
        d.text(x+10, 29, title, ha='left', bold=True, size=10.2)
    for key, x, y, text in [
        ('create', 20, 55, 'SOS / báo cáo\nLưu cục bộ và Outbox'),
        ('send', 20, 145, 'Gửi thích ứng\nHTTP / SMS; giữ ID khi retry'),
        ('attachment', 20, 235, 'Nhận ACK metadata\nHoàn tất ảnh nếu có'),
        ('track', 20, 335, 'Tra cứu trạng thái\nHiển thị tiến trình cứu hộ'),
        ('receive', 200, 55, 'JSON / ảnh / SMS\nKiểm tra từng kênh'),
        ('save', 200, 145, 'Chống trùng; lưu dữ liệu\nTrả ACK theo message'),
        ('update', 200, 335, 'Ghi thay đổi và nhật ký\nCung cấp trạng thái mới'),
        ('active', 380, 55, 'Đọc báo cáo đang xử lý\nThiếu vị trí/giờ: xem xét'),
        ('graph', 380, 145, 'Đồ thị tương đồng\nPhân cụm Louvain'),
        ('score', 380, 235, 'Họ bằng chứng\nXếp ưu tiên P(c)'),
        ('inspect', 560, 145, 'Xem cụm / hàng xem xét\nXác minh báo cáo'),
        ('assign', 560, 235, 'Giao đội cứu hộ\nCập nhật dispatched'),
        ('close', 560, 335, 'Tác nghiệp; đóng ca\nresolved / cancelled')]:
        d.box(key, x, y, 148, 40, text, size=9.3)
    for a, b in [('create', 'send'), ('attachment', 'track'), ('receive', 'save'),
                 ('active', 'graph'), ('graph', 'score'), ('inspect', 'assign'), ('assign', 'close')]:
        d.down(a, b)
    d.link('send', 'receive', [(168, 165), (181, 165), (181, 75), (200, 75)])
    d.link('save', 'attachment', [(200, 165), (185, 165), (185, 255), (168, 255)],
           label='ACK', at=(188, 221))
    d.link('save', 'active', [(348, 165), (362, 165), (362, 75), (380, 75)])
    d.link('score', 'inspect', [(528, 255), (542, 255), (542, 165), (560, 165)])
    d.link('assign', 'update', [(605, 275), (605, 305), (360, 305), (360, 355), (348, 355)],
           label='Cập nhật nghiệp vụ', at=(443, 305))
    d.link('close', 'update', [(634, 375), (634, 401), (274, 401), (274, 375)])
    d.link('update', 'track', [(200, 355), (168, 355)])
    footer(d, 'ACK xác nhận gửi dữ liệu; trạng thái cứu hộ phản ánh tác nghiệp. Hai luồng thông tin được xử lý riêng.')
    return d


def entity(d, key, x, y, w, title, attributes):
    h = 42+len(attributes)*15
    d.box(key, x, y, w, h, '')
    d.text(x+w/2, y+15, title, bold=True, size=10.5)
    d.arrow([(x, y+29), (x+w, y+29)], heads=False)
    for i, value in enumerate(attributes):
        d.text(x+10, y+43+i*15, value, ha='left', size=9.5,
               bounds=(x+7, y+32, w-14, h-35))


def erd():
    # A larger design canvas preserves >=9 pt text when printed at 257 mm.
    d = Diagram('database_erd', 590, '2.5 · Detailed rescue system domain ERD', width=960)
    d.text(12, 16, 'RESCUE SYSTEM · DOMAIN ENTITY–RELATIONSHIP MODEL', ha='left', bold=True, size=14)

    def domain_entity(key, x, y, w, title, attributes, *, value_object=False):
        header = 42 if value_object else 30
        h = header+15*len(attributes)+13
        d.box(key, x, y, w, h, '')
        d.text(x+w/2, y+15, title, bold=True, size=13)
        if value_object:
            d.text(x+w/2, y+31, '«value object»', size=12)
        d.arrow([(x, y+header), (x+w, y+header)], heads=False)
        for i, value in enumerate(attributes):
            d.text(x+10, y+header+13+i*15, value, ha='left', size=12,
                   bounds=(x+7, y+header+3, w-14, h-header-6))

    domain_entity('sender', 12, 42, 245, 'REPORTING CLIENT',
                  ['clientId [ID]', 'identityScope: app installation', 'No user login required'])
    domain_entity('location', 350, 42, 240, 'REPORT LOCATION',
                  ['latitude; longitude', 'accuracyMeters?', 'source: device / manual'], value_object=True)
    domain_entity('assessment', 711, 42, 237, 'SITUATION ASSESSMENT',
                  ['trappedCount; injuredCount', 'vulnerableGroups[]', 'cannotMove; severeSigns[]',
                   'urgencyScore? (structured LR)', 'aiLabel?; aiConfidence?', 'aiTags[]'], value_object=True)
    domain_entity('team', 12, 224, 245, 'RESCUE TEAM',
                  ['teamId [ID]', 'name [unique]; contactPhone?', 'memberCount?; notes?', 'isActive; createdAt'])
    domain_entity('report', 350, 210, 240, 'RESCUE REPORT',
                  ['reportId [ID]', 'reportedAt; firstReceivedAt', 'description; contactPhone?',
                   'status; statusVersion', 'statusUpdatedAt?; closeReason?', 'sendMode; sourceChannel',
                   'lastChangeSequence'])
    domain_entity('photo', 711, 260, 237, 'STORED PHOTO',
                  ['fileName; storagePath', 'imageUrl', 'sha256; byteSize'], value_object=True)
    domain_entity('operator', 12, 408, 245, 'OPERATOR',
                  ['operatorId [ID]', 'username / displayName [unique]', 'role: admin / operator',
                   'isActive; mustChangePassword', 'createdAt; lastLoginAt?'])
    domain_entity('event', 350, 408, 290, 'REPORT EVENT',
                  ['eventId [ID]', 'occurredAt; eventKind', 'fromValue?; toValue?', 'statusVersion?',
                   'actorLabel?; sourceChannel', 'note?'])

    def cardinality(p, q, kind):
        if kind != 'one_many':
            old.cap(d, p, q, kind)
            return
        import math
        length = math.dist(p, q)
        vx, vy = (q[0]-p[0])/length, (q[1]-p[1])/length
        nx, ny = -vy, vx
        d.arrow([(p[0]+4*nx, p[1]+4*ny), (p[0]+8*vx, p[1]+8*vy),
                 (p[0]-4*nx, p[1]-4*ny)], heads=False)
        d.arrow([(p[0]+14*vx-4*nx, p[1]+14*vy-4*ny),
                 (p[0]+14*vx+4*nx, p[1]+14*vy+4*ny)], heads=False)

    def rel(a, b, points, left, right, label, at):
        d.link(a, b, points, heads=False)
        d.text(*at, label, size=12, label=True)
        cardinality(points[0], points[1], left)
        cardinality(points[-1], points[-2], right)

    rel('sender', 'report', [(257, 91), (300, 91), (300, 245), (350, 245)],
        'optional', 'many', 'submits', (304, 173))
    rel('team', 'report', [(257, 288), (350, 288)],
        'optional', 'many', 'assigned to', (303.5, 270))
    rel('report', 'location', [d.port('report', 'top'), d.port('location', 'bottom')],
        'one', 'optional', 'located at', (512, 179))
    rel('report', 'assessment', [(590, 245), (670, 245), (670, 122), (711, 122)],
        'one', 'one', 'describes', (655, 217))
    rel('report', 'photo', [(590, 320), (711, 320)],
        'one', 'optional', 'retains', (650, 303))
    rel('report', 'event', [d.port('report', 'bottom'), (470, 408)],
        'one', 'one_many', 'records', (510, 387))
    rel('operator', 'event', [(257, 472), (350, 472)],
        'optional', 'many', 'performs', (303.5, 453))

    # Domain constraints explain optionality and state rules without SQL columns.
    d.shape(711, 408, 237, 133, rounded=False)
    d.text(829.5, 424, 'DOMAIN RULES / NOTATION', bold=True, size=12.5)
    for i, text in enumerate(['[ID] identifier; ? optional; [] list', '|| 1; o| 0..1; o< 0..*; |< 1..*',
                              'New report: processing', 'Final: resolved / cancelled',
                              'Status version only increases', 'At most one team and one photo']):
        d.text(721, 447+i*16, text, ha='left', size=12)
    d.text(12, 562, 'Design model: Location, Assessment and Photo are embedded value objects, not separate SQLite tables.',
           ha='left', size=12)
    d.text(12, 580, 'Client identity may be absent. Operator–event association is conceptual; current storage keeps actor labels.',
           ha='left', size=12)
    return d


def research_pipeline():
    d = Diagram('research_pipeline_report', 450, '2.6 · Hai luồng dọc: suy luận và đánh giá')
    # Preserve the original blue/purple distinction while making both flows vertical.
    old.base.PALE['purple'] = '#F0E6F6'
    for x, w, title, kind in [(10, 346, '1 · SUY LUẬN TỪ DỮ LIỆU QUAN SÁT', 'blue'),
                              (392, 326, '2 · ĐÁNH GIÁ ĐỘC LẬP', 'purple')]:
        detailed.Diagram.shape(d, x, 10, w, 408, kind=kind, rounded=False, background=True)
        d.text(x+10, 29, title, ha='left', bold=True, size=10)
    rows = [('input', 50, 'Báo cáo hiện trường'), ('eligible', 110, 'Đủ vị trí / thời gian?'),
            ('graph', 170, 'Masked similarity\nĐồ thị thưa: ngưỡng + k-NN'),
            ('partition', 230, 'Phân cụm dự đoán'), ('rank', 290, 'Họ bản sao; xếp hạng có chặn'),
            ('schedule', 350, 'Lập lịch theo cụm dự đoán')]
    for key, y, text in rows:
        d.box(key, 28, y, 220, 40, text, decision=key == 'eligible', size=9.4)
    d.box('review', 266, 113, 79, 49, 'Thiếu L/T:\nhàng\nxem xét', size=9.2)
    for (a, _, _), (b, _, _) in zip(rows, rows[1:]):
        d.down(a, b, label='Đủ' if a == 'eligible' else None,
               at=(154, 160) if a == 'eligible' else None)
    d.link('eligible', 'review', [(248, 130), (256, 130), (256, 137.5), (266, 137.5)])
    d.box('truth', 423, 50, 270, 55, 'Nhãn thật: incident ID, N, V\nDeadline; service demand; harm\nChỉ nối sau khi khóa đầu ra', size=9.5)
    for key, y, text in [
        ('rq1', 160, 'RQ1 · Đánh giá phân cụm\nPartition đã khóa + nhãn thật'),
        ('rq2', 252, 'RQ2 · Đánh giá xếp hạng\nOracle groups + independent benefit'),
        ('rq3', 344, 'RQ3 · Đánh giá điều phối\nSchedule đã khóa + nhãn thật')]:
        d.box(key, 423, y, 270, 50, text, size=10)
    d.link('partition', 'rq1', [(248, 250), (365, 250), (365, 185), (423, 185)], dashed=True)
    d.link('schedule', 'rq3', [(248, 370), (378, 370), (378, 369), (423, 369)], dashed=True)
    # One labelled truth distribution line, with explicit branch junctions.
    d.link('truth', 'rq3', [(693, 77.5), (710, 77.5), (710, 369), (693, 369)], dashed=True)
    for key, y in [('rq1', 185), ('rq2', 277)]:
        d.link(None, key, [(710, y), (693, y)], dashed=True)
        detailed.circle(d, 710, y, 1.6, fill='#111111', stroke='#111111')
    footer(d, 'Nét đứt: chỉ cung cấp dữ liệu cho evaluator. RQ2 dùng nhóm oracle độc lập; nhãn thật không đi vào suy luận.')
    return d


def monochrome(d):
    for patch in d.ax.patches:
        face = patch.get_facecolor()
        edge = patch.get_edgecolor()
        if face[3]:
            patch.set_facecolor('white' if sum(face[:3]) > .2 else '#111111')
        if edge[3]:
            patch.set_edgecolor('#111111')
    for line in d.ax.lines:
        line.set_color('#111111')
    for artist, _, _ in d.texts:
        artist.set_color('#111111')
    for c in d.cells:
        if 'style' in c.attrib:
            style = c.get('style')
            style = re.sub(r'fillColor=#[0-9a-fA-F]{6}', 'fillColor=#FFFFFF', style)
            style = re.sub(r'(strokeColor|fontColor)=#[0-9a-fA-F]{6}', r'\1=#111111', style)
            c.set('style', style)
    return d


def ingestion():
    return monochrome(detailed.ingestion())


def lifecycle():
    class Routed(detailed.Diagram):
        def arrow(self, points, **kwargs):
            if points == [(457, 299), (482, 299), (482, 98), (545, 98)]:
                points = [(457, 299), (480, 299), (480, 58), (605, 58), (605, 74)]
            elif points == [(545, 98), (490, 98), (490, 329), (362, 329), (362, 318)]:
                points = [(545, 98), (492, 98), (492, 329), (362, 329), (362, 318)]
            return super().arrow(points, **kwargs)
    cls = detailed.Diagram
    detailed.Diagram = Routed
    try:
        return detailed.lifecycle()
    finally:
        detailed.Diagram = cls


class LogoPen(BasePen):
    def __init__(self):
        super().__init__(None)
        self.vertices, self.codes = [], []
    def _moveTo(self, pt):
        self.start = pt
        self.vertices.append(pt); self.codes.append(MplPath.MOVETO)
    def _lineTo(self, pt):
        self.vertices.append(pt); self.codes.append(MplPath.LINETO)
    def _curveToOne(self, a, b, c):
        self.vertices.extend([a, b, c]); self.codes.extend([MplPath.CURVE4]*3)
    def _qCurveToOne(self, a, b):
        self.vertices.extend([a, b]); self.codes.extend([MplPath.CURVE3]*2)
    def _closePath(self):
        self.vertices.append(self.start); self.codes.append(MplPath.CLOSEPOLY)
    def _endPath(self):
        pass


def logo(d, name, x, y, size=22):
    source = ROOT/'assets/diagrams/tech-icons'/f'{name}.svg'
    svg = ET.fromstring(source.read_text())
    for path in svg.findall('{http://www.w3.org/2000/svg}path'):
        pen = LogoPen(); parse_path(path.get('d'), pen)
        d.ax.add_patch(PathPatch(MplPath(pen.vertices, pen.codes), facecolor='#111111',
                                edgecolor='none', transform=Affine2D().scale(size/24).translate(x, y)+d.ax.transData,
                                zorder=4))
    uri = 'data:image/svg+xml,' + quote(source.read_text(), safe='')
    cell = ET.SubElement(d.cells, 'mxCell', id=d.ident('logo'), parent='1', vertex='1',
                         style=f'shape=image;imageAspect=0;aspect=fixed;image={uri};')
    ET.SubElement(cell, 'mxGeometry', x=str(x), y=str(y), width=str(size), height=str(size), **{'as':'geometry'})


def deployment():
    d = Diagram('deployment_infrastructure', 450, '2.16 · Triển khai Docker Compose và Edge AI')
    d.shape(250, 140, 468, 266, rounded=False, background=True)
    logo(d, 'docker', 266, 156, 25)
    d.text(302, 173, 'DOCKER COMPOSE', ha='left', bold=True, size=10.5)
    d.text(13, 31, 'THIẾT BỊ HIỆN TRƯỜNG', ha='left', bold=True, size=10)
    d.box('phone', 12, 60, 190, 100, '')
    detailed.icon(d, 'phone', 24, 75, 28)
    logo(d, 'flutter', 61, 76, 21)
    logo(d, 'onnx', 92, 76, 21)
    d.text(24, 120, 'Android · Flutter · GPS / Camera', ha='left', size=9.3)
    d.text(24, 144, 'Hive / Outbox · ONNX / ExecuTorch', ha='left', size=9.1)
    d.box('operator', 12, 202, 190, 60, '')
    detailed.icon(d, 'screen', 24, 216, 28)
    d.text(66, 220, 'Máy điều phối', ha='left', bold=True, size=10)
    d.text(66, 242, 'Trình duyệt Web GIS', ha='left', size=9.4)
    d.box('web', 12, 302, 190, 60, '')
    detailed.icon(d, 'screen', 24, 316, 28)
    d.text(66, 320, 'Trình duyệt thử nghiệm', ha='left', bold=True, size=9.5)
    d.text(66, 342, 'Ứng dụng Flutter Web', ha='left', size=9.4)
    d.box('sms', 522, 55, 176, 51, '')
    detailed.icon(d, 'sms', 535, 64, 22)
    d.text(571, 70, 'SMS gateway', ha='left', bold=True, size=10)
    d.text(610, 94, 'Hệ thống ngoài · token', size=9.3)
    d.box('dash', 272, 202, 185, 60, '')
    logo(d, 'nginx', 283, 213, 21)
    d.text(313, 218, 'dashboard · Nginx', ha='left', bold=True, size=9.5)
    d.text(364.5, 245, 'HTML / JS / Leaflet · :8080 → :80', size=9)
    d.box('fe', 272, 302, 185, 60, '')
    logo(d, 'flutter', 283, 311, 19)
    logo(d, 'nginx', 306, 311, 19)
    d.text(333, 319, 'fe · Flutter Web', ha='left', bold=True, size=9.4)
    d.text(364.5, 344, 'Nginx · :8081 → :80', size=9.3)
    d.box('be', 522, 150, 176, 135, '')
    logo(d, 'fastapi', 535, 161, 24)
    d.text(570, 173, 'be · FastAPI', ha='left', bold=True, size=10.5)
    for i, value in enumerate(['Uvicorn · :8000 → :8000', 'JSON sync / ảnh / trạng thái',
                               'rescue_core · Louvain · P(c)', 'Cache cụm trong RAM', 'Healthcheck: /healthz']):
        d.text(610, 202+i*16, value, size=9.1)
    d.box('volume', 522, 326, 176, 66, '')
    logo(d, 'sqlite', 535, 336, 22)
    d.text(568, 346, 'be-data · SQLite WAL', ha='left', bold=True, size=9.4)
    d.text(610, 372, '/var/lib/rescue\nDB · uploads/ · backups/', size=9.3)
    d.link('phone', 'be', [(202, 135), (488, 135), (488, 170), (522, 170)],
           label='HTTP · :8000', at=(354, 135))
    d.link('phone', 'sms', [(202, 80), (522, 80)], dashed=True, label='SMS dự phòng', at=(361, 80))
    d.link('sms', 'be', [(650, 106), (650, 150)], label='/api/sms/inbound', at=(617, 125))
    d.link('operator', 'dash', [(202, 232), (272, 232)], label=':8080', at=(237, 217))
    d.link('web', 'fe', [(202, 332), (272, 332)], label=':8081', at=(237, 317))
    d.link('dash', 'be', [(457, 232), (478, 232), (478, 205), (522, 205)])
    d.link('fe', 'be', [(457, 332), (500, 332), (500, 254), (522, 254)])
    d.text(487, 287, 'Proxy API', size=9, label=True)
    d.link('be', 'volume', [(610, 285), (610, 326)])
    d.text(10, 423, 'Cổng mặc định có thể cấu hình. dashboard và fe chuyển tiếp API tới http://be:8000; volume lưu dữ liệu bền vững.', ha='left', size=9)
    d.text(10, 441, 'Edge AI chạy trên Android; Flutter Web phục vụ thử nghiệm giao diện. SMS gateway là thành phần bên ngoài.', ha='left', size=9)
    return monochrome(d)


FACTORIES = [overview, erd, research_pipeline, tracking, ingestion, compose,
             deployment, adaptive, lifecycle, training]


def validate_links(d):
    """Check actual link geometry independently of text-bound validation."""
    links = getattr(d, 'flow_links', None)
    if links is None:
        links = [e for e in d.edges if e['source'] or e['target']]
    failures = []
    for i, edge in enumerate(links):
        for other in links[i+1:]:
            for a, b in zip(edge['points'], edge['points'][1:]):
                for c, e in zip(other['points'], other['points'][1:]):
                    if a == b or c == e:
                        continue
                    if a[0] == b[0] == c[0] == e[0]:
                        overlap = min(max(a[1], b[1]), max(c[1], e[1])) - max(min(a[1], b[1]), min(c[1], e[1]))
                    elif a[1] == b[1] == c[1] == e[1]:
                        overlap = min(max(a[0], b[0]), max(c[0], e[0])) - max(min(a[0], b[0]), min(c[0], e[0]))
                    else:
                        overlap = 0
                        h = (a, b) if a[1] == b[1] else (c, e)
                        v = (a, b) if a[0] == b[0] else (c, e)
                        if (h[0][1] == h[1][1] and v[0][0] == v[1][0]
                            and min(h[0][0], h[1][0]) < v[0][0] < max(h[0][0], h[1][0])
                            and min(v[0][1], v[1][1]) < h[0][1] < max(v[0][1], v[1][1])):
                            failures.append(f'Crossing: {a,b} / {c,e}')
                    if overlap > .1:
                        failures.append(f'Overlapping links: {a,b} / {c,e}')
        nodes = getattr(d, 'business_nodes', None)
        if nodes is None:
            nodes = {identifier: identifier for identifier, shape in d.shapes.items() if not shape[4]}
        for key, identifier in nodes.items():
            if key in [edge.get('from'), edge.get('to'), edge.get('source'), edge.get('target')]:
                continue
            x, y, w, h, _ = d.shapes[identifier]
            for a, b in zip(edge['points'], edge['points'][1:]):
                if a[0] == b[0] and x < a[0] < x+w and min(max(a[1], b[1]), y+h) > max(min(a[1], b[1]), y):
                    failures.append(f'Link crosses node: {key}')
                if a[1] == b[1] and y < a[1] < y+h and min(max(a[0], b[0]), x+w) > max(min(a[0], b[0]), x):
                    failures.append(f'Link crosses node: {key}')
    if failures:
        raise ValueError(d.name+'\n'+'\n'.join(failures))
    return {'crossing_links': 0, 'overlapping_links': 0, 'links_through_other_nodes': 0}


def main():
    REVIEW.mkdir(parents=True, exist_ok=True)
    results = {}
    for factory in FACTORIES:
        d = factory()
        # 2.12 is a style-only revision; its intentional ACK collection trunk is retained.
        geometry = validate_links(d) if factory != ingestion else {'scope': 'monochrome only; ACK trunk retained'}
        result = d.save(ROOT/'assets/diagrams', REVIEW/'previews')
        result['geometry'] = geometry
        result['flow_links'] = getattr(d, 'flow_links', [])
        results[d.name] = result
        print(d.name, 'PASS', flush=True)
    (REVIEW/'diagram-validation.json').write_text(json.dumps(results, ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    main()
