#!/usr/bin/env python3
"""Tạo lại database_erd.drawio và database_erd.pdf chuẩn xác 100% theo schema SQLite thực tế (storage.py & contact_db.md)."""

import html
from pathlib import Path
import xml.etree.ElementTree as ET
import fitz

ROOT = Path(__file__).resolve().parents[1]
DIAGRAMS_DIR = ROOT / "assets" / "diagrams"
DRAWIO_PATH = DIAGRAMS_DIR / "database_erd.drawio"
PDF_PATH = DIAGRAMS_DIR / "database_erd.pdf"


def build_erd_data():
    """Định nghĩa schema 7 bảng CSDL chuẩn xác tuyệt đối theo SQLite backend."""

    # Bố cục 3 cột rộng rãi, khoảng cách giữa các cột 130px:
    # Cột 1 (Trái): messages_dedup (x=40, w=340), server_meta (x=40, w=340) -> x: 40..380
    # Cột 2 (Giữa): reports (x=510, w=400), teams (x=510, w=400) -> x: 510..910
    # Cột 3 (Phải): report_events, operators, sessions (x=1040, w=340) -> x: 1040..1380
    # Gap Cột 1-2: 510 - 380 = 130px
    # Gap Cột 2-3: 1040 - 910 = 130px

    tables = [
        {
            "id": "t_reports",
            "title": "reports (Báo cáo cứu hộ khẩn cấp)",
            "x": 510,
            "y": 50,
            "w": 400,
            "h": 605,
            "fill": "#EDE7F6",
            "stroke": "#512DA8",
            "columns": [
                ("PK  id", "TEXT PRIMARY KEY (Mã SOS duy nhất)", "pk"),
                ("    server_received_at", "TEXT NOT NULL (ISO-8601 UTC)", "def"),
                ("    created_at", "TEXT (Thời điểm tạo tại client)", "def"),
                ("    lat, lng", "REAL (Tọa độ WGS84 GPS hiện trường)", "def"),
                ("    trapped_count", "INTEGER DEFAULT 0 (Số người mắc kẹt)", "def"),
                ("    injured_count", "INTEGER DEFAULT 0 (Số người bị thương)", "def"),
                ("    vulnerable_groups", "TEXT (JSON: trẻ em, người già...)", "def"),
                ("    description", "TEXT (Mô tả hiện trường / khẩn cấp)", "def"),
                ("    ai_tags", "TEXT (JSON kết quả Edge AI on-device)", "def"),
                ("    send_mode", "TEXT (Chế độ gửi: HTTP, Sync, SMS)", "def"),
                ("    status", "TEXT DEFAULT 'processing'", "def"),
                ("    status_version", "INTEGER DEFAULT 1 (Phiên bản đồng bộ)", "def"),
                ("    image_sha256", "TEXT (SHA-256 hash ảnh hiện trường)", "def"),
                ("    image_size_bytes", "INTEGER (Dung lượng ảnh byte)", "def"),
                ("    image_filename, image_url", "TEXT (Tên file & URL xem ảnh)", "def"),
                ("    raw_payload", "TEXT NOT NULL (Canonical RFC 8785)", "def"),
                ("FK  assigned_team_id", "INTEGER [Ref: teams.id]", "fk"),
                ("    location_source", "TEXT ('device' GPS | 'manual')", "def"),
                ("    owner_client_id", "TEXT (Client ID thiết bị sở hữu)", "def"),
                ("    close_reason", "TEXT (Lý do khi status='cancelled')", "def"),
                ("    first_received_at", "TEXT (Thời điểm nhận đầu tính SLA)", "def"),
                ("    status_updated_at", "TEXT (Lần đổi trạng thái gần nhất)", "def"),
                ("    updated_seq", "INTEGER DEFAULT 0 (Seq counter delta)", "def"),
            ],
        },
        {
            "id": "t_dedup",
            "title": "messages_dedup (Chống trùng lặp Outbox)",
            "x": 40,
            "y": 50,
            "w": 340,
            "h": 305,
            "fill": "#EDE7F6",
            "stroke": "#512DA8",
            "columns": [
                ("PK  message_id", "TEXT PRIMARY KEY (UUID outbox)", "pk"),
                ("UQ  client_id", "TEXT NOT NULL (Định danh thiết bị)", "uq"),
                ("UQ  sequence_number", "INTEGER NOT NULL (Tuần tự tăng dần)", "uq"),
                ("    operation_type", "TEXT NOT NULL (CREATE_REPORT...)", "def"),
                ("    payload_hash", "TEXT NOT NULL (RFC 8785 SHA-256)", "def"),
                ("    status", "TEXT NOT NULL (PROCESSED, DUPLICATE...)", "def"),
                ("    error_code", "TEXT (Mã lỗi nếu bị từ chối)", "def"),
                ("    result_data", "TEXT (JSON: record_id, ack token)", "def"),
                ("    processed_at", "TEXT NOT NULL (Thời điểm server xử lý)", "def"),
                ("    created_at", "TEXT NOT NULL (Thời điểm tạo client)", "def"),
                ("    expires_at", "TEXT (Thời điểm hết hạn lưu trữ)", "def"),
            ],
        },
        {
            "id": "t_events",
            "title": "report_events (Nhật ký kiểm toán truy vết)",
            "x": 1040,
            "y": 50,
            "w": 340,
            "h": 280,
            "fill": "#EDE7F6",
            "stroke": "#512DA8",
            "columns": [
                ("PK  id", "INTEGER PRIMARY KEY AUTOINCREMENT", "pk"),
                ("FK  report_id", "TEXT NOT NULL [Ref: reports.id]", "fk"),
                ("    kind", "TEXT NOT NULL (status/assign/note/loc...)", "def"),
                ("    from_value", "TEXT (Giá trị trước thao tác)", "def"),
                ("    to_value", "TEXT (Giá trị sau thao tác)", "def"),
                ("    status_version", "INTEGER (Phiên bản trạng thái)", "def"),
                ("    actor", "TEXT (Điều phối viên / App client)", "def"),
                ("    source", "TEXT NOT NULL (app/sync/sms/dashboard)", "def"),
                ("    note", "TEXT (Ghi chú điều phối / lý do hủy)", "def"),
                ("    created_at", "TEXT NOT NULL (ISO-8601 UTC)", "def"),
            ],
        },
        {
            "id": "t_teams",
            "title": "teams (Đội cứu hộ / Cứu nạn cơ động)",
            "x": 510,
            "y": 710,
            "w": 400,
            "h": 205,
            "fill": "#EDE7F6",
            "stroke": "#512DA8",
            "columns": [
                ("PK  id", "INTEGER PRIMARY KEY AUTOINCREMENT", "pk"),
                ("UQ  name", "TEXT NOT NULL UNIQUE (Tên đội thực địa)", "uq"),
                ("    phone", "TEXT (Số điện thoại liên lạc chỉ huy)", "def"),
                ("    members", "INTEGER (Số lượng thành viên trong đội)", "def"),
                ("    note", "TEXT (Năng lực, phương tiện xuồng/ca nô)", "def"),
                ("    active", "INTEGER NOT NULL DEFAULT 1 (Sẵn sàng)", "def"),
                ("    created_at", "TEXT NOT NULL (ISO-8601 UTC)", "def"),
            ],
        },
        {
            "id": "t_operators",
            "title": "operators (Tài khoản điều phối & Quản trị)",
            "x": 1040,
            "y": 410,
            "w": 340,
            "h": 255,
            "fill": "#EDE7F6",
            "stroke": "#512DA8",
            "columns": [
                ("PK  id", "INTEGER PRIMARY KEY AUTOINCREMENT", "pk"),
                ("UQ  username", "TEXT NOT NULL UNIQUE COLLATE NOCASE", "uq"),
                ("UQ  display_name", "TEXT NOT NULL UNIQUE (Actor log)", "uq"),
                ("    password_hash", "TEXT NOT NULL (PBKDF2-SHA256)", "def"),
                ("    role", "TEXT NOT NULL DEFAULT 'operator'", "def"),
                ("    active", "INTEGER NOT NULL DEFAULT 1 (Hoạt động)", "def"),
                ("    must_change_password", "INTEGER NOT NULL DEFAULT 0", "def"),
                ("    created_at", "TEXT NOT NULL (ISO-8601 UTC)", "def"),
                ("    last_login_at", "TEXT (Lần đăng nhập gần nhất)", "def"),
            ],
        },
        {
            "id": "t_sessions",
            "title": "sessions (Phiên đăng nhập Web Dashboard)",
            "x": 1040,
            "y": 730,
            "w": 340,
            "h": 155,
            "fill": "#EDE7F6",
            "stroke": "#512DA8",
            "columns": [
                ("PK  token_hash", "TEXT PRIMARY KEY (SHA-256 session)", "pk"),
                ("FK  operator_id", "INTEGER [Ref: operators.id]", "fk"),
                ("    operator", "TEXT NOT NULL (Tên hiển thị lúc login)", "def"),
                ("    created_at", "TEXT NOT NULL (Thời điểm cấp phiên)", "def"),
                ("    expires_at", "TEXT NOT NULL (Thời điểm hết hạn)", "def"),
            ],
        },
        {
            "id": "t_meta",
            "title": "server_meta (Metadata đồng bộ hệ thống)",
            "x": 40,
            "y": 430,
            "w": 340,
            "h": 155,
            "fill": "#EDE7F6",
            "stroke": "#512DA8",
            "columns": [
                ("PK  key", "TEXT PRIMARY KEY ('seq', 'epoch'..)", "pk"),
                ("    value", "TEXT NOT NULL (Counter / UUID / Rev)", "def"),
                ("    -- seq", "Bộ đếm tăng dần cho Polling delta", "alt"),
                ("    -- epoch", "Đổi khi reset dữ liệu (Hard sync)", "alt"),
                ("    -- cluster_rev", "Phiên bản đầu vào phân cụm Louvain", "alt"),
            ],
        },
    ]

    relationships = [
        {
            "id": "erd_e1",
            "label": "1 : N (Giao đội: assigned_team_id)",
            "source": "t_teams",
            "target": "t_reports",
            "exit_x": 0.5,
            "exit_y": 0.0,
            "entry_x": 0.5,
            "entry_y": 1.0,
        },
        {
            "id": "erd_e2",
            "label": "1 : N (Events)",
            "source": "t_reports",
            "target": "t_events",
            "exit_x": 1.0,
            "exit_y": 0.2,
            "entry_x": 0.0,
            "entry_y": 0.35,
        },
        {
            "id": "erd_e3",
            "label": "1 : N (Phiên làm việc)",
            "source": "t_operators",
            "target": "t_sessions",
            "exit_x": 0.5,
            "exit_y": 1.0,
            "entry_x": 0.5,
            "entry_y": 0.0,
        },
        {
            "id": "erd_e4",
            "label": "1 : N (Upsert)",
            "source": "t_dedup",
            "target": "t_reports",
            "exit_x": 1.0,
            "exit_y": 0.3,
            "entry_x": 0.0,
            "entry_y": 0.2,
        },
        {
            "id": "erd_e5",
            "label": "Audit: actor",
            "source": "t_operators",
            "target": "t_events",
            "exit_x": 0.5,
            "exit_y": 0.0,
            "entry_x": 0.5,
            "entry_y": 1.0,
        },
    ]

    return tables, relationships


def generate_drawio_xml():
    tables, relationships = build_erd_data()

    tbl_style = (
        "shape=swimlane;fontStyle=1;align=center;verticalAlign=top;"
        "childLayout=stackLayout;horizontal=1;startSize=30;horizontalStack=0;"
        "resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=0;marginBottom=0;"
        "whiteSpace=wrap;html=1;fontFamily=Helvetica;fontSize=11;"
        "fillColor=#EDE7F6;strokeColor=#512DA8;swimlaneFillColor=#FFFFFF;"
    )

    style_map = {
        "pk": (
            "text;strokeColor=none;fillColor=#FFF9C4;align=left;verticalAlign=middle;"
            "spacingLeft=8;spacingRight=4;overflow=hidden;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;"
            "rotatable=0;whiteSpace=wrap;html=1;fontStyle=1;fontSize=10;fontFamily=Helvetica;"
        ),
        "uq": (
            "text;strokeColor=none;fillColor=#E8F5E9;align=left;verticalAlign=middle;"
            "spacingLeft=8;spacingRight=4;overflow=hidden;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;"
            "rotatable=0;whiteSpace=wrap;html=1;fontStyle=1;fontSize=10;fontFamily=Helvetica;"
        ),
        "fk": (
            "text;strokeColor=none;fillColor=#E1F5FE;align=left;verticalAlign=middle;"
            "spacingLeft=8;spacingRight=4;overflow=hidden;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;"
            "rotatable=0;whiteSpace=wrap;html=1;fontStyle=2;fontSize=10;fontFamily=Helvetica;"
        ),
        "def": (
            "text;strokeColor=none;fillColor=#FFFFFF;align=left;verticalAlign=middle;"
            "spacingLeft=8;spacingRight=4;overflow=hidden;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;"
            "rotatable=0;whiteSpace=wrap;html=1;fontSize=10;fontFamily=Helvetica;"
        ),
        "alt": (
            "text;strokeColor=none;fillColor=#F8F9FA;align=left;verticalAlign=middle;"
            "spacingLeft=8;spacingRight=4;overflow=hidden;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;"
            "rotatable=0;whiteSpace=wrap;html=1;fontSize=9;fontStyle=2;fontFamily=Helvetica;fontColor=#546E7A;"
        ),
    }

    mxfile = ET.Element("mxfile", host="app.diagrams.net", agent="Antigravity", version="24.0.0")
    diagram = ET.SubElement(mxfile, "diagram", id="diag-1", name="So-do-Thuc-the-Lien-ket-CSDL-ERD")
    model = ET.SubElement(
        diagram, "mxGraphModel",
        dx="1422", dy="800", grid="1", gridSize="10", guides="1", tooltips="1",
        connect="1", arrows="1", fold="1", page="1", pageScale="1",
        pageWidth="1420", pageHeight="960", math="0", shadow="0"
    )
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")

    for tbl in tables:
        t_cell = ET.SubElement(root, "mxCell", {
            "id": tbl["id"],
            "value": f"Table: {tbl['title']}",
            "style": tbl_style,
            "parent": "1",
            "vertex": "1"
        })
        ET.SubElement(t_cell, "mxGeometry", {
            "x": str(tbl["x"]),
            "y": str(tbl["y"]),
            "width": str(tbl["w"]),
            "height": str(tbl["h"]),
            "as": "geometry"
        })

        for i, (col_name, col_type, ctype) in enumerate(tbl["columns"]):
            c_id = f"{tbl['id']}_c{i+1}"
            c_val = f"{col_name} : {col_type}" if col_type else col_name
            c_style = style_map.get(ctype, style_map["def"])
            y_offset = 30 + i * 25

            row_cell = ET.SubElement(root, "mxCell", {
                "id": c_id,
                "value": c_val,
                "style": c_style,
                "parent": tbl["id"],
                "vertex": "1"
            })
            ET.SubElement(row_cell, "mxGeometry", {
                "x": "0",
                "y": str(y_offset),
                "width": str(tbl["w"]),
                "height": "25",
                "as": "geometry"
            })

    edge_style = "endArrow=diamondThin;endFill=1;startArrow=none;html=1;strokeColor=#455A64;strokeWidth=1.5;fontSize=10;"
    for rel in relationships:
        e_style = edge_style
        if "exit_x" in rel:
            e_style += f"exitX={rel['exit_x']};exitY={rel['exit_y']};exitDx=0;exitDy=0;"
        if "entry_x" in rel:
            e_style += f"entryX={rel['entry_x']};entryY={rel['entry_y']};entryDx=0;entryDy=0;"

        e_cell = ET.SubElement(root, "mxCell", {
            "id": rel["id"],
            "value": rel["label"],
            "style": e_style,
            "parent": "1",
            "edge": "1",
            "source": rel["source"],
            "target": rel["target"]
        })
        ET.SubElement(e_cell, "mxGeometry", {"relative": "1", "as": "geometry"})

    return ET.tostring(mxfile, encoding="utf-8", xml_declaration=True).decode("utf-8")


def generate_vector_svg():
    """Tạo file SVG chuẩn vector hiển thị sắc nét toàn bộ các bảng và mối quan hệ ERD."""
    tables, relationships = build_erd_data()

    W, H = 1420, 960
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
        '''<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M 0 1 L 10 5 L 0 9 z" fill="#37474F"/>
  </marker>
  <marker id="diamond" viewBox="0 0 12 12" refX="6" refY="6" markerWidth="8" markerHeight="8" orient="auto">
    <polygon points="6,1 11,6 6,11 1,6" fill="#37474F" stroke="#37474F" stroke-width="1"/>
  </marker>
  <filter id="shadow" x="-3%" y="-2%" width="106%" height="106%">
    <feDropShadow dx="1" dy="2" stdDeviation="2" flood-color="#000000" flood-opacity="0.08"/>
  </filter>
</defs>
<style>
  .tbl-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 11.5px; font-weight: bold; fill: #FFFFFF; }
  .col-pk { font-family: "SF Mono", Consolas, Menlo, Monaco, monospace; font-size: 9.8px; font-weight: bold; fill: #212121; }
  .col-uq { font-family: "SF Mono", Consolas, Menlo, Monaco, monospace; font-size: 9.8px; font-weight: bold; fill: #1B5E20; }
  .col-fk { font-family: "SF Mono", Consolas, Menlo, Monaco, monospace; font-size: 9.8px; font-style: italic; fill: #0D47A1; }
  .col-def { font-family: "SF Mono", Consolas, Menlo, Monaco, monospace; font-size: 9.8px; fill: #37474F; }
  .col-alt { font-family: "SF Mono", Consolas, Menlo, Monaco, monospace; font-size: 9.2px; font-style: italic; fill: #607D8B; }
  .edge-lbl { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 9.5px; font-weight: 500; fill: #37474F; text-anchor: middle; }
</style>
<rect width="100%" height="100%" fill="#F8F9FA"/>
'''
    ]

    # VẼ TỪNG BẢNG TRƯỚC (TABLE CARDS)
    color_map = {
        "pk": ("#FFF9C4", "col-pk"),
        "uq": ("#E8F5E9", "col-uq"),
        "fk": ("#E1F5FE", "col-fk"),
        "def": ("#FFFFFF", "col-def"),
        "alt": ("#F5F5F5", "col-alt"),
    }

    for tbl in tables:
        x, y, w, h = tbl["x"], tbl["y"], tbl["w"], tbl["h"]
        svg_parts.append(f'<g transform="translate({x}, {y})" filter="url(#shadow)">')
        # Khung toàn bảng
        svg_parts.append(
            f'<rect width="{w}" height="{h}" rx="5" fill="#FFFFFF" stroke="#512DA8" stroke-width="1.8"/>'
        )
        # Tiêu đề bảng (Header banner)
        svg_parts.append(
            f'<path d="M 0 5 Q 0 0 5 0 L {w-5} 0 Q {w} 0 {w} 5 L {w} 30 L 0 30 Z" fill="#512DA8"/>'
        )
        svg_parts.append(
            f'<text x="{w/2}" y="19" class="tbl-title" text-anchor="middle">{html.escape(tbl["title"])}</text>'
        )

        # Các hàng cột (Columns)
        for i, (col_name, col_type, ctype) in enumerate(tbl["columns"]):
            row_y = 30 + i * 25
            bg_col, cls_name = color_map.get(ctype, ("#FFFFFF", "col-def"))
            # Đường gạch phân chia hàng
            svg_parts.append(
                f'<rect y="{row_y}" width="{w}" height="25" fill="{bg_col}" stroke="#E0E0E0" stroke-width="0.5"/>'
            )
            # Text nội dung cột
            col_text = f"{col_name} : {col_type}" if col_type else col_name
            svg_parts.append(
                f'<text x="8" y="{row_y + 16}" class="{cls_name}">{html.escape(col_text)}</text>'
            )

        svg_parts.append('</g>')

    # VẼ CÁC ĐƯỜNG QUAN HỆ SAU CÙNG ĐỂ NẰM TRÊN MỌI BẢNG (RELATIONSHIP EDGES & LABELS)
    table_lookup = {t["id"]: t for t in tables}
    for rel in relationships:
        src = table_lookup[rel["source"]]
        dst = table_lookup[rel["target"]]

        sx = src["x"] + src["w"] * rel["exit_x"]
        sy = src["y"] + src["h"] * rel["exit_y"]
        dx = dst["x"] + dst["w"] * rel["entry_x"]
        dy = dst["y"] + dst["h"] * rel["entry_y"]

        # Đường nối
        if abs(sx - dx) < 15 or abs(sy - dy) < 15:
            path_d = f"M {sx:.1f} {sy:.1f} L {dx:.1f} {dy:.1f}"
            mx = (sx + dx) / 2
            my = (sy + dy) / 2
        else:
            mx = (sx + dx) / 2
            my = (sy + dy) / 2
            path_d = f"M {sx:.1f} {sy:.1f} C {mx:.1f} {sy:.1f}, {mx:.1f} {dy:.1f}, {dx:.1f} {dy:.1f}"

        svg_parts.append(
            f'<path d="{path_d}" fill="none" stroke="#455A64" stroke-width="1.8" '
            f'marker-start="url(#diamond)" marker-end="url(#arrow)"/>'
        )
        # Background cho nhãn quan hệ
        lbl_w = len(rel["label"]) * 6.2 + 16
        svg_parts.append(
            f'<rect x="{mx - lbl_w/2:.1f}" y="{my - 9:.1f}" width="{lbl_w:.1f}" height="18" rx="3" '
            f'fill="#FFFFFF" stroke="#CFD8DC" stroke-width="0.8"/>'
        )
        svg_parts.append(f'<text x="{mx:.1f}" y="{my + 3.5:.1f}" class="edge-lbl">{html.escape(rel["label"])}</text>')

    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


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


if __name__ == "__main__":
    main()
