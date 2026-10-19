#!/usr/bin/env python3
"""Tạo lại usecase.drawio và usecase.pdf chuẩn xác 100% theo tiêu chuẩn UML 2.5.
Tối ưu hóa hình học tuyệt đối:
1. UC-08 (Giám sát bản đồ) include ngang sang UC-09 (Tự động gom cụm) ở cùng độ cao cy=290, gap 95px.
2. Mọi Use Case Cột 1 Dashboard nằm chính xác tại trung điểm khoảng trống của Cột 2.
3. Hành lang định tuyến (Corridor x=1390) dẫn các đường nối từ Dispatcher tới Cột 1 đi qua chính giữa các khe hở thoáng.
4. Mobile App: Nhãn «extend» (khi mất mạng) nằm chính xác tại điểm giữa (cx=505, cy=358), cách mép oval hơn 45px.
5. Nhãn «include» AI nằm chính xác tại (cx=505, cy=265), cách mép oval hơn 10px.
"""

import html
from pathlib import Path
import xml.etree.ElementTree as ET
import fitz

ROOT = Path(__file__).resolve().parents[1]
DIAGRAMS_DIR = ROOT / "assets" / "diagrams"
DRAWIO_PATH = DIAGRAMS_DIR / "usecase.drawio"
PDF_PATH = DIAGRAMS_DIR / "usecase.pdf"


def build_layout_data():
    """Tọa độ và kích thước tuyệt đối chuẩn xác cho từng phần tử."""
    # Hệ thống tổng
    sys = {"x": 220, "y": 40, "w": 1190, "h": 880}

    # Phân hệ Di động (Mobile App)
    sub_fe = {"x": sys["x"] + 25, "y": sys["y"] + 45, "w": 525, "h": 805}

    # Phân hệ Điều phối (Dashboard)
    sub_da = {"x": sys["x"] + 575, "y": sys["y"] + 45, "w": 590, "h": 805}

    # Actors
    actors = {
        "act_citizen": {"name": "Người dân /\nNạn nhân", "x": 75, "y": 200, "w": 50, "h": 90, "fill": "#E3F2FD", "stroke": "#1976D2"},
        "act_rescuer": {"name": "Đội cứu hộ\nthực địa", "x": 75, "y": 460, "w": 50, "h": 90, "fill": "#E8F5E9", "stroke": "#388E3C"},
        "act_sms_gw": {"name": "«external system»\nSMS Gateway /\nNhà mạng viễn thông", "x": 30, "y": 730, "w": 140, "h": 65, "fill": "#ECEFF1", "stroke": "#455A64"},
        "act_dispatcher": {"name": "Điều phối viên\n(Dispatcher)", "x": 1460, "y": 300, "w": 50, "h": 90, "fill": "#FFF3E0", "stroke": "#F57C00"},
        "act_admin": {"name": "Quản trị viên\n(Administrator)", "x": 1460, "y": 725, "w": 50, "h": 90, "fill": "#EDE7F6", "stroke": "#512DA8"},
    }

    # Use Cases - Mobile
    fe_c1_x = 360
    fe_c2_x = 650

    # Use Cases - Dashboard (sub_da: x=795..1385)
    # da_c1_x = 910 (rx=108 -> x: 802..1018)
    # da_c2_x = 1225 (rx=112 -> x: 1113..1337)
    # Gap: 1113 - 1018 = 95px!
    da_c1_x = 910
    da_c2_x = 1225

    usecases = [
        # --- MOBILE (6 Use Cases) ---
        {
            "id": "uc_01", "name": "UC-01: Gửi yêu cầu SOS khẩn cấp", "sub": "(1 chạm, định vị nhanh)",
            "cx": fe_c1_x, "cy": sub_fe["y"] + 70, "rx": 105, "ry": 26,
            "fill": "#FFFFFF", "stroke": "#1E88E5", "txt": "#0D47A1"
        },
        {
            "id": "uc_02", "name": "UC-02: Tạo báo cáo cứu hộ chi tiết", "sub": "(vị trí, số người, ảnh hiện trường)",
            "cx": fe_c1_x, "cy": sub_fe["y"] + 200, "rx": 105, "ry": 26,
            "fill": "#FFFFFF", "stroke": "#1E88E5", "txt": "#0D47A1"
        },
        {
            "id": "uc_03", "name": "UC-03: Nhận diện mức ngập từ ảnh", "sub": "(Edge AI on-device MobileNetV3)",
            "cx": fe_c2_x, "cy": sub_fe["y"] + 200, "rx": 105, "ry": 26,
            "fill": "#FCE4EC", "stroke": "#D81B60", "txt": "#880E4F"
        },
        {
            "id": "uc_04", "name": "UC-04: Gửi tin nhắn SMS dự phòng", "sub": "(khi mất hoàn toàn dữ liệu mạng)",
            "cx": fe_c2_x, "cy": sub_fe["y"] + 345, "rx": 105, "ry": 26,
            "fill": "#FFEBEE", "stroke": "#E53935", "txt": "#B71C1C"
        },
        {
            "id": "uc_05", "name": "UC-05: Đồng bộ báo cáo ngoại tuyến", "sub": "(tự động gửi khi khôi phục mạng)",
            "cx": fe_c1_x, "cy": sub_fe["y"] + 480, "rx": 105, "ry": 26,
            "fill": "#FFFFFF", "stroke": "#1E88E5", "txt": "#0D47A1"
        },
        {
            "id": "uc_06", "name": "UC-06: Tra cứu trạng thái cứu hộ", "sub": "(tiến trình xử lý & vị trí đội)",
            "cx": fe_c1_x, "cy": sub_fe["y"] + 615, "rx": 105, "ry": 26,
            "fill": "#FFFFFF", "stroke": "#1E88E5", "txt": "#0D47A1"
        },

        # --- DASHBOARD (12 Use Cases) ---
        # Col 2 (Phải - Đối diện Dispatcher):
        # cy = 85 + 75 = 160
        # cy = 85 + 205 = 290
        # cy = 85 + 335 = 420
        # cy = 85 + 465 = 550
        # cy = 85 + 595 = 680
        # cy = 85 + 745 = 830
        {
            "id": "uc_07", "name": "UC-07: Đăng nhập & Xác thực phiên", "sub": "(phân quyền Dispatcher / Admin)",
            "cx": da_c2_x, "cy": sub_da["y"] + 75, "rx": 112, "ry": 25,
            "fill": "#FFFFFF", "stroke": "#F57C00", "txt": "#E65100"
        },
        {
            "id": "uc_08", "name": "UC-08: Giám sát bản đồ sự cố", "sub": "& thứ tự ưu tiên cứu hộ",
            "cx": da_c2_x, "cy": sub_da["y"] + 205, "rx": 112, "ry": 25,
            "fill": "#FFFFFF", "stroke": "#F57C00", "txt": "#E65100"
        },
        {
            "id": "uc_13", "name": "UC-13: Phân công & điều động", "sub": "đội cứu hộ thực địa",
            "cx": da_c2_x, "cy": sub_da["y"] + 335, "rx": 112, "ry": 25,
            "fill": "#FFFFFF", "stroke": "#F57C00", "txt": "#E65100"
        },
        {
            "id": "uc_14", "name": "UC-14: Cập nhật tiến độ nhiệm vụ", "sub": "(dispatched -> resolved / close)",
            "cx": da_c2_x, "cy": sub_da["y"] + 465, "rx": 112, "ry": 25,
            "fill": "#FFFFFF", "stroke": "#F57C00", "txt": "#E65100"
        },
        {
            "id": "uc_16", "name": "UC-16: Xuất dữ liệu báo cáo", "sub": "(CSV / GeoJSON / Thống kê)",
            "cx": da_c2_x, "cy": sub_da["y"] + 595, "rx": 112, "ry": 25,
            "fill": "#FFFFFF", "stroke": "#F57C00", "txt": "#E65100"
        },
        {
            "id": "uc_18", "name": "UC-18: Sao lưu & phục hồi CSDL", "sub": "(CSDL và ảnh hiện trường)",
            "cx": da_c2_x, "cy": sub_da["y"] + 745, "rx": 112, "ry": 25,
            "fill": "#FFFFFF", "stroke": "#512DA8", "txt": "#311B92"
        },

        # Col 1 (Trái trong sub_da):
        # UC-09 nằm ngang hàng với UC-08 (cy = 85 + 205 = 290)
        # Các Use Case khác nằm sole ở trung điểm:
        # cy = 85 + 140 = 225
        # cy = 85 + 270 = 355
        # cy = 85 + 400 = 485
        # cy = 85 + 530 = 615
        # cy = 85 + 670 = 755
        {
            "id": "uc_10", "name": "UC-10: Quản lý & tra cứu danh sách", "sub": "báo cáo hiện trường",
            "cx": da_c1_x, "cy": sub_da["y"] + 140, "rx": 108, "ry": 25,
            "fill": "#FFFFFF", "stroke": "#F57C00", "txt": "#E65100"
        },
        {
            "id": "uc_09", "name": "UC-09: Tự động gom cụm & xếp hạng", "sub": "ưu tiên cứu hộ (Louvain & P(c))",
            "cx": da_c1_x, "cy": sub_da["y"] + 205, "rx": 110, "ry": 25,
            "fill": "#F3E5F5", "stroke": "#6A1B9A", "txt": "#4A148C"
        },
        {
            "id": "uc_11", "name": "UC-11: Tiếp nhận báo cáo tổng đài", "sub": "(nhập cứu hộ thủ công)",
            "cx": da_c1_x, "cy": sub_da["y"] + 270, "rx": 108, "ry": 25,
            "fill": "#FFFFFF", "stroke": "#F57C00", "txt": "#E65100"
        },
        {
            "id": "uc_12", "name": "UC-12: Tiếp nhận báo cáo qua SMS", "sub": "(đồng bộ tự động từ Gateway)",
            "cx": da_c1_x, "cy": sub_da["y"] + 400, "rx": 108, "ry": 25,
            "fill": "#FFFFFF", "stroke": "#F57C00", "txt": "#E65100"
        },
        {
            "id": "uc_15", "name": "UC-15: Bổ sung tọa độ thủ công", "sub": "(ca thiếu GPS / hàng xem xét)",
            "cx": da_c1_x, "cy": sub_da["y"] + 530, "rx": 108, "ry": 25,
            "fill": "#FFFFFF", "stroke": "#F57C00", "txt": "#E65100"
        },
        {
            "id": "uc_17", "name": "UC-17: Quản lý tài khoản điều phối", "sub": "(CRUD danh mục cán bộ)",
            "cx": da_c1_x, "cy": sub_da["y"] + 670, "rx": 108, "ry": 25,
            "fill": "#FFFFFF", "stroke": "#512DA8", "txt": "#311B92"
        },
    ]

    return sys, sub_fe, sub_da, actors, usecases


def generate_drawio_xml():
    sys, sub_fe, sub_da, actors, usecases = build_layout_data()
    uc_map = {uc["id"]: uc for uc in usecases}

    mxfile = ET.Element("mxfile", {"host": "app.diagrams.net", "agent": "Antigravity", "version": "24.0.0"})
    diagram = ET.SubElement(mxfile, "diagram", {"id": "diag-usecase", "name": "So-do-Use-Case-Tong-The"})
    model = ET.SubElement(
        diagram, "mxGraphModel",
        {"dx": "1400", "dy": "900", "grid": "1", "gridSize": "10", "guides": "1", "tooltips": "1",
         "connect": "1", "arrows": "1", "fold": "1", "page": "1", "pageScale": "1",
         "pageWidth": "1600", "pageHeight": "950", "math": "0", "shadow": "0"}
    )
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})

    def add_cell(cell_id, value, style, parent="1", x=0, y=0, w=120, h=60):
        cell = ET.Element("mxCell", {
            "id": str(cell_id), "value": value, "style": style,
            "parent": str(parent), "vertex": "1"
        })
        ET.SubElement(cell, "mxGeometry", {
            "x": str(x), "y": str(y), "width": str(w), "height": str(h), "as": "geometry"
        })
        root.append(cell)
        return cell

    def add_edge(edge_id, value, style, source, target, parent="1", points=None):
        cell = ET.Element("mxCell", {
            "id": str(edge_id), "value": value, "style": style,
            "parent": str(parent), "edge": "1", "source": str(source), "target": str(target)
        })
        geo = ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
        if points:
            arr = ET.SubElement(geo, "Array", {"as": "points"})
            for px, py in points:
                ET.SubElement(arr, "mxPoint", {"x": str(px), "y": str(py)})
        root.append(cell)
        return cell

    # 1. System Boundary
    add_cell(
        "sys_bound", "HỆ THỐNG HỖ TRỢ CỨU HỘ BÃO LŨ (THS2026-68)",
        "shape=swimlane;whiteSpace=wrap;html=1;startSize=32;horizontal=1;fillColor=#FAFAFA;strokeColor=#37474F;strokeWidth=1.5;fontStyle=1;fontSize=14;fontFamily=Helvetica;fontColor=#263238;",
        x=sys["x"], y=sys["y"], w=sys["w"], h=sys["h"]
    )

    # 2. Subsystems
    subsys_style = "rounded=1;whiteSpace=wrap;html=1;dashed=1;verticalAlign=top;fontStyle=1;fontSize=12;spacingTop=8;strokeWidth=1.2;"
    add_cell(
        "sub_fe", "Phân hệ Di động Biên (Edge Mobile App - Flutter)",
        subsys_style + "fillColor=#F0F7FF;strokeColor=#64B5F6;fontColor=#0D47A1;",
        parent="sys_bound", x=sub_fe["x"] - sys["x"], y=sub_fe["y"] - sys["y"], w=sub_fe["w"], h=sub_fe["h"]
    )
    add_cell(
        "sub_dash", "Phân hệ Điều phối & Quản trị Web (Dispatch Dashboard)",
        subsys_style + "fillColor=#FFFDF5;strokeColor=#FFB74D;fontColor=#E65100;",
        parent="sys_bound", x=sub_da["x"] - sys["x"], y=sub_da["y"] - sys["y"], w=sub_da["w"], h=sub_da["h"]
    )

    # 3. Actors
    actor_style = "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fontFamily=Helvetica;fontSize=12;fontStyle=1;"
    for aid, a in actors.items():
        if aid == "act_sms_gw":
            ext_sys_style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#ECEFF1;strokeColor=#546E7A;strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontStyle=1;fontColor=#263238;align=center;"
            add_cell(aid, a["name"], ext_sys_style, x=a["x"], y=a["y"], w=a["w"], h=a["h"])
        else:
            add_cell(aid, a["name"], actor_style + f"fillColor={a['fill']};strokeColor={a['stroke']};", x=a["x"], y=a["y"], w=a["w"], h=a["h"])

    # Generalization Actor: Admin --|> Dispatcher
    gen_style = "endArrow=block;endFill=0;html=1;strokeColor=#512DA8;strokeWidth=1.5;edgeStyle=orthogonalEdgeStyle;rounded=0;"
    add_edge("edge_gen_admin", "", gen_style, "act_admin", "act_dispatcher")

    # 4. Use Cases
    for uc in usecases:
        st = f"ellipse;whiteSpace=wrap;html=1;fillColor={uc['fill']};strokeColor={uc['stroke']};strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor={uc['txt']};fontStyle=1;"
        lbl = f"{uc['name']}\n{uc['sub']}" if uc["sub"] else uc["name"]
        add_cell(
            uc["id"], lbl, st, parent="sys_bound",
            x=uc["cx"] - sys["x"] - uc["rx"], y=uc["cy"] - sys["y"] - uc["ry"],
            w=uc["rx"] * 2, h=uc["ry"] * 2
        )

    # 5. Edges
    edge_style = "endArrow=none;html=1;strokeColor=#455A64;strokeWidth=1.2;"
    inc_style = "endArrow=open;dashed=1;html=1;strokeColor=#D81B60;strokeWidth=1.3;fontSize=10;fontColor=#D81B60;fontStyle=1;"
    ext_style = "endArrow=open;dashed=1;html=1;strokeColor=#E53935;strokeWidth=1.3;fontSize=10;fontColor=#E53935;fontStyle=1;"

    # Citizen
    for ucid in ["uc_01", "uc_02", "uc_05", "uc_06"]:
        add_edge(f"e_c_{ucid}", "", edge_style + "strokeColor=#1976D2;", "act_citizen", ucid)

    # Rescuer
    for ucid in ["uc_01", "uc_02", "uc_05", "uc_06"]:
        add_edge(f"e_r_{ucid}", "", edge_style + "strokeColor=#388E3C;", "act_rescuer", ucid)

    # Includes & Extends
    add_edge("e_inc_ai", "«include»", inc_style, "uc_02", "uc_03")
    add_edge("e_ext_sms", "«extend»\n(mất mạng)", ext_style, "uc_04", "uc_02", points=[(505, 360)])
    add_edge("e_inc_cluster", "«include»", inc_style, "uc_08", "uc_09")

    # SMS Gateway
    add_edge("e_sms_out", "", edge_style + "strokeColor=#E53935;", "act_sms_gw", "uc_04", points=[(180, 410)])
    add_edge("e_sms_in", "", edge_style + "strokeColor=#546E7A;dashed=1;", "act_sms_gw", "uc_12", points=[(100, 890), (uc_map["uc_12"]["cx"], 890)])

    # Dispatcher (Orthogonal Corridor Routing)
    for ucid in ["uc_07", "uc_08", "uc_10", "uc_11", "uc_13", "uc_14", "uc_15", "uc_16"]:
        u = uc_map[ucid]
        if u["cx"] < 1100:  # Col 1
            pts = [(1390, u["cy"]), (1040, u["cy"])]
            add_edge(f"e_d_{ucid}", "", edge_style + "strokeColor=#F57C00;", "act_dispatcher", ucid, points=pts)
        else:
            add_edge(f"e_d_{ucid}", "", edge_style + "strokeColor=#F57C00;", "act_dispatcher", ucid)

    # Admin
    u17 = uc_map["uc_17"]
    pts_adm = [(1390, u17["cy"]), (1040, u17["cy"])]
    add_edge("e_a_17", "", edge_style + "strokeColor=#512DA8;", "act_admin", "uc_17", points=pts_adm)
    add_edge("e_a_18", "", edge_style + "strokeColor=#512DA8;", "act_admin", "uc_18")

    return ET.tostring(mxfile, encoding="utf-8", xml_declaration=True).decode("utf-8")


def generate_vector_svg():
    sys, sub_fe, sub_da, actors, usecases = build_layout_data()
    uc_map = {uc["id"]: uc for uc in usecases}
    w = 1600
    h = 950

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'style="background-color: #FFFFFF; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Helvetica, Arial, sans-serif;">',
        '<defs>',
        '  <marker id="arrow-inc" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '    <path d="M 0 1 L 8 5 L 0 9" fill="none" stroke="#D81B60" stroke-width="1.6" stroke-linecap="round"/>',
        '  </marker>',
        '  <marker id="arrow-ext" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '    <path d="M 0 1 L 8 5 L 0 9" fill="none" stroke="#E53935" stroke-width="1.6" stroke-linecap="round"/>',
        '  </marker>',
        '  <marker id="arrow-gen" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="8" markerHeight="8" orient="auto">',
        '    <polygon points="0,1 10,6 0,11" fill="#FFFFFF" stroke="#512DA8" stroke-width="1.6" />',
        '  </marker>',
        '</defs>',
        '<style>',
        '  .title-sys { font-size: 15px; font-weight: 700; fill: #263238; letter-spacing: 0.5px; }',
        '  .title-sub { font-size: 12.5px; font-weight: 700; }',
        '  .actor-lbl { font-size: 11.5px; font-weight: 700; text-anchor: middle; }',
        '  .uc-lbl { font-size: 10.5px; font-weight: 700; text-anchor: middle; }',
        '  .uc-sub { font-size: 9.2px; text-anchor: middle; font-weight: 500; }',
        '  .rel-lbl { font-size: 10px; font-weight: 700; text-anchor: middle; fill: #D81B60; }',
        '  .rel-ext-lbl { font-size: 10px; font-weight: 700; text-anchor: middle; fill: #E53935; }',
        '</style>'
    ]

    # 1. System Boundary
    bx, by, bw, bh = sys["x"], sys["y"], sys["w"], sys["h"]
    svg.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="10" fill="#FAFAFA" stroke="#37474F" stroke-width="1.8"/>')
    svg.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="36" rx="10" fill="#ECEFF1" stroke="#37474F" stroke-width="1.8"/>')
    svg.append(f'<text x="{bx + bw/2}" y="{by + 23}" class="title-sys" text-anchor="middle">HỆ THỐNG HỖ TRỢ CỨU HỘ BÃO LŨ (THS2026-68)</text>')

    # 2. Subsystems
    fe_x, fe_y, fe_w, fe_h = sub_fe["x"], sub_fe["y"], sub_fe["w"], sub_fe["h"]
    svg.append(f'<rect x="{fe_x}" y="{fe_y}" width="{fe_w}" height="{fe_h}" rx="8" fill="#F0F7FF" stroke="#64B5F6" stroke-width="1.4" stroke-dasharray="6,4"/>')
    svg.append(f'<text x="{fe_x + 20}" y="{fe_y + 25}" class="title-sub" fill="#0D47A1">Phân hệ Di động Biên (Edge Mobile App - Flutter)</text>')

    da_x, da_y, da_w, da_h = sub_da["x"], sub_da["y"], sub_da["w"], sub_da["h"]
    svg.append(f'<rect x="{da_x}" y="{da_y}" width="{da_w}" height="{da_h}" rx="8" fill="#FFFDF5" stroke="#FFB74D" stroke-width="1.4" stroke-dasharray="6,4"/>')
    svg.append(f'<text x="{da_x + 20}" y="{da_y + 25}" class="title-sub" fill="#E65100">Phân hệ Điều phối &amp; Quản trị Web (Dispatch Dashboard)</text>')

    # 3. Actor Drawing Helper
    def draw_actor(x, y, name, color, stroke):
        head_r = 13
        svg.append(f'<circle cx="{x}" cy="{y - 28}" r="{head_r}" fill="{color}" stroke="{stroke}" stroke-width="1.8"/>')
        svg.append(f'<line x1="{x}" y1="{y - 15}" x2="{x}" y2="{y + 14}" stroke="{stroke}" stroke-width="2"/>')
        svg.append(f'<line x1="{x - 20}" y1="{y - 3}" x2="{x + 20}" y2="{y - 3}" stroke="{stroke}" stroke-width="2"/>')
        svg.append(f'<line x1="{x}" y1="{y + 14}" x2="{x - 16}" y2="{y + 42}" stroke="{stroke}" stroke-width="2"/>')
        svg.append(f'<line x1="{x}" y1="{y + 14}" x2="{x + 16}" y2="{y + 42}" stroke="{stroke}" stroke-width="2"/>')
        lines = name.split('\n')
        for i, l in enumerate(lines):
            svg.append(f'<text x="{x}" y="{y + 58 + i*13}" class="actor-lbl" fill="{stroke}">{html.escape(l)}</text>')

    # 4. Association Lines
    # Citizen
    cx, cy = actors["act_citizen"]["x"] + 25, actors["act_citizen"]["y"] + 20
    for ucid in ["uc_01", "uc_02", "uc_05", "uc_06"]:
        u = uc_map[ucid]
        svg.append(f'<line x1="{cx}" y1="{cy}" x2="{u["cx"] - u["rx"]}" y2="{u["cy"]}" stroke="#1976D2" stroke-width="1.2"/>')

    # Rescuer
    rx, ry = actors["act_rescuer"]["x"] + 25, actors["act_rescuer"]["y"] + 20
    for ucid in ["uc_01", "uc_02", "uc_05", "uc_06"]:
        u = uc_map[ucid]
        svg.append(f'<line x1="{rx}" y1="{ry}" x2="{u["cx"] - u["rx"]}" y2="{u["cy"]}" stroke="#388E3C" stroke-width="1.2"/>')

    # SMS Gateway to UC-04 (Fallback SMS)
    gw = actors["act_sms_gw"]
    gwx = gw["x"] + gw["w"]
    gwy = gw["y"] + 20
    u4 = uc_map["uc_04"]
    svg.append(f'<path d="M {gwx} {gwy} C 190 {gwy}, 190 {u4["cy"] + 45}, {u4["cx"] - 30} {u4["cy"] + u4["ry"]}" fill="none" stroke="#E53935" stroke-width="1.3"/>')

    # SMS Gateway to UC-12 (Inbound SMS)
    u12 = uc_map["uc_12"]
    svg.append(f'<path d="M {gw["x"] + gw["w"]/2} {gw["y"] + gw["h"]} L {gw["x"] + gw["w"]/2} {by + bh - 25} L {u12["cx"]} {by + bh - 25} L {u12["cx"]} {u12["cy"] + u12["ry"]}" fill="none" stroke="#546E7A" stroke-width="1.3" stroke-dasharray="4,3"/>')
    svg.append(f'<rect x="430" y="{by + bh - 34}" width="140" height="18" rx="4" fill="#FFFFFF" stroke="#546E7A" stroke-width="0.8"/>')
    svg.append(f'<text x="500" y="{by + bh - 21}" class="uc-sub" font-weight="bold" fill="#37474F">Webhook / Inbound API</text>')

    # Dispatcher: Sử dụng hành lang định tuyến (Routing Corridor tại x = 1390)
    dx = actors["act_dispatcher"]["x"] - 10
    dy = actors["act_dispatcher"]["y"] + 20
    corridor_x = 1390

    for ucid in ["uc_07", "uc_08", "uc_10", "uc_11", "uc_13", "uc_14", "uc_15", "uc_16"]:
        u = uc_map[ucid]
        if u["cx"] > 1100:  # Cột 2
            svg.append(f'<line x1="{dx}" y1="{dy}" x2="{u["cx"] + u["rx"]}" y2="{u["cy"]}" stroke="#F57C00" stroke-width="1.2"/>')
        else:  # Cột 1
            svg.append(f'<path d="M {dx} {dy} L {corridor_x} {u["cy"]} L {u["cx"] + u["rx"]} {u["cy"]}" fill="none" stroke="#F57C00" stroke-width="1.2"/>')

    # Admin to UC-17, UC-18
    ax = actors["act_admin"]["x"] - 10
    ay = actors["act_admin"]["y"] + 20
    u17 = uc_map["uc_17"]
    u18 = uc_map["uc_18"]
    svg.append(f'<path d="M {ax} {ay} L {corridor_x} {u17["cy"]} L {u17["cx"] + u17["rx"]} {u17["cy"]}" fill="none" stroke="#512DA8" stroke-width="1.4"/>')
    svg.append(f'<line x1="{ax}" y1="{ay}" x2="{u18["cx"] + u18["rx"]}" y2="{u18["cy"]}" stroke="#512DA8" stroke-width="1.4"/>')

    # Generalization Admin -> Dispatcher
    adm_x = actors["act_admin"]["x"] + 25
    adm_y = actors["act_admin"]["y"] - 35
    disp_x = actors["act_dispatcher"]["x"] + 25
    disp_y = actors["act_dispatcher"]["y"] + 80
    svg.append(f'<line x1="{adm_x}" y1="{adm_y}" x2="{disp_x}" y2="{disp_y}" stroke="#512DA8" stroke-width="1.8" marker-end="url(#arrow-gen)"/>')
    mid_gen_y = (adm_y + disp_y) / 2
    svg.append(f'<rect x="{adm_x - 55}" y="{mid_gen_y - 9}" width="110" height="18" rx="3" fill="#FFFFFF" stroke="#512DA8" stroke-width="0.8"/>')
    svg.append(f'<text x="{adm_x}" y="{mid_gen_y + 4}" class="uc-sub" font-weight="bold" fill="#512DA8">Kế thừa quyền</text>')

    # Internal Use Case Relationships
    # 1. UC-02 includes UC-03 (AI)
    u2 = uc_map["uc_02"]
    u3 = uc_map["uc_03"]
    svg.append(f'<line x1="{u2["cx"] + u2["rx"]}" y1="{u2["cy"]}" x2="{u3["cx"] - u3["rx"]}" y2="{u3["cy"]}" stroke="#D81B60" stroke-width="1.5" stroke-dasharray="5,4" marker-end="url(#arrow-inc)"/>')
    mid_x_inc = (u2["cx"] + u2["rx"] + u3["cx"] - u3["rx"]) / 2
    svg.append(f'<rect x="{mid_x_inc - 32}" y="{u2["cy"] - 22}" width="64" height="16" rx="3" fill="#FFFFFF" stroke="#D81B60" stroke-width="0.8"/>')
    svg.append(f'<text x="{mid_x_inc}" y="{u2["cy"] - 10}" class="rel-lbl">«include»</text>')

    # 2. UC-04 extends UC-02 (SMS Fallback when offline) -> Extension points to Base!
    # Đi cong trong khoảng trống rộng giữa UC-02, UC-04 và UC-05, nhãn đặt tại (505, 358)
    svg.append(f'<path d="M {u4["cx"] - 70} {u4["cy"] - u4["ry"]} C {u4["cx"] - 130} {u4["cy"] - 70}, {u2["cx"] + 110} {u2["cy"] + 80}, {u2["cx"] + 50} {u2["cy"] + u2["ry"]}" fill="none" stroke="#E53935" stroke-width="1.5" stroke-dasharray="5,4" marker-end="url(#arrow-ext)"/>')
    svg.append(f'<rect x="463" y="345" width="84" height="26" rx="3" fill="#FFFFFF" stroke="#E53935" stroke-width="0.8"/>')
    svg.append(f'<text x="505" y="357" class="rel-ext-lbl">«extend»</text>')
    svg.append(f'<text x="505" y="368" class="uc-sub" font-size="8.5px" fill="#B71C1C">(khi mất mạng)</text>')

    # 3. UC-08 includes UC-09 (Clustering & Priority Ranking)
    # Ngang hàng tại cy=290: Mũi tên từ UC-08 (bên phải) sang UC-09 (bên trái)
    u8 = uc_map["uc_08"]
    u9 = uc_map["uc_09"]
    svg.append(f'<line x1="{u8["cx"] - u8["rx"]}" y1="{u8["cy"]}" x2="{u9["cx"] + u9["rx"]}" y2="{u9["cy"]}" stroke="#6A1B9A" stroke-width="1.5" stroke-dasharray="5,4" marker-end="url(#arrow-inc)"/>')
    mid_x_cluster = (u8["cx"] - u8["rx"] + u9["cx"] + u9["rx"]) / 2
    svg.append(f'<rect x="{mid_x_cluster - 32}" y="{u8["cy"] - 22}" width="64" height="16" rx="3" fill="#FFFFFF" stroke="#6A1B9A" stroke-width="0.8"/>')
    svg.append(f'<text x="{mid_x_cluster}" y="{u8["cy"] - 10}" class="rel-lbl" fill="#6A1B9A">«include»</text>')

    # 5. Draw Use Case Ovals & Text (On top of lines)
    for uc in usecases:
        svg.append(f'<ellipse cx="{uc["cx"]}" cy="{uc["cy"]}" rx="{uc["rx"]}" ry="{uc["ry"]}" fill="{uc["fill"]}" stroke="{uc["stroke"]}" stroke-width="1.4"/>')
        svg.append(f'<text x="{uc["cx"]}" y="{uc["cy"] - 3}" class="uc-lbl" fill="{uc["txt"]}">{html.escape(uc["name"])}</text>')
        if uc["sub"]:
            svg.append(f'<text x="{uc["cx"]}" y="{uc["cy"] + 11}" class="uc-sub" fill="{uc["txt"]}">{html.escape(uc["sub"])}</text>')

    # 6. Draw Actors
    for aid, a in actors.items():
        if aid == "act_sms_gw":
            svg.append(f'<rect x="{a["x"]}" y="{a["y"]}" width="{a["w"]}" height="{a["h"]}" rx="6" fill="{a["fill"]}" stroke="{a["stroke"]}" stroke-width="1.8"/>')
            svg.append(f'<text x="{a["x"] + a["w"]/2}" y="{a["y"] + 18}" class="uc-sub" font-weight="bold" fill="#37474F">&laquo;external system&raquo;</text>')
            svg.append(f'<text x="{a["x"] + a["w"]/2}" y="{a["y"] + 36}" class="actor-lbl" fill="#263238" font-size="11px">SMS Gateway /</text>')
            svg.append(f'<text x="{a["x"] + a["w"]/2}" y="{a["y"] + 51}" class="actor-lbl" fill="#263238" font-size="11px">Nhà mạng viễn thông</text>')
        else:
            draw_actor(a["x"] + 25, a["y"] + 20, a["name"], a["fill"], a["stroke"])

    svg.append('</svg>')
    return '\n'.join(svg)


def main():
    print(f"Generating updated {DRAWIO_PATH.name}...")
    xml_content = generate_drawio_xml()
    DRAWIO_PATH.write_text(xml_content, encoding="utf-8")
    print(f"Wrote {len(xml_content)} bytes to {DRAWIO_PATH}")

    print(f"Generating vector PDF {PDF_PATH.name}...")
    svg_content = generate_vector_svg()
    doc = fitz.open(stream=svg_content.encode("utf-8"), filetype="svg")
    pdf_bytes = doc.convert_to_pdf()
    pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pdf_doc.save(str(PDF_PATH))
    print(f"Wrote {PDF_PATH.stat().st_size} bytes to {PDF_PATH}")

    # Export PNG Preview
    png_preview_path = DIAGRAMS_DIR / "usecase_preview.png"
    page = pdf_doc[0]
    pix = page.get_pixmap(dpi=200)
    pix.save(str(png_preview_path))
    print(f"Exported PNG preview to {png_preview_path}")


if __name__ == "__main__":
    main()
