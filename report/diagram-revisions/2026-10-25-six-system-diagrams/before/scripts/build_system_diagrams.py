#!/usr/bin/env python3
"""Rebuild four report diagrams as vector PDF, SVG and editable Draw.io.

Coordinates and font sizes are PDF points; the 160 mm canvas is inserted at
the report's actual text width. No product code or application DB is imported.
Run with report/build/visual-env/bin/python (matplotlib).
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
from matplotlib.path import Path as MplPath

ROOT = Path(__file__).resolve().parents[1]
WIDTH = 160 / 25.4 * 72
FONT = "DejaVu Sans"
INK = "#203B50"
LINE = "#587489"
PALE = {"blue": "#EDF4FA", "teal": "#EAF5F2", "amber": "#FFF5E5",
        "gray": "#F4F5F6", "red": "#FBEFEB", "white": "#FFFFFF"}
matplotlib.rcParams.update({"font.family": FONT, "font.size": 9.5,
                           "pdf.fonttype": 42, "svg.fonttype": "none",
                           "svg.hashsalt": "nckh2-system-diagrams"})


class Diagram:
    def __init__(self, name, height, title):
        self.name, self.height, self.title = name, height, title
        self.fig = plt.figure(figsize=(WIDTH / 72, height / 72))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set(xlim=(0, WIDTH), ylim=(height, 0))
        self.ax.axis("off")
        self.texts, self.shapes, self.edges = [], {}, []
        self.serial = 0
        self.mx = ET.Element("mxfile", host="app.diagrams.net", version="26.0.0")
        diagram = ET.SubElement(self.mx, "diagram", id=name, name=title)
        model = ET.SubElement(diagram, "mxGraphModel", page="1", pageScale="1",
                              pageWidth=str(WIDTH), pageHeight=str(height),
                              math="0", grid="0", shadow="0")
        self.cells = ET.SubElement(model, "root")
        ET.SubElement(self.cells, "mxCell", id="0")
        ET.SubElement(self.cells, "mxCell", id="1", parent="0")

    def ident(self, prefix):
        self.serial += 1
        return f"{prefix}{self.serial}"

    def text(self, x, y, value, *, size=9.5, bold=False, ha="center", color=INK,
             bounds=None, label=False):
        if size < 9:
            raise ValueError("Diagram text must be at least 9 pt at print size")
        artist = self.ax.text(x, y, value, fontsize=size, fontweight="bold" if bold else "normal",
                              ha=ha, va="center", linespacing=1.3, color=color, zorder=6,
                              bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.2}
                              if label else None)
        # Separate editable text objects keep font and line breaks explicit.
        lines = value.splitlines() or [""]
        width = max(18, max(len(s) for s in lines) * size * .64)
        height = max(size * 1.5, len(lines) * size * 1.3 + 4)
        left = x - width / 2 if ha == "center" else x
        cell = ET.SubElement(self.cells, "mxCell", id=self.ident("text"), parent="1", vertex="1",
                             value="<div>" + "<br>".join(html.escape(s) for s in lines) + "</div>",
                             style=f"text;html=1;whiteSpace=wrap;align={ha if ha != 'left' else 'left'};"
                                   f"verticalAlign=middle;fontFamily={FONT};fontSize={size};"
                                   f"fontStyle={1 if bold else 0};fontColor={color};"
                                   "spacing=0;overflow=visible;")
        geometry = ET.SubElement(cell, "mxGeometry", x=str(left), y=str(y-height/2),
                                 width=str(width), height=str(height), **{"as": "geometry"})
        self.texts.append((artist, bounds, geometry))
        return artist

    def shape(self, x, y, w, h, *, kind="white", rounded=True, dashed=False,
              diamond=False, line=LINE, identifier=None, background=False):
        identifier = identifier or self.ident("node")
        if diamond:
            patch = Polygon([(x+w/2, y), (x+w, y+h/2), (x+w/2, y+h), (x, y+h/2)],
                            closed=True, facecolor=PALE[kind], edgecolor=line, lw=.9)
        elif rounded:
            patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=4",
                                  facecolor=PALE[kind], edgecolor=line, lw=.9)
        else:
            patch = Rectangle((x, y), w, h, facecolor=PALE[kind], edgecolor=line, lw=.9)
        if dashed:
            patch.set_linestyle((0, (4, 3)))
        patch.set_zorder(0 if background else 2)
        self.ax.add_patch(patch)
        style = ("rhombus;" if diamond else f"rounded={int(rounded)};")
        cell = ET.SubElement(self.cells, "mxCell", id=identifier, parent="1", vertex="1",
                             style=style + f"fillColor={PALE[kind]};strokeColor={line};"
                                   f"strokeWidth=0.9;dashed={int(dashed)};")
        ET.SubElement(cell, "mxGeometry", x=str(x), y=str(y), width=str(w), height=str(h),
                      **{"as": "geometry"})
        self.shapes[identifier] = (x, y, w, h, background)
        return identifier

    def node(self, x, y, w, h, value, **kwargs):
        shape = self.shape(x, y, w, h, **kwargs)
        self.text(x+w/2, y+h/2, value, bounds=(x+7, y+4, w-14, h-8))
        return shape

    def card(self, x, y, w, h, title, lines, *, kind="blue"):
        shape = self.shape(x, y, w, h, kind=kind)
        self.text(x+w/2, y+15, title, bold=True, size=10,
                  bounds=(x+7, y+4, w-14, 22))
        self.arrow([(x+9,y+28),(x+w-9,y+28)],heads=False)
        for i, value in enumerate(lines):
            self.text(x+10, y+41+i*14, value, ha="left",
                      bounds=(x+8, y+30, w-16, h-34))
        return shape

    def arrow(self, points, *, label=None, at=None, dashed=False, double=False,
              source=None, target=None, heads=True):
        path = MplPath(points, [MplPath.MOVETO] + [MplPath.LINETO]*(len(points)-1))
        arrow = FancyArrowPatch(path=path, arrowstyle="<->" if double else ("->" if heads else "-"),
                                mutation_scale=9, linewidth=.9, color=LINE,
                                linestyle=(0, (3, 2)) if dashed else "-", zorder=3)
        self.ax.add_patch(arrow)
        if label:
            self.text(*at, label, size=9, label=True)
        self.edges.append({"points": points, "source": source, "target": target,
                           "dashed": dashed})
        attrs = {"id": self.ident("edge"), "parent": "1", "edge": "1",
                 "style": f"html=1;rounded=0;strokeColor={LINE};strokeWidth=0.9;"
                          f"dashed={int(dashed)};endArrow={'classic' if heads else 'none'};"
                          f"startArrow={'classic' if double else 'none'};"}
        for key, value in [("source", source), ("target", target)]:
            if value:
                attrs[key] = value
                x, y, w, h, _ = self.shapes[value]
                px, py = points[0] if key == "source" else points[-1]
                prefix = "exit" if key == "source" else "entry"
                attrs["style"] += f"{prefix}X={(px-x)/w};{prefix}Y={(py-y)/h};"
        cell = ET.SubElement(self.cells, "mxCell", **attrs)
        geometry = ET.SubElement(cell, "mxGeometry", relative="1", **{"as": "geometry"})
        for key, point in [("sourcePoint", points[0]), ("targetPoint", points[-1])]:
            ET.SubElement(geometry, "mxPoint", x=str(point[0]), y=str(point[1]), **{"as": key})
        if len(points) > 2:
            array = ET.SubElement(geometry, "Array", **{"as": "points"})
            for x, y in points[1:-1]:
                ET.SubElement(array, "mxPoint", x=str(x), y=str(y))

    def table(self, x, y, w, title, rows, *, kind="blue"):
        h = 28 + 15*len(rows)
        node = self.shape(x, y, w, h, kind=kind, rounded=False)
        self.text(x+w/2, y+13, title, size=10, bold=True,
                  bounds=(x+6, y+3, w-12, 21))
        self.arrow([(x,y+26),(x+w,y+26)],heads=False)
        for i, row in enumerate(rows):
            self.text(x+9, y+36+i*15, row, ha="left", size=9.2,
                      bounds=(x+6, y+28, w-12, h-30))
        return node, h

    def relation(self, points, *, start="one", finish="many", source=None, target=None):
        self.arrow(points, dashed=True, heads=False, source=source, target=target)
        # Crow's-foot caps; a circle denotes zero and a bar denotes one.
        for endpoint, neighbor, cardinality in [(points[0], points[1], start),
                                                (points[-1], points[-2], finish)]:
            import numpy as np
            p, q = np.array(endpoint, float), np.array(neighbor, float)
            inward = (q-p) / np.linalg.norm(q-p)
            normal = np.array([-inward[1], inward[0]])
            if cardinality in ("many", "optionalone"):
                c = p+inward*13
                self.ax.add_patch(plt.Circle(c, 2.4, facecolor="white", edgecolor=LINE, lw=.8, zorder=4))
            if cardinality == "many":
                center = p+inward*8
                for tip in [p+normal*4, p-normal*4]:
                    self.ax.plot([center[0], tip[0]], [center[1], tip[1]], color=LINE, lw=.9, zorder=4)
            else:
                c = p+inward*5
                self.ax.plot([c[0]-normal[0]*4, c[0]+normal[0]*4],
                             [c[1]-normal[1]*4, c[1]+normal[1]*4], color=LINE, lw=.9, zorder=4)
        # The editable source uses Draw.io's equivalent cardinality markers.
        cell = list(self.cells)[-1]
        caps = {"one": "ERone", "many": "ERzeroToMany", "optionalone": "ERzeroToOne"}
        cell.set("style", cell.get("style") + f"startArrow={caps[start]};endArrow={caps[finish]};")

    def save(self, output, preview):
        self.fig.canvas.draw()
        renderer = self.fig.canvas.get_renderer()
        failures = []
        for artist, allowed, geometry in self.texts:
            box = artist.get_window_extent(renderer).transformed(self.ax.transData.inverted())
            xmin, xmax = min(box.x0, box.x1), max(box.x0, box.x1)
            ymin, ymax = min(box.y0, box.y1), max(box.y0, box.y1)
            geometry.set("x", str(xmin-1))
            geometry.set("y", str(ymin-1))
            geometry.set("width", str(xmax-xmin+2))
            geometry.set("height", str(ymax-ymin+2))
            if xmin < -.5 or xmax > WIDTH+.5 or ymin < -.5 or ymax > self.height+.5:
                failures.append(f"Outside canvas: {artist.get_text()!r}")
            if allowed:
                x, y, w, h = allowed
                if xmin < x-.5 or xmax > x+w+.5 or ymin < y-.5 or ymax > y+h+.5:
                    failures.append(f"Text overflows box: {artist.get_text()!r}")
        if failures:
            raise ValueError(self.name + "\n" + "\n".join(failures))
        output.mkdir(parents=True, exist_ok=True)
        preview.mkdir(parents=True, exist_ok=True)
        # Write editable source first; PDF is newer so the ordinary build keeps it.
        ET.indent(self.mx)
        ET.ElementTree(self.mx).write(output / f"{self.name}.drawio", encoding="utf-8", xml_declaration=True)
        svg = output / f"{self.name}.svg"
        self.fig.savefig(svg, facecolor="white", metadata={"Date": None})
        svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines())+"\n")
        self.fig.savefig(output / f"{self.name}.pdf", facecolor="white", metadata={
            "Title": self.title, "Author": "NCKH THS2026-68", "CreationDate": None,
            "ModDate": None, "Subject": "Source-backed system diagram; 160 mm print width"})
        self.fig.savefig(preview / f"{self.name}.png", dpi=160, facecolor="white")
        plt.close(self.fig)
        return {"title": self.title, "width_pt": WIDTH, "height_pt": self.height,
                "minimum_font_pt": 9, "text_count": len(self.texts), "text_bounds": "PASS",
                "artifacts": {ext: hashlib.sha256((output/f"{self.name}.{ext}").read_bytes()).hexdigest()
                              for ext in ["pdf", "svg", "drawio"]}}


def architecture():
    d = Diagram("functional_architecture", 470, "Hình 2.1 — Kiến trúc chức năng hệ thống")
    app = d.card(10, 20, 195, 108, "Ứng dụng Flutter", [
        "Người dân / đội cứu hộ", "SOS; báo cáo, ảnh tùy chọn", "AI tại thiết bị; lưu Hive",
        "Outbox; theo dõi trạng thái"])
    web = d.card(249, 20, 195, 108, "Bàn điều phối Web GIS", [
        "Điều phối viên đăng nhập", "Xem bản đồ, cụm, hàng xem xét", "Xác minh và giao đội cứu hộ",
        "Cập nhật trạng thái; nhật ký"], kind="amber")
    sms = d.node(10, 206, 102, 66, "SMS gateway\nNhận SMS SOS\nChuyển webhook", kind="gray", dashed=True)
    api = d.card(157, 206, 287, 66, "API và dịch vụ backend · FastAPI", [
        "Tiếp nhận, kiểm tra và gộp báo cáo", "API điều phối, tra cứu và xác thực"])
    db = d.card(10, 350, 195, 90, "Lưu trữ bền vững", [
        "SQLite · chế độ WAL", "Báo cáo, đội, đồng bộ, nhật ký", "Tệp ảnh trong uploads/"], kind="teal")
    core = d.card(249, 350, 195, 90, "ClusterService + rescue_core", [
        "Louvain; điểm ưu tiên P(c)", "Hàng xem xét thiếu vị trí/giờ", "Cache kết quả trong RAM"], kind="teal")
    d.arrow([(190,128),(190,206)], double=True, source=app, target=api,
            label="HTTP: metadata, ảnh\nvà trạng thái", at=(253,165))
    d.arrow([(350,128),(350,206)], double=True, source=web, target=api,
            label="API điều phối\nJSON / ETag", at=(397,165))
    d.arrow([(61,128),(61,206)], dashed=True, source=app, target=sms,
            label="SMS\ndự phòng", at=(38,165))
    d.arrow([(112,239),(157,239)], source=sms, target=api,
            label="Webhook", at=(134,224))
    d.arrow([(197,272),(197,312),(107,312),(107,350)], double=True, source=api, target=db,
            label="Đọc / ghi", at=(150,300))
    d.arrow([(346,272),(346,350)], double=True, source=api, target=core,
            label="Lấy cụm và\nhàng xem xét", at=(395,310))
    d.arrow([(249,395),(205,395)], source=core, target=db,
            label="Đọc", at=(227,381))
    d.text(10, 457, "Nét đứt: tuyến SMS dự phòng. Lõi phân cụm chạy trong backend.", ha="left", size=9)
    return d


def overview():
    d = Diagram("flowchart", 630, "Hình 2.2 — Quy trình cứu hộ và phản hồi")
    for y,h,title,kind in [(10,164,"1 · ỨNG DỤNG DI ĐỘNG","blue"),
                            (190,122,"2 · BACKEND","teal"),
                            (328,145,"3 · ĐIỀU PHỐI VÀ THỰC ĐỊA","amber"),
                            (489,105,"4 · PHẢN HỒI TRẠNG THÁI","blue")]:
        d.shape(10,y,434,h,kind=kind,background=True)
        d.text(21,y+14,title,bold=True,ha="left",size=9.5)
    sos=d.node(21,48,173,44,"SOS một chạm\nKhông bắt buộc ảnh / AI")
    report=d.node(260,48,173,44,"Báo cáo chi tiết\nẢnh / AI là tùy chọn")
    queue=d.node(126,117,202,44,"Lưu cục bộ + Outbox\nChọn cách gửi; giữ ID khi retry")
    d.arrow([(107,92),(107,104),(186,104),(186,117)],source=sos,target=queue)
    d.arrow([(346,92),(346,104),(268,104),(268,117)],source=report,target=queue)
    ingest=d.node(21,224,173,53,"Tiếp nhận HTTP / SMS\nKiểm tra theo từng kênh\nLưu mới hoặc gộp báo cáo")
    clusters=d.node(260,224,173,53,"Đủ vị trí + thời gian:\nphân cụm, tính P(c)\nThiếu: hàng xem xét")
    d.arrow([(227,161),(227,213),(107,213),(107,224)],source=queue,target=ingest)
    d.text(296,183,"HTTP / SMS",size=9,label=True)
    d.arrow([(194,250),(260,250)],source=ingest,target=clusters,
            label="Dữ liệu",at=(227,237))
    d.text(21,294,"ACK metadata ≠ ảnh đã gửi xong",ha="left",size=9)
    verify=d.node(260,360,173,44,"Xem cụm / hàng xem xét\nXác minh và chọn xử lý")
    dispatch=d.node(21,360,173,44,"Giao đội cứu hộ\nCập nhật trạng thái riêng")
    d.arrow([(346,277),(346,360)],source=clusters,target=verify)
    d.arrow([(260,382),(194,382)],source=verify,target=dispatch,
            label="Quyết định",at=(227,367))
    field=d.node(21,428,412,31,"Tác nghiệp thực địa; điều phối viên ghi nhận kết quả",kind="gray",dashed=True)
    d.arrow([(107,404),(107,428)],source=dispatch,target=field)
    server=d.node(260,521,173,57,"Ghi trạng thái + nhật ký\nCa chưa kết thúc: tiếp tục\nCa kết thúc: giữ kết quả")
    app=d.node(21,521,173,57,"Ứng dụng tra cứu trạng thái\nprocessing / dispatched\nresolved / cancelled")
    d.arrow([(346,459),(346,521)],source=field,target=server)
    d.arrow([(260,549),(194,549)],double=True,source=server,target=app,
            label="Tra cứu",at=(227,534))
    d.text(10,609,"HTTP chưa ACK: giữ Outbox để thử lại. SMS chỉ được thử khi đủ điều kiện.\nTác nghiệp thực địa nằm ngoài phần mềm; ACK không xác nhận ca đã được cứu.",
           ha="left",size=9)
    return d


def erd():
    d=Diagram("database_erd",609,"Hình 2.5 — Các bảng và liên hệ logic chính của backend")
    reports,rh=d.table(10,20,210,"reports",[
        "id TEXT  [PK]", "assigned_team_id INTEGER", "status TEXT; status_version INTEGER",
        "lat, lng REAL", "raw_payload TEXT", "image_url TEXT"])
    events,eh=d.table(244,20,200,"report_events",[
        "id INTEGER  [PK]", "report_id TEXT", "kind TEXT; actor TEXT",
        "from_value, to_value TEXT", "created_at TEXT"])
    d.relation([(220,75),(244,75)],source=reports,target=events)
    teams,th=d.table(10,188,210,"teams",[
        "id INTEGER  [PK]", "name TEXT  [UQ]", "active INTEGER"],kind="teal")
    d.relation([(115,20+rh),(115,188)],start="many",finish="optionalone",source=reports,target=teams)
    d.text(158,163,"giao đội",size=9,label=True)
    d.table(244,188,200,"messages_dedup",[
        "message_id TEXT  [PK]", "client_id TEXT", "sequence_number INTEGER",
        "payload_hash TEXT", "status TEXT; result_data TEXT",
        "UQ (client_id, sequence_number)"],kind="gray")
    operators,oh=d.table(10,359,210,"operators",[
        "id INTEGER  [PK]", "username TEXT  [UQ, NOCASE]",
        "display_name TEXT  [UQ, NOCASE]", "role TEXT"],kind="amber")
    sessions,sh=d.table(244,359,200,"sessions",[
        "token_hash TEXT  [PK]", "operator_id INTEGER", "operator TEXT", "expires_at TEXT"],kind="amber")
    d.relation([(220,403),(244,403)],source=operators,target=sessions)
    d.table(10,501,210,"server_meta",["key TEXT  [PK]", "value TEXT"],kind="gray")
    d.text(250,510,"PK: khóa chính; UQ: duy nhất.\nNét đứt: liên hệ do mã quản lý.\nDDL chưa khai báo khóa ngoại.\nactor lưu tên, không phải FK.",
           ha="left",size=9,bounds=(246,482,198,90))
    d.text(10,581,"Chỉ liệt kê các cột chính. messages_dedup không có khóa ngoại đến reports.\nKý hiệu: | một; o| không hoặc một; o< không hoặc nhiều.",ha="left",size=9)
    return d


def ingest():
    d=Diagram("flow_05_backend_ingest_dedup",620,"Hình 2.12 — Xử lý request và message JSON sync")
    d.text(10,12,"A · REQUEST /sync/messages",ha="left",bold=True,size=10)
    req=d.node(20,33,234,42,"Kiểm tra header v1, JSON\nsố message và dung lượng request",kind="blue")
    valid=d.node(51,94,172,52,"Request\nhợp lệ?",kind="amber",diamond=True)
    request_error=d.node(285,88,155,68,"HTTP 400: version,\nJSON hoặc >50 message\nHTTP 413: >256 KiB\nDừng cả request",kind="red")
    d.arrow([(137,75),(137,94)],source=req,target=valid)
    d.arrow([(223,120),(285,120)],source=valid,target=request_error,label="Không",at=(254,107))
    d.text(285,173,"B · TỪNG MESSAGE\nACK theo message_id",ha="left",bold=True,size=9.5)
    checks=d.node(20,181,234,52,"Kiểm tra cấu trúc, hash và hạn dùng\nJCS (RFC 8785) → SHA-256; so hash\nSai payload / hash / TTL: từ chối",kind="blue")
    invalid=d.node(285,208,155,40,"rejected\nPayload / hash / TTL sai",kind="red")
    d.arrow([(137,146),(137,181)],source=valid,target=checks,label="Có",at=(151,163))
    d.arrow([(254,222),(285,222)],source=checks,target=invalid)
    identity=d.node(51,256,172,52,"ID / sequence\nđã có?",kind="amber",diamond=True)
    d.arrow([(137,233),(137,256)],source=checks,target=identity)
    reused=d.node(285,268,155,78,"Cùng ID + hash:\nduplicate + kết quả cũ\nKhác hash / tái dùng seq:\nrejected + mã lỗi",kind="amber")
    d.arrow([(223,282),(285,282)],source=identity,target=reused,label="Đã có",at=(254,270))
    business=d.node(20,332,234,76,"Thao tác mới\nKiểm tra operation và quyền\nTạo, gộp hoặc đổi trạng thái\nGhi nghiệp vụ + dedup\nCommit cùng transaction",kind="blue")
    d.arrow([(137,308),(137,332)],source=identity,target=business,label="Chưa",at=(155,320))
    rejected=d.node(285,369,155,40,"rejected\nSai nghiệp vụ / quyền",kind="red")
    d.arrow([(254,387),(285,387)],source=business,target=rejected)
    accepted=d.node(20,433,234,42,"accepted\nNghiệp vụ và dedup đã commit",kind="teal")
    d.arrow([(137,408),(137,433)],source=business,target=accepted)
    retry=d.node(285,433,155,54,"Rollback message\nretry_later\nGiữ message để thử lại",kind="red")
    d.arrow([(225,408),(225,418),(270,418),(270,460),(285,460)],source=business,target=retry)
    d.text(340,422,"Lỗi server",size=9,label=True)
    result=d.node(20,515,420,44,"Xong batch → HTTP 200 với results theo message_id\nMỗi message có accepted / duplicate / rejected / retry_later",kind="teal")
    d.arrow([(137,475),(137,515)],source=accepted,target=result)
    # ACK results converge at the batch response; this is aggregation, not control flow.
    for node,y in [(invalid,228),(reused,308),(rejected,389),(retry,460)]:
        d.arrow([(440,y),(449,y)],dashed=True,heads=False,source=node)
    d.arrow([(449,228),(449,537),(440,537)],dashed=True,target=result)
    d.text(10,587,"Hình mô tả JSON sync; multipart và SMS có luồng riêng.\nNét đứt: gom ACK. Lỗi một message không hủy các message khác.\nCùng ID và hash chỉ cho biết thao tác đã được xử lý, không xác định lý do retry.",
           ha="left",size=9)
    return d


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir",type=Path,default=ROOT/"assets/diagrams")
    parser.add_argument("--review-dir",type=Path,
                        default=ROOT/"diagram-revisions/2026-10-25-report-four-figures")
    args=parser.parse_args()
    args.review_dir.mkdir(parents=True,exist_ok=True)
    manifest={}
    combined = ET.Element("mxfile", host="app.diagrams.net", version="26.0.0")
    for builder in [architecture,overview,erd,ingest]:
        d=builder()
        manifest[d.name]=d.save(args.output_dir,args.review_dir/"previews")
        combined.append(d.mx.find("diagram"))
        print(f"{d.name}: vector PDF / SVG / editable Draw.io; text bounds PASS")
    ET.indent(combined)
    ET.ElementTree(combined).write(args.review_dir/"00-four-report-figures.drawio",
                                   encoding="utf-8",xml_declaration=True)
    sources=["products/be/main.py","products/be/storage.py","products/be/cluster_service.py",
             "products/be/sms_intake.py","products/fe/app/lib/domain/usecases/send_sos_usecase.dart",
             "products/fe/app/lib/domain/usecases/deliver_record.dart",
             "products/fe/app/lib/data/repositories/rescue_repository_impl.dart"]
    provenance={"figures":manifest,"sources_sha256":{
        p:hashlib.sha256((ROOT.parent/p).read_bytes()).hexdigest() for p in sources}}
    provenance["generator_sha256"]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (args.review_dir/"validation.json").write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+"\n")


if __name__ == "__main__":
    main()
