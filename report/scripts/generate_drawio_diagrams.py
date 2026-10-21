#!/usr/bin/env python3
"""Sinh trọn bộ 19 sơ đồ Draw.io (native XML) cho báo cáo NCKH THS2026-68.
Bao gồm:
  1. usecase.drawio (Use Case tổng thể 3 phân hệ)
  2. usecase_mobile.drawio (Use Case chi tiết Mobile App)
  3. usecase_dashboard.drawio (Use Case chi tiết Web Dashboard & Quản trị)
  4. flowchart.drawio (Lưu đồ 4 làn End-to-End)
  5. flowchart_adaptive_mobile.drawio (Lưu đồ thích ứng mạng & On-device AI)
  6. flowchart_backend_dedup.drawio (Lưu đồ tiếp nhận & chống trùng Backend)
  7. system_architecture.drawio (Kiến trúc tổng thể 3 tầng)
  8. database_erd.drawio (Sơ đồ thực thể liên kết CSDL quan hệ chi tiết)
  9. mobile_architecture.drawio (Kiến trúc phân lớp Clean Architecture Mobile)
  10. deployment_infrastructure.drawio (Sơ đồ triển khai Container Docker Compose)
  11. flow_01_sos_one_touch.drawio (Quy trình SOS 1 chạm định vị nhanh)
  12. flow_02_create_report_edge_ai.drawio (Quy trình tạo báo cáo & Edge AI ONNX/ExecuTorch)
  13. flow_03_adaptive_network_send.drawio (Quy trình gửi thích ứng 4 chế độ theo Bảng 3.2)
  14. flow_04_track_rescue_status.drawio (Quy trình theo dõi tiến trình 4 trạng thái)
  15. flow_05_backend_ingest_dedup.drawio (Quy trình Ingestion, RFC 8785 SHA-256 & Dedup)
  16. flow_06_clustering_priority.drawio (Quy trình phân cụm Louvain, P(c) & Review Queue)
  17. flow_07_manual_intake_location.drawio (Quy trình tiếp nhận tổng đài & gán vị trí)
  18. flow_08_dispatch_lifecycle.drawio (Quy trình vòng đời điều phối, gán đội & đóng ca)
  19. flow_09_ai_training_optimization.drawio (Pipeline huấn luyện, nén & xuất Runtime AI)
"""
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "report" / "assets" / "diagrams"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def create_diagram_xml(title: str, elements: list, w="1654", h="1169") -> str:
    mxfile = ET.Element("mxfile", host="app.diagrams.net", agent="Antigravity", version="24.0.0")
    diagram = ET.SubElement(mxfile, "diagram", id="diag-1", name=title)
    model = ET.SubElement(
        diagram, "mxGraphModel",
        dx="1422", dy="800", grid="1", gridSize="10", guides="1", tooltips="1",
        connect="1", arrows="1", fold="1", page="1", pageScale="1",
        pageWidth=w, pageHeight=h, math="0", shadow="0"
    )
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")

    for elem in elements:
        root.append(elem)

    return ET.tostring(mxfile, encoding="utf-8", xml_declaration=True).decode("utf-8")


def add_cell(cell_id, value, style, parent="1", vertex="1", x=0, y=0, w=120, h=60):
    cell = ET.Element("mxCell", {
        "id": str(cell_id), "value": value, "style": style,
        "parent": str(parent), "vertex": str(vertex)
    })
    ET.SubElement(cell, "mxGeometry", {
        "x": str(x), "y": str(y), "width": str(w), "height": str(h), "as": "geometry"
    })
    return cell


def add_edge(edge_id, value, style, source, target, parent="1", exit_x=None, exit_y=None, entry_x=None, entry_y=None, points=None, offset_y=0):
    if exit_x is not None and exit_y is not None:
        style += f"exitX={exit_x};exitY={exit_y};exitDx=0;exitDy=0;"
    if entry_x is not None and entry_y is not None:
        style += f"entryX={entry_x};entryY={entry_y};entryDx=0;entryDy=0;"
    cell = ET.Element("mxCell", {
        "id": str(edge_id), "value": value, "style": style,
        "parent": str(parent), "edge": "1", "source": str(source), "target": str(target)
    })
    geo = ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
    if offset_y != 0:
        ET.SubElement(geo, "mxPoint", {"as": "offset", "y": str(offset_y)})
    if points:
        arr = ET.SubElement(geo, "Array", {"as": "points"})
        for px, py in points:
            ET.SubElement(arr, "mxPoint", {"x": str(px), "y": str(py)})
    return cell


# Common styling definitions
STYLE_START = "ellipse;whiteSpace=wrap;html=1;fillColor=#4CAF50;strokeColor=#2E7D32;fontColor=#FFFFFF;fontStyle=1;fontFamily=Helvetica;"
STYLE_END = "ellipse;whiteSpace=wrap;html=1;fillColor=#607D8B;strokeColor=#37474F;fontColor=#FFFFFF;fontStyle=1;fontFamily=Helvetica;"
STYLE_ACT = "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1E88E5;fontSize=11;fontFamily=Helvetica;"
STYLE_DEC = "rhombus;whiteSpace=wrap;html=1;fillColor=#FFF3E0;strokeColor=#FB8C00;fontSize=10;fontFamily=Helvetica;"
STYLE_DB = "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;fillColor=#ECEFF1;strokeColor=#455A64;fontSize=10;fontFamily=Helvetica;"
STYLE_AI = "rounded=1;whiteSpace=wrap;html=1;fillColor=#FCE4EC;strokeColor=#D81B60;fontSize=11;fontFamily=Helvetica;"
STYLE_WARN = "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFEBEE;strokeColor=#E53935;fontSize=11;fontFamily=Helvetica;"
STYLE_OK = "rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F5E9;strokeColor=#2E7D32;fontSize=11;fontFamily=Helvetica;"
STYLE_EDGE = "endArrow=classic;html=1;strokeColor=#37474F;strokeWidth=1.3;fontSize=10;fontFamily=Helvetica;"
STYLE_EDGE_DASH = "endArrow=open;dashed=1;html=1;strokeColor=#D81B60;strokeWidth=1.2;fontSize=10;fontFamily=Helvetica;"


# =========================================================================
# 1. USE CASE TỔNG THỂ
# =========================================================================
def generate_usecase():
    nodes = []
    # 1. System Boundary
    nodes.append(add_cell(
        "sys_bound", "HỆ THỐNG HỖ TRỢ CỨU HỘ BÃO LŨ (THS2026-68)",
        "shape=swimlane;whiteSpace=wrap;html=1;startSize=32;horizontal=1;fillColor=#FAFAFA;strokeColor=#37474F;strokeWidth=1.5;fontStyle=1;fontSize=14;fontFamily=Helvetica;fontColor=#263238;",
        x=220, y=40, w=1190, h=880
    ))

    # 2. Subsystems
    subsys_style = "rounded=1;whiteSpace=wrap;html=1;dashed=1;verticalAlign=top;fontStyle=1;fontSize=12;spacingTop=8;strokeWidth=1.2;"
    nodes.append(add_cell(
        "sub_fe", "Phân hệ Di động Biên (Edge Mobile App - Flutter)",
        subsys_style + "fillColor=#F0F7FF;strokeColor=#64B5F6;fontColor=#0D47A1;",
        parent="sys_bound", x=25, y=45, w=525, h=805
    ))
    nodes.append(add_cell(
        "sub_dash", "Phân hệ Điều phối & Quản trị Web (Dispatch Dashboard)",
        subsys_style + "fillColor=#FFFDF5;strokeColor=#FFB74D;fontColor=#E65100;",
        parent="sys_bound", x=575, y=45, w=590, h=805
    ))

    # 3. Actors
    actor_style = "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fontFamily=Helvetica;fontSize=12;fontStyle=1;"
    nodes.append(add_cell("act_citizen", "Người dân /\nNạn nhân", actor_style + "fillColor=#E3F2FD;strokeColor=#1976D2;", x=75, y=200, w=50, h=90))
    nodes.append(add_cell("act_rescuer", "Đội cứu hộ\nthực địa", actor_style + "fillColor=#E8F5E9;strokeColor=#388E3C;", x=75, y=460, w=50, h=90))
    nodes.append(add_cell("act_sms_gw", "«external system»\nSMS Gateway /\nNhà mạng viễn thông", 
                          "rounded=1;whiteSpace=wrap;html=1;fillColor=#ECEFF1;strokeColor=#546E7A;strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontStyle=1;fontColor=#263238;align=center;", 
                          x=30, y=730, w=140, h=65))
    nodes.append(add_cell("act_dispatcher", "Điều phối viên\n(Dispatcher)", actor_style + "fillColor=#FFF3E0;strokeColor=#F57C00;", x=1460, y=300, w=50, h=90))
    nodes.append(add_cell("act_admin", "Quản trị viên\n(Administrator)", actor_style + "fillColor=#EDE7F6;strokeColor=#512DA8;", x=1460, y=725, w=50, h=90))

    # Generalization: Admin --|> Dispatcher
    nodes.append(add_edge("edge_gen_admin", "", "endArrow=block;endFill=0;html=1;strokeColor=#512DA8;strokeWidth=1.5;edgeStyle=orthogonalEdgeStyle;rounded=0;", "act_admin", "act_dispatcher"))

    # 4. Use Cases - Mobile
    uc_fe_style = "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1E88E5;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#0D47A1;fontStyle=1;"
    uc_ai_style = "ellipse;whiteSpace=wrap;html=1;fillColor=#FCE4EC;strokeColor=#D81B60;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#880E4F;fontStyle=1;"
    uc_sms_style = "ellipse;whiteSpace=wrap;html=1;fillColor=#FFEBEE;strokeColor=#E53935;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#B71C1C;fontStyle=1;"

    nodes.append(add_cell("uc_01", "UC-01: Gửi yêu cầu SOS khẩn cấp\n(1 chạm, định vị nhanh)", uc_fe_style, parent="sys_bound", x=35, y=89, w=210, h=52))
    nodes.append(add_cell("uc_02", "UC-02: Tạo báo cáo cứu hộ chi tiết\n(vị trí, số người, ảnh hiện trường)", uc_fe_style, parent="sys_bound", x=35, y=219, w=210, h=52))
    nodes.append(add_cell("uc_03", "UC-03: Nhận diện mức ngập từ ảnh\n(Edge AI on-device MobileNetV3)", uc_ai_style, parent="sys_bound", x=325, y=219, w=210, h=52))
    nodes.append(add_cell("uc_04", "UC-04: Gửi tin nhắn SMS dự phòng\n(khi mất hoàn toàn dữ liệu mạng)", uc_sms_style, parent="sys_bound", x=325, y=364, w=210, h=52))
    nodes.append(add_cell("uc_05", "UC-05: Đồng bộ báo cáo ngoại tuyến\n(tự động gửi khi khôi phục mạng)", uc_fe_style, parent="sys_bound", x=35, y=499, w=210, h=52))
    nodes.append(add_cell("uc_06", "UC-06: Tra cứu trạng thái cứu hộ\n(tiến trình xử lý & vị trí đội)", uc_fe_style, parent="sys_bound", x=35, y=634, w=210, h=52))

    # 5. Use Cases - Dashboard
    uc_dash_style = "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#F57C00;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#E65100;fontStyle=1;"
    uc_algo_style = "ellipse;whiteSpace=wrap;html=1;fillColor=#F3E5F5;strokeColor=#6A1B9A;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#4A148C;fontStyle=1;"
    uc_adm_style = "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#512DA8;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#311B92;fontStyle=1;"

    nodes.append(add_cell("uc_07", "UC-07: Đăng nhập & Xác thực phiên\n(phân quyền Dispatcher / Admin)", uc_dash_style, parent="sys_bound", x=893, y=95, w=224, h=50))
    nodes.append(add_cell("uc_08", "UC-08: Giám sát bản đồ sự cố\n& thứ tự ưu tiên cứu hộ", uc_dash_style, parent="sys_bound", x=893, y=225, w=224, h=50))
    nodes.append(add_cell("uc_13", "UC-13: Phân công & điều động\nđội cứu hộ thực địa", uc_dash_style, parent="sys_bound", x=893, y=355, w=224, h=50))
    nodes.append(add_cell("uc_14", "UC-14: Cập nhật tiến độ nhiệm vụ\n(dispatched -> resolved / close)", uc_dash_style, parent="sys_bound", x=893, y=485, w=224, h=50))
    nodes.append(add_cell("uc_16", "UC-16: Xuất dữ liệu báo cáo\n(CSV / GeoJSON / Thống kê)", uc_dash_style, parent="sys_bound", x=893, y=615, w=224, h=50))
    nodes.append(add_cell("uc_18", "UC-18: Sao lưu & phục hồi CSDL\n(CSDL và ảnh hiện trường)", uc_adm_style, parent="sys_bound", x=893, y=765, w=224, h=50))

    nodes.append(add_cell("uc_10", "UC-10: Quản lý & tra cứu danh sách\nbáo cáo hiện trường", uc_dash_style, parent="sys_bound", x=582, y=160, w=216, h=50))
    nodes.append(add_cell("uc_09", "UC-09: Tự động gom cụm & xếp hạng\nưu tiên cứu hộ (Louvain & P(c))", uc_algo_style, parent="sys_bound", x=580, y=225, w=220, h=50))
    nodes.append(add_cell("uc_11", "UC-11: Tiếp nhận báo cáo tổng đài\n(nhập cứu hộ thủ công)", uc_dash_style, parent="sys_bound", x=582, y=290, w=216, h=50))
    nodes.append(add_cell("uc_12", "UC-12: Tiếp nhận báo cáo qua SMS\n(đồng bộ tự động từ Gateway)", uc_dash_style, parent="sys_bound", x=582, y=420, w=216, h=50))
    nodes.append(add_cell("uc_15", "UC-15: Bổ sung tọa độ thủ công\n(ca thiếu GPS / hàng xem xét)", uc_dash_style, parent="sys_bound", x=582, y=550, w=216, h=50))
    nodes.append(add_cell("uc_17", "UC-17: Quản lý tài khoản điều phối\n(CRUD danh mục cán bộ)", uc_adm_style, parent="sys_bound", x=582, y=690, w=216, h=50))

    # 6. Edges
    edge_style = "endArrow=none;html=1;strokeColor=#455A64;strokeWidth=1.2;"
    inc_style = "endArrow=open;dashed=1;html=1;strokeColor=#D81B60;strokeWidth=1.3;fontSize=10;fontColor=#D81B60;fontStyle=1;"
    ext_style = "endArrow=open;dashed=1;html=1;strokeColor=#E53935;strokeWidth=1.3;fontSize=10;fontColor=#E53935;fontStyle=1;"

    # Citizen
    for ucid in ["uc_01", "uc_02", "uc_05", "uc_06"]:
        nodes.append(add_edge(f"e_c_{ucid}", "", edge_style + "strokeColor=#1976D2;", "act_citizen", ucid))

    # Rescuer
    for ucid in ["uc_01", "uc_02", "uc_05", "uc_06"]:
        nodes.append(add_edge(f"e_r_{ucid}", "", edge_style + "strokeColor=#388E3C;", "act_rescuer", ucid))

    # Includes & Extends
    nodes.append(add_edge("e_inc_ai", "«include»", inc_style, "uc_02", "uc_03"))
    nodes.append(add_edge("e_ext_sms", "«extend»\n(mất mạng)", ext_style, "uc_04", "uc_02", points=[(505, 360)]))
    nodes.append(add_edge("e_inc_cluster", "«include»", inc_style, "uc_08", "uc_09"))

    # SMS Gateway
    nodes.append(add_edge("e_sms_out", "", edge_style + "strokeColor=#E53935;", "act_sms_gw", "uc_04", points=[(180, 410)]))
    nodes.append(add_edge("e_sms_in", "", edge_style + "strokeColor=#546E7A;dashed=1;", "act_sms_gw", "uc_12", points=[(100, 890), (910, 890)]))

    # Dispatcher (Corridor Routing)
    for ucid in ["uc_07", "uc_08", "uc_13", "uc_14", "uc_16"]:
        nodes.append(add_edge(f"e_d_{ucid}", "", edge_style + "strokeColor=#F57C00;", "act_dispatcher", ucid))
    for ucid in ["uc_10", "uc_11", "uc_15"]:
        cy = 225 if ucid == "uc_10" else (355 if ucid == "uc_11" else 615)
        pts = [(1390, cy), (1040, cy)]
        nodes.append(add_edge(f"e_d_{ucid}", "", edge_style + "strokeColor=#F57C00;", "act_dispatcher", ucid, points=pts))

    # Admin
    nodes.append(add_edge("e_a_17", "", edge_style + "strokeColor=#512DA8;", "act_admin", "uc_17", points=[(1390, 755), (1040, 755)]))
    nodes.append(add_edge("e_a_18", "", edge_style + "strokeColor=#512DA8;", "act_admin", "uc_18"))

    return create_diagram_xml("So-do-Use-Case-Tong-The", nodes, w="1600", h="950")


# =========================================================================
# 2. USE CASE CHI TIẾT MOBILE APP
# =========================================================================
def generate_usecase_mobile():
    nodes = []
    nodes.append(add_cell("sys_bound", "PHÂN HỆ DI ĐỘNG BIÊN (EDGE MOBILE APP - FLUTTER)",
                          "shape=swimlane;whiteSpace=wrap;html=1;startSize=32;horizontal=1;fillColor=#F8F9FA;strokeColor=#1976D2;strokeWidth=1.5;fontStyle=1;fontSize=14;fontFamily=Helvetica;fontColor=#0D47A1;",
                          x=220, y=40, w=850, h=710))

    actor_style = "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fontFamily=Helvetica;fontSize=12;fontStyle=1;"
    nodes.append(add_cell("act_citizen", "Người dân /\nNạn nhân", actor_style + "fillColor=#E3F2FD;strokeColor=#1976D2;", x=65, y=200, w=50, h=90))
    nodes.append(add_cell("act_rescuer", "Đội cứu hộ\nthực địa", actor_style + "fillColor=#E8F5E9;strokeColor=#2E7D32;", x=65, y=555, w=50, h=90))
    nodes.append(add_cell("act_sms_gw", "«external system»\nSMS Gateway /\nNhà mạng viễn thông",
                          "rounded=1;whiteSpace=wrap;html=1;fillColor=#ECEFF1;strokeColor=#546E7A;strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontColor=#263238;align=center;",
                          x=1115, y=353, w=145, h=65))

    uc_c1_x = 90
    uc_c2_x = 490

    # Cột 1: Người dân
    nodes.append(add_cell("uc_01", "UC-01: Gửi yêu cầu SOS khẩn cấp\n(1 chạm, tọa độ GPS & mã thiết bị)",
                          "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1E88E5;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#0D47A1;",
                          parent="sys_bound", x=uc_c1_x, y=58, w=240, h=50))
    nodes.append(add_cell("uc_02", "UC-02: Tạo báo cáo cứu hộ chi tiết\n(số người kẹt, bị thương, nhóm yếu thế)",
                          "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1E88E5;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#0D47A1;",
                          parent="sys_bound", x=uc_c1_x, y=144, w=240, h=50))
    nodes.append(add_cell("uc_06", "UC-06: Tra cứu trạng thái cứu hộ\n(tiến trình xử lý & phản hồi thực địa)",
                          "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1E88E5;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#0D47A1;",
                          parent="sys_bound", x=uc_c1_x, y=230, w=240, h=50))
    nodes.append(add_cell("uc_09m", "UC-09M: Tra cứu cẩm nang & điểm trú\n(bản đồ vùng an toàn & kỹ năng sinh tồn)",
                          "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1E88E5;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#0D47A1;",
                          parent="sys_bound", x=uc_c1_x, y=316, w=240, h=50))

    # Cột 1: Dùng chung (Offline Sync)
    nodes.append(add_cell("uc_05", "UC-05: Đồng bộ dữ liệu ngoại tuyến\n(tự động gửi lại từ Outbox khi có mạng)",
                          "ellipse;whiteSpace=wrap;html=1;fillColor=#EDE7F6;strokeColor=#5E35B1;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#311B92;",
                          parent="sys_bound", x=uc_c1_x, y=402, w=240, h=50))

    # Cột 1: Đội cứu hộ
    nodes.append(add_cell("uc_07m", "UC-07M: Tiếp nhận nhiệm vụ cứu nạn\n(danh sách ca cứu trợ, lộ trình & bản đồ)",
                          "ellipse;whiteSpace=wrap;html=1;fillColor=#E8F5E9;strokeColor=#2E7D32;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#1B5E20;",
                          parent="sys_bound", x=uc_c1_x, y=488, w=240, h=50))
    nodes.append(add_cell("uc_08m", "UC-08M: Cập nhật tiến độ hiện trường\n(đang tiếp cận, đã giải cứu nạn nhân)",
                          "ellipse;whiteSpace=wrap;html=1;fillColor=#E8F5E9;strokeColor=#2E7D32;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#1B5E20;",
                          parent="sys_bound", x=uc_c1_x, y=574, w=240, h=50))
    nodes.append(add_cell("uc_11m", "UC-11M: Báo cáo kết quả & xin chi viện\n(đánh giá hiện trạng & yêu cầu thêm nhân lực)",
                          "ellipse;whiteSpace=wrap;html=1;fillColor=#E8F5E9;strokeColor=#2E7D32;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#1B5E20;",
                          parent="sys_bound", x=uc_c1_x, y=660, w=240, h=50))

    # Cột 2: AI, Adaptivity, SMS
    nodes.append(add_cell("uc_03", "UC-03: Nhận diện mức ngập từ ảnh\n(Edge AI on-device MobileNetV3)",
                          "ellipse;whiteSpace=wrap;html=1;fillColor=#FCE4EC;strokeColor=#D81B60;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#880E4F;",
                          parent="sys_bound", x=uc_c2_x, y=110, w=244, h=50))
    nodes.append(add_cell("uc_10m", "UC-10M: Truyền dữ liệu thích ứng\n(ảnh gốc / nén JPEG / metadata theo mạng)",
                          "ellipse;whiteSpace=wrap;html=1;fillColor=#E1F5FE;strokeColor=#0288D1;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#01579B;",
                          parent="sys_bound", x=uc_c2_x, y=205, w=244, h=50))
    nodes.append(add_cell("uc_04", "UC-04: Gửi tin nhắn SMS dự phòng\n(khi mất hoàn toàn dữ liệu Internet)",
                          "ellipse;whiteSpace=wrap;html=1;fillColor=#FFEBEE;strokeColor=#E53935;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#B71C1C;",
                          parent="sys_bound", x=uc_c2_x, y=345, w=244, h=52))

    # Association Edges
    assoc_blue = "endArrow=none;html=1;strokeColor=#1976D2;strokeWidth=1.2;"
    assoc_green = "endArrow=none;html=1;strokeColor=#2E7D32;strokeWidth=1.2;"
    assoc_red = "endArrow=none;html=1;strokeColor=#E53935;strokeWidth=1.2;"

    for ucid in ["uc_01", "uc_02", "uc_06", "uc_09m", "uc_05"]:
        nodes.append(add_edge(f"e_cit_{ucid}", "", assoc_blue, "act_citizen", ucid))

    for ucid in ["uc_05", "uc_07m", "uc_08m", "uc_11m"]:
        nodes.append(add_edge(f"e_res_{ucid}", "", assoc_green, "act_rescuer", ucid))

    nodes.append(add_edge("e_sms_gw_uc04", "", assoc_red, "uc_04", "act_sms_gw"))

    # UML include and extend
    inc_style_pink = "endArrow=open;dashed=1;html=1;strokeColor=#D81B60;strokeWidth=1.3;fontSize=10;fontColor=#D81B60;"
    inc_style_blue = "endArrow=open;dashed=1;html=1;strokeColor=#0288D1;strokeWidth=1.3;fontSize=10;fontColor=#0288D1;"
    ext_style = "endArrow=open;dashed=1;html=1;strokeColor=#E53935;strokeWidth=1.3;fontSize=10;fontColor=#E53935;"

    nodes.append(add_edge("e_inc_ai", "«include»", inc_style_pink, "uc_02", "uc_03"))
    nodes.append(add_edge("e_inc_adapt", "«include»", inc_style_blue, "uc_02", "uc_10m"))
    nodes.append(add_edge("e_ext_sms", "«extend»\n(khi mất mạng)", ext_style, "uc_04", "uc_02"))

    return create_diagram_xml("So-do-Use-Case-Chi-tiet-Mobile-App", nodes, w="1320", h="790")


# =========================================================================
# 3. USE CASE CHI TIẾT WEB DASHBOARD & ADMIN
# =========================================================================
def generate_usecase_dashboard():
    nodes = []
    nodes.append(add_cell("sys_bound", "PHÂN HỆ ĐIỀU PHỐI & QUẢN TRỊ WEB (DISPATCH DASHBOARD)",
                          "shape=swimlane;whiteSpace=wrap;html=1;startSize=32;horizontal=1;fillColor=#FFFDE7;strokeColor=#F57C00;strokeWidth=1.5;fontStyle=1;fontSize=14;fontFamily=Helvetica;fontColor=#E65100;",
                          x=220, y=40, w=870, h=680))

    actor_style = "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fontFamily=Helvetica;fontSize=12;fontStyle=1;"
    nodes.append(add_cell("act_dispatcher", "Điều phối viên\n(Dispatcher)", actor_style + "fillColor=#FFF3E0;strokeColor=#F57C00;", x=65, y=270, w=50, h=90))
    nodes.append(add_cell("act_admin", "Quản trị viên\n(Administrator)", actor_style + "fillColor=#EDE7F6;strokeColor=#512DA8;", x=1150, y=510, w=50, h=90))
    nodes.append(add_cell("act_sms_gw", "«external system»\nSMS Gateway /\nNhà mạng viễn thông",
                          "rounded=1;whiteSpace=wrap;html=1;fillColor=#ECEFF1;strokeColor=#546E7A;strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontColor=#263238;align=center;",
                          x=1115, y=333, w=145, h=65))

    uc_c1_x = 90
    uc_c2_x = 490

    # Cột 1: Nghiệp vụ điều phối chính
    nodes.append(add_cell("uc_07", "UC-07: Đăng nhập & Xác thực phiên\n(phân quyền Dispatcher / Admin)",
                          "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#F57C00;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#E65100;",
                          parent="sys_bound", x=uc_c1_x, y=55, w=240, h=50))
    nodes.append(add_cell("uc_08", "UC-08: Giám sát bản đồ sự cố\n(& thứ tự ưu tiên cứu hộ)",
                          "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#F57C00;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#E65100;",
                          parent="sys_bound", x=uc_c1_x, y=145, w=240, h=50))
    nodes.append(add_cell("uc_10", "UC-10: Quản lý danh sách báo cáo\n(xác minh tin báo & lọc dữ liệu)",
                          "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#F57C00;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#E65100;",
                          parent="sys_bound", x=uc_c1_x, y=235, w=240, h=50))
    nodes.append(add_cell("uc_11", "UC-11: Tiếp nhận báo cáo tổng đài\n(nhập thủ công tin báo hotline)",
                          "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#F57C00;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#E65100;",
                          parent="sys_bound", x=uc_c1_x, y=325, w=240, h=50))
    nodes.append(add_cell("uc_13", "UC-13: Phân công & điều động cứu hộ\n(giao nhiệm vụ cho đội cơ động)",
                          "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#F57C00;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#E65100;",
                          parent="sys_bound", x=uc_c1_x, y=415, w=240, h=50))
    nodes.append(add_cell("uc_14", "UC-14: Cập nhật tiến độ nhiệm vụ\n(tiến trình cứu nạn tại hiện trường)",
                          "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#F57C00;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#E65100;",
                          parent="sys_bound", x=uc_c1_x, y=505, w=240, h=50))
    nodes.append(add_cell("uc_16", "UC-16: Xuất dữ liệu báo cáo cứu hộ\n(kết xuất CSV, GeoJSON, thống kê)",
                          "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#F57C00;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#E65100;",
                          parent="sys_bound", x=uc_c1_x, y=595, w=240, h=50))

    # Cột 2: Thuật toán & Quản trị
    nodes.append(add_cell("uc_09", "UC-09: Tự động gom cụm & xếp hạng\n(thuật toán Louvain & P(c))",
                          "ellipse;whiteSpace=wrap;html=1;fillColor=#F3E5F5;strokeColor=#6A1B9A;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#4A148C;",
                          parent="sys_bound", x=uc_c2_x, y=145, w=244, h=50))
    nodes.append(add_cell("uc_15", "UC-15: Bổ sung tọa độ thủ công\n(chấm bản đồ hoặc nhập tọa độ)",
                          "ellipse;whiteSpace=wrap;html=1;fillColor=#FFF8E1;strokeColor=#F57C00;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#E65100;",
                          parent="sys_bound", x=uc_c2_x, y=235, w=244, h=50))
    nodes.append(add_cell("uc_12", "UC-12: Tiếp nhận báo cáo qua SMS\n(Webhook từ SMS Gateway)",
                          "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#F57C00;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#E65100;",
                          parent="sys_bound", x=uc_c2_x, y=325, w=244, h=50))
    nodes.append(add_cell("uc_17", "UC-17: Quản trị tài khoản điều phối\n(CRUD operators & phân quyền)",
                          "ellipse;whiteSpace=wrap;html=1;fillColor=#EDE7F6;strokeColor=#512DA8;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#311B92;",
                          parent="sys_bound", x=uc_c2_x, y=505, w=244, h=50))
    nodes.append(add_cell("uc_18", "UC-18: Sao lưu, phục hồi & kiểm toán\n(CSDL & nhật ký hệ thống Audit Logs)",
                          "ellipse;whiteSpace=wrap;html=1;fillColor=#EDE7F6;strokeColor=#512DA8;strokeWidth=1.3;fontFamily=Helvetica;fontSize=11;fontColor=#311B92;",
                          parent="sys_bound", x=uc_c2_x, y=595, w=244, h=50))

    # Association Edges
    assoc_orange = "endArrow=none;html=1;strokeColor=#F57C00;strokeWidth=1.2;"
    assoc_purple = "endArrow=none;html=1;strokeColor=#512DA8;strokeWidth=1.2;"
    assoc_gray = "endArrow=none;html=1;strokeColor=#546E7A;strokeWidth=1.2;"

    for ucid in ["uc_07", "uc_08", "uc_10", "uc_11", "uc_13", "uc_14", "uc_16"]:
        nodes.append(add_edge(f"e_disp_{ucid}", "", assoc_orange, "act_dispatcher", ucid))

    for ucid in ["uc_17", "uc_18"]:
        nodes.append(add_edge(f"e_adm_{ucid}", "", assoc_purple, "act_admin", ucid))

    nodes.append(add_edge("e_sms_gw_uc12", "", assoc_gray, "uc_12", "act_sms_gw"))

    # Generalization: Administrator -> Dispatcher
    gen_style = "endArrow=block;endFill=0;html=1;strokeColor=#512DA8;strokeWidth=1.6;edgeStyle=orthogonalEdgeStyle;rounded=0;fontSize=10;fontColor=#512DA8;"
    nodes.append(add_edge("e_gen_admin_disp", "Kế thừa quyền điều phối", gen_style, "act_admin", "act_dispatcher"))

    # UML include and extend
    inc_style_purple = "endArrow=open;dashed=1;html=1;strokeColor=#6A1B9A;strokeWidth=1.3;fontSize=10;fontColor=#6A1B9A;"
    ext_style = "endArrow=open;dashed=1;html=1;strokeColor=#E53935;strokeWidth=1.3;fontSize=10;fontColor=#E53935;"

    nodes.append(add_edge("e_inc_cluster", "«include»", inc_style_purple, "uc_08", "uc_09"))
    nodes.append(add_edge("e_ext_geocode", "«extend»\n(khi thiếu GPS)", ext_style, "uc_15", "uc_10"))

    return create_diagram_xml("So-do-Use-Case-Chi-tiet-Dashboard", nodes, w="1360", h="820")


# =========================================================================
# 4. FLOWCHART TỔNG THỂ 4 LÀN
# =========================================================================
def generate_flowchart():
    nodes = []
    lane_style = "shape=swimlane;whiteSpace=wrap;html=1;startSize=28;fontStyle=1;fontSize=12;fontFamily=Helvetica;"
    nodes.append(add_cell("lane_mobile", "ỨNG DỤNG DI ĐỘNG (EDGE MOBILE APP)", lane_style + "fillColor=#E3F2FD;strokeColor=#1976D2;", x=40, y=40, w=420, h=1060))
    nodes.append(add_cell("lane_server", "MÁY CHỦ TIẾP NHẬN & DEDUP (FASTAPI / SQLITE)", lane_style + "fillColor=#EDE7F6;strokeColor=#512DA8;", x=500, y=40, w=450, h=1060))
    nodes.append(add_cell("lane_core", "LÕI PHÂN CỤM & ƯU TIÊN (RESCUE_CORE)", lane_style + "fillColor=#EFEBE9;strokeColor=#5D4037;", x=990, y=40, w=420, h=1060))
    nodes.append(add_cell("lane_dash", "ĐIỀU PHỐI VIÊN & ĐỘI CỨU HỘ (DASHBOARD)", lane_style + "fillColor=#FFF8E1;strokeColor=#F57C00;", x=1450, y=40, w=420, h=1060))

    # Lane 1: Mobile Flow
    nodes.append(add_cell("m_start", "Bắt đầu\n(Mở App)", STYLE_START, parent="lane_mobile", x=160, y=50, w=100, h=40))
    nodes.append(add_cell("m_choose", "Chọn: Gửi SOS 1 chạm\nhoặc Báo cáo chi tiết", STYLE_ACT, parent="lane_mobile", x=120, y=110, w=180, h=45))
    nodes.append(add_cell("m_ai", "Chụp ảnh -> On-device AI\n(MobileNetV3 ONNX/ExecuTorch)\n-> Mức ngập & Confidence", STYLE_AI, parent="lane_mobile", x=120, y=180, w=180, h=55))
    nodes.append(add_cell("m_form", "Nhập tọa độ (GPS/tay),\nsố người kẹt, bị thương,\nnhóm yếu thế -> Urgency score", STYLE_ACT, parent="lane_mobile", x=120, y=260, w=180, h=50))
    nodes.append(add_cell("m_hive", "Ghi Outbox (Hive)\nStore-and-Forward\n(RFC 8785 SHA-256 hash)", STYLE_DB, parent="lane_mobile", x=135, y=335, w=150, h=55))
    nodes.append(add_cell("m_probe", "Đo throughput\n(GET /probe 64 KB)", STYLE_ACT, parent="lane_mobile", x=135, y=415, w=150, h=40))
    nodes.append(add_cell("m_net_dec", "Đánh giá mạng\n& Confidence AI", STYLE_DEC, parent="lane_mobile", x=140, y=480, w=140, h=65))
    
    nodes.append(add_cell("m_sms", "Gửi SMS dự phòng\ntới Gateway\n(kèm pending Outbox)", STYLE_WARN, parent="lane_mobile", x=20, y=575, w=130, h=50))
    nodes.append(add_cell("m_meta_only", "Gửi chỉ Metadata JSON\n(POST /sync/messages)", STYLE_ACT, parent="lane_mobile", x=160, y=575, w=140, h=50))
    nodes.append(add_cell("m_img_post", "Nén/giữ ảnh + Meta\n(POST /api/reports multipart)", STYLE_ACT, parent="lane_mobile", x=280, y=650, w=130, h=50))

    nodes.append(add_cell("m_wait_ack", "Nhận phản hồi ACK\n& cập nhật synced=true", STYLE_ACT, parent="lane_mobile", x=135, y=730, w=150, h=45))
    nodes.append(add_cell("m_poll", "Polling 15s trạng thái\n(GET /api/reports/status)\nnhận tiến trình cứu hộ", STYLE_ACT, parent="lane_mobile", x=135, y=805, w=150, h=50))
    nodes.append(add_cell("m_end", "Kết thúc\n(Được cứu / Hoàn tất)", STYLE_END, parent="lane_mobile", x=160, y=890, w=100, h=40))

    # Lane 2: Server Flow
    nodes.append(add_cell("s_recv", "Tiếp nhận Request\n(Sync batch / Reports / SMS)", STYLE_ACT, parent="lane_server", x=140, y=180, w=170, h=45))
    nodes.append(add_cell("s_val", "Kiểm tra Header version,\nbounds size & tính canonical\nSHA-256 payload", STYLE_ACT, parent="lane_server", x=140, y=250, w=170, h=55))
    nodes.append(add_cell("s_dedup_dec", "Tra cứu messages_dedup\n(message_id, hash, seq)", STYLE_DEC, parent="lane_server", x=145, y=330, w=160, h=70))
    nodes.append(add_cell("s_dup", "Trùng id & hash:\nTrả ACK duplicate cũ\n(Idempotent, không ghi đè)", STYLE_OK, parent="lane_server", x=20, y=430, w=135, h=55))
    nodes.append(add_cell("s_rej", "Trùng id khác hash /\ntái sử dụng sequence:\nTừ chối 409 Conflict", STYLE_WARN, parent="lane_server", x=295, y=430, w=135, h=55))
    nodes.append(add_cell("s_tx", "Thao tác hợp lệ:\nMở DB Transaction,\nKiểm tra report_owner\n(Merge ảnh/trường trống)", STYLE_ACT, parent="lane_server", x=140, y=515, w=170, h=65))
    nodes.append(add_cell("s_db", "Lưu SQLite: reports,\nmessages_dedup, files ảnh;\nGhi log report_events", STYLE_DB, parent="lane_server", x=145, y=610, w=160, h=60))
    nodes.append(add_cell("s_meta", "Tăng version dữ liệu\ntrong server_meta\n(đánh dấu cụm stale)", STYLE_ACT, parent="lane_server", x=145, y=700, w=160, h=45))
    nodes.append(add_cell("s_ack", "Trả HTTP Response\n(accepted / 201 Created)", STYLE_ACT, parent="lane_server", x=145, y=770, w=160, h=40))

    # Lane 3: Core Clustering Flow
    nodes.append(add_cell("c_trig", "Kích hoạt phân cụm\n(Polling Dashboard /\nbackground warmup)", STYLE_ACT, parent="lane_core", x=130, y=200, w=160, h=45))
    nodes.append(add_cell("c_ver_dec", "Kiểm tra ETag /\ncluster_version đổi?", STYLE_DEC, parent="lane_core", x=140, y=275, w=140, h=60))
    nodes.append(add_cell("c_304", "Không đổi: Trả 304\nNot Modified (ETag)", STYLE_ACT, parent="lane_core", x=20, y=360, w=120, h=45))
    nodes.append(add_cell("c_fetch", "Có đổi: Lấy danh sách\nbáo cáo active_only\n(bỏ resolved/cancelled)", STYLE_ACT, parent="lane_core", x=140, y=360, w=160, h=50))
    nodes.append(add_cell("c_adapt", "Adapter to_report_v2:\nTrích xuất [F, U, N, V],\nTách ca thiếu tọa độ", STYLE_ACT, parent="lane_core", x=140, y=435, w=160, h=50))
    nodes.append(add_cell("c_rev", "Đưa ca thiếu GPS vào\nHàng xem xét (Review Queue)", "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF3E0;strokeColor=#FB8C00;fontSize=11;fontFamily=Helvetica;", parent="lane_core", x=20, y=515, w=140, h=50))
    nodes.append(add_cell("c_graph", "Xây dựng ma trận tương đồng\nC_ij (khoảng cách Haversine,\nmức ngập, độ khẩn cấp)", STYLE_ACT, parent="lane_core", x=180, y=515, w=170, h=55))
    nodes.append(add_cell("c_louvain", "Phân cụm cộng đồng Louvain\n& Xác định clusterKey\n(ID nhỏ nhất trong cụm)", STYLE_ACT, parent="lane_core", x=180, y=595, w=170, h=55))
    nodes.append(add_cell("c_score", "Tính điểm ưu tiên P(c)\ncho từng cụm -> Xếp hạng cụm\n& Ghi cache Snapshot", STYLE_ACT, parent="lane_core", x=140, y=675, w=160, h=50))
    nodes.append(add_cell("c_resp", "Trả JSON cụm + ETag\ncho Dashboard", STYLE_ACT, parent="lane_core", x=140, y=750, w=160, h=40))

    # Lane 4: Dashboard Flow
    nodes.append(add_cell("d_login", "Đăng nhập Dashboard\n(Phiên làm việc Operator)", STYLE_ACT, parent="lane_dash", x=130, y=100, w=160, h=45))
    nodes.append(add_cell("d_poll", "Polling 5s (/changes)\n& Cập nhật bản đồ Leaflet\n+ Hàng xem xét / Cụm", STYLE_ACT, parent="lane_dash", x=130, y=170, w=160, h=50))
    nodes.append(add_cell("d_view", "Chọn cụm/báo cáo:\nXem ảnh, nhãn AI, vị trí,\nsố nạn nhân, gọi xác minh", STYLE_ACT, parent="lane_dash", x=130, y=245, w=160, h=55))
    nodes.append(add_cell("d_loc_sup", "Bổ sung vị trí thủ công\n(nếu ca thuộc Review Queue)", STYLE_ACT, parent="lane_dash", x=130, y=325, w=160, h=45))
    nodes.append(add_cell("d_assign", "Giao đội cứu hộ (teams)\n& Chuyển status -> dispatched\n(tăng statusVersion)", STYLE_OK, parent="lane_dash", x=130, y=395, w=160, h=55))
    nodes.append(add_cell("d_field", "Đội cứu hộ nhận lệnh,\ntiếp cận hiện trường,\ntriển khai ứng cứu", STYLE_ACT, parent="lane_dash", x=130, y=475, w=160, h=50))
    nodes.append(add_cell("d_res_dec", "Kết quả cứu hộ\ntại hiện trường?", STYLE_DEC, parent="lane_dash", x=145, y=550, w=130, h=60))
    nodes.append(add_cell("d_ok", "Thành công: Cập nhật\nstatus -> resolved", STYLE_OK, parent="lane_dash", x=40, y=635, w=140, h=45))
    nodes.append(add_cell("d_cancel", "Hủy / Tin giả: Cập nhật\nstatus -> cancelled\n(bắt buộc chọn reason)", STYLE_WARN, parent="lane_dash", x=210, y=635, w=140, h=50))
    nodes.append(add_cell("d_log", "Hệ thống ghi report_events\n(actor, action, timestamp);\nLoại khỏi active clusters", STYLE_ACT, parent="lane_dash", x=130, y=715, w=160, h=50))
    nodes.append(add_cell("d_export", "Xuất báo cáo tổng kết\n(CSV / GeoJSON / Stats)", STYLE_ACT, parent="lane_dash", x=130, y=790, w=160, h=45))

    # Connectors
    nodes.append(add_edge("fl_m1", "", STYLE_EDGE, "m_start", "m_choose"))
    nodes.append(add_edge("fl_m2", "", STYLE_EDGE, "m_choose", "m_ai"))
    nodes.append(add_edge("fl_m3", "", STYLE_EDGE, "m_ai", "m_form"))
    nodes.append(add_edge("fl_m4", "", STYLE_EDGE, "m_form", "m_hive"))
    nodes.append(add_edge("fl_m5", "", STYLE_EDGE, "m_hive", "m_probe"))
    nodes.append(add_edge("fl_m6", "", STYLE_EDGE, "m_probe", "m_net_dec"))
    nodes.append(add_edge("fl_m7", "Mất mạng", STYLE_EDGE, "m_net_dec", "m_sms"))
    nodes.append(add_edge("fl_m8", "Yếu / conf cao", STYLE_EDGE, "m_net_dec", "m_meta_only"))
    nodes.append(add_edge("fl_m9", "Tốt / ảnh nén", STYLE_EDGE, "m_net_dec", "m_img_post"))

    nodes.append(add_edge("fl_x1", "Gửi tin", STYLE_EDGE, "m_sms", "s_recv"))
    nodes.append(add_edge("fl_x2", "Sync", STYLE_EDGE, "m_meta_only", "s_recv"))
    nodes.append(add_edge("fl_x3", "Upload", STYLE_EDGE, "m_img_post", "s_recv"))

    nodes.append(add_edge("fl_s1", "", STYLE_EDGE, "s_recv", "s_val"))
    nodes.append(add_edge("fl_s2", "", STYLE_EDGE, "s_val", "s_dedup_dec"))
    nodes.append(add_edge("fl_s3", "Duplicate", STYLE_EDGE, "s_dedup_dec", "s_dup"))
    nodes.append(add_edge("fl_s4", "Xung đột", STYLE_EDGE, "s_dedup_dec", "s_rej"))
    nodes.append(add_edge("fl_s5", "Hợp lệ", STYLE_EDGE, "s_dedup_dec", "s_tx"))
    nodes.append(add_edge("fl_s6", "", STYLE_EDGE, "s_tx", "s_db"))
    nodes.append(add_edge("fl_s7", "", STYLE_EDGE, "s_db", "s_meta"))
    nodes.append(add_edge("fl_s8", "", STYLE_EDGE, "s_meta", "s_ack"))
    nodes.append(add_edge("fl_s9", "ACK", STYLE_EDGE, "s_ack", "m_wait_ack"))
    nodes.append(add_edge("fl_s10", "", STYLE_EDGE, "m_wait_ack", "m_poll"))
    nodes.append(add_edge("fl_s11", "", STYLE_EDGE, "m_poll", "m_end"))

    nodes.append(add_edge("fl_sc1", "Dữ liệu mới", STYLE_EDGE, "s_meta", "c_trig"))
    nodes.append(add_edge("fl_c1", "", STYLE_EDGE, "c_trig", "c_ver_dec"))
    nodes.append(add_edge("fl_c2", "Không đổi", STYLE_EDGE, "c_ver_dec", "c_304"))
    nodes.append(add_edge("fl_c3", "Đổi", STYLE_EDGE, "c_ver_dec", "c_fetch"))
    nodes.append(add_edge("fl_c4", "", STYLE_EDGE, "c_fetch", "c_adapt"))
    nodes.append(add_edge("fl_c5", "Thiếu GPS", STYLE_EDGE, "c_adapt", "c_rev"))
    nodes.append(add_edge("fl_c6", "Có GPS", STYLE_EDGE, "c_adapt", "c_graph"))
    nodes.append(add_edge("fl_c7", "", STYLE_EDGE, "c_graph", "c_louvain"))
    nodes.append(add_edge("fl_c8", "", STYLE_EDGE, "c_louvain", "c_score"))
    nodes.append(add_edge("fl_c9", "", STYLE_EDGE, "c_score", "c_resp"))

    nodes.append(add_edge("fl_cd1", "Cụm & ETag", STYLE_EDGE, "c_resp", "d_poll"))
    nodes.append(add_edge("fl_d1", "", STYLE_EDGE, "d_login", "d_poll"))
    nodes.append(add_edge("fl_d2", "", STYLE_EDGE, "d_poll", "d_view"))
    nodes.append(add_edge("fl_d3", "Cần bổ sung vị trí", STYLE_EDGE, "d_view", "d_loc_sup"))
    nodes.append(add_edge("fl_d4", "", STYLE_EDGE, "d_loc_sup", "d_assign"))
    nodes.append(add_edge("fl_d5", "Đã đủ vị trí", STYLE_EDGE, "d_view", "d_assign"))
    nodes.append(add_edge("fl_d6", "", STYLE_EDGE, "d_assign", "d_field"))
    nodes.append(add_edge("fl_d7", "", STYLE_EDGE, "d_field", "d_res_dec"))
    nodes.append(add_edge("fl_d8", "Thành công", STYLE_EDGE, "d_res_dec", "d_ok"))
    nodes.append(add_edge("fl_d9", "Hủy / Lỗi", STYLE_EDGE, "d_res_dec", "d_cancel"))
    nodes.append(add_edge("fl_d10", "", STYLE_EDGE, "d_ok", "d_log"))
    nodes.append(add_edge("fl_d11", "", STYLE_EDGE, "d_cancel", "d_log"))
    nodes.append(add_edge("fl_d12", "", STYLE_EDGE, "d_log", "d_export"))
    nodes.append(add_edge("fl_ds1", "PATCH /status", STYLE_EDGE, "d_assign", "s_recv"))
    nodes.append(add_edge("fl_ds2", "Update status", STYLE_EDGE, "d_log", "s_recv"))

    return create_diagram_xml("Luu-do-Quy-trinh-He-thong", nodes, w="1900", h="1150")


# =========================================================================
# 5. FLOWCHART ADAPTIVE MOBILE
# =========================================================================
def generate_flowchart_adaptive_mobile():
    nodes = []
    nodes.append(add_cell("am_start", "Khởi tạo Báo cáo\n(SOS / Post)", STYLE_START, x=340, y=40, w=160, h=45))
    nodes.append(add_cell("am_img_dec", "Người dùng có\nđính kèm ảnh?", STYLE_DEC, x=350, y=115, w=140, h=65))
    nodes.append(add_cell("am_ai", "Edge AI MobileNetV3 suy luận:\n- Nhãn ngập: non/low/med/high\n- Confidence score", STYLE_AI, x=160, y=210, w=200, h=55))
    nodes.append(add_cell("am_no_img", "Không có ảnh:\nGán nhãn non_flood mặc định", STYLE_ACT, x=480, y=215, w=180, h=45))
    nodes.append(add_cell("am_fields", "Nhập thông tin cứu hộ:\n- Tọa độ GPS (hoặc để trống/nhập tay)\n- Số người kẹt, số người bị thương\n- Nhóm yếu thế (người già, trẻ nhỏ...)\n- Tự động tính Urgency Score", STYLE_ACT, x=310, y=295, w=220, h=75))
    nodes.append(add_cell("am_hive", "Ghi ngay vào Hive Outbox\n(Store-and-forward cục bộ)\nTrạng thái: pending", STYLE_DB, x=345, y=395, w=150, h=60))
    nodes.append(add_cell("am_probe", "Gọi GET /probe (64 KB)\nĐo thông lượng mạng thực tế (kbps)", STYLE_ACT, x=330, y=485, w=180, h=45))
    nodes.append(add_cell("am_net_eval", "Phân loại thông lượng\n& Điều kiện gửi?", STYLE_DEC, x=330, y=560, w=180, h=75))
    
    nodes.append(add_cell("am_sms", "MẤT MẠNG HOÀN TOÀN:\n- Kiểm tra số hotline SMS Android\n- Gửi tin SOS|id:... qua SMS\n- Giữ bản ghi trong Outbox chờ mạng", STYLE_WARN, x=40, y=670, w=200, h=65))
    nodes.append(add_cell("am_meta", "MẠNG YẾU (<50 kbps)\nhoặc (Mạnh & Conf >= 0.90):\n- Gửi metadata JSON qua\n  POST /sync/messages (<=256 KB)", STYLE_ACT, x=265, y=670, w=190, h=65))
    nodes.append(add_cell("am_comp", "MẠNG TRUNG BÌNH (50-1000 kbps):\n- Nén JPEG (max 1024px, q=60)\n- Gửi multipart qua POST /api/reports", "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF8E1;strokeColor=#F57C00;fontSize=11;fontFamily=Helvetica;", x=480, y=670, w=200, h=65))
    nodes.append(add_cell("am_orig", "MẠNG MẠNH (>=1000 kbps & Conf<0.9):\n- Giữ nguyên ảnh gốc\n- Gửi multipart POST /api/reports", STYLE_OK, x=705, y=670, w=210, h=65))

    nodes.append(add_cell("am_res", "Nhận phản hồi từ Server:\n- accepted: Xóa khỏi Outbox, synced=true\n- duplicate: Dùng kết quả cũ, synced=true\n- retry_later / lỗi mạng: Backoff retry\n- rejected: Chuyển dead-letter", STYLE_ACT, x=330, y=775, w=220, h=75))
    nodes.append(add_cell("am_poll", "Khởi động Timer Polling 15s:\nGọi GET /api/reports/status\nđể nhận cập nhật tiến trình điều phối", STYLE_ACT, x=330, y=875, w=220, h=50))
    nodes.append(add_cell("am_end", "Hoàn tất luồng client", STYLE_END, x=390, y=950, w=100, h=40))

    nodes.append(add_edge("ae_1", "", STYLE_EDGE, "am_start", "am_img_dec"))
    nodes.append(add_edge("ae_2", "Có ảnh", STYLE_EDGE, "am_img_dec", "am_ai"))
    nodes.append(add_edge("ae_3", "Không ảnh", STYLE_EDGE, "am_img_dec", "am_no_img"))
    nodes.append(add_edge("ae_4", "", STYLE_EDGE, "am_ai", "am_fields"))
    nodes.append(add_edge("ae_5", "", STYLE_EDGE, "am_no_img", "am_fields"))
    nodes.append(add_edge("ae_6", "", STYLE_EDGE, "am_fields", "am_hive"))
    nodes.append(add_edge("ae_7", "", STYLE_EDGE, "am_hive", "am_probe"))
    nodes.append(add_edge("ae_8", "", STYLE_EDGE, "am_probe", "am_net_eval"))
    nodes.append(add_edge("ae_9", "Mất data", STYLE_EDGE, "am_net_eval", "am_sms"))
    nodes.append(add_edge("ae_10", "<50 kbps", STYLE_EDGE, "am_net_eval", "am_meta"))
    nodes.append(add_edge("ae_11", "50-1000 kbps", STYLE_EDGE, "am_net_eval", "am_comp"))
    nodes.append(add_edge("ae_12", ">=1000 kbps", STYLE_EDGE, "am_net_eval", "am_orig"))
    nodes.append(add_edge("ae_13", "", STYLE_EDGE, "am_sms", "am_res"))
    nodes.append(add_edge("ae_14", "", STYLE_EDGE, "am_meta", "am_res"))
    nodes.append(add_edge("ae_15", "", STYLE_EDGE, "am_comp", "am_res"))
    nodes.append(add_edge("ae_16", "", STYLE_EDGE, "am_orig", "am_res"))
    nodes.append(add_edge("ae_17", "", STYLE_EDGE, "am_res", "am_poll"))
    nodes.append(add_edge("ae_18", "", STYLE_EDGE, "am_poll", "am_end"))

    return create_diagram_xml("Luu-do-Gui-Bao-cao-Thich-ung-App", nodes, w="1000", h="1050")


# =========================================================================
# 6. FLOWCHART BACKEND DEDUP
# =========================================================================
def generate_flowchart_backend_dedup():
    nodes = []
    nodes.append(add_cell("bd_start", "Nhận Request tới Backend\n(Sync batch / Multipart / SMS)", STYLE_START, x=330, y=40, w=180, h=45))
    nodes.append(add_cell("bd_header", "Kiểm tra header bắt buộc:\nX-Message-Contract-Version: 1", STYLE_DEC, x=340, y=110, w=160, h=65))
    nodes.append(add_cell("bd_bounds", "Kiểm tra giới hạn kích thước:\n- Batch <= 50 messages\n- Tổng request <= 256 KiB\n- Meta <= 64 KiB, Ảnh <= 15 MB", STYLE_DEC, x=330, y=200, w=180, h=70))
    nodes.append(add_cell("bd_jcs", "Chuẩn tắc hóa JSON theo RFC 8785\n& Tính mã băm SHA-256 payload", "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#512DA8;fontSize=11;fontFamily=Helvetica;", x=325, y=295, w=190, h=50))
    nodes.append(add_cell("bd_lookup", "Tra cứu bảng messages_dedup\ntheo message_id & client_id", "rounded=1;whiteSpace=wrap;html=1;fillColor=#EDE7F6;strokeColor=#512DA8;fontSize=11;fontFamily=Helvetica;", x=325, y=370, w=190, h=50))
    nodes.append(add_cell("bd_dedup_check", "Kết quả đối chiếu\nchống trùng lặp?", STYLE_DEC, x=335, y=445, w=170, h=70))
    
    nodes.append(add_cell("bd_dup_ok", "TRÙNG MESSAGE_ID & HASH:\n- Phát hiện mất ACK sau commit\n- Trả duplicate + kết quả cũ\n- Không sửa đổi CSDL (Idempotent)", STYLE_OK, x=40, y=545, w=210, h=65))
    nodes.append(add_cell("bd_err_conflict", "TRÙNG ID KHÁC HASH HOẶC TÁI DÙNG SEQ:\n- Trả lỗi 409 Conflict\n- Mã ID_REUSED_WITH_DIFFERENT_PAYLOAD\n  hoặc SEQUENCE_REUSED", STYLE_WARN, x=600, y=545, w=230, h=65))
    nodes.append(add_cell("bd_new_tx", "THAO TÁC HỢP LỆ (MỚI):\nMở SQLite Database Transaction\nKiểm tra quyền sở hữu report_owner", "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#512DA8;fontSize=11;fontFamily=Helvetica;", x=325, y=545, w=190, h=65))

    nodes.append(add_cell("bd_merge_check", "Báo cáo đã có trong DB?", STYLE_DEC, x=345, y=635, w=150, h=65))
    nodes.append(add_cell("bd_merge_apply", "Báo cáo cũ (gộp dữ liệu):\n- Chỉ bổ sung trường còn trống\n- Gắn ảnh nếu trước đó chưa có ảnh\n- Giữ nguyên ảnh đầu tiên và ngày tạo", "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#512DA8;fontSize=11;fontFamily=Helvetica;", x=150, y=725, w=220, h=65))
    nodes.append(add_cell("bd_create_apply", "Báo cáo mới hoàn toàn:\n- Tạo bản ghi mới trong bảng reports\n- Trạng thái khởi tạo: processing\n- Lưu file ảnh vật lý (nếu có)", "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#512DA8;fontSize=11;fontFamily=Helvetica;", x=470, y=725, w=220, h=65))

    nodes.append(add_cell("bd_commit", "Commit Transaction:\n- Ghi vết bảng messages_dedup\n- Ghi nhật ký vào report_events\n- Tăng server_meta version (báo cụm stale)", STYLE_DB, x=320, y=820, w=200, h=70))
    nodes.append(add_cell("bd_ack", "Trả phản hồi HTTP cho Client\n(accepted / 201 Created)", STYLE_OK, x=340, y=915, w=160, h=45))
    nodes.append(add_cell("bd_end", "Kết thúc xử lý", STYLE_END, x=370, y=985, w=100, h=40))
    nodes.append(add_cell("bd_err_bad", "Trả lỗi 400 Bad Request\n(UNSUPPORTED_CONTRACT_VERSION\nhoặc REQUEST_TOO_LARGE)", STYLE_WARN, x=600, y=155, w=230, h=60))

    nodes.append(add_edge("bde_1", "", STYLE_EDGE, "bd_start", "bd_header"))
    nodes.append(add_edge("bde_2", "Sai version", STYLE_EDGE, "bd_header", "bd_err_bad"))
    nodes.append(add_edge("bde_3", "Đúng version", STYLE_EDGE, "bd_header", "bd_bounds"))
    nodes.append(add_edge("bde_4", "Vượt kích thước", STYLE_EDGE, "bd_bounds", "bd_err_bad"))
    nodes.append(add_edge("bde_5", "Hợp lệ", STYLE_EDGE, "bd_bounds", "bd_jcs"))
    nodes.append(add_edge("bde_6", "", STYLE_EDGE, "bd_jcs", "bd_lookup"))
    nodes.append(add_edge("bde_7", "", STYLE_EDGE, "bd_lookup", "bd_dedup_check"))
    nodes.append(add_edge("bde_8", "Duplicate", STYLE_EDGE, "bd_dedup_check", "bd_dup_ok"))
    nodes.append(add_edge("bde_9", "Xung đột", STYLE_EDGE, "bd_dedup_check", "bd_err_conflict"))
    nodes.append(add_edge("bde_10", "Hợp lệ", STYLE_EDGE, "bd_dedup_check", "bd_new_tx"))
    nodes.append(add_edge("bde_11", "", STYLE_EDGE, "bd_new_tx", "bd_merge_check"))
    nodes.append(add_edge("bde_12", "Đã có id", STYLE_EDGE, "bd_merge_check", "bd_merge_apply"))
    nodes.append(add_edge("bde_13", "Chưa có", STYLE_EDGE, "bd_merge_check", "bd_create_apply"))
    nodes.append(add_edge("bde_14", "", STYLE_EDGE, "bd_merge_apply", "bd_commit"))
    nodes.append(add_edge("bde_15", "", STYLE_EDGE, "bd_create_apply", "bd_commit"))
    nodes.append(add_edge("bde_16", "", STYLE_EDGE, "bd_commit", "bd_ack"))
    nodes.append(add_edge("bde_17", "", STYLE_EDGE, "bd_ack", "bd_end"))
    nodes.append(add_edge("bde_18", "", STYLE_EDGE, "bd_dup_ok", "bd_end"))
    nodes.append(add_edge("bde_19", "", STYLE_EDGE, "bd_err_conflict", "bd_end"))
    nodes.append(add_edge("bde_20", "", STYLE_EDGE, "bd_err_bad", "bd_end"))

    return create_diagram_xml("Luu-do-Tiep-nhan-va-Chong-trung-Backend", nodes, w="900", h="1080")


# =========================================================================
# 7. KIẾN TRÚC TỔNG THỂ HỆ THỐNG (SYSTEM ARCHITECTURE)
# =========================================================================
def generate_system_architecture():
    nodes = []

    # Common styles matching sample_ctu_architecture.drawio
    card_base = "rounded=1;whiteSpace=wrap;html=1;strokeWidth=1.5;fontSize=14;fontFamily=Helvetica;arcSize=12;"

    # 4 Perfectly Aligned Column X-Positions
    # Col 1: x = 65,  w = 250 (Center = 190)
    # Col 2: x = 360, w = 250 (Center = 485)
    # Col 3: x = 655, w = 250 (Center = 780)
    # Col 4: x = 950, w = 250 (Center = 1075)

    # =========================================================================
    # TIER 1: THIẾT BỊ DI ĐỘNG BIÊN (EDGE MOBILE CLIENT & ON-DEVICE AI)
    # y = 25..195, h = 170, w = 1180
    # =========================================================================
    t1_box_style = (
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#EBF3FA;strokeColor=#1976D2;"
        "strokeWidth=2;dashed=1;dashPattern=8 4;arcSize=8;fontSize=18;"
    )
    nodes.append(add_cell("tier1_box", "", t1_box_style, x=40, y=25, w=1180, h=170))

    t1_lbl_style = "text;html=1;align=left;verticalAlign=top;spacingLeft=8;spacingTop=4;fontSize=16;fontColor=#0D47A1;fontFamily=Helvetica;"
    nodes.append(add_cell("tier1_label", "<b>Tier 1: Thiết bị Di động Biên &amp; Edge AI (Flutter 3 / Android Client)</b>", t1_lbl_style, x=50, y=28, w=600, h=26))

    # 1.1 SOS 1 chạm (Col 1)
    c_sos = (
        "<b>SOS Khẩn cấp 1 chạm</b><br>"
        "<font style=\"font-size:12px;color:#37474F;\">"
        "• Định vị GPS tức thời<br>"
        "• Gói tin cứu nạn tối giản<br>"
        "• Ưu tiên phát tin khẩn cấp"
        "</font>"
    )
    nodes.append(add_cell("ui_sos", c_sos, card_base + "fillColor=#FFFFFF;strokeColor=#1976D2;", x=65, y=65, w=250, h=110))

    # 1.2 Báo cáo đa phương thức (Col 2)
    c_report = (
        "<b>Báo cáo Đa phương thức</b><br>"
        "<font style=\"font-size:12px;color:#37474F;\">"
        "• Chụp ảnh ngập + Tọa độ<br>"
        "• Số người mắc kẹt (N)<br>"
        "• Nhóm yếu thế &amp; thương tích (V)"
        "</font>"
    )
    nodes.append(add_cell("ui_report", c_report, card_base + "fillColor=#FFFFFF;strokeColor=#1976D2;", x=360, y=65, w=250, h=110))

    # 1.3 Edge AI On-device (Col 3)
    c_ai = (
        "<b>Suy luận Edge AI On-device</b><br>"
        "<font style=\"font-size:12px;color:#37474F;\">"
        "• MobileNetV3-Large (256×256)<br>"
        "• Phân loại 4 mức ngập (F) &amp; U<br>"
        "• ONNX Dart &amp; ExecuTorch JNI"
        "</font>"
    )
    nodes.append(add_cell("ai_edge", c_ai, card_base + "fillColor=#FCE4EC;strokeColor=#D81B60;strokeWidth=2;", x=655, y=65, w=250, h=110))

    # 1.4 Hive Outbox (Col 4)
    c_outbox = (
        "<b>Hive Outbox &amp; Toàn vẹn</b><br>"
        "<font style=\"font-size:12px;color:#37474F;\">"
        "• Store-and-Forward chống mất tin<br>"
        "• RFC 8785 Canonical JCS<br>"
        "• Toàn vẹn mã băm SHA-256"
        "</font>"
    )
    nodes.append(add_cell("hive_outbox", c_outbox, card_base + "fillColor=#F5F5F5;strokeColor=#455A64;", x=950, y=65, w=250, h=110))

    # =========================================================================
    # INTERMEDIATE NODE: BỘ ĐIỀU PHỐI MẠNG THÍCH ỨNG & KÊNH TRUYỀN
    # y = 225..273, h = 48, w = 1135
    # =========================================================================
    trans_node_style = (
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF9C4;strokeColor=#F9A825;"
        "strokeWidth=2;fontSize=14;fontFamily=Helvetica;arcSize=10;"
    )
    trans_text = (
        "<b>Bộ Điều phối Kênh Truyền Thích ứng (Adaptive Network &amp; Transport Channels)</b><br>"
        "<font style=\"font-size:12px;color:#5D4037;\">"
        "Kênh IP (4G/LTE/Wi-Fi): REST Batch (≤50 msg), Multipart Upload ảnh, GET /probe (64 KB)   |   Kênh GSM: SMS SOS Fallback dự phòng"
        "</font>"
    )
    nodes.append(add_cell("trans_node", trans_text, trans_node_style, x=65, y=225, w=1135, h=48))

    # =========================================================================
    # TIER 2: MÁY CHỦ TIẾP NHẬN & XỬ LÝ LÕI BACKEND (FASTAPI / RESCUE_CORE)
    # y = 300..475, h = 175, w = 1180
    # =========================================================================
    t2_box_style = (
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#F3E5F5;strokeColor=#7B1FA2;"
        "strokeWidth=2;dashed=1;dashPattern=8 4;arcSize=8;fontSize=18;"
    )
    nodes.append(add_cell("tier2_box", "", t2_box_style, x=40, y=300, w=1180, h=175))

    t2_lbl_style = "text;html=1;align=left;verticalAlign=top;spacingLeft=8;spacingTop=4;fontSize=16;fontColor=#7B1FA2;fontFamily=Helvetica;"
    nodes.append(add_cell("tier2_label", "<b>Tier 2: Máy chủ Tiếp nhận &amp; Xử lý Nghiệp vụ Lõi (FastAPI Backend Core &amp; rescue_core Engine)</b>", t2_lbl_style, x=50, y=304, w=720, h=26))

    # 2.1 Graph & Clustering Engine (Col 1)
    c_core = (
        "<b>Lõi Đồ thị &amp; Phân cụm</b><br>"
        "<font style=\"font-size:12px;color:#37474F;\">"
        "• Ma trận tương đồng C_ij<br>"
        "• Phân cụm Louvain (Modularity Q)<br>"
        "• Điểm ưu tiên cụm P(c)"
        "</font>"
    )
    nodes.append(add_cell("be_core", c_core, card_base + "fillColor=#EFEBE9;strokeColor=#4E342E;strokeWidth=2;", x=65, y=340, w=250, h=115))

    # 2.2 Review Queue (Col 2)
    c_review = (
        "<b>Hàng xem xét (Review Queue)</b><br>"
        "<font style=\"font-size:12px;color:#37474F;\">"
        "• Tách riêng ca thiếu GPS<br>"
        "• Thẩm tra &amp; gọi điện xác minh<br>"
        "• Tránh suy diễn tọa độ sai"
        "</font>"
    )
    nodes.append(add_cell("be_review", c_review, card_base + "fillColor=#FFF8E1;strokeColor=#FF8F00;", x=360, y=340, w=250, h=115))

    # 2.3 Dedup & Integrity Engine (Col 3)
    c_dedup = (
        "<b>Toàn vẹn &amp; Dedup Engine</b><br>"
        "<font style=\"font-size:12px;color:#37474F;\">"
        "• Header X-Message-Contract: 1<br>"
        "• RFC 8785 Canonical JCS Hash<br>"
        "• Idempotency qua messages_dedup"
        "</font>"
    )
    nodes.append(add_cell("be_dedup", c_dedup, card_base + "fillColor=#E8F5E9;strokeColor=#2E7D32;", x=655, y=340, w=250, h=115))

    # 2.4 API Ingestion Gateway (Col 4)
    c_api = (
        "<b>Cổng Tiếp nhận (API Gateway)</b><br>"
        "<font style=\"font-size:12px;color:#37474F;\">"
        "• POST /sync/messages (Batch)<br>"
        "• POST /api/reports (Multipart)<br>"
        "• Webhook POST /api/sms/inbound"
        "</font>"
    )
    nodes.append(add_cell("be_api", c_api, card_base + "fillColor=#FFFFFF;strokeColor=#7B1FA2;", x=950, y=340, w=250, h=115))

    # =========================================================================
    # TIER 3: BÀN ĐIỀU PHỐI WEB GIS & LƯU TRỮ BỀN VỮNG
    # y = 525..735, h = 210, w = 1180
    # =========================================================================
    t3_box_style = (
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF3E0;strokeColor=#E65100;"
        "strokeWidth=2;dashed=1;dashPattern=8 4;arcSize=8;fontSize=18;"
    )
    nodes.append(add_cell("tier3_box", "", t3_box_style, x=40, y=525, w=1180, h=210))

    # Đặt nhãn Tier 3 ở đáy tầng 3, ngay dưới Cột 1 (x=55..350, y=686..718).
    # Không có mũi tên nào đi qua vùng này (các xa lộ kết thúc ở y=545 tại đỉnh các card,
    # và đường phản hồi xuất phát từ Cột 2 ở x=485).
    t3_lbl_style = "text;html=1;align=left;verticalAlign=middle;spacingLeft=8;fontSize=14;fontColor=#E65100;fontFamily=Helvetica;"
    nodes.append(add_cell(
        "tier3_label",
        "<b>Tier 3: Bàn Điều phối Web GIS &amp; Lưu trữ Dữ liệu Bền vững</b><br>"
        "<font style=\"font-size:11px;color:#BF360C;\">(Dashboard Leaflet GIS &amp; Persistent SQLite WAL Engine)</font>",
        t3_lbl_style, x=55, y=686, w=300, h=32
    ))

    # 3.1 Leaflet GIS Map (Col 1)
    c_map = (
        "<b>Bản đồ Giám sát Leaflet GIS</b><br>"
        "<font style=\"font-size:12px;color:#37474F;\">"
        "• Leaflet GIS đóng gói cục bộ<br>"
        "• Ranh giới cụm &amp; Màu ưu tiên<br>"
        "• Chấm gán tọa độ thủ công<br>"
        "• Polling đồng bộ 5s (/changes)"
        "</font>"
    )
    nodes.append(add_cell("d_map", c_map, card_base + "fillColor=#FFFFFF;strokeColor=#F57C00;", x=65, y=545, w=250, h=130))

    # 3.2 Bảng Cụm & Điều phối Ca (Col 2)
    c_dispatch = (
        "<b>Bảng Cụm &amp; Điều phối Ca</b><br>"
        "<font style=\"font-size:12px;color:#37474F;\">"
        "• Thứ bậc ưu tiên giảm dần P(c)<br>"
        "• Khóa clusterKey nhất quán khi poll<br>"
        "• Giao đội (/team) &amp; 4 trạng thái<br>"
        "• Nhật ký kiểm toán report_events"
        "</font>"
    )
    nodes.append(add_cell("d_dispatch", c_dispatch, card_base + "fillColor=#FFF8E1;strokeColor=#FFA000;", x=360, y=545, w=250, h=130))

    # 3.3 CSDL SQLite WAL (Col 3)
    c_db = (
        "<b>Cơ sở Dữ liệu SQLite WAL</b><br>"
        "<font style=\"font-size:12px;color:#37474F;\">"
        "• reports: Báo cáo &amp; trạng thái<br>"
        "• messages_dedup: Chống trùng<br>"
        "• report_events: Lịch sử điều phối<br>"
        "• teams, operators, sessions, meta"
        "</font>"
    )
    nodes.append(add_cell("db_sqlite", c_db, card_base + "fillColor=#ECEFF1;strokeColor=#455A64;", x=655, y=545, w=250, h=130))

    # 3.4 Uploads Storage (Col 4)
    c_fs = (
        "<b>Kho Lưu trữ Tệp Hiện trường</b><br>"
        "<font style=\"font-size:12px;color:#37474F;\">"
        "• Thư mục uploads/ ảnh JPEG<br>"
        "• Lưu ảnh gốc &amp; ảnh nén hiện trường<br>"
        "• Đối soát toàn vẹn SHA-256<br>"
        "• Static Server trả ảnh tức thời"
        "</font>"
    )
    nodes.append(add_cell("fs_uploads", c_fs, card_base + "fillColor=#FFFFFF;strokeColor=#546E7A;", x=950, y=545, w=250, h=130))

    # =========================================================================
    # FOOTER LEGEND BOX (y = 770..800, h = 30, w = 1180)
    # =========================================================================
    legend_style = (
        "rounded=1;whiteSpace=wrap;html=1;arcSize=6;fillColor=#FAFAFA;strokeColor=#B0BEC5;"
        "strokeWidth=1;fontFamily=Helvetica;align=center;"
    )
    legend_text = (
        "<font style=\"font-size:11px;color:#263238;\"><b>CHÚ GIẢI QUY ƯỚC DÒNG DỮ LIỆU:</b>   "
        "<font color=\"#1565C0\">━━━ <b>Xanh Dương</b>: Luồng dữ liệu Thiết bị Biên (Tier 1)</font>   |   "
        "<font color=\"#7B1FA2\">━━━ <b>Tím</b>: Luồng xử lý Lõi Backend (Tier 2)</font>   |   "
        "<font color=\"#E65100\">━━━ <b>Cam</b>: Luồng Điều phối Web &amp; GIS (Tier 3)</font>   |   "
        "<font color=\"#2E7D32\">━━━ <b>Xanh Lá</b>: Giao dịch CSDL &amp; Giao đội</font></font>"
    )
    nodes.append(add_cell("legend_box", legend_text, legend_style, x=40, y=770, w=1180, h=30))

    # =========================================================================
    # EDGES & CONNECTORS (CLEAN DIRECT ORTHOGONAL LANES, NO OVERLAP)
    # =========================================================================
    edge_t1 = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;html=1;strokeWidth=2;strokeColor=#1976D2;endArrow=block;endFill=1;fontSize=12;fontColor=#0D47A1;labelBackgroundColor=#FFFFFF;"
    edge_t2 = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;html=1;strokeWidth=2;strokeColor=#7B1FA2;endArrow=block;endFill=1;fontSize=12;fontColor=#7B1FA2;labelBackgroundColor=#FFFFFF;"
    edge_t3 = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;html=1;strokeWidth=2;strokeColor=#E65100;endArrow=block;endFill=1;fontSize=12;fontColor=#E65100;labelBackgroundColor=#FFFFFF;"
    edge_green = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;html=1;strokeWidth=2;strokeColor=#2E7D32;endArrow=block;endFill=1;fontSize=12;fontColor=#1B5E20;labelBackgroundColor=#FFFFFF;"

    # 1. Inside Tier 1: Left to Right
    nodes.append(add_edge("e_report_ai", "Ảnh &amp; Meta", edge_t1, "ui_report", "ai_edge", exit_x=1.0, exit_y=0.5, entry_x=0.0, entry_y=0.5))
    nodes.append(add_edge("e_ai_outbox", "[F, U, N, V]", edge_t1, "ai_edge", "hive_outbox", exit_x=1.0, exit_y=0.5, entry_x=0.0, entry_y=0.5))

    # 2. Tier 1 -> Intermediate Layer:
    nodes.append(add_edge("e_sos_trans", "Gói SOS", edge_t1, "ui_sos", "trans_node", exit_x=0.5, exit_y=1.0, entry_x=0.11, entry_y=0.0))
    nodes.append(add_edge("e_outbox_trans", "Đồng bộ Outbox", edge_t1, "hive_outbox", "trans_node", exit_x=0.5, exit_y=1.0, entry_x=0.89, entry_y=0.0))

    # 3. Intermediate Layer -> Tier 2 (Col 4: be_api):
    nodes.append(add_edge("e_trans_api", "HTTP REST &amp; Webhook SMS", edge_t2, "trans_node", "be_api", exit_x=0.89, exit_y=1.0, entry_x=0.5, entry_y=0.0))

    # 4. Inside Tier 2: Right to Left Processing Pipeline
    nodes.append(add_edge("e_api_dedup", "Xác thực Hợp đồng", edge_t2, "be_api", "be_dedup", exit_x=0.0, exit_y=0.5, entry_x=1.0, entry_y=0.5))
    nodes.append(add_edge("e_dedup_rev", "Báo cáo Hợp lệ", edge_t2, "be_dedup", "be_review", exit_x=0.0, exit_y=0.5, entry_x=1.0, entry_y=0.5))
    nodes.append(add_edge("e_rev_core", "Đủ GPS", edge_t2, "be_review", "be_core", exit_x=0.0, exit_y=0.5, entry_x=1.0, entry_y=0.5))

    # 5. Tier 2 -> Tier 3: FOUR PERFECTLY PARALLEL STRAIGHT VERTICAL HIGHWAYS (ZERO CROSSINGS)
    # Highway 1 (Col 1, x = 190): be_core -> d_map
    nodes.append(add_edge(
        "e_core_map",
        "Cụm Louvain (ETag 304)",
        edge_t3, "be_core", "d_map",
        exit_x=0.5, exit_y=1.0, entry_x=0.5, entry_y=0.0,
        offset_y=-8
    ))

    # Highway 2 (Col 2, x = 485): be_review -> d_dispatch
    nodes.append(add_edge(
        "e_rev_dispatch",
        "Ca Thẩm tra &amp; Điểm P(c)",
        edge_t3, "be_review", "d_dispatch",
        exit_x=0.5, exit_y=1.0, entry_x=0.5, entry_y=0.0,
        offset_y=-8
    ))

    # Highway 3 (Col 3, x = 780): be_dedup -> db_sqlite
    nodes.append(add_edge(
        "e_dedup_db",
        "Giao dịch WAL Mode",
        edge_green, "be_dedup", "db_sqlite",
        exit_x=0.5, exit_y=1.0, entry_x=0.5, entry_y=0.0,
        offset_y=-8
    ))

    # Highway 4 (Col 4, x = 1075): be_api -> fs_uploads
    nodes.append(add_edge(
        "e_api_uploads",
        "Lưu trữ Ảnh Hiện trường",
        edge_t1, "be_api", "fs_uploads",
        exit_x=0.5, exit_y=1.0, entry_x=0.5, entry_y=0.0,
        offset_y=-8
    ))

    # 6. Reverse Feedback (Dispatch Action -> API Gateway):
    # Smooth bypass cleanly below Tier 3 (y = 748) and along the right edge (x = 1245)
    nodes.append(add_edge(
        "e_dispatch_team",
        "Giao Đội (/team)",
        edge_green, "d_dispatch", "be_api",
        exit_x=0.5, exit_y=1.0, entry_x=1.0, entry_y=0.5,
        points=[(485, 748), (1245, 748), (1245, 402)]
    ))

    return create_diagram_xml("Kien-truc-Tong-the-3-Tang-NCKH", nodes, w="1280", h="825")



# =========================================================================
# 8. SƠ ĐỒ THỰC THỂ LIÊN KẾT CSDL (DATABASE ERD)
# =========================================================================
def generate_database_erd():
    nodes = []
    tbl_style = (
        "shape=swimlane;fontStyle=1;align=center;verticalAlign=top;"
        "childLayout=stackLayout;horizontal=1;startSize=30;horizontalStack=0;"
        "resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=0;marginBottom=0;"
        "whiteSpace=wrap;html=1;fontFamily=Helvetica;fontSize=11;"
        "fillColor=#EDE7F6;strokeColor=#512DA8;swimlaneFillColor=#FFFFFF;"
    )
    cell_pk = (
        "text;strokeColor=none;fillColor=#FFF9C4;align=left;verticalAlign=middle;"
        "spacingLeft=8;spacingRight=4;overflow=hidden;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;"
        "rotatable=0;whiteSpace=wrap;html=1;fontStyle=1;fontSize=10;fontFamily=Helvetica;"
    )
    cell_uq = (
        "text;strokeColor=none;fillColor=#E8F5E9;align=left;verticalAlign=middle;"
        "spacingLeft=8;spacingRight=4;overflow=hidden;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;"
        "rotatable=0;whiteSpace=wrap;html=1;fontStyle=1;fontSize=10;fontFamily=Helvetica;"
    )
    cell_fk = (
        "text;strokeColor=none;fillColor=#E1F5FE;align=left;verticalAlign=middle;"
        "spacingLeft=8;spacingRight=4;overflow=hidden;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;"
        "rotatable=0;whiteSpace=wrap;html=1;fontStyle=2;fontSize=10;fontFamily=Helvetica;"
    )
    cell_def = (
        "text;strokeColor=none;fillColor=#FFFFFF;align=left;verticalAlign=middle;"
        "spacingLeft=8;spacingRight=4;overflow=hidden;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;"
        "rotatable=0;whiteSpace=wrap;html=1;fontSize=10;fontFamily=Helvetica;"
    )
    cell_alt = (
        "text;strokeColor=none;fillColor=#F8F9FA;align=left;verticalAlign=middle;"
        "spacingLeft=8;spacingRight=4;overflow=hidden;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;"
        "rotatable=0;whiteSpace=wrap;html=1;fontSize=9;fontStyle=2;fontFamily=Helvetica;fontColor=#546E7A;"
    )

    # 1. Table: reports (Báo cáo cứu hộ khẩn cấp - Cốt lõi hệ thống)
    nodes.append(add_cell("t_reports", "Table: reports (Báo cáo cứu hộ khẩn cấp)", tbl_style, x=510, y=50, w=400, h=605))
    cols_reports = [
        ("r_c1", "PK  id", "TEXT PRIMARY KEY (Mã SOS duy nhất)", cell_pk),
        ("r_c2", "    server_received_at", "TEXT NOT NULL (ISO-8601 UTC)", cell_def),
        ("r_c3", "    created_at", "TEXT (Thời điểm tạo tại client)", cell_def),
        ("r_c4", "    lat, lng", "REAL (Tọa độ WGS84 GPS hiện trường)", cell_def),
        ("r_c5", "    trapped_count", "INTEGER DEFAULT 0 (Số người mắc kẹt)", cell_def),
        ("r_c6", "    injured_count", "INTEGER DEFAULT 0 (Số người bị thương)", cell_def),
        ("r_c7", "    vulnerable_groups", "TEXT (JSON: trẻ em, người già...)", cell_def),
        ("r_c8", "    description", "TEXT (Mô tả hiện trường / khẩn cấp)", cell_def),
        ("r_c9", "    ai_tags", "TEXT (JSON kết quả Edge AI on-device)", cell_def),
        ("r_c10", "    send_mode", "TEXT (Chế độ gửi: HTTP, Sync, SMS)", cell_def),
        ("r_c11", "    status", "TEXT DEFAULT 'processing'", cell_def),
        ("r_c12", "    status_version", "INTEGER DEFAULT 1 (Phiên bản đồng bộ)", cell_def),
        ("r_c13", "    image_sha256", "TEXT (SHA-256 hash ảnh hiện trường)", cell_def),
        ("r_c14", "    image_size_bytes", "INTEGER (Dung lượng ảnh byte)", cell_def),
        ("r_c15", "    image_filename, image_url", "TEXT (Tên file & URL xem ảnh)", cell_def),
        ("r_c16", "    raw_payload", "TEXT NOT NULL (Canonical RFC 8785)", cell_def),
        ("r_c17", "FK  assigned_team_id", "INTEGER [Ref: teams.id]", cell_fk),
        ("r_c18", "    location_source", "TEXT ('device' GPS | 'manual')", cell_def),
        ("r_c19", "    owner_client_id", "TEXT (Client ID thiết bị sở hữu)", cell_def),
        ("r_c20", "    close_reason", "TEXT (Lý do khi status='cancelled')", cell_def),
        ("r_c21", "    first_received_at", "TEXT (Thời điểm nhận đầu tính SLA)", cell_def),
        ("r_c22", "    status_updated_at", "TEXT (Lần đổi trạng thái gần nhất)", cell_def),
        ("r_c23", "    updated_seq", "INTEGER DEFAULT 0 (Seq counter delta)", cell_def),
    ]
    for i, (cid, name, dtype, cstyle) in enumerate(cols_reports):
        nodes.append(add_cell(cid, f"{name} : {dtype}" if dtype else name, cstyle, parent="t_reports", x=0, y=30 + i * 25, w=400, h=25))

    # 2. Table: messages_dedup (Nhật ký chống trùng lặp & Outbox Store-and-Forward)
    nodes.append(add_cell("t_dedup", "Table: messages_dedup (Chống trùng lặp Outbox)", tbl_style, x=40, y=50, w=340, h=305))
    cols_dedup = [
        ("d_c1", "PK  message_id", "TEXT PRIMARY KEY (UUID outbox)", cell_pk),
        ("d_c2", "UQ  client_id", "TEXT NOT NULL (Định danh thiết bị)", cell_uq),
        ("d_c3", "UQ  sequence_number", "INTEGER NOT NULL (Tuần tự tăng dần)", cell_uq),
        ("d_c4", "    operation_type", "TEXT NOT NULL (CREATE_REPORT...)", cell_def),
        ("d_c5", "    payload_hash", "TEXT NOT NULL (RFC 8785 SHA-256)", cell_def),
        ("d_c6", "    status", "TEXT NOT NULL (PROCESSED, DUPLICATE...)", cell_def),
        ("d_c7", "    error_code", "TEXT (Mã lỗi nếu bị từ chối)", cell_def),
        ("d_c8", "    result_data", "TEXT (JSON: record_id, ack token)", cell_def),
        ("d_c9", "    processed_at", "TEXT NOT NULL (Thời điểm server xử lý)", cell_def),
        ("d_c10", "    created_at", "TEXT NOT NULL (Thời điểm tạo client)", cell_def),
        ("d_c11", "    expires_at", "TEXT (Thời điểm hết hạn lưu trữ)", cell_def),
    ]
    for i, (cid, name, dtype, cstyle) in enumerate(cols_dedup):
        nodes.append(add_cell(cid, f"{name} : {dtype}" if dtype else name, cstyle, parent="t_dedup", x=0, y=30 + i * 25, w=340, h=25))

    # 3. Table: report_events (Nhật ký kiểm toán truy vết sự kiện)
    nodes.append(add_cell("t_events", "Table: report_events (Nhật ký kiểm toán truy vết)", tbl_style, x=1040, y=50, w=340, h=280))
    cols_events = [
        ("e_c1", "PK  id", "INTEGER PRIMARY KEY AUTOINCREMENT", cell_pk),
        ("e_c2", "FK  report_id", "TEXT NOT NULL [Ref: reports.id]", cell_fk),
        ("e_c3", "    kind", "TEXT NOT NULL (status/assign/note/loc...)", cell_def),
        ("e_c4", "    from_value", "TEXT (Giá trị trước thao tác)", cell_def),
        ("e_c5", "    to_value", "TEXT (Giá trị sau thao tác)", cell_def),
        ("e_c6", "    status_version", "INTEGER (Phiên bản trạng thái)", cell_def),
        ("e_c7", "    actor", "TEXT (Điều phối viên / App client)", cell_def),
        ("e_c8", "    source", "TEXT NOT NULL (app/sync/sms/dashboard)", cell_def),
        ("e_c9", "    note", "TEXT (Ghi chú điều phối / lý do hủy)", cell_def),
        ("e_c10", "    created_at", "TEXT NOT NULL (ISO-8601 UTC)", cell_def),
    ]
    for i, (cid, name, dtype, cstyle) in enumerate(cols_events):
        nodes.append(add_cell(cid, f"{name} : {dtype}" if dtype else name, cstyle, parent="t_events", x=0, y=30 + i * 25, w=340, h=25))

    # 4. Table: teams (Đội cứu hộ / Cứu nạn cơ động thực địa)
    nodes.append(add_cell("t_teams", "Table: teams (Đội cứu hộ / Cứu nạn cơ động)", tbl_style, x=510, y=710, w=400, h=205))
    cols_teams = [
        ("tm_c1", "PK  id", "INTEGER PRIMARY KEY AUTOINCREMENT", cell_pk),
        ("tm_c2", "UQ  name", "TEXT NOT NULL UNIQUE (Tên đội thực địa)", cell_uq),
        ("tm_c3", "    phone", "TEXT (Số điện thoại liên lạc chỉ huy)", cell_def),
        ("tm_c4", "    members", "INTEGER (Số lượng thành viên trong đội)", cell_def),
        ("tm_c5", "    note", "TEXT (Năng lực, phương tiện xuồng/ca nô)", cell_def),
        ("tm_c6", "    active", "INTEGER NOT NULL DEFAULT 1 (Sẵn sàng)", cell_def),
        ("tm_c7", "    created_at", "TEXT NOT NULL (ISO-8601 UTC)", cell_def),
    ]
    for i, (cid, name, dtype, cstyle) in enumerate(cols_teams):
        nodes.append(add_cell(cid, f"{name} : {dtype}" if dtype else name, cstyle, parent="t_teams", x=0, y=30 + i * 25, w=400, h=25))

    # 5. Table: operators (Tài khoản điều phối & Quản trị)
    nodes.append(add_cell("t_operators", "Table: operators (Tài khoản điều phối & Quản trị)", tbl_style, x=1040, y=410, w=340, h=255))
    cols_operators = [
        ("op_c1", "PK  id", "INTEGER PRIMARY KEY AUTOINCREMENT", cell_pk),
        ("op_c2", "UQ  username", "TEXT NOT NULL UNIQUE COLLATE NOCASE", cell_uq),
        ("op_c3", "UQ  display_name", "TEXT NOT NULL UNIQUE (Actor log)", cell_uq),
        ("op_c4", "    password_hash", "TEXT NOT NULL (PBKDF2-SHA256)", cell_def),
        ("op_c5", "    role", "TEXT NOT NULL DEFAULT 'operator'", cell_def),
        ("op_c6", "    active", "INTEGER NOT NULL DEFAULT 1 (Hoạt động)", cell_def),
        ("op_c7", "    must_change_password", "INTEGER NOT NULL DEFAULT 0", cell_def),
        ("op_c8", "    created_at", "TEXT NOT NULL (ISO-8601 UTC)", cell_def),
        ("op_c9", "    last_login_at", "TEXT (Lần đăng nhập gần nhất)", cell_def),
    ]
    for i, (cid, name, dtype, cstyle) in enumerate(cols_operators):
        nodes.append(add_cell(cid, f"{name} : {dtype}" if dtype else name, cstyle, parent="t_operators", x=0, y=30 + i * 25, w=340, h=25))

    # 6. Table: sessions (Phiên đăng nhập Web Dashboard)
    nodes.append(add_cell("t_sessions", "Table: sessions (Phiên đăng nhập Web Dashboard)", tbl_style, x=1040, y=730, w=340, h=155))
    cols_sessions = [
        ("s_c1", "PK  token_hash", "TEXT PRIMARY KEY (SHA-256 session)", cell_pk),
        ("s_c2", "FK  operator_id", "INTEGER [Ref: operators.id]", cell_fk),
        ("s_c3", "    operator", "TEXT NOT NULL (Tên hiển thị lúc login)", cell_def),
        ("s_c4", "    created_at", "TEXT NOT NULL (Thời điểm cấp phiên)", cell_def),
        ("s_c5", "    expires_at", "TEXT NOT NULL (Thời điểm hết hạn)", cell_def),
    ]
    for i, (cid, name, dtype, cstyle) in enumerate(cols_sessions):
        nodes.append(add_cell(cid, f"{name} : {dtype}" if dtype else name, cstyle, parent="t_sessions", x=0, y=30 + i * 25, w=340, h=25))

    # 7. Table: server_meta (Metadata đồng bộ hệ thống)
    nodes.append(add_cell("t_meta", "Table: server_meta (Metadata đồng bộ hệ thống)", tbl_style, x=40, y=430, w=340, h=155))
    cols_meta = [
        ("m_c1", "PK  key", "TEXT PRIMARY KEY ('seq', 'epoch'..)", cell_pk),
        ("m_c2", "    value", "TEXT NOT NULL (Counter / UUID / Rev)", cell_def),
        ("m_c3", "    -- seq", "Bộ đếm tăng dần cho Polling delta", cell_alt),
        ("m_c4", "    -- epoch", "Đổi khi reset dữ liệu (Hard sync)", cell_alt),
        ("m_c5", "    -- cluster_rev", "Phiên bản đầu vào phân cụm Louvain", cell_alt),
    ]
    for i, (cid, name, dtype, cstyle) in enumerate(cols_meta):
        nodes.append(add_cell(cid, f"{name} : {dtype}" if dtype else name, cstyle, parent="t_meta", x=0, y=30 + i * 25, w=340, h=25))

    # Relationships
    erd_edge = "endArrow=diamondThin;endFill=1;startArrow=none;html=1;strokeColor=#455A64;strokeWidth=1.5;fontSize=10;"
    nodes.append(add_edge("erd_e1", "1 : N (Giao đội: assigned_team_id)", erd_edge, "t_teams", "t_reports", exit_x=0.5, exit_y=0.0, entry_x=0.5, entry_y=1.0))
    nodes.append(add_edge("erd_e2", "1 : N (Events)", erd_edge, "t_reports", "t_events", exit_x=1.0, exit_y=0.2, entry_x=0.0, entry_y=0.35))
    nodes.append(add_edge("erd_e3", "1 : N (Phiên làm việc)", erd_edge, "t_operators", "t_sessions", exit_x=0.5, exit_y=1.0, entry_x=0.5, entry_y=0.0))
    nodes.append(add_edge("erd_e4", "1 : N (Upsert)", erd_edge, "t_dedup", "t_reports", exit_x=1.0, exit_y=0.3, entry_x=0.0, entry_y=0.2))
    nodes.append(add_edge("erd_e5", "Audit: actor", erd_edge, "t_operators", "t_events", exit_x=0.5, exit_y=0.0, entry_x=0.5, entry_y=1.0))

    return create_diagram_xml("So-do-Thuc-the-Lien-ket-CSDL-ERD", nodes, w="1420", h="960")


# =========================================================================
# 9. KIẾN TRÚC PHÂN LỚP MOBILE FLUTTER (CLEAN ARCHITECTURE)
# =========================================================================
def generate_mobile_architecture():
    nodes = []
    layer_style = "shape=swimlane;whiteSpace=wrap;html=1;startSize=28;fontStyle=1;fontSize=12;fontFamily=Helvetica;"

    nodes.append(add_cell("l_pres", "1. PRESENTATION LAYER (GIAO DIỆN &amp; QUẢN LÝ TRẠNG THÁI)", layer_style + "fillColor=#E3F2FD;strokeColor=#1976D2;", x=40, y=40, w=1120, h=180))
    nodes.append(add_cell("l_dom", "2. DOMAIN LAYER (NGHIỆP VỤ &amp; QUY TẮC CỐT LÕI - THUẦN DART)", layer_style + "fillColor=#EDE7F6;strokeColor=#512DA8;", x=40, y=250, w=1120, h=180))
    nodes.append(add_cell("l_data", "3. DATA LAYER (DỮ LIỆU &amp; HIỆN THỰC REPOSITORY)", layer_style + "fillColor=#E8F5E9;strokeColor=#2E7D32;", x=40, y=460, w=1120, h=200))
    nodes.append(add_cell("l_plat", "4. PLATFORM CHANNELS &amp; NATIVE HARDWARE BRIDGES", layer_style + "fillColor=#ECEFF1;strokeColor=#455A64;", x=40, y=690, w=1120, h=160))

    # Presentation Layer
    nodes.append(add_cell("p_views", "UI Views &amp; Screens:\n- HomeScreen (Tổng quan &amp; Nút SOS 1 chạm)\n- ComposeScreen (Soạn báo cáo cứu trợ kèm ảnh)\n- HistoryScreen / SubmittedScreen (Tra cứu tiến trình)\n- SettingsScreen (Cấu hình máy chủ &amp; Tải model AI)", STYLE_ACT, parent="l_pres", x=40, y=45, w=480, h=110))
    nodes.append(add_cell("p_ctrl", "Controllers &amp; State Management:\n- AppController (Quản lý trạng thái trung tâm qua ChangeNotifier)\n- Điều phối luồng gửi SOS &amp; Soạn bài cứu nạn\n- Đánh giá thông lượng mạng (Probe) &amp; Chọn chế độ gửi thích ứng\n- Thăm dò định kỳ trạng thái điều phối (15s Timer)", STYLE_ACT, parent="l_pres", x=560, y=45, w=520, h=110))

    # Domain Layer
    nodes.append(add_cell("d_repo_intf", "Repository Interfaces (Abstractions):\n- RescueRepository (Lưu &amp; gửi báo cáo)\n- InferenceRepository (Suy luận AI)\n- NetworkRepository (Đo kiểm mạng)", STYLE_ACT, parent="l_dom", x=40, y=45, w=340, h=115))
    nodes.append(add_cell("d_uc", "Use Cases &amp; Business Policies:\n- SendSosUseCase (Gửi SOS khẩn)\n- SubmitRescuePostUseCase (Gửi bài kèm ảnh)\n- DeliverRecordUseCase (Thực thi gửi thích ứng)\n- AdaptiveSendPolicy &amp; UrgencyLogisticModel", STYLE_ACT, parent="l_dom", x=410, y=45, w=350, h=115))
    nodes.append(add_cell("d_ent", "Entities &amp; Value Objects:\n- RescueRecord (id, status, gps, urgency)\n- AiTag (label, confidence)\n- SendMode (fullImage, compressedImage,\n  textOnly, smsFallback, queuedOffline)\n- SyncMessage (payload_hash, sequence)", STYLE_ACT, parent="l_dom", x=790, y=45, w=300, h=115))

    # Data Layer
    nodes.append(add_cell("dt_repo", "Repository Implementations:\n- RescueRepositoryImpl\n- InferenceRepositoryImpl (Conditional export)\n- NetworkRepositoryImpl", STYLE_ACT, parent="l_data", x=40, y=45, w=340, h=130))
    nodes.append(add_cell("dt_local", "Local DataSources:\n- OutboxLocalDataSource (Hive store-and-forward)\n- RecordLocalDataSource (Lưu trữ bản ghi offline)\n- RFC 8785 Canonical JCS &amp; SHA-256 Hasher", "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#ECEFF1;strokeColor=#455A64;fontSize=10;fontFamily=Helvetica;spacingTop=16;align=center;", parent="l_data", x=410, y=45, w=340, h=130))
    nodes.append(add_cell("dt_remote", "Remote &amp; Native DataSources:\n- SenderRemoteDataSource (FastAPI REST &amp; Multipart)\n- SyncRemoteDataSource (/sync/messages Batch)\n- NetworkRemoteDataSource (GET /probe 64KB)\n- InferenceLocalDataSource (ONNX / ExecuTorch PTE)", STYLE_ACT, parent="l_data", x=780, y=45, w=310, h=130))

    # Platform Layer
    nodes.append(add_cell("pl_gps", "Geolocator (GPS Location Service)", STYLE_ACT, parent="l_plat", x=40, y=50, w=240, h=65))
    nodes.append(add_cell("pl_cam", "Camera &amp; Image Picker (Ảnh hiện trường)", STYLE_ACT, parent="l_plat", x=310, y=50, w=240, h=65))
    nodes.append(add_cell("pl_sms", "Android Telephony (MethodChannel rescue/sms)", STYLE_WARN, parent="l_plat", x=580, y=50, w=240, h=65))
    nodes.append(add_cell("pl_wm", "Workmanager (Tiến trình nền 15 phút)", STYLE_ACT, parent="l_plat", x=850, y=50, w=240, h=65))

    # Connectors
    nodes.append(add_edge("ma_e1", "Calls", STYLE_EDGE, "p_ctrl", "d_uc"))
    nodes.append(add_edge("ma_e6", "Uses", STYLE_EDGE, "d_uc", "d_repo_intf"))
    nodes.append(add_edge("ma_e10", "Uses", STYLE_EDGE, "d_uc", "d_ent"))
    nodes.append(add_edge("ma_e2", "Implements", "endArrow=classic;html=1;strokeColor=#2E7D32;strokeWidth=1.5;fontSize=10;fontFamily=Helvetica;fontStyle=1;", "dt_repo", "d_repo_intf"))
    nodes.append(add_edge("ma_e3", "Uses", STYLE_EDGE, "dt_repo", "dt_local"))
    nodes.append(add_edge("ma_e4", "Uses", STYLE_EDGE, "dt_repo", "dt_remote"))
    nodes.append(add_edge("ma_e5", "Hardware Channel", "endArrow=classic;html=1;strokeColor=#E53935;strokeWidth=1.3;fontSize=10;fontFamily=Helvetica;", "dt_remote", "pl_sms"))
    nodes.append(add_edge("ma_e7", "Background Sync", "endArrow=classic;html=1;strokeColor=#455A64;strokeWidth=1.2;fontSize=10;fontFamily=Helvetica;dashed=1;", "dt_local", "pl_wm"))
    nodes.append(add_edge("ma_e8", "Platform Service", "endArrow=classic;html=1;strokeColor=#455A64;strokeWidth=1.2;fontSize=10;fontFamily=Helvetica;dashed=1;", "dt_repo", "pl_gps"))
    nodes.append(add_edge("ma_e9", "Device Picker", "endArrow=classic;html=1;strokeColor=#455A64;strokeWidth=1.2;fontSize=10;fontFamily=Helvetica;dashed=1;", "dt_repo", "pl_cam"))

    return create_diagram_xml("Kien-truc-Phan-lop-Mobile-Flutter", nodes, w="1220", h="920")


# =========================================================================
# 10. SƠ ĐỒ TRIỂN KHAI HẠ TẦNG (DEPLOYMENT INFRASTRUCTURE)
# =========================================================================
def generate_deployment_infrastructure():
    nodes = []
    host_style = "shape=swimlane;whiteSpace=wrap;html=1;startSize=30;fontStyle=1;fontSize=13;fontFamily=Helvetica;fillColor=#F5F5F5;strokeColor=#424242;"
    nodes.append(add_cell("d_host", "MÁY CHỦ TRIỂN KHAI DỊCH VỤ (DOCKER COMPOSE HOST)", host_style, x=380, y=40, w=820, h=780))

    # Containers
    cnt_style = "rounded=1;whiteSpace=wrap;html=1;fontStyle=1;fontSize=11;fontFamily=Helvetica;align=center;"
    nodes.append(add_cell("c_backend", "Container: rescue-backend\n- FastAPI + Uvicorn Server\n- Lõi rescue_core phân cụm Louvain\n- Port 8000:8000 (Internal API)", cnt_style + "fillColor=#EDE7F6;strokeColor=#512DA8;", parent="d_host", x=40, y=60, w=350, h=90))
    nodes.append(add_cell("c_dashboard", "Container: rescue-dashboard\n- Nginx Web Server\n- React + Leaflet SPA static files\n- Port 8080:80 (Dispatcher Dashboard)", cnt_style + "fillColor=#FFF8E1;strokeColor=#F57C00;", parent="d_host", x=420, y=60, w=350, h=90))
    nodes.append(add_cell("c_frontend_demo", "Container: rescue-demo-frontend\n- Flutter Web compiled bundle\n- Môi trường kiểm thử web app\n- Port 8081:80 (Demo Web App)", cnt_style + "fillColor=#E3F2FD;strokeColor=#1976D2;", parent="d_host", x=40, y=190, w=350, h=85))

    # Volumes
    nodes.append(add_cell("v_db", "Docker Named Volume: sqlite_data\n- /app/data/rescue.db (SQLite WAL Mode)\n- Dữ liệu reports, deduplication, teams, events", STYLE_DB, parent="d_host", x=40, y=320, w=350, h=80))
    nodes.append(add_cell("v_uploads", "Docker Named Volume: uploads_data\n- /app/uploads/ (Ảnh chụp hiện trường)\n- Đọc/ghi ảnh multipart từ thiết bị", STYLE_DB, parent="d_host", x=420, y=320, w=350, h=80))

    # External devices
    nodes.append(add_cell("dev_phone", "Thiết bị Di động Android (Client):\n- Cài đặt file APK (Flutter App)\n- Camera, GPS, Local Hive DB\n- ONNX Runtime & ExecuTorch Native", cnt_style + "fillColor=#E8F5E9;strokeColor=#2E7D32;", x=40, y=160, w=280, h=110))
    nodes.append(add_cell("dev_dispatcher", "Máy tính Điều phối viên (Dispatcher PC):\n- Trình duyệt Web (Chrome, Edge, Firefox)\n- Truy cập Dashboard qua Port 8080", cnt_style + "fillColor=#FFF3E0;strokeColor=#FB8C00;", x=40, y=420, w=280, h=100))
    nodes.append(add_cell("dev_sms_gw", "SMS Gateway / GSM Modem GSM:\n- Tiếp nhận tin nhắn SOS từ vùng mất mạng\n- Chuyển tiếp Webhook tới /api/sms/inbound", cnt_style + "fillColor=#FFEBEE;strokeColor=#E53935;", x=40, y=650, w=280, h=100))

    # Connections
    nodes.append(add_edge("dep_e1", "Wi-Fi / 4G (HTTP :8000)", STYLE_EDGE, "dev_phone", "c_backend"))
    nodes.append(add_edge("dep_e2", "Web Browser (HTTP :8080)", STYLE_EDGE, "dev_dispatcher", "c_dashboard"))
    nodes.append(add_edge("dep_e3", "API Proxy / Data", STYLE_EDGE, "c_dashboard", "c_backend"))
    nodes.append(add_edge("dep_e4", "SMS Webhook (:8000)", STYLE_EDGE, "dev_sms_gw", "c_backend"))
    nodes.append(add_edge("dep_e5", "Mounts", STYLE_EDGE, "c_backend", "v_db"))
    nodes.append(add_edge("dep_e6", "Mounts", STYLE_EDGE, "c_backend", "v_uploads"))

    return create_diagram_xml("So-do-Trien-khai-Ha-tang-Docker", nodes, w="1250", h="880")


# =========================================================================
# 11. FLOW 01: SOS ONE TOUCH
# =========================================================================
def generate_flow_01():
    nodes = []
    nodes.append(add_cell("start", "Bắt đầu", STYLE_START, x=370, y=40, w=100, h=40))
    nodes.append(add_cell("press_sos", "Người dùng nhấn nút\n'SOS Khẩn cấp' (1 chạm)", STYLE_ACT, x=330, y=110, w=180, h=50))
    nodes.append(add_cell("get_gps", "Lấy tọa độ GPS tức thời\n(Geolocator accuracy high)", STYLE_ACT, x=330, y=190, w=180, h=50))
    nodes.append(add_cell("gps_ok", "Tọa độ GPS\nkhả dụng?", STYLE_DEC, x=350, y=270, w=140, h=65))
    
    # 2D branches for GPS
    nodes.append(add_cell("set_gps", "Gán tọa độ (lat, lng)\nvào bản ghi", STYLE_OK, x=490, y=365, w=160, h=50))
    nodes.append(add_cell("set_null", "Đặt lat/lng = null\n(chờ tổng đài định vị)", STYLE_WARN, x=190, y=365, w=160, h=50))

    # Merge
    nodes.append(add_cell("make_record", "Khởi tạo RescueRecord:\n- id: sos-*\n- status: processing\n- urgency: 1.0 (khẩn cấp)", STYLE_ACT, x=320, y=445, w=200, h=60))
    nodes.append(add_cell("save_outbox", "Ghi Outbox Hive Box\n(Store-and-forward, RFC 8785)", STYLE_DB, x=345, y=535, w=150, h=55))
    nodes.append(add_cell("probe", "Đo thông lượng mạng\n(GET /probe 64 KB)", STYLE_ACT, x=330, y=620, w=180, h=45))
    nodes.append(add_cell("mode_dec", "Đánh giá kết nối\nmạng?", STYLE_DEC, x=350, y=695, w=140, h=65))

    # 3 branches for Send Mode
    nodes.append(add_cell("send_sms", "MẤT MẠNG:\nGửi tin SMS cứu nạn\ntới hotline tổng đài", STYLE_WARN, x=100, y=795, w=180, h=55))
    nodes.append(add_cell("queue_retry", "MẠNG CHẬP CHỜN:\nĐặt lịch WorkManager\nđồng bộ ngầm", STYLE_ACT, x=330, y=795, w=180, h=55))
    nodes.append(add_cell("send_http", "CÓ KẾT NỐI:\nGửi HTTP POST trực tiếp\n/sync/messages", STYLE_OK, x=560, y=795, w=180, h=55))

    # Merge
    nodes.append(add_cell("show_status", "Hiển thị trạng thái:\n'Đã gửi / Đang chờ điều phối'", STYLE_ACT, x=320, y=890, w=200, h=50))
    nodes.append(add_cell("poll_timer", "Khởi động Timer Polling 15s\ntheo dõi phản hồi từ trung tâm", STYLE_ACT, x=320, y=965, w=200, h=45))
    nodes.append(add_cell("end", "Kết thúc", STYLE_END, x=370, y=1035, w=100, h=40))

    nodes.append(add_edge("e1", "", STYLE_EDGE, "start", "press_sos"))
    nodes.append(add_edge("e2", "", STYLE_EDGE, "press_sos", "get_gps"))
    nodes.append(add_edge("e3", "", STYLE_EDGE, "get_gps", "gps_ok"))
    nodes.append(add_edge("e4", "Có", STYLE_EDGE, "gps_ok", "set_gps"))
    nodes.append(add_edge("e5", "Không", STYLE_EDGE, "gps_ok", "set_null"))
    nodes.append(add_edge("e6", "", STYLE_EDGE, "set_gps", "make_record"))
    nodes.append(add_edge("e7", "", STYLE_EDGE, "set_null", "make_record"))
    nodes.append(add_edge("e8", "", STYLE_EDGE, "make_record", "save_outbox"))
    nodes.append(add_edge("e9", "", STYLE_EDGE, "save_outbox", "probe"))
    nodes.append(add_edge("e10", "", STYLE_EDGE, "probe", "mode_dec"))
    nodes.append(add_edge("e11", "Mất data", STYLE_EDGE, "mode_dec", "send_sms"))
    nodes.append(add_edge("e12", "Chập chờn", STYLE_EDGE, "mode_dec", "queue_retry"))
    nodes.append(add_edge("e13", "Có mạng", STYLE_EDGE, "mode_dec", "send_http"))
    nodes.append(add_edge("e14", "", STYLE_EDGE, "send_sms", "show_status"))
    nodes.append(add_edge("e15", "", STYLE_EDGE, "queue_retry", "show_status"))
    nodes.append(add_edge("e16", "", STYLE_EDGE, "send_http", "show_status"))
    nodes.append(add_edge("e17", "", STYLE_EDGE, "show_status", "poll_timer"))
    nodes.append(add_edge("e18", "", STYLE_EDGE, "poll_timer", "end"))

    return create_diagram_xml("Luu-do-01-SOS-Khancap-1-Cham", nodes, w="850", h="1120")


# =========================================================================
# 12. FLOW 02: CREATE REPORT & EDGE AI
# =========================================================================
def generate_flow_02():
    nodes = []
    nodes.append(add_cell("start", "Bắt đầu", STYLE_START, x=370, y=40, w=100, h=40))
    nodes.append(add_cell("open_form", "Mở biểu mẫu\n'Tạo Báo cáo Cứu hộ'", STYLE_ACT, x=330, y=110, w=180, h=50))
    nodes.append(add_cell("img_dec", "Người dùng có\nđính kèm ảnh?", STYLE_DEC, x=350, y=190, w=140, h=65))

    # Branch with image
    nodes.append(add_cell("capture", "Chụp ảnh hiện trường\nhoặc chọn từ thư viện", STYLE_ACT, x=130, y=280, w=200, h=50))
    nodes.append(add_cell("run_ai", "AnalyzeImageUseCase:\nChạy MobileNetV3 On-device\n(ONNX Runtime / ExecuTorch .pte)", STYLE_AI, x=130, y=360, w=200, h=65))
    nodes.append(add_cell("ai_out", "Trích xuất kết quả AI:\nNhãn ngập (non/low/med/high)\n& Điểm tin cậy (Confidence)", STYLE_AI, x=130, y=455, w=200, h=60))
    nodes.append(add_cell("gen_tags", "Sinh mảng AiTag[]\n(label, confidence, timestamp)", STYLE_ACT, x=130, y=545, w=200, h=50))

    # Branch without image
    nodes.append(add_cell("skip_ai", "Không có ảnh:\nGán nhãn non_flood mặc định", STYLE_ACT, x=530, y=280, w=200, h=50))

    # Merge
    nodes.append(add_cell("fill_info", "Nhập thông tin cứu hộ chi tiết:\n- Số người kẹt, số người bị thương\n- Nhóm yếu thế (người già, trẻ nhỏ...)\n- Mô tả tình hình hiện trường", STYLE_ACT, x=320, y=630, w=220, h=75))
    nodes.append(add_cell("calc_urgency", "Tự động tính độ khẩn cấp:\nUrgency Score (E_i / U_i)", STYLE_ACT, x=330, y=735, w=200, h=50))
    nodes.append(add_cell("get_gps", "Lấy tọa độ GPS (hoặc để trống/nhập tay)", STYLE_ACT, x=330, y=815, w=200, h=45))
    nodes.append(add_cell("make_rec", "Đóng gói RescueRecord:\nid=post-*, status=processing", STYLE_ACT, x=330, y=890, w=200, h=50))
    nodes.append(add_cell("deliver", "Chuyển sang chính sách\ngửi thích ứng (deliverRecord)", STYLE_OK, x=330, y=970, w=200, h=50))
    nodes.append(add_cell("end", "Kết thúc", STYLE_END, x=380, y=1050, w=100, h=40))

    nodes.append(add_edge("e1", "", STYLE_EDGE, "start", "open_form"))
    nodes.append(add_edge("e2", "", STYLE_EDGE, "open_form", "img_dec"))
    nodes.append(add_edge("e3", "Có ảnh", STYLE_EDGE, "img_dec", "capture"))
    nodes.append(add_edge("e4", "Không", STYLE_EDGE, "img_dec", "skip_ai"))
    nodes.append(add_edge("e5", "", STYLE_EDGE, "capture", "run_ai"))
    nodes.append(add_edge("e6", "", STYLE_EDGE, "run_ai", "ai_out"))
    nodes.append(add_edge("e7", "", STYLE_EDGE, "ai_out", "gen_tags"))
    nodes.append(add_edge("e8", "", STYLE_EDGE, "gen_tags", "fill_info"))
    nodes.append(add_edge("e9", "", STYLE_EDGE, "skip_ai", "fill_info"))
    nodes.append(add_edge("e10", "", STYLE_EDGE, "fill_info", "calc_urgency"))
    nodes.append(add_edge("e11", "", STYLE_EDGE, "calc_urgency", "get_gps"))
    nodes.append(add_edge("e12", "", STYLE_EDGE, "get_gps", "make_rec"))
    nodes.append(add_edge("e13", "", STYLE_EDGE, "make_rec", "deliver"))
    nodes.append(add_edge("e14", "", STYLE_EDGE, "deliver", "end"))

    return create_diagram_xml("Luu-do-02-Tao-Bao-cao-Edge-AI", nodes, w="850", h="1130")


# =========================================================================
# 13. FLOW 03: ADAPTIVE NETWORK SEND
# =========================================================================
def generate_flow_03():
    nodes = []
    nodes.append(add_cell("start", "Bắt đầu", STYLE_START, x=430, y=40, w=100, h=40))
    nodes.append(add_cell("call_deliv", "Gọi deliverRecord(record, imageFile)", STYLE_ACT, x=380, y=110, w=200, h=45))
    nodes.append(add_cell("save_hive", "Ghi vào Outbox Hive Box\n(Store-and-forward, pending)", STYLE_DB, x=405, y=185, w=150, h=55))
    nodes.append(add_cell("probe", "Đo thông lượng mạng\n(GET /probe 64 KB trong 6s)", STYLE_ACT, x=390, y=270, w=180, h=45))
    nodes.append(add_cell("eval_net", "Phân loại băng thông\n& Độ tin cậy AI?", STYLE_DEC, x=390, y=345, w=180, h=75))

    # 4 Adaptive branches matching Table 3.2
    nodes.append(add_cell("mode_sms", "1. MẤT DATA HOÀN TOÀN:\n- Gửi tin SMS SOS tóm tắt\n- Giữ Outbox chờ mạng", STYLE_WARN, x=40, y=460, w=190, h=65))
    nodes.append(add_cell("mode_meta", "2. MẠNG YẾU (<50 kbps)\nhoặc (Mạnh & Conf >= 0.90):\n- Gửi metadata JSON\n  POST /sync/messages", STYLE_ACT, x=255, y=460, w=200, h=65))
    nodes.append(add_cell("mode_comp", "3. MẠNG TRUNG BÌNH (50-1000 kbps):\n- Nén JPEG (max 1024px, q=60)\n- Gửi multipart POST /api/reports", "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF8E1;strokeColor=#F57C00;fontSize=11;fontFamily=Helvetica;", x=480, y=460, w=215, h=65))
    nodes.append(add_cell("mode_orig", "4. MẠNG MẠNH (>=1000 kbps & Conf<0.9):\n- Giữ nguyên ảnh gốc\n- Gửi multipart POST /api/reports", STYLE_OK, x=720, y=460, w=220, h=65))

    # Merge
    nodes.append(add_cell("recv_resp", "Nhận phản hồi từ Server:\naccepted, duplicate, retry_later, rejected", STYLE_ACT, x=370, y=565, w=220, h=65))
    nodes.append(add_cell("resp_dec", "Phản hồi\nhợp lệ?", STYLE_DEC, x=400, y=660, w=160, h=65))

    nodes.append(add_cell("on_success", "Thành công (accepted / duplicate):\nĐánh dấu synced=true, xóa khỏi Outbox", STYLE_OK, x=560, y=755, w=220, h=55))
    nodes.append(add_cell("on_retry", "Lỗi tạm thời (408, 429, 5xx):\nGiữ Outbox, Exponential Backoff + Jitter", STYLE_WARN, x=180, y=755, w=220, h=55))

    nodes.append(add_cell("poll_status", "Khởi động Timer Polling 15s\nGET /api/reports/status", STYLE_ACT, x=370, y=845, w=220, h=45))
    nodes.append(add_cell("end", "Kết thúc", STYLE_END, x=430, y=925, w=100, h=40))

    nodes.append(add_edge("e1", "", STYLE_EDGE, "start", "call_deliv"))
    nodes.append(add_edge("e2", "", STYLE_EDGE, "call_deliv", "save_hive"))
    nodes.append(add_edge("e3", "", STYLE_EDGE, "save_hive", "probe"))
    nodes.append(add_edge("e4", "", STYLE_EDGE, "probe", "eval_net"))
    nodes.append(add_edge("e5", "Mất data", STYLE_EDGE, "eval_net", "mode_sms"))
    nodes.append(add_edge("e6", "<50k / c>=0.9", STYLE_EDGE, "eval_net", "mode_meta"))
    nodes.append(add_edge("e7", "50-1000k", STYLE_EDGE, "eval_net", "mode_comp"))
    nodes.append(add_edge("e8", ">=1000k", STYLE_EDGE, "eval_net", "mode_orig"))
    nodes.append(add_edge("e9", "", STYLE_EDGE, "mode_sms", "recv_resp"))
    nodes.append(add_edge("e10", "", STYLE_EDGE, "mode_meta", "recv_resp"))
    nodes.append(add_edge("e11", "", STYLE_EDGE, "mode_comp", "recv_resp"))
    nodes.append(add_edge("e12", "", STYLE_EDGE, "mode_orig", "recv_resp"))
    nodes.append(add_edge("e13", "", STYLE_EDGE, "recv_resp", "resp_dec"))
    nodes.append(add_edge("e14", "Thành công", STYLE_EDGE, "resp_dec", "on_success"))
    nodes.append(add_edge("e15", "Lỗi mạng", STYLE_EDGE, "resp_dec", "on_retry"))
    nodes.append(add_edge("e16", "", STYLE_EDGE, "on_success", "poll_status"))
    nodes.append(add_edge("e17", "", STYLE_EDGE, "on_retry", "poll_status"))
    nodes.append(add_edge("e18", "", STYLE_EDGE, "poll_status", "end"))

    return create_diagram_xml("Luu-do-03-Gui-Thich-ung-Bang-thong", nodes, w="980", h="1010")


# =========================================================================
# 14. FLOW 04: TRACK RESCUE STATUS
# =========================================================================
def generate_flow_04():
    nodes = []
    nodes.append(add_cell("start", "Bắt đầu", STYLE_START, x=390, y=40, w=100, h=40))
    nodes.append(add_cell("open_view", "Người dùng mở màn hình\n'Theo dõi Cứu hộ'", STYLE_ACT, x=340, y=110, w=200, h=45))
    nodes.append(add_cell("net_check", "Có kết nối\nmạng?", STYLE_DEC, x=370, y=185, w=140, h=65))

    nodes.append(add_cell("read_local", "MẤT MẠNG:\nĐọc trạng thái lưu trong\nHive Local Storage", STYLE_DB, x=150, y=280, w=190, h=55))
    nodes.append(add_cell("call_api", "CÓ MẠNG:\nGọi GET /api/reports/status\n(truyền danh sách report_ids)", STYLE_ACT, x=540, y=280, w=200, h=55))

    nodes.append(add_cell("update_store", "Cập nhật CSDL cục bộ Hive\n(Chỉ nhận trạng thái tiến, không lùi)", STYLE_ACT, x=340, y=370, w=200, h=55))
    nodes.append(add_cell("status_dec", "Phân loại trạng thái\nnghiệp vụ hiện tại?", STYLE_DEC, x=350, y=455, w=180, h=70))

    # 4 Status states
    nodes.append(add_cell("st_proc", "processing:\n'Đang tiếp nhận & phân loại'\n(Chờ gán đội)", STYLE_ACT, x=40, y=560, w=180, h=60))
    nodes.append(add_cell("st_disp", "dispatched:\n'Đội cứu hộ đã xuất phát'\n(Hiển thị tên đội & liên hệ)", STYLE_OK, x=245, y=560, w=190, h=60))
    nodes.append(add_cell("st_res", "resolved:\n'Đã cứu hộ thành công'\n(Nạn nhân đã an toàn)", STYLE_OK, x=460, y=560, w=180, h=60))
    nodes.append(add_cell("st_canc", "cancelled:\n'Yêu cầu cứu trợ đã đóng'\n(Hiển thị lý do hủy ca)", STYLE_WARN, x=665, y=560, w=185, h=60))

    # Merge
    nodes.append(add_cell("render_ui", "Cập nhật thanh tiến trình giao diện\n(Timeline trực quan cho người dân)", STYLE_ACT, x=340, y=655, w=200, h=50))
    nodes.append(add_cell("timer_loop", "Đặt lịch Polling chu kỳ 15s tiếp theo", STYLE_ACT, x=340, y=735, w=200, h=40))
    nodes.append(add_cell("end", "Kết thúc", STYLE_END, x=390, y=805, w=100, h=40))

    nodes.append(add_edge("e1", "", STYLE_EDGE, "start", "open_view"))
    nodes.append(add_edge("e2", "", STYLE_EDGE, "open_view", "net_check"))
    nodes.append(add_edge("e3", "Mất mạng", STYLE_EDGE, "net_check", "read_local"))
    nodes.append(add_edge("e4", "Có mạng", STYLE_EDGE, "net_check", "call_api"))
    nodes.append(add_edge("e5", "", STYLE_EDGE, "read_local", "update_store"))
    nodes.append(add_edge("e6", "", STYLE_EDGE, "call_api", "update_store"))
    nodes.append(add_edge("e7", "", STYLE_EDGE, "update_store", "status_dec"))
    nodes.append(add_edge("e8", "processing", STYLE_EDGE, "status_dec", "st_proc"))
    nodes.append(add_edge("e9", "dispatched", STYLE_EDGE, "status_dec", "st_disp"))
    nodes.append(add_edge("e10", "resolved", STYLE_EDGE, "status_dec", "st_res"))
    nodes.append(add_edge("e11", "cancelled", STYLE_EDGE, "status_dec", "st_canc"))
    nodes.append(add_edge("e12", "", STYLE_EDGE, "st_proc", "render_ui"))
    nodes.append(add_edge("e13", "", STYLE_EDGE, "st_disp", "render_ui"))
    nodes.append(add_edge("e14", "", STYLE_EDGE, "st_res", "render_ui"))
    nodes.append(add_edge("e15", "", STYLE_EDGE, "st_canc", "render_ui"))
    nodes.append(add_edge("e16", "", STYLE_EDGE, "render_ui", "timer_loop"))
    nodes.append(add_edge("e17", "", STYLE_EDGE, "timer_loop", "end"))

    return create_diagram_xml("Luu-do-04-Theo-doi-Tien-trinh-Cuu-ho", nodes, w="900", h="890")


# =========================================================================
# 15. FLOW 05: BACKEND INGEST DEDUP
# =========================================================================
def generate_flow_05():
    # Calling the dedicated clean 2D generator for backend dedup
    return generate_flowchart_backend_dedup()


# =========================================================================
# 16. FLOW 06: CLUSTERING & PRIORITY
# =========================================================================
def generate_flow_06():
    nodes = []
    nodes.append(add_cell("start", "Bắt đầu", STYLE_START, x=390, y=40, w=100, h=40))
    nodes.append(add_cell("trigger", "Kích hoạt Phân cụm:\n- Polling từ Web Dashboard\n- Thay đổi version trong server_meta", STYLE_ACT, x=330, y=110, w=220, h=55))
    nodes.append(add_cell("etag_dec", "So sánh ETag /\ncluster_version?", STYLE_DEC, x=370, y=195, w=140, h=65))

    nodes.append(add_cell("ret_304", "Không đổi: Trả 304 Not Modified\n(Tận dụng Client Cache, giảm tải CPU)", STYLE_ACT, x=610, y=200, w=220, h=55))
    nodes.append(add_cell("fetch_active", "Dữ liệu mới: Truy vấn SQLite\nLấy báo cáo active_only=True\n(Loại bỏ resolved & cancelled)", STYLE_ACT, x=330, y=290, w=220, h=60))

    nodes.append(add_cell("adapter_v2", "Adapter to_report_v2:\nTrích xuất [F, U, N, V]\n& Tọa độ địa lý (lat, lng)", STYLE_ACT, x=330, y=380, w=220, h=60))
    nodes.append(add_cell("gps_dec", "Báo cáo có\ntọa độ GPS?", STYLE_DEC, x=370, y=470, w=140, h=65))

    # 2 Branches: Missing GPS -> Review Queue vs GPS OK -> Graph
    nodes.append(add_cell("to_review", "THIẾU GPS:\nĐưa vào Hàng xem xét (Review Queue)\nđể điều phối viên xác minh thủ công", STYLE_WARN, x=100, y=565, w=230, h=65))
    nodes.append(add_cell("build_graph", "CÓ GPS:\nXây ma trận tương đồng C_ij\n(Khoảng cách Haversine, ngập F, khẩn cấp U)", STYLE_ACT, x=450, y=565, w=250, h=65))

    nodes.append(add_cell("louvain", "Thuật toán Phân cụm Louvain:\n- Tối ưu hóa Modularité mạng lưới\n- Xác định clusterKey (ID nhỏ nhất)", STYLE_ACT, x=450, y=665, w=250, h=65))
    nodes.append(add_cell("score_calc", "Tính điểm ưu tiên cụm P(c):\nP(c) = w1*Nc + w2*Vc + w3*Fc + w4*Uc\nSắp xếp thứ bậc ưu tiên điều phối", STYLE_OK, x=450, y=765, w=250, h=65))

    # Merge
    nodes.append(add_cell("save_cache", "Lưu Snapshot Cache & ETag mới\n(Cập nhật cluster_version)", STYLE_DB, x=330, y=860, w=220, h=55))
    nodes.append(add_cell("resp_dash", "Trả dữ liệu JSON cho Dashboard:\nDanh sách cụm ưu tiên & Review Queue", STYLE_ACT, x=330, y=945, w=220, h=50))
    nodes.append(add_cell("end", "Kết thúc", STYLE_END, x=390, y=1025, w=100, h=40))

    nodes.append(add_edge("e1", "", STYLE_EDGE, "start", "trigger"))
    nodes.append(add_edge("e2", "", STYLE_EDGE, "trigger", "etag_dec"))
    nodes.append(add_edge("e3", "Không đổi", STYLE_EDGE, "etag_dec", "ret_304"))
    nodes.append(add_edge("e4", "Có đổi", STYLE_EDGE, "etag_dec", "fetch_active"))
    nodes.append(add_edge("e5", "", STYLE_EDGE, "fetch_active", "adapter_v2"))
    nodes.append(add_edge("e6", "", STYLE_EDGE, "adapter_v2", "gps_dec"))
    nodes.append(add_edge("e7", "Thiếu GPS", STYLE_EDGE, "gps_dec", "to_review"))
    nodes.append(add_edge("e8", "Có GPS", STYLE_EDGE, "gps_dec", "build_graph"))
    nodes.append(add_edge("e9", "", STYLE_EDGE, "build_graph", "louvain"))
    nodes.append(add_edge("e10", "", STYLE_EDGE, "louvain", "score_calc"))
    nodes.append(add_edge("e11", "", STYLE_EDGE, "to_review", "save_cache"))
    nodes.append(add_edge("e12", "", STYLE_EDGE, "score_calc", "save_cache"))
    nodes.append(add_edge("e13", "", STYLE_EDGE, "save_cache", "resp_dash"))
    nodes.append(add_edge("e14", "", STYLE_EDGE, "ret_304", "end"))
    nodes.append(add_edge("e15", "", STYLE_EDGE, "resp_dash", "end"))

    return create_diagram_xml("Luu-do-06-Phan-cum-va-Uu-tien", nodes, w="900", h="1100")


# =========================================================================
# 17. FLOW 07: MANUAL INTAKE & LOCATION
# =========================================================================
def generate_flow_07():
    nodes = []
    nodes.append(add_cell("start", "Bắt đầu", STYLE_START, x=390, y=40, w=100, h=40))
    nodes.append(add_cell("recv_call", "Điều phối viên tiếp nhận:\nCuộc gọi cứu nạn hotline hoặc SMS Gateway", STYLE_ACT, x=320, y=110, w=240, h=55))
    nodes.append(add_cell("open_modal", "Mở modal 'Nhập báo cáo thủ công'\ntrên giao diện Web Dashboard", STYLE_ACT, x=330, y=195, w=220, h=50))
    nodes.append(add_cell("enter_info", "Nhập thông tin người gọi:\nTên, SĐT, mô tả, số người kẹt, nhóm yếu thế", STYLE_ACT, x=320, y=275, w=240, h=55))
    nodes.append(add_cell("loc_dec", "Người gọi có cung cấp\nđịa chỉ / tọa độ?", STYLE_DEC, x=370, y=360, w=140, h=70))

    # 2 Branches
    nodes.append(add_cell("pick_map", "XÁC ĐỊNH ĐƯỢC VỊ TRÍ:\nChấm vị trí trên bản đồ Leaflet\nhoặc nhập địa chỉ cụ thể", STYLE_OK, x=510, y=460, w=230, h=60))
    nodes.append(add_cell("no_loc", "CHƯA RÕ VỊ TRÍ:\nĐặt lat/lng = null\nĐưa vào Hàng xem xét (Review Queue)", STYLE_WARN, x=150, y=460, w=230, h=60))

    # Merge
    nodes.append(add_cell("submit_api", "Gọi POST /api/reports/manual:\n- Gán source = 'manual'\n- Ghi operator_id thực hiện", STYLE_ACT, x=330, y=555, w=220, h=60))
    nodes.append(add_cell("log_event", "Ghi nhật ký vào report_events\n(Actor: operator, action: create_manual)", STYLE_DB, x=340, y=645, w=200, h=55))
    nodes.append(add_cell("auto_cluster", "Cập nhật dữ liệu hoạt động\n-> Kích hoạt phân cụm tự động", STYLE_ACT, x=330, y=730, w=220, h=50))
    nodes.append(add_cell("end", "Kết thúc", STYLE_END, x=390, y=810, w=100, h=40))

    nodes.append(add_edge("e1", "", STYLE_EDGE, "start", "recv_call"))
    nodes.append(add_edge("e2", "", STYLE_EDGE, "recv_call", "open_modal"))
    nodes.append(add_edge("e3", "", STYLE_EDGE, "open_modal", "enter_info"))
    nodes.append(add_edge("e4", "", STYLE_EDGE, "enter_info", "loc_dec"))
    nodes.append(add_edge("e5", "Có địa chỉ", STYLE_EDGE, "loc_dec", "pick_map"))
    nodes.append(add_edge("e6", "Chưa rõ", STYLE_EDGE, "loc_dec", "no_loc"))
    nodes.append(add_edge("e7", "", STYLE_EDGE, "pick_map", "submit_api"))
    nodes.append(add_edge("e8", "", STYLE_EDGE, "no_loc", "submit_api"))
    nodes.append(add_edge("e9", "", STYLE_EDGE, "submit_api", "log_event"))
    nodes.append(add_edge("e10", "", STYLE_EDGE, "log_event", "auto_cluster"))
    nodes.append(add_edge("e11", "", STYLE_EDGE, "auto_cluster", "end"))

    return create_diagram_xml("Luu-do-07-Tiep-nhan-Tong-dai-va-Gan-Vi-tri", nodes, w="850", h="890")


# =========================================================================
# 18. FLOW 08: DISPATCH LIFECYCLE
# =========================================================================
def generate_flow_08():
    nodes = []
    nodes.append(add_cell("start", "Bắt đầu", STYLE_START, x=390, y=40, w=100, h=40))
    nodes.append(add_cell("view_board", "Điều phối viên xem danh sách cụm ưu tiên\nvà bản đồ sự cố Leaflet GIS", STYLE_ACT, x=320, y=110, w=240, h=55))
    nodes.append(add_cell("select_case", "Chọn ca cứu hộ cần xử lý:\nXem ảnh hiện trường, nhãn AI, số nạn nhân", STYLE_ACT, x=330, y=195, w=220, h=55))
    nodes.append(add_cell("gps_check", "Ca cứu hộ đã có\ntọa độ GPS?", STYLE_DEC, x=370, y=280, w=140, h=65))

    # Branch missing GPS
    nodes.append(add_cell("add_loc", "BỔ SUNG VỊ TRÍ:\nGọi xác minh & cập nhật tọa độ\nPUT /api/reports/{id}/location", STYLE_WARN, x=130, y=375, w=220, h=60))
    nodes.append(add_cell("loc_ready", "Tọa độ hợp lệ,\nchuyển sang bước điều động", STYLE_OK, x=530, y=375, w=210, h=50))

    # Merge
    nodes.append(add_cell("pick_team", "Lựa chọn đội cứu hộ (teams)\nphù hợp địa bàn và năng lực", STYLE_ACT, x=330, y=465, w=220, h=55))
    nodes.append(add_cell("assign_dispatch", "Giao đội & Chuyển trạng thái:\nPUT /api/reports/{id}/team\nstatus -> dispatched (tăng statusVersion)", STYLE_OK, x=320, y=550, w=240, h=65))
    nodes.append(add_cell("field_action", "Đội cứu hộ tiếp cận hiện trường\nvà triển khai cứu nạn", STYLE_ACT, x=330, y=645, w=220, h=50))
    nodes.append(add_cell("res_dec", "Kết quả cứu hộ\ntại thực địa?", STYLE_DEC, x=370, y=725, w=140, h=70))

    # 2 Outcome branches
    nodes.append(add_cell("mark_resolved", "CỨU HỘ THÀNH CÔNG:\nCập nhật status -> resolved\n(Nạn nhân đã được an toàn)", STYLE_OK, x=180, y=825, w=220, h=60))
    nodes.append(add_cell("mark_cancelled", "HỦY CA / TIN GIẢ:\nCập nhật status -> cancelled\n(Bắt buộc chọn lý do hủy)", STYLE_WARN, x=480, y=825, w=220, h=60))

    # Merge
    nodes.append(add_cell("log_audit", "Ghi audit log vào report_events\n(Actor, action, timestamp);\nLoại ca khỏi active clusters", STYLE_DB, x=320, y=915, w=240, h=65))
    nodes.append(add_cell("end", "Kết thúc", STYLE_END, x=390, y=1010, w=100, h=40))

    nodes.append(add_edge("e1", "", STYLE_EDGE, "start", "view_board"))
    nodes.append(add_edge("e2", "", STYLE_EDGE, "view_board", "select_case"))
    nodes.append(add_edge("e3", "", STYLE_EDGE, "select_case", "gps_check"))
    nodes.append(add_edge("e4", "Chưa có", STYLE_EDGE, "gps_check", "add_loc"))
    nodes.append(add_edge("e5", "Đã có", STYLE_EDGE, "gps_check", "loc_ready"))
    nodes.append(add_edge("e6", "", STYLE_EDGE, "add_loc", "pick_team"))
    nodes.append(add_edge("e7", "", STYLE_EDGE, "loc_ready", "pick_team"))
    nodes.append(add_edge("e8", "", STYLE_EDGE, "pick_team", "assign_dispatch"))
    nodes.append(add_edge("e9", "", STYLE_EDGE, "assign_dispatch", "field_action"))
    nodes.append(add_edge("e10", "", STYLE_EDGE, "field_action", "res_dec"))
    nodes.append(add_edge("e11", "Thành công", STYLE_EDGE, "res_dec", "mark_resolved"))
    nodes.append(add_edge("e12", "Hủy / Lỗi", STYLE_EDGE, "res_dec", "mark_cancelled"))
    nodes.append(add_edge("e13", "", STYLE_EDGE, "mark_resolved", "log_audit"))
    nodes.append(add_edge("e14", "", STYLE_EDGE, "mark_cancelled", "log_audit"))
    nodes.append(add_edge("e15", "", STYLE_EDGE, "log_audit", "end"))

    return create_diagram_xml("Luu-do-08-Vong-doi-Dieu-phoi-Cuu-ho", nodes, w="850", h="1080")


# =========================================================================
# 19. FLOW 09: AI TRAINING & OPTIMIZATION PIPELINE
# =========================================================================
# 19. FLOW 09: AI TRAINING & OPTIMIZATION PIPELINE
# =========================================================================
def generate_flow_09():
    nodes = []
    # Phase group containers
    grp_style1 = "rounded=1;whiteSpace=wrap;html=1;dashed=1;verticalAlign=top;fontStyle=1;fontSize=11;spacingTop=6;fillColor=#EBF3FA;strokeColor=#90CAF9;fontFamily=Helvetica;"
    grp_style2 = "rounded=1;whiteSpace=wrap;html=1;dashed=1;verticalAlign=top;fontStyle=1;fontSize=11;spacingTop=6;fillColor=#FCE4EC;strokeColor=#F48FB1;fontFamily=Helvetica;"
    grp_style3 = "rounded=1;whiteSpace=wrap;html=1;dashed=1;verticalAlign=top;fontStyle=1;fontSize=11;spacingTop=6;fillColor=#E8F5E9;strokeColor=#A5D6A7;fontFamily=Helvetica;"

    nodes.append(add_cell("grp_phase1", "GIAI ĐOẠN 1: CHUẨN BỊ DỮ LIỆU & THIẾT KẾ KIẾN TRÚC", grp_style1, x=30, y=30, w=1080, h=115))
    nodes.append(add_cell("grp_phase2", "GIAI ĐOẠN 2: HUẤN LUYỆN 2 GIAI ĐOẠN & CHỌN CHECKPOINT TỐI ƯU", grp_style2, x=30, y=165, w=1080, h=115))
    nodes.append(add_cell("grp_phase3", "GIAI ĐOẠN 3: ĐÁNH GIÁ ĐỘC LẬP, TỐI ƯU NÉN & XUẤT RUNTIME KÉP", grp_style3, x=30, y=300, w=1080, h=115))

    # --- ROW 1: Data Preparation & Architecture (Left to Right ->) ---
    nodes.append(add_cell("start", "Bắt đầu", STYLE_START, x=50, y=78, w=70, h=38))
    nodes.append(add_cell("dataset", "Tập dữ liệu ảnh bão lũ cứu hộ:\n1.702 mẫu ảnh (4 mức ngập:\nnon_flood, low, medium, high)", STYLE_DB, x=140, y=65, w=200, h=65))
    nodes.append(add_cell("strat_split", "Phân chia Stratified Split (Seed 42):\n- Train Set (70%): ~1.192 ảnh\n- Validation Set (15%): ~254 ảnh\n- Test Set độc lập (15%): 256 ảnh", STYLE_ACT, x=370, y=65, w=220, h=65))
    nodes.append(add_cell("augment", "Tiền xử lý & Tăng cường ảnh:\n- Letterbox Resize 256x256 RGB\n- RandomHorizontalFlip, ColorJitter\n- Normalization ImageNet stats", STYLE_ACT, x=620, y=65, w=220, h=65))
    nodes.append(add_cell("init_arch", "MobileNetV3-Large Backbone\nThay thế Classifier Head tùy biến:\nDropout(0.25) -> Linear(1280, 4)", STYLE_AI, x=870, y=65, w=220, h=65))

    # --- ROW 2: Training & Checkpoint Selection (Right to Left <-) ---
    nodes.append(add_cell("phase1", "Pha 1: Khóa Backbone (eval mode)\nHuấn luyện Classifier Head\n(3 epoch khởi tạo)", STYLE_ACT, x=870, y=200, w=220, h=65))
    nodes.append(add_cell("phase2", "Pha 2: Mở toàn bộ mạng\nFine-tuning AdamW + CosineAnnealing\nLoss: CrossEntropy + 0.1 SeverityLoss", STYLE_AI, x=620, y=200, w=220, h=65))
    nodes.append(add_cell("val_check", "Đánh giá Validation Set:\nVal Loss & Tỷ lệ lỗi nặng\n(Early Stopping patience=7)?", STYLE_DEC, x=380, y=200, w=200, h=65))
    nodes.append(add_cell("best_ckpt", "Lưu Checkpoint tối ưu nhất\n(Accuracy: ~75.78%,\nMacro-F1: ~74.26%)", STYLE_OK, x=140, y=200, w=200, h=65))

    # --- ROW 3: Test Evaluation, Compression & Dual Export (Left to Right ->) ---
    nodes.append(add_cell("test_eval", "Đánh giá trên Test Set độc lập:\n- 256 ảnh kiểm định độc lập\n- Confusion Matrix & Macro-F1\n- Kiểm tra tỷ lệ lỗi nghiêm trọng", STYLE_ACT, x=140, y=335, w=200, h=65))
    nodes.append(add_cell("pruning_opt", "Tối ưu hóa nén mô hình:\n- Cắt tỉa kênh L1 Pruning (tỷ lệ 1%)\n- Lượng tử hóa INT8 (PTQ/QAT QDQ)", STYLE_ACT, x=370, y=335, w=220, h=65))
    nodes.append(add_cell("export_dual", "Xuất định dạng Runtime di động kép:\n1) ONNX Model (.onnx) qua onnxruntime\n2) ExecuTorch Program (.pte) di động", STYLE_OK, x=620, y=335, w=220, h=65))
    nodes.append(add_cell("mobile_deploy", "Tích hợp Flutter Edge App:\nSuy luận On-device thời gian thực\n(Hoạt động hoàn toàn Offline)", STYLE_ACT, x=870, y=335, w=155, h=65))
    nodes.append(add_cell("end", "Sẵn sàng", STYLE_END, x=1045, y=348, w=65, h=38))

    # Edges - Row 1 (Left to Right)
    nodes.append(add_edge("e1", "", STYLE_EDGE, "start", "dataset"))
    nodes.append(add_edge("e2", "", STYLE_EDGE, "dataset", "strat_split"))
    nodes.append(add_edge("e3", "", STYLE_EDGE, "strat_split", "augment"))
    nodes.append(add_edge("e4", "", STYLE_EDGE, "augment", "init_arch"))

    # Transition Row 1 -> Row 2 (Straight down at the right)
    nodes.append(add_edge("e5", "", STYLE_EDGE, "init_arch", "phase1"))

    # Edges - Row 2 (Right to Left)
    nodes.append(add_edge("e6", "", STYLE_EDGE, "phase1", "phase2"))
    nodes.append(add_edge("e7", "", STYLE_EDGE, "phase2", "val_check"))
    nodes.append(add_edge("e8", "Đạt chuẩn", STYLE_EDGE, "val_check", "best_ckpt"))

    # Transition Row 2 -> Row 3 (Straight down at the left)
    nodes.append(add_edge("e9", "", STYLE_EDGE, "best_ckpt", "test_eval"))

    # Edges - Row 3 (Left to Right)
    nodes.append(add_edge("e10", "", STYLE_EDGE, "test_eval", "pruning_opt"))
    nodes.append(add_edge("e11", "", STYLE_EDGE, "pruning_opt", "export_dual"))
    nodes.append(add_edge("e12", "", STYLE_EDGE, "export_dual", "mobile_deploy"))
    nodes.append(add_edge("e13", "", STYLE_EDGE, "mobile_deploy", "end"))

    return create_diagram_xml("Luu-do-09-Pipeline-Huan-luyen-va-Toi-uu-AI", nodes, w="1140", h="450")


# =========================================================================
# MAIN GENERATION DISPATCHER
# =========================================================================
def main():
    generators = {
        # Core Architecture & Use Case
        "usecase.drawio": generate_usecase,
        "usecase_mobile.drawio": generate_usecase_mobile,
        "usecase_dashboard.drawio": generate_usecase_dashboard,
        "system_architecture.drawio": generate_system_architecture,
        "database_erd.drawio": generate_database_erd,
        "mobile_architecture.drawio": generate_mobile_architecture,
        "deployment_infrastructure.drawio": generate_deployment_infrastructure,

        # System Flowcharts
        "flowchart.drawio": generate_flowchart,
        "flowchart_adaptive_mobile.drawio": generate_flowchart_adaptive_mobile,
        "flowchart_backend_dedup.drawio": generate_flowchart_backend_dedup,

        # Detailed Flowcharts 01 - 09
        "flow_01_sos_one_touch.drawio": generate_flow_01,
        "flow_02_create_report_edge_ai.drawio": generate_flow_02,
        "flow_03_adaptive_network_send.drawio": generate_flow_03,
        "flow_04_track_rescue_status.drawio": generate_flow_04,
        "flow_05_backend_ingest_dedup.drawio": generate_flow_05,
        "flow_06_clustering_priority.drawio": generate_flow_06,
        "flow_07_manual_intake_location.drawio": generate_flow_07,
        "flow_08_dispatch_lifecycle.drawio": generate_flow_08,
        "flow_09_ai_training_optimization.drawio": generate_flow_09,
    }

    print(f"Bắt đầu sinh {len(generators)} sơ đồ Draw.io tại {OUT_DIR}...")
    for filename, fn in generators.items():
        xml_content = fn()
        out_path = OUT_DIR / filename
        out_path.write_text(xml_content, encoding="utf-8")
        print(f"  [OK] Đã xuất: {filename:<40} ({len(xml_content):>6} bytes)")

    print(f"\nHoàn tất thành công toàn bộ {len(generators)} sơ đồ Draw.io chuẩn XML!")


if __name__ == "__main__":
    main()
