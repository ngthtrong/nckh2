#!/usr/bin/env python3
"""
Tạo lại usecase_mobile.drawio và usecase_mobile.pdf chuẩn 100% theo UML 2.5.
Tối ưu hóa hình học tuyệt đối:
1. Phân nhóm rõ ràng theo 2 Actor: Người dân (UC-01, 02, 06, 09M) và Đội cứu hộ (UC-07M, 08M, 11M).
2. Điểm giao duy nhất giữa 2 Actor là UC-05 (Đồng bộ dữ liệu ngoại tuyến) đặt tại trung tâm (cy = 442).
3. Triệt tiêu 100% hiện tượng đường nối cắt chéo nhau giữa 2 Actor.
4. SMS Gateway đặt ngang hàng tuyệt đối với UC-04 (y_center = 385).
5. Nhãn «extend» đặt tại x=675, y=285 (cách UC-06 hơn 120px, hoàn toàn thoáng).
6. Phông chữ Roboto / DejaVu Sans vector sans-serif trực tiếp trên thẻ text.
"""

import html
from pathlib import Path
import xml.etree.ElementTree as ET
import fitz

ROOT = Path(__file__).resolve().parents[1]
DIAGRAMS_DIR = ROOT / "assets" / "diagrams"
DRAWIO_PATH = DIAGRAMS_DIR / "usecase_mobile.drawio"
PDF_PATH = DIAGRAMS_DIR / "usecase_mobile.pdf"
PREVIEW_PATH = DIAGRAMS_DIR / "usecase_mobile_preview.png"


def build_mobile_data():
    """Tọa độ và kích thước cho từng phần tử của phân hệ Di động Biên."""
    canvas_w = 1320
    canvas_h = 790

    # System boundary
    sys = {
        "x": 220, "y": 40, "w": 850, "h": 710,
        "title": "PHÂN HỆ DI ĐỘNG BIÊN (EDGE MOBILE APP - FLUTTER)"
    }

    # Cột 1: cx = 430 (rx = 120 -> x: 310..550)
    # Cột 2: cx = 830 (rx = 122 -> x: 708..952)
    # Khoảng cách giữa 2 cột: 708 - 550 = 158px
    c1_x = 430
    c2_x = 830

    # Actors
    actors = {
        "act_citizen": {
            "name": "Người dân /\nNạn nhân",
            "x": 65, "y": 200, "w": 50, "h": 90,
            "fill": "#E3F2FD", "stroke": "#1976D2"
        },
        "act_rescuer": {
            "name": "Đội cứu hộ\nthực địa",
            "x": 65, "y": 555, "w": 50, "h": 90,
            "fill": "#E8F5E9", "stroke": "#2E7D32"
        },
        "act_sms_gw": {
            "name": "«external system»\nSMS Gateway /\nNhà mạng viễn thông",
            "x": 1115, "y": sys["y"] + 345 - 32, "w": 145, "h": 65,
            "fill": "#ECEFF1", "stroke": "#546E7A"
        }
    }

    usecases = [
        # --- CỘT 1: Nhóm Người dân (cy = 98 .. 356) ---
        {
            "id": "uc_01", "name": "UC-01: Gửi yêu cầu SOS khẩn cấp",
            "sub": "(1 chạm, tọa độ GPS & mã thiết bị)",
            "cx": c1_x, "cy": sys["y"] + 58, "rx": 120, "ry": 25,
            "fill": "#FFFFFF", "stroke": "#1E88E5", "txt": "#0D47A1"
        },
        {
            "id": "uc_02", "name": "UC-02: Tạo báo cáo cứu hộ chi tiết",
            "sub": "(số người kẹt, bị thương, nhóm yếu thế)",
            "cx": c1_x, "cy": sys["y"] + 144, "rx": 120, "ry": 25,
            "fill": "#FFFFFF", "stroke": "#1E88E5", "txt": "#0D47A1"
        },
        {
            "id": "uc_06", "name": "UC-06: Tra cứu trạng thái cứu hộ",
            "sub": "(tiến trình xử lý & phản hồi thực địa)",
            "cx": c1_x, "cy": sys["y"] + 230, "rx": 120, "ry": 25,
            "fill": "#FFFFFF", "stroke": "#1E88E5", "txt": "#0D47A1"
        },
        {
            "id": "uc_09m", "name": "UC-09M: Tra cứu cẩm nang & điểm trú",
            "sub": "(bản đồ vùng an toàn & kỹ năng sinh tồn)",
            "cx": c1_x, "cy": sys["y"] + 316, "rx": 120, "ry": 25,
            "fill": "#FFFFFF", "stroke": "#1E88E5", "txt": "#0D47A1"
        },

        # --- CỘT 1: Dùng chung tại trung tâm (cy = 402) ---
        {
            "id": "uc_05", "name": "UC-05: Đồng bộ dữ liệu ngoại tuyến",
            "sub": "(tự động gửi lại từ Outbox khi có mạng)",
            "cx": c1_x, "cy": sys["y"] + 402, "rx": 120, "ry": 25,
            "fill": "#EDE7F6", "stroke": "#5E35B1", "txt": "#311B92"
        },

        # --- CỘT 1: Nhóm Đội cứu hộ thực địa (cy = 488 .. 660) ---
        {
            "id": "uc_07m", "name": "UC-07M: Tiếp nhận nhiệm vụ cứu nạn",
            "sub": "(danh sách ca cứu trợ, lộ trình & bản đồ)",
            "cx": c1_x, "cy": sys["y"] + 488, "rx": 120, "ry": 25,
            "fill": "#E8F5E9", "stroke": "#2E7D32", "txt": "#1B5E20"
        },
        {
            "id": "uc_08m", "name": "UC-08M: Cập nhật tiến độ hiện trường",
            "sub": "(đang tiếp cận, đã giải cứu nạn nhân)",
            "cx": c1_x, "cy": sys["y"] + 574, "rx": 120, "ry": 25,
            "fill": "#E8F5E9", "stroke": "#2E7D32", "txt": "#1B5E20"
        },
        {
            "id": "uc_11m", "name": "UC-11M: Báo cáo kết quả & xin chi viện",
            "sub": "(đánh giá hiện trạng & yêu cầu thêm nhân lực)",
            "cx": c1_x, "cy": sys["y"] + 660, "rx": 120, "ry": 25,
            "fill": "#E8F5E9", "stroke": "#2E7D32", "txt": "#1B5E20"
        },

        # --- CỘT 2: Ca mở rộng, AI & Ngoại vi ---
        {
            "id": "uc_03", "name": "UC-03: Nhận diện mức ngập từ ảnh",
            "sub": "(Edge AI on-device MobileNetV3)",
            "cx": c2_x, "cy": sys["y"] + 110, "rx": 122, "ry": 25,
            "fill": "#FCE4EC", "stroke": "#D81B60", "txt": "#880E4F"
        },
        {
            "id": "uc_10m", "name": "UC-10M: Truyền dữ liệu thích ứng",
            "sub": "(ảnh gốc / nén JPEG / metadata theo mạng)",
            "cx": c2_x, "cy": sys["y"] + 205, "rx": 122, "ry": 25,
            "fill": "#E1F5FE", "stroke": "#0288D1", "txt": "#01579B"
        },
        {
            "id": "uc_04", "name": "UC-04: Gửi tin nhắn SMS dự phòng",
            "sub": "(khi mất hoàn toàn dữ liệu Internet)",
            "cx": c2_x, "cy": sys["y"] + 345, "rx": 122, "ry": 26,
            "fill": "#FFEBEE", "stroke": "#E53935", "txt": "#B71C1C"
        },
    ]

    return canvas_w, canvas_h, sys, actors, usecases


def generate_drawio_xml():
    """Tạo tệp XML chuẩn cho diagrams.net (Draw.io)."""
    canvas_w, canvas_h, sys, actors, usecases = build_mobile_data()

    root = ET.Element("mxfile", host="Electron", agent="Antigravity")
    diagram = ET.SubElement(root, "diagram", id="diag-usecase-mobile", name="So-do-Use-Case-Chi-tiet-Mobile-App")
    model = ET.SubElement(diagram, "mxGraphModel",
                          dx="1400", dy="900", grid="1", gridSize="10",
                          guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1",
                          pageScale="1", pageWidth=str(canvas_w), pageHeight=str(canvas_h),
                          math="0", shadow="0")
    root_cell = ET.SubElement(model, "root")
    ET.SubElement(root_cell, "mxCell", id="0")
    ET.SubElement(root_cell, "mxCell", id="1", **{"parent": "0"})

    # 1. System boundary
    sys_style = ("shape=swimlane;whiteSpace=wrap;html=1;startSize=32;horizontal=1;"
                 "fillColor=#F8F9FA;strokeColor=#1976D2;strokeWidth=1.5;fontStyle=1;"
                 "fontSize=14;fontFamily=Helvetica;fontColor=#0D47A1;")
    cell_sys = ET.SubElement(root_cell, "mxCell", id="sys_bound", value=sys["title"],
                             style=sys_style, vertex="1", **{"parent": "1"})
    ET.SubElement(cell_sys, "mxGeometry", x=str(sys["x"]), y=str(sys["y"]),
                  width=str(sys["w"]), height=str(sys["h"]), **{"as": "geometry"})

    # 2. Use Cases inside sys_bound
    for uc in usecases:
        rel_x = uc["cx"] - uc["rx"] - sys["x"]
        rel_y = uc["cy"] - uc["ry"] - sys["y"]
        val = f"{uc['name']}&#xa;{uc['sub']}"
        style = (f"ellipse;whiteSpace=wrap;html=1;fillColor={uc['fill']};strokeColor={uc['stroke']};"
                 f"strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor={uc['txt']};")
        c = ET.SubElement(root_cell, "mxCell", id=uc["id"], value=val,
                          style=style, vertex="1", **{"parent": "sys_bound"})
        ET.SubElement(c, "mxGeometry", x=str(int(rel_x)), y=str(int(rel_y)),
                      width=str(int(uc["rx"] * 2)), height=str(int(uc["ry"] * 2)), **{"as": "geometry"})

    # 3. Actors outside sys_bound
    for aid, a in actors.items():
        if aid == "act_sms_gw":
            gw_style = (f"rounded=1;whiteSpace=wrap;html=1;fillColor={a['fill']};strokeColor={a['stroke']};"
                        f"strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontColor=#263238;align=center;")
            c = ET.SubElement(root_cell, "mxCell", id=aid, value=a["name"].replace("\n", "&#xa;"),
                              style=gw_style, vertex="1", **{"parent": "1"})
        else:
            act_style = (f"shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;"
                         f"fontFamily=Helvetica;fontSize=12;fontStyle=1;fillColor={a['fill']};strokeColor={a['stroke']};")
            c = ET.SubElement(root_cell, "mxCell", id=aid, value=a["name"].replace("\n", "&#xa;"),
                              style=act_style, vertex="1", **{"parent": "1"})
        ET.SubElement(c, "mxGeometry", x=str(a["x"]), y=str(a["y"]),
                      width=str(a["w"]), height=str(a["h"]), **{"as": "geometry"})

    # 4. Association Edges
    assoc_blue = "endArrow=none;html=1;strokeColor=#1976D2;strokeWidth=1.2;"
    assoc_green = "endArrow=none;html=1;strokeColor=#2E7D32;strokeWidth=1.2;"
    assoc_red = "endArrow=none;html=1;strokeColor=#E53935;strokeWidth=1.2;"

    # Citizen connections (Không cắt ngang Rescuer)
    for ucid in ["uc_01", "uc_02", "uc_06", "uc_09m", "uc_05"]:
        e = ET.SubElement(root_cell, "mxCell", id=f"e_cit_{ucid}", value="",
                          style=assoc_blue, edge="1",
                          source="act_citizen", target=ucid, **{"parent": "1"})
        ET.SubElement(e, "mxGeometry", relative="1", **{"as": "geometry"})

    # Rescuer connections (Không cắt ngang Citizen)
    for ucid in ["uc_05", "uc_07m", "uc_08m", "uc_11m"]:
        e = ET.SubElement(root_cell, "mxCell", id=f"e_res_{ucid}", value="",
                          style=assoc_green, edge="1",
                          source="act_rescuer", target=ucid, **{"parent": "1"})
        ET.SubElement(e, "mxGeometry", relative="1", **{"as": "geometry"})

    # SMS Gateway to UC-04
    e_sms = ET.SubElement(root_cell, "mxCell", id="e_sms_gw_uc04", value="",
                          style=assoc_red, edge="1",
                          source="uc_04", target="act_sms_gw", **{"parent": "1"})
    ET.SubElement(e_sms, "mxGeometry", relative="1", **{"as": "geometry"})

    # 5. Internal UML Stereotypes: «include» and «extend»
    inc_style_pink = "endArrow=open;dashed=1;html=1;strokeColor=#D81B60;strokeWidth=1.3;fontSize=10;fontColor=#D81B60;"
    inc_style_blue = "endArrow=open;dashed=1;html=1;strokeColor=#0288D1;strokeWidth=1.3;fontSize=10;fontColor=#0288D1;"
    ext_style = "endArrow=open;dashed=1;html=1;strokeColor=#E53935;strokeWidth=1.3;fontSize=10;fontColor=#E53935;"

    # UC-02 includes UC-03 (AI On-device)
    e_inc1 = ET.SubElement(root_cell, "mxCell", id="e_inc_ai", value="&laquo;include&raquo;",
                           style=inc_style_pink, edge="1",
                           source="uc_02", target="uc_03", **{"parent": "1"})
    ET.SubElement(e_inc1, "mxGeometry", relative="1", **{"as": "geometry"})

    # UC-02 includes UC-10M (Truyền thích ứng)
    e_inc2 = ET.SubElement(root_cell, "mxCell", id="e_inc_adapt", value="&laquo;include&raquo;",
                           style=inc_style_blue, edge="1",
                           source="uc_02", target="uc_10m", **{"parent": "1"})
    ET.SubElement(e_inc2, "mxGeometry", relative="1", **{"as": "geometry"})

    # UC-04 extends UC-02 (SMS dự phòng khi mất mạng)
    e_ext = ET.SubElement(root_cell, "mxCell", id="e_ext_sms",
                          value="&laquo;extend&raquo;&#xa;(khi mất mạng)",
                          style=ext_style, edge="1",
                          source="uc_04", target="uc_02", **{"parent": "1"})
    geo_ext = ET.SubElement(e_ext, "mxGeometry", relative="1", **{"as": "geometry"})
    pts_ext = ET.SubElement(geo_ext, "Array", **{"as": "points"})
    ET.SubElement(pts_ext, "mxPoint", x="670", y="285")

    return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")


def generate_svg():
    """Tạo biểu diễn SVG sắc nét với phông Roboto / DejaVu Sans trên từng text element."""
    canvas_w, canvas_h, sys, actors, usecases = build_mobile_data()
    uc_map = {uc["id"]: uc for uc in usecases}
    font_attr = 'font-family="Roboto, DejaVu Sans, Arial, sans-serif"'

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_w} {canvas_h}" width="{canvas_w}" height="{canvas_h}">')
    svg.append('<defs>')

    # Markers for include / extend
    svg.append('<marker id="arrow-inc-pink" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">')
    svg.append('<path d="M 0 1 L 9 5 L 0 9" fill="none" stroke="#D81B60" stroke-width="1.4"/>')
    svg.append('</marker>')

    svg.append('<marker id="arrow-inc-blue" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">')
    svg.append('<path d="M 0 1 L 9 5 L 0 9" fill="none" stroke="#0288D1" stroke-width="1.4"/>')
    svg.append('</marker>')

    svg.append('<marker id="arrow-ext-red" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">')
    svg.append('<path d="M 0 1 L 9 5 L 0 9" fill="none" stroke="#E53935" stroke-width="1.4"/>')
    svg.append('</marker>')

    svg.append('</defs>')

    # Canvas Background
    svg.append(f'<rect width="{canvas_w}" height="{canvas_h}" fill="#FFFFFF"/>')

    # Helper: draw stick-man actor
    def draw_actor(x, y, name, fill, stroke):
        head_r = 14
        body_len = 32
        svg.append(f'<circle cx="{x}" cy="{y}" r="{head_r}" fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>')
        svg.append(f'<line x1="{x}" y1="{y + head_r}" x2="{x}" y2="{y + head_r + body_len}" stroke="{stroke}" stroke-width="1.8"/>')
        svg.append(f'<line x1="{x - 18}" y1="{y + head_r + 10}" x2="{x + 18}" y2="{y + head_r + 10}" stroke="{stroke}" stroke-width="1.8"/>')
        svg.append(f'<line x1="{x}" y1="{y + head_r + body_len}" x2="{x - 14}" y2="{y + head_r + body_len + 24}" stroke="{stroke}" stroke-width="1.8"/>')
        svg.append(f'<line x1="{x}" y1="{y + head_r + body_len}" x2="{x + 14}" y2="{y + head_r + body_len + 24}" stroke="{stroke}" stroke-width="1.8"/>')
        lines = name.split('\n')
        if len(lines) == 1:
            svg.append(f'<text x="{x}" y="{y + head_r + body_len + 40}" {font_attr} font-size="12px" font-weight="bold" text-anchor="middle" fill="{stroke}">{lines[0]}</text>')
        else:
            svg.append(f'<text x="{x}" y="{y + head_r + body_len + 38}" {font_attr} font-size="12px" font-weight="bold" text-anchor="middle" fill="{stroke}">{lines[0]}</text>')
            svg.append(f'<text x="{x}" y="{y + head_r + body_len + 52}" {font_attr} font-size="12px" font-weight="bold" text-anchor="middle" fill="{stroke}">{lines[1]}</text>')

    # 1. System Boundary
    bx, by, bw, bh = sys["x"], sys["y"], sys["w"], sys["h"]
    svg.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="8" fill="#F8F9FA" stroke="#1976D2" stroke-width="1.6"/>')
    svg.append(f'<path d="M {bx} {by + 34} L {bx + bw} {by + 34}" stroke="#1976D2" stroke-width="1.2"/>')
    svg.append(f'<text x="{bx + bw/2}" y="{by + 23}" {font_attr} font-size="14px" font-weight="bold" fill="#0D47A1" letter-spacing="0.5px" text-anchor="middle">{sys["title"]}</text>')

    # 2. Draw Association Edges (Underneath ovals)
    # Citizen edges (Nối tới các UC cy <= 442)
    cit = actors["act_citizen"]
    cit_x, cit_y = cit["x"] + 25, cit["y"] + 20
    for ucid in ["uc_01", "uc_02", "uc_06", "uc_09m", "uc_05"]:
        u = uc_map[ucid]
        svg.append(f'<line x1="{cit_x}" y1="{cit_y}" x2="{u["cx"] - u["rx"]}" y2="{u["cy"]}" stroke="#1976D2" stroke-width="1.2"/>')

    # Rescuer edges (Nối tới UC-05 và các UC cy >= 488)
    res = actors["act_rescuer"]
    res_x, res_y = res["x"] + 25, res["y"] + 20
    for ucid in ["uc_05", "uc_07m", "uc_08m", "uc_11m"]:
        u = uc_map[ucid]
        svg.append(f'<line x1="{res_x}" y1="{res_y}" x2="{u["cx"] - u["rx"]}" y2="{u["cy"]}" stroke="#2E7D32" stroke-width="1.2"/>')

    # SMS Gateway edge (Nối thẳng ngang sang UC-04)
    gw = actors["act_sms_gw"]
    gw_x, gw_y = gw["x"], gw["y"] + gw["h"] / 2
    u4 = uc_map["uc_04"]
    svg.append(f'<line x1="{u4["cx"] + u4["rx"]}" y1="{u4["cy"]}" x2="{gw_x}" y2="{gw_y}" stroke="#E53935" stroke-width="1.3"/>')

    # 3. Internal UML Relationships
    u2 = uc_map["uc_02"]
    u3 = uc_map["uc_03"]
    u10m = uc_map["uc_10m"]

    # UC-02 includes UC-03 (AI On-device)
    svg.append(f'<line x1="{u2["cx"] + u2["rx"]}" y1="{u2["cy"] - 8}" x2="{u3["cx"] - u3["rx"]}" y2="{u3["cy"] + 8}" stroke="#D81B60" stroke-width="1.4" stroke-dasharray="5,4" marker-end="url(#arrow-inc-pink)"/>')
    mid_inc1_x = (u2["cx"] + u2["rx"] + u3["cx"] - u3["rx"]) / 2
    mid_inc1_y = (u2["cy"] - 8 + u3["cy"] + 8) / 2
    svg.append(f'<rect x="{mid_inc1_x - 30}" y="{mid_inc1_y - 10}" width="60" height="16" rx="3" fill="#FFFFFF" stroke="#D81B60" stroke-width="0.8"/>')
    svg.append(f'<text x="{mid_inc1_x}" y="{mid_inc1_y + 2}" {font_attr} font-size="10px" font-weight="bold" fill="#D81B60" text-anchor="middle">«include»</text>')

    # UC-02 includes UC-10M (Truyền thích ứng)
    svg.append(f'<line x1="{u2["cx"] + u2["rx"]}" y1="{u2["cy"] + 8}" x2="{u10m["cx"] - u10m["rx"]}" y2="{u10m["cy"] - 8}" stroke="#0288D1" stroke-width="1.4" stroke-dasharray="5,4" marker-end="url(#arrow-inc-blue)"/>')
    mid_inc2_x = (u2["cx"] + u2["rx"] + u10m["cx"] - u10m["rx"]) / 2
    mid_inc2_y = (u2["cy"] + 8 + u10m["cy"] - 8) / 2
    svg.append(f'<rect x="{mid_inc2_x - 30}" y="{mid_inc2_y - 10}" width="60" height="16" rx="3" fill="#FFFFFF" stroke="#0288D1" stroke-width="0.8"/>')
    svg.append(f'<text x="{mid_inc2_x}" y="{mid_inc2_y + 2}" {font_attr} font-size="10px" font-weight="bold" fill="#0288D1" text-anchor="middle">«include»</text>')

    # UC-04 extends UC-02 (SMS Fallback when offline)
    # Đường cong từ UC-04 sang UC-02, đi qua (670, 285) cách UC-06 hơn 120px
    svg.append(f'<path d="M {u4["cx"] - 75} {u4["cy"] - u4["ry"]} C 685 315, 650 230, {u2["cx"] + 75} {u2["cy"] + u2["ry"]}" fill="none" stroke="#E53935" stroke-width="1.4" stroke-dasharray="5,4" marker-end="url(#arrow-ext-red)"/>')
    svg.append(f'<rect x="635" y="270" width="82" height="26" rx="3" fill="#FFFFFF" stroke="#E53935" stroke-width="0.8"/>')
    svg.append(f'<text x="676" y="282" {font_attr} font-size="10px" font-weight="bold" fill="#E53935" text-anchor="middle">«extend»</text>')
    svg.append(f'<text x="676" y="293" {font_attr} font-size="8.5px" fill="#B71C1C" text-anchor="middle">(khi mất mạng)</text>')

    # 4. Draw Use Case Ovals on top
    for uc in usecases:
        svg.append(f'<ellipse cx="{uc["cx"]}" cy="{uc["cy"]}" rx="{uc["rx"]}" ry="{uc["ry"]}" fill="{uc["fill"]}" stroke="{uc["stroke"]}" stroke-width="1.4"/>')
        svg.append(f'<text x="{uc["cx"]}" y="{uc["cy"] - 3}" {font_attr} font-size="11.5px" font-weight="bold" text-anchor="middle" fill="{uc["txt"]}">{html.escape(uc["name"])}</text>')
        if uc["sub"]:
            svg.append(f'<text x="{uc["cx"]}" y="{uc["cy"] + 11}" {font_attr} font-size="9.5px" text-anchor="middle" fill="{uc["txt"]}">{html.escape(uc["sub"])}</text>')

    # 5. Draw Actors
    for aid, a in actors.items():
        if aid == "act_sms_gw":
            svg.append(f'<rect x="{a["x"]}" y="{a["y"]}" width="{a["w"]}" height="{a["h"]}" rx="6" fill="{a["fill"]}" stroke="{a["stroke"]}" stroke-width="1.8"/>')
            svg.append(f'<text x="{a["x"] + a["w"]/2}" y="{a["y"] + 18}" {font_attr} font-size="9.5px" font-weight="bold" text-anchor="middle" fill="#37474F">&laquo;external system&raquo;</text>')
            svg.append(f'<text x="{a["x"] + a["w"]/2}" y="{a["y"] + 36}" {font_attr} font-size="11px" font-weight="bold" text-anchor="middle" fill="#263238">SMS Gateway /</text>')
            svg.append(f'<text x="{a["x"] + a["w"]/2}" y="{a["y"] + 51}" {font_attr} font-size="11px" font-weight="bold" text-anchor="middle" fill="#263238">Nhà mạng viễn thông</text>')
        else:
            draw_actor(a["x"] + 25, a["y"] + 20, a["name"], a["fill"], a["stroke"])

    svg.append('</svg>')
    return '\n'.join(svg)


def main():
    print("1. Đang xuất Draw.io XML sang", DRAWIO_PATH)
    xml_str = generate_drawio_xml()
    DRAWIO_PATH.write_text(xml_str, encoding="utf-8")
    print(f"   -> Đã ghi {len(xml_str)} bytes vào {DRAWIO_PATH.name}")

    print("2. Đang tạo SVG và xuất vector PDF sang", PDF_PATH)
    svg_str = generate_svg()
    
    # Chuyển SVG sang PDF bằng PyMuPDF
    doc = fitz.open()
    doc.insert_pdf(fitz.open("pdf", fitz.open(stream=svg_str.encode("utf-8"), filetype="svg").convert_to_pdf()))
    doc.save(str(PDF_PATH), garbage=4, deflate=True)
    doc.close()
    print(f"   -> Đã ghi {PDF_PATH.stat().st_size} bytes vào {PDF_PATH.name}")

    print("3. Đang xuất ảnh kiểm tra PNG preview sang", PREVIEW_PATH)
    doc_pdf = fitz.open(str(PDF_PATH))
    page = doc_pdf[0]
    pix = page.get_pixmap(dpi=200)
    pix.save(str(PREVIEW_PATH))
    doc_pdf.close()
    print(f"   -> Đã lưu ảnh preview: {PREVIEW_PATH.name} ({pix.width}x{pix.height} px)")


if __name__ == "__main__":
    main()
