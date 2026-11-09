#!/usr/bin/env python3
"""
Tạo lại usecase_dashboard.drawio và usecase_dashboard.pdf chuẩn 100% theo UML 2.5.
Tập trung 100% vào nghiệp vụ Điều phối viên (Dispatcher) - Loại bỏ vai trò Quản trị viên (Admin).
Tối ưu hóa hình học tuyệt đối:
1. 7 Use Cases nghiệp vụ điều phối chính nằm thẳng hàng tại Cột 1.
2. 3 Use Cases mở rộng/thuật toán tại Cột 2:
   - UC-09 «include» từ UC-08 (cùng độ cao cy = 190, mũi tên ngang tuyệt đối).
   - UC-15 «extend» từ UC-10 (cùng độ cao cy = 275, mũi tên ngang tuyệt đối).
   - UC-12 tiếp nhận SMS nối ngang sang SMS Gateway (cy = 360).
3. Dispatcher nằm tại vị trí trung tâm (cy = 360), tỏa đều các đường liên kết sang Cột 1.
4. Triệt tiêu hoàn toàn hiện tượng chồng chéo đường nối.
5. Phông chữ Roboto / DejaVu Sans vector sắc nét cho PDF và Draw.io XML.
"""

import html
from pathlib import Path
import xml.etree.ElementTree as ET
import fitz

ROOT = Path(__file__).resolve().parents[1]
DIAGRAMS_DIR = ROOT / "assets" / "diagrams"
DRAWIO_PATH = DIAGRAMS_DIR / "usecase_dashboard.drawio"
PDF_PATH = DIAGRAMS_DIR / "usecase_dashboard.pdf"
PREVIEW_PATH = DIAGRAMS_DIR / "usecase_dashboard_preview.png"


def build_dashboard_data():
    """Tọa độ và kích thước cho từng phần tử của phân hệ Dispatch Dashboard."""
    canvas_w = 1320
    canvas_h = 750

    # System boundary
    sys = {
        "x": 220, "y": 40, "w": 850, "h": 660,
        "title": "PHÂN HỆ ĐIỀU PHỐI WEB (DISPATCH DASHBOARD)"
    }

    # Cột 1: cx = 430 (rx = 120 -> x: 310..550)
    # Cột 2: cx = 830 (rx = 122 -> x: 708..952)
    # Khoảng cách giữa 2 cột: 708 - 550 = 158px (rộng rãi cho nhãn include và extend)
    c1_x = 430
    c2_x = 830

    # Actors
    actors = {
        "act_dispatcher": {
            "name": "Điều phối viên\n(Dispatcher)",
            "x": 65, "y": 315, "w": 50, "h": 90,
            "fill": "#FFF3E0", "stroke": "#F57C00"
        },
        "act_sms_gw": {
            "name": "«external system»\nSMS Gateway /\nNhà mạng viễn thông",
            "x": 1115, "y": sys["y"] + 320 - 32, "w": 145, "h": 65,
            "fill": "#ECEFF1", "stroke": "#546E7A"
        }
    }

    usecases = [
        # --- CỘT 1: Nghiệp vụ điều phối chính (cy = 105 .. 615, bước 85px) ---
        {
            "id": "uc_07", "name": "UC-07: Đăng nhập & Xác thực phiên",
            "sub": "(phiên làm việc điều phối viên)",
            "cx": c1_x, "cy": sys["y"] + 65, "rx": 120, "ry": 25,
            "fill": "#FFFFFF", "stroke": "#F57C00", "txt": "#E65100"
        },
        {
            "id": "uc_08", "name": "UC-08: Giám sát bản đồ sự cố",
            "sub": "(& thứ tự ưu tiên cứu hộ)",
            "cx": c1_x, "cy": sys["y"] + 150, "rx": 120, "ry": 25,
            "fill": "#FFFFFF", "stroke": "#F57C00", "txt": "#E65100"
        },
        {
            "id": "uc_10", "name": "UC-10: Quản lý danh sách báo cáo",
            "sub": "(xác minh tin báo & lọc dữ liệu)",
            "cx": c1_x, "cy": sys["y"] + 235, "rx": 120, "ry": 25,
            "fill": "#FFFFFF", "stroke": "#F57C00", "txt": "#E65100"
        },
        {
            "id": "uc_11", "name": "UC-11: Tiếp nhận báo cáo tổng đài",
            "sub": "(nhập thủ công tin báo hotline)",
            "cx": c1_x, "cy": sys["y"] + 320, "rx": 120, "ry": 25,
            "fill": "#FFFFFF", "stroke": "#F57C00", "txt": "#E65100"
        },
        {
            "id": "uc_13", "name": "UC-13: Phân công & điều động cứu hộ",
            "sub": "(giao nhiệm vụ cho đội cơ động)",
            "cx": c1_x, "cy": sys["y"] + 405, "rx": 120, "ry": 25,
            "fill": "#FFFFFF", "stroke": "#F57C00", "txt": "#E65100"
        },
        {
            "id": "uc_14", "name": "UC-14: Cập nhật tiến độ nhiệm vụ",
            "sub": "(tiến trình cứu nạn tại hiện trường)",
            "cx": c1_x, "cy": sys["y"] + 490, "rx": 120, "ry": 25,
            "fill": "#FFFFFF", "stroke": "#F57C00", "txt": "#E65100"
        },
        {
            "id": "uc_16", "name": "UC-16: Xuất dữ liệu báo cáo cứu hộ",
            "sub": "(kết xuất CSV, GeoJSON, thống kê)",
            "cx": c1_x, "cy": sys["y"] + 575, "rx": 120, "ry": 25,
            "fill": "#FFFFFF", "stroke": "#F57C00", "txt": "#E65100"
        },

        # --- CỘT 2: Thuật toán, Mở rộng & Tự động tiếp nhận ---
        {
            "id": "uc_09", "name": "UC-09: Tự động gom cụm & xếp hạng",
            "sub": "(thuật toán Louvain & P(c))",
            "cx": c2_x, "cy": sys["y"] + 150, "rx": 122, "ry": 25,
            "fill": "#F3E5F5", "stroke": "#6A1B9A", "txt": "#4A148C"
        },
        {
            "id": "uc_15", "name": "UC-15: Bổ sung tọa độ thủ công",
            "sub": "(chấm bản đồ hoặc nhập tọa độ)",
            "cx": c2_x, "cy": sys["y"] + 235, "rx": 122, "ry": 25,
            "fill": "#FFF8E1", "stroke": "#F57C00", "txt": "#E65100"
        },
        {
            "id": "uc_12", "name": "UC-12: Tiếp nhận báo cáo qua SMS",
            "sub": "(Webhook từ SMS Gateway)",
            "cx": c2_x, "cy": sys["y"] + 320, "rx": 122, "ry": 25,
            "fill": "#FFFFFF", "stroke": "#F57C00", "txt": "#E65100"
        },
    ]

    return canvas_w, canvas_h, sys, actors, usecases


def generate_drawio_xml():
    """Tạo tệp XML chuẩn cho diagrams.net (Draw.io)."""
    canvas_w, canvas_h, sys, actors, usecases = build_dashboard_data()

    root = ET.Element("mxfile", host="Electron", agent="Antigravity")
    diagram = ET.SubElement(root, "diagram", id="diag-usecase-dashboard", name="So-do-Use-Case-Chi-tiet-Dashboard")
    model = ET.SubElement(diagram, "mxGraphModel",
                          dx="1400", dy="900", grid="1", gridSize="10",
                          guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1",
                          pageScale="1", pageWidth=str(canvas_w), pageHeight=str(canvas_h),
                          math="0", shadow="0")
    root_cell = ET.SubElement(model, "root")
    ET.SubElement(root_cell, "mxCell", id="0")
    ET.SubElement(root_cell, "mxCell", attrib={"id": "1", "parent": "0"})

    # 1. System boundary
    sys_style = ("shape=swimlane;whiteSpace=wrap;html=1;startSize=32;horizontal=1;"
                 "fillColor=#FFFDE7;strokeColor=#F57C00;strokeWidth=1.5;fontStyle=1;"
                 "fontSize=14;fontFamily=Helvetica;fontColor=#E65100;")
    cell_sys = ET.SubElement(root_cell, "mxCell", attrib={
        "id": "sys_bound", "value": sys["title"], "style": sys_style, "vertex": "1", "parent": "1"
    })
    ET.SubElement(cell_sys, "mxGeometry", attrib={
        "x": str(sys["x"]), "y": str(sys["y"]), "width": str(sys["w"]), "height": str(sys["h"]), "as": "geometry"
    })

    # 2. Use Cases inside sys_bound
    for uc in usecases:
        rel_x = uc["cx"] - uc["rx"] - sys["x"]
        rel_y = uc["cy"] - uc["ry"] - sys["y"]
        val = f"{uc['name']}&#xa;{uc['sub']}"
        style = (f"ellipse;whiteSpace=wrap;html=1;fillColor={uc['fill']};strokeColor={uc['stroke']};"
                 f"strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor={uc['txt']};")
        c = ET.SubElement(root_cell, "mxCell", attrib={
            "id": uc["id"], "value": val, "style": style, "vertex": "1", "parent": "sys_bound"
        })
        ET.SubElement(c, "mxGeometry", attrib={
            "x": str(int(rel_x)), "y": str(int(rel_y)),
            "width": str(int(uc["rx"] * 2)), "height": str(int(uc["ry"] * 2)),
            "as": "geometry"
        })

    # 3. Actors outside sys_bound
    for aid, a in actors.items():
        if aid == "act_sms_gw":
            gw_style = (f"rounded=1;whiteSpace=wrap;html=1;fillColor={a['fill']};strokeColor={a['stroke']};"
                        f"strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontColor=#263238;align=center;")
            c = ET.SubElement(root_cell, "mxCell", attrib={
                "id": aid, "value": a["name"].replace("\n", "&#xa;"), "style": gw_style, "vertex": "1", "parent": "1"
            })
        else:
            act_style = (f"shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;"
                         f"fontFamily=Helvetica;fontSize=12;fontStyle=1;fillColor={a['fill']};strokeColor={a['stroke']};")
            c = ET.SubElement(root_cell, "mxCell", attrib={
                "id": aid, "value": a["name"].replace("\n", "&#xa;"), "style": act_style, "vertex": "1", "parent": "1"
            })
        ET.SubElement(c, "mxGeometry", attrib={
            "x": str(a["x"]), "y": str(a["y"]), "width": str(a["w"]), "height": str(a["h"]), "as": "geometry"
        })

    # 4. Association Edges
    assoc_orange = "endArrow=none;html=1;strokeColor=#F57C00;strokeWidth=1.2;"
    assoc_gray = "endArrow=none;html=1;strokeColor=#546E7A;strokeWidth=1.2;"

    # Dispatcher connections (tới Cột 1)
    for ucid in ["uc_07", "uc_08", "uc_10", "uc_11", "uc_13", "uc_14", "uc_16"]:
        e = ET.SubElement(root_cell, "mxCell", attrib={
            "id": f"e_disp_{ucid}", "value": "", "style": assoc_orange, "edge": "1",
            "source": "act_dispatcher", "target": ucid, "parent": "1"
        })
        ET.SubElement(e, "mxGeometry", attrib={"relative": "1", "as": "geometry"})

    # SMS Gateway to UC-12
    e_sms = ET.SubElement(root_cell, "mxCell", attrib={
        "id": "e_sms_gw_uc12", "value": "", "style": assoc_gray, "edge": "1",
        "source": "uc_12", "target": "act_sms_gw", "parent": "1"
    })
    ET.SubElement(e_sms, "mxGeometry", attrib={"relative": "1", "as": "geometry"})

    # 5. Internal UML Stereotypes: «include» and «extend»
    inc_style_purple = "endArrow=open;dashed=1;html=1;strokeColor=#6A1B9A;strokeWidth=1.3;fontSize=10;fontColor=#6A1B9A;"
    ext_style = "endArrow=open;dashed=1;html=1;strokeColor=#E53935;strokeWidth=1.3;fontSize=10;fontColor=#E53935;"

    # UC-08 includes UC-09 (Gom cụm & ưu tiên Louvain/P(c))
    e_inc = ET.SubElement(root_cell, "mxCell", attrib={
        "id": "e_inc_cluster", "value": "&laquo;include&raquo;", "style": inc_style_purple, "edge": "1",
        "source": "uc_08", "target": "uc_09", "parent": "1"
    })
    ET.SubElement(e_inc, "mxGeometry", attrib={"relative": "1", "as": "geometry"})

    # UC-15 extends UC-10 (Bổ sung tọa độ thủ công khi thiếu GPS)
    e_ext = ET.SubElement(root_cell, "mxCell", attrib={
        "id": "e_ext_geocode", "value": "&laquo;extend&raquo;&#xa;(khi thiếu GPS)",
        "style": ext_style, "edge": "1", "source": "uc_15", "target": "uc_10", "parent": "1"
    })
    ET.SubElement(e_ext, "mxGeometry", attrib={"relative": "1", "as": "geometry"})

    return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")


def generate_svg():
    """Tạo biểu diễn SVG sắc nét với phông Roboto / DejaVu Sans."""
    canvas_w, canvas_h, sys, actors, usecases = build_dashboard_data()
    uc_map = {uc["id"]: uc for uc in usecases}
    font_attr = 'font-family="Roboto, DejaVu Sans, Arial, sans-serif"'

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_w} {canvas_h}" width="{canvas_w}" height="{canvas_h}">')
    svg.append('<defs>')

    # Markers for include / extend
    svg.append('<marker id="arrow-inc-purple" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">')
    svg.append('<path d="M 0 1 L 9 5 L 0 9" fill="none" stroke="#6A1B9A" stroke-width="1.4"/>')
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
    svg.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="8" fill="#FFFDE7" stroke="#F57C00" stroke-width="1.6"/>')
    svg.append(f'<path d="M {bx} {by + 34} L {bx + bw} {by + 34}" stroke="#F57C00" stroke-width="1.2"/>')
    svg.append(f'<text x="{bx + bw/2}" y="{by + 23}" {font_attr} font-size="14px" font-weight="bold" fill="#E65100" letter-spacing="0.5px" text-anchor="middle">{sys["title"]}</text>')

    # 2. Draw Association Edges (Underneath ovals)
    # Dispatcher edges (Nối tới mép trái Cột 1)
    disp = actors["act_dispatcher"]
    disp_x, disp_y = disp["x"] + 25, disp["y"] + 20
    for ucid in ["uc_07", "uc_08", "uc_10", "uc_11", "uc_13", "uc_14", "uc_16"]:
        u = uc_map[ucid]
        svg.append(f'<line x1="{disp_x}" y1="{disp_y}" x2="{u["cx"] - u["rx"]}" y2="{u["cy"]}" stroke="#F57C00" stroke-width="1.2"/>')

    # SMS Gateway edge (Nối ngang sang UC-12)
    gw = actors["act_sms_gw"]
    gw_x, gw_y = gw["x"], gw["y"] + gw["h"] / 2
    u12 = uc_map["uc_12"]
    svg.append(f'<line x1="{u12["cx"] + u12["rx"]}" y1="{u12["cy"]}" x2="{gw_x}" y2="{gw_y}" stroke="#546E7A" stroke-width="1.3"/>')

    # 3. Internal UML Relationships (Chạy ngang hoàn toàn)
    # UC-08 includes UC-09 (cy = 190)
    u8 = uc_map["uc_08"]
    u9 = uc_map["uc_09"]
    svg.append(f'<line x1="{u8["cx"] + u8["rx"]}" y1="{u8["cy"]}" x2="{u9["cx"] - u9["rx"]}" y2="{u9["cy"]}" stroke="#6A1B9A" stroke-width="1.4" stroke-dasharray="5,4" marker-end="url(#arrow-inc-purple)"/>')
    mid_inc_x = (u8["cx"] + u8["rx"] + u9["cx"] - u9["rx"]) / 2
    svg.append(f'<rect x="{mid_inc_x - 30}" y="{u8["cy"] - 18}" width="60" height="16" rx="3" fill="#FFFFFF" stroke="#6A1B9A" stroke-width="0.8"/>')
    svg.append(f'<text x="{mid_inc_x}" y="{u8["cy"] - 6}" {font_attr} font-size="10px" font-weight="bold" fill="#6A1B9A" text-anchor="middle">«include»</text>')

    # UC-15 extends UC-10 (cy = 275) - Extension points to Base!
    u10 = uc_map["uc_10"]
    u15 = uc_map["uc_15"]
    svg.append(f'<line x1="{u15["cx"] - u15["rx"]}" y1="{u15["cy"]}" x2="{u10["cx"] + u10["rx"]}" y2="{u10["cy"]}" stroke="#E53935" stroke-width="1.4" stroke-dasharray="5,4" marker-end="url(#arrow-ext-red)"/>')
    mid_ext_x = (u10["cx"] + u10["rx"] + u15["cx"] - u15["rx"]) / 2
    svg.append(f'<rect x="{mid_ext_x - 42}" y="{u10["cy"] - 22}" width="84" height="26" rx="3" fill="#FFFFFF" stroke="#E53935" stroke-width="0.8"/>')
    svg.append(f'<text x="{mid_ext_x}" y="{u10["cy"] - 10}" {font_attr} font-size="10px" font-weight="bold" fill="#E53935" text-anchor="middle">«extend»</text>')
    svg.append(f'<text x="{mid_ext_x}" y="{u10["cy"] + 1}" {font_attr} font-size="8.5px" fill="#B71C1C" text-anchor="middle">(khi thiếu GPS)</text>')

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
