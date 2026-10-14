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


def add_edge(edge_id, value, style, source, target, parent="1"):
    cell = ET.Element("mxCell", {
        "id": str(edge_id), "value": value, "style": style,
        "parent": str(parent), "edge": "1", "source": str(source), "target": str(target)
    })
    ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
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
    nodes.append(add_cell("sys_bound", "HỆ THỐNG HỖ TRỢ CỨU HỘ BÃO LŨ (THS2026-68)", 
                          "shape=swimlane;whiteSpace=wrap;html=1;startSize=30;horizontal=1;fillColor=#F8F9FA;strokeColor=#4A5568;fontStyle=1;fontSize=14;fontFamily=Helvetica;",
                          x=260, y=40, w=1120, h=920))

    actor_style = "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fontFamily=Helvetica;fontSize=12;fontStyle=1;"
    nodes.append(add_cell("act_citizen", "Người dân /\nNạn nhân", actor_style + "fillColor=#E3F2FD;strokeColor=#1976D2;", x=80, y=200, w=50, h=90))
    nodes.append(add_cell("act_rescuer", "Đội cứu hộ\nthực địa", actor_style + "fillColor=#E8F5E9;strokeColor=#388E3C;", x=80, y=550, w=50, h=90))
    nodes.append(add_cell("act_dispatcher", "Điều phối viên\n(Dispatcher)", actor_style + "fillColor=#FFF3E0;strokeColor=#F57C00;", x=1460, y=320, w=50, h=90))
    nodes.append(add_cell("act_admin", "Quản trị viên\n(Administrator)", actor_style + "fillColor=#EDE7F6;strokeColor=#512DA8;", x=1460, y=700, w=50, h=90))
    nodes.append(add_cell("act_sms_gw", "SMS Gateway /\nNhà mạng", actor_style + "fillColor=#ECEFF1;strokeColor=#455A64;", x=80, y=780, w=50, h=90))

    subsys_style = "rounded=1;whiteSpace=wrap;html=1;dashed=1;verticalAlign=top;fontStyle=1;fontSize=12;spacingTop=6;"
    nodes.append(add_cell("sub_fe", "Phân hệ Di động Biên (Edge Mobile App - Flutter)", subsys_style + "fillColor=#EBF3FA;strokeColor=#90CAF9;", parent="sys_bound", x=40, y=50, w=500, h=520))
    nodes.append(add_cell("sub_be", "Phân hệ Lõi & Xử lý Tự động (Backend Core)", subsys_style + "fillColor=#EFEBE9;strokeColor=#BCAAA4;", parent="sys_bound", x=40, y=600, w=1040, h=280))
    nodes.append(add_cell("sub_dash", "Phân hệ Điều phối & Quản trị Web (Dispatch Dashboard)", subsys_style + "fillColor=#FFF8E1;strokeColor=#FFE082;", parent="sys_bound", x=580, y=50, w=500, h=520))

    uc_style = "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1E88E5;fontFamily=Helvetica;fontSize=11;"
    nodes.append(add_cell("uc_sos", "UC-01: Gửi SOS khẩn cấp\n(1 chạm, định vị nhanh)", uc_style, parent="sys_bound", x=70, y=90, w=200, h=60))
    nodes.append(add_cell("uc_post", "UC-02: Tạo báo cáo cứu hộ\n(ảnh, số người, vị trí)", uc_style, parent="sys_bound", x=70, y=180, w=200, h=60))
    nodes.append(add_cell("uc_ai", "UC-03: Nhận diện mức ngập on-device\n(Edge AI MobileNetV3)", uc_style + "strokeColor=#D81B60;fillColor=#FCE4EC;", parent="sys_bound", x=310, y=180, w=200, h=60))
    nodes.append(add_cell("uc_outbox", "UC-04: Lưu trữ Outbox ngoại tuyến\n(Hive Store-and-Forward)", uc_style, parent="sys_bound", x=70, y=280, w=200, h=60))
    nodes.append(add_cell("uc_probe", "UC-05: Đo thông lượng mạng (/probe)\n& Chọn chế độ truyền thích ứng", uc_style, parent="sys_bound", x=310, y=280, w=200, h=60))
    nodes.append(add_cell("uc_sms", "UC-06: Gửi SMS dự phòng\nkhi mất hoàn toàn kết nối", uc_style + "strokeColor=#E53935;fillColor=#FFEBEE;", parent="sys_bound", x=70, y=380, w=200, h=60))
    nodes.append(add_cell("uc_sync", "UC-07: Đồng bộ tự động nền\n(Workmanager / Reconnect)", uc_style, parent="sys_bound", x=310, y=380, w=200, h=60))
    nodes.append(add_cell("uc_status", "UC-08: Tra cứu trạng thái cứu hộ\n(Polling 15s /api/reports/status)", uc_style, parent="sys_bound", x=70, y=470, w=200, h=60))

    uc_dash_style = "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#F57C00;fontFamily=Helvetica;fontSize=11;"
    nodes.append(add_cell("uc_login", "UC-09: Đăng nhập & Xác thực phiên\n(PBKDF2 /api/auth/login)", uc_dash_style, parent="sys_bound", x=610, y=90, w=200, h=60))
    nodes.append(add_cell("uc_map", "UC-10: Giám sát bản đồ sự cố\n(Leaflet theo cụm / mức ưu tiên)", uc_dash_style, parent="sys_bound", x=850, y=90, w=200, h=60))
    nodes.append(add_cell("uc_list", "UC-11: Lọc, phân trang & xem chi tiết\nbáo cáo hiện trường", uc_dash_style, parent="sys_bound", x=610, y=180, w=200, h=60))
    nodes.append(add_cell("uc_manual", "UC-12: Nhập báo cáo tổng đài\n(/api/reports/manual)", uc_dash_style, parent="sys_bound", x=850, y=180, w=200, h=60))
    nodes.append(add_cell("uc_team_assign", "UC-13: Giao / điều chuyển đội cứu hộ\n(/api/reports/{id}/team)", uc_dash_style, parent="sys_bound", x=610, y=280, w=200, h=60))
    nodes.append(add_cell("uc_update_status", "UC-14: Cập nhật trạng thái nhiệm vụ\n(dispatched -> resolved / cancelled)", uc_dash_style, parent="sys_bound", x=850, y=280, w=200, h=60))
    nodes.append(add_cell("uc_manual_loc", "UC-15: Bổ sung tọa độ thủ công\n(ca thiếu GPS / hàng xem xét)", uc_dash_style, parent="sys_bound", x=610, y=380, w=200, h=60))
    nodes.append(add_cell("uc_export", "UC-16: Xuất dữ liệu báo cáo\n(CSV / GeoJSON / Thống kê)", uc_dash_style, parent="sys_bound", x=850, y=380, w=200, h=60))

    uc_adm_style = "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#512DA8;fontFamily=Helvetica;fontSize=11;"
    nodes.append(add_cell("uc_manage_acc", "UC-17: Quản lý tài khoản điều phối\n(CRUD operators)", uc_adm_style, parent="sys_bound", x=610, y=470, w=200, h=60))
    nodes.append(add_cell("uc_backup", "UC-18: Sao lưu CSDL & ảnh hiện trường\n(/api/admin/backup)", uc_adm_style, parent="sys_bound", x=850, y=470, w=200, h=60))

    uc_be_style = "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#5D4037;fontFamily=Helvetica;fontSize=11;"
    nodes.append(add_cell("uc_ingest", "UC-19: Tiếp nhận & kiểm tra toàn vẹn\n(RFC 8785 JSON SHA-256)", uc_be_style, parent="sys_bound", x=80, y=660, w=220, h=60))
    nodes.append(add_cell("uc_dedup", "UC-20: Chống trùng lặp & Idempotency\n(messages_dedup theo hash/seq)", uc_be_style, parent="sys_bound", x=340, y=660, w=220, h=60))
    nodes.append(add_cell("uc_cluster", "UC-21: Xây dựng đồ thị & Phân cụm\n(Graph Louvain Community)", uc_be_style, parent="sys_bound", x=600, y=660, w=220, h=60))
    nodes.append(add_cell("uc_rank", "UC-22: Tính điểm ưu tiên cụm P(c)\n& Quản lý Hàng xem xét", uc_be_style, parent="sys_bound", x=850, y=660, w=220, h=60))
    nodes.append(add_cell("uc_sms_in", "UC-23: Tiếp nhận SMS Gateway\n(Token auth /api/sms/inbound)", uc_be_style, parent="sys_bound", x=200, y=770, w=220, h=60))
    nodes.append(add_cell("uc_audit", "UC-24: Ghi nhật ký truy vết sự kiện\n(report_events audit log)", uc_be_style, parent="sys_bound", x=700, y=770, w=220, h=60))

    edge_style = "endArrow=none;html=1;strokeColor=#546E7A;strokeWidth=1.2;"
    inc_style = "endArrow=open;dashed=1;html=1;strokeColor=#D81B60;strokeWidth=1.2;fontSize=10;fontColor=#D81B60;"
    ext_style = "endArrow=open;dashed=1;html=1;strokeColor=#E53935;strokeWidth=1.2;fontSize=10;fontColor=#E53935;"

    nodes.append(add_edge("e_c_1", "", edge_style, "act_citizen", "uc_sos"))
    nodes.append(add_edge("e_c_2", "", edge_style, "act_citizen", "uc_post"))
    nodes.append(add_edge("e_c_3", "", edge_style, "act_citizen", "uc_status"))
    nodes.append(add_edge("e_r_1", "", edge_style, "act_rescuer", "uc_post"))
    nodes.append(add_edge("e_r_2", "", edge_style, "act_rescuer", "uc_status"))
    nodes.append(add_edge("e_sms_1", "", edge_style, "act_sms_gw", "uc_sms_in"))

    nodes.append(add_edge("e_d_1", "", edge_style, "act_dispatcher", "uc_login"))
    nodes.append(add_edge("e_d_2", "", edge_style, "act_dispatcher", "uc_map"))
    nodes.append(add_edge("e_d_3", "", edge_style, "act_dispatcher", "uc_list"))
    nodes.append(add_edge("e_d_4", "", edge_style, "act_dispatcher", "uc_manual"))
    nodes.append(add_edge("e_d_5", "", edge_style, "act_dispatcher", "uc_team_assign"))
    nodes.append(add_edge("e_d_6", "", edge_style, "act_dispatcher", "uc_update_status"))
    nodes.append(add_edge("e_d_7", "", edge_style, "act_dispatcher", "uc_manual_loc"))
    nodes.append(add_edge("e_d_8", "", edge_style, "act_dispatcher", "uc_export"))

    nodes.append(add_edge("e_a_1", "", edge_style, "act_admin", "uc_manage_acc"))
    nodes.append(add_edge("e_a_2", "", edge_style, "act_admin", "uc_backup"))

    nodes.append(add_edge("e_inc_1", "«include»", inc_style, "uc_post", "uc_ai"))
    nodes.append(add_edge("e_inc_2", "«include»", inc_style, "uc_post", "uc_outbox"))
    nodes.append(add_edge("e_inc_3", "«include»", inc_style, "uc_outbox", "uc_probe"))
    nodes.append(add_edge("e_ext_1", "«extend»\n(mất mạng)", ext_style, "uc_sms", "uc_probe"))
    nodes.append(add_edge("e_inc_4", "«include»", inc_style, "uc_ingest", "uc_dedup"))
    nodes.append(add_edge("e_inc_5", "«include»", inc_style, "uc_cluster", "uc_rank"))
    nodes.append(add_edge("e_inc_6", "«include»", inc_style, "uc_update_status", "uc_audit"))

    return create_diagram_xml("So-do-Use-Case-Tong-The", nodes)


# =========================================================================
# 2. USE CASE CHI TIẾT MOBILE APP
# =========================================================================
def generate_usecase_mobile():
    nodes = []
    nodes.append(add_cell("sys_bound", "PHÂN HỆ DI ĐỘNG BIÊN (EDGE MOBILE APP - FLUTTER)",
                          "shape=swimlane;whiteSpace=wrap;html=1;startSize=30;horizontal=1;fillColor=#F8F9FA;strokeColor=#1976D2;fontStyle=1;fontSize=14;fontFamily=Helvetica;",
                          x=260, y=40, w=880, h=780))

    actor_style = "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fontFamily=Helvetica;fontSize=12;fontStyle=1;"
    nodes.append(add_cell("act_citizen", "Người dân /\nNạn nhân", actor_style + "fillColor=#E3F2FD;strokeColor=#1976D2;", x=80, y=220, w=50, h=90))
    nodes.append(add_cell("act_rescuer", "Đội cứu hộ\nthực địa", actor_style + "fillColor=#E8F5E9;strokeColor=#388E3C;", x=80, y=520, w=50, h=90))
    nodes.append(add_cell("act_sms_gw", "SMS Gateway /\nNhà mạng", actor_style + "fillColor=#ECEFF1;strokeColor=#455A64;", x=1220, y=450, w=50, h=90))

    uc_style = "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1E88E5;fontFamily=Helvetica;fontSize=11;"
    nodes.append(add_cell("uc_m01", "UC-M01: Gửi SOS khẩn cấp\n(1 chạm, định vị nhanh)", uc_style, parent="sys_bound", x=60, y=60, w=210, h=60))
    nodes.append(add_cell("uc_m02", "UC-M02: Tạo báo cáo cứu nạn\n(số người kẹt, bị thương, yếu thế)", uc_style, parent="sys_bound", x=60, y=150, w=210, h=60))
    nodes.append(add_cell("uc_m03", "UC-M03: Chụp ảnh hiện trường\nngập lụt từ camera/thư viện", uc_style, parent="sys_bound", x=330, y=100, w=210, h=60))
    nodes.append(add_cell("uc_m04", "UC-M04: Phân loại mức ngập On-device\n(MobileNetV3 ONNX/ExecuTorch)", uc_style + "strokeColor=#D81B60;fillColor=#FCE4EC;", parent="sys_bound", x=600, y=100, w=240, h=60))
    nodes.append(add_cell("uc_m05", "UC-M05: Tự động tính độ khẩn cấp\n(Urgency Score)", uc_style, parent="sys_bound", x=330, y=190, w=210, h=60))
    nodes.append(add_cell("uc_m06", "UC-M06: Lưu trữ ngoại tuyến Outbox\n(Hive Box Store-and-Forward)", uc_style, parent="sys_bound", x=60, y=260, w=210, h=60))
    nodes.append(add_cell("uc_m07", "UC-M07: Đo thông lượng mạng (/probe)\n& Chọn chế độ truyền thích ứng", uc_style, parent="sys_bound", x=330, y=280, w=220, h=60))
    nodes.append(add_cell("uc_m08", "UC-M08: Nén ảnh thông minh\n(JPEG max 1024px, quality 60)", uc_style, parent="sys_bound", x=600, y=280, w=220, h=60))
    nodes.append(add_cell("uc_m09", "UC-M09: Gửi SMS dự phòng\nkhi mất hoàn toàn dữ liệu mạng", uc_style + "strokeColor=#E53935;fillColor=#FFEBEE;", parent="sys_bound", x=600, y=390, w=220, h=60))
    nodes.append(add_cell("uc_m10", "UC-M10: Đồng bộ tự động nền\n(WorkManager khi có mạng)", uc_style, parent="sys_bound", x=60, y=370, w=210, h=60))
    nodes.append(add_cell("uc_m11", "UC-M11: Theo dõi tiến trình cứu hộ\n(Polling 15s trạng thái)", uc_style, parent="sys_bound", x=60, y=470, w=210, h=60))
    nodes.append(add_cell("uc_m12", "UC-M12: Xem lịch sử yêu cầu\n& chi tiết phản hồi cứu hộ", uc_style, parent="sys_bound", x=60, y=570, w=210, h=60))

    edge_style = "endArrow=none;html=1;strokeColor=#546E7A;strokeWidth=1.2;"
    inc_style = "endArrow=open;dashed=1;html=1;strokeColor=#D81B60;strokeWidth=1.2;fontSize=10;fontColor=#D81B60;"
    ext_style = "endArrow=open;dashed=1;html=1;strokeColor=#E53935;strokeWidth=1.2;fontSize=10;fontColor=#E53935;"

    nodes.append(add_edge("e_mc_1", "", edge_style, "act_citizen", "uc_m01"))
    nodes.append(add_edge("e_mc_2", "", edge_style, "act_citizen", "uc_m02"))
    nodes.append(add_edge("e_mc_3", "", edge_style, "act_citizen", "uc_m11"))
    nodes.append(add_edge("e_mc_4", "", edge_style, "act_citizen", "uc_m12"))
    nodes.append(add_edge("e_mr_1", "", edge_style, "act_rescuer", "uc_m02"))
    nodes.append(add_edge("e_mr_2", "", edge_style, "act_rescuer", "uc_m11"))
    nodes.append(add_edge("e_mr_3", "", edge_style, "act_rescuer", "uc_m12"))
    nodes.append(add_edge("e_msms", "", edge_style, "uc_m09", "act_sms_gw"))

    nodes.append(add_edge("e_minc_1", "«include»", inc_style, "uc_m02", "uc_m03"))
    nodes.append(add_edge("e_minc_2", "«include»", inc_style, "uc_m03", "uc_m04"))
    nodes.append(add_edge("e_minc_3", "«include»", inc_style, "uc_m02", "uc_m05"))
    nodes.append(add_edge("e_minc_4", "«include»", inc_style, "uc_m02", "uc_m06"))
    nodes.append(add_edge("e_minc_5", "«include»", inc_style, "uc_m01", "uc_m06"))
    nodes.append(add_edge("e_minc_6", "«include»", inc_style, "uc_m06", "uc_m07"))
    nodes.append(add_edge("e_mext_1", "«extend»\n(50-1000 kbps)", ext_style, "uc_m08", "uc_m07"))
    nodes.append(add_edge("e_mext_2", "«extend»\n(mất mạng)", ext_style, "uc_m09", "uc_m07"))
    nodes.append(add_edge("e_minc_7", "«include»", inc_style, "uc_m06", "uc_m10"))

    return create_diagram_xml("So-do-Use-Case-Chi-tiet-Mobile-App", nodes, w="1400", h="900")


# =========================================================================
# 3. USE CASE CHI TIẾT WEB DASHBOARD & ADMIN
# =========================================================================
def generate_usecase_dashboard():
    nodes = []
    nodes.append(add_cell("sys_bound", "PHÂN HỆ ĐIỀU PHỐI & QUẢN TRỊ WEB (DISPATCH DASHBOARD)",
                          "shape=swimlane;whiteSpace=wrap;html=1;startSize=30;horizontal=1;fillColor=#FFFDE7;strokeColor=#F57C00;fontStyle=1;fontSize=14;fontFamily=Helvetica;",
                          x=260, y=40, w=880, h=820))

    actor_style = "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fontFamily=Helvetica;fontSize=12;fontStyle=1;"
    nodes.append(add_cell("act_dispatcher", "Điều phối viên\n(Dispatcher)", actor_style + "fillColor=#FFF3E0;strokeColor=#F57C00;", x=80, y=300, w=50, h=90))
    nodes.append(add_cell("act_admin", "Quản trị viên\n(Administrator)", actor_style + "fillColor=#EDE7F6;strokeColor=#512DA8;", x=1220, y=400, w=50, h=90))

    uc_style = "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#F57C00;fontFamily=Helvetica;fontSize=11;"
    nodes.append(add_cell("uc_d01", "UC-D01: Đăng nhập & Quản lý phiên\n(PBKDF2 session token)", uc_style, parent="sys_bound", x=60, y=60, w=220, h=60))
    nodes.append(add_cell("uc_d02", "UC-D02: Giám sát bản đồ sự cố không gian\n(Leaflet GIS hiển thị điểm & cụm)", uc_style, parent="sys_bound", x=60, y=140, w=230, h=60))
    nodes.append(add_cell("uc_d03", "UC-D03: Xem danh sách cụm cứu hộ\ntheo thứ bậc ưu tiên P(c)", uc_style, parent="sys_bound", x=60, y=220, w=220, h=60))
    nodes.append(add_cell("uc_d04", "UC-D04: Xem chi tiết báo cáo hiện trường\n(ảnh, nhãn AI, số nạn nhân, mô tả)", uc_style, parent="sys_bound", x=60, y=300, w=220, h=60))
    nodes.append(add_cell("uc_d05", "UC-D05: Quản lý hàng xem xét\n(Review Queue ca thiếu tọa độ)", uc_style + "fillColor=#FFF8E1;", parent="sys_bound", x=60, y=380, w=220, h=60))
    nodes.append(add_cell("uc_d06", "UC-D06: Bổ sung tọa độ thủ công\n(Chấm bản đồ hoặc nhập tọa độ)", uc_style, parent="sys_bound", x=340, y=380, w=220, h=60))
    nodes.append(add_cell("uc_d07", "UC-D07: Nhập báo cáo tổng đài/hotline\n(/api/reports/manual)", uc_style, parent="sys_bound", x=60, y=460, w=220, h=60))
    nodes.append(add_cell("uc_d08", "UC-D08: Giao / điều chuyển đội cứu hộ\n(/api/reports/{id}/team)", uc_style, parent="sys_bound", x=60, y=540, w=220, h=60))
    nodes.append(add_cell("uc_d09", "UC-D09: Cập nhật trạng thái nhiệm vụ\n(dispatched -> resolved / cancelled)", uc_style, parent="sys_bound", x=60, y=620, w=220, h=60))
    nodes.append(add_cell("uc_d10", "UC-D10: Xuất dữ liệu báo cáo cứu hộ\n(CSV, GeoJSON, thống kê)", uc_style, parent="sys_bound", x=60, y=700, w=220, h=60))

    uc_adm_style = "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#512DA8;fontFamily=Helvetica;fontSize=11;"
    nodes.append(add_cell("uc_d11", "UC-D11: Quản lý tài khoản điều phối\n(CRUD operators & phân quyền)", uc_adm_style, parent="sys_bound", x=600, y=300, w=230, h=60))
    nodes.append(add_cell("uc_d12", "UC-D12: Sao lưu & phục hồi CSDL/ảnh\n(/api/admin/backup)", uc_adm_style, parent="sys_bound", x=600, y=400, w=230, h=60))
    nodes.append(add_cell("uc_d13", "UC-D13: Tra cứu nhật ký kiểm toán\n(Audit Log report_events)", uc_adm_style, parent="sys_bound", x=600, y=500, w=230, h=60))

    edge_style = "endArrow=none;html=1;strokeColor=#546E7A;strokeWidth=1.2;"
    inc_style = "endArrow=open;dashed=1;html=1;strokeColor=#D81B60;strokeWidth=1.2;fontSize=10;fontColor=#D81B60;"
    ext_style = "endArrow=open;dashed=1;html=1;strokeColor=#E53935;strokeWidth=1.2;fontSize=10;fontColor=#E53935;"

    for u in ["uc_d01", "uc_d02", "uc_d03", "uc_d04", "uc_d05", "uc_d07", "uc_d08", "uc_d09", "uc_d10"]:
        nodes.append(add_edge(f"e_disp_{u}", "", edge_style, "act_dispatcher", u))

    for u in ["uc_d01", "uc_d11", "uc_d12", "uc_d13"]:
        nodes.append(add_edge(f"e_adm_{u}", "", edge_style, "act_admin", u))

    nodes.append(add_edge("e_dext_1", "«extend»\n(bổ sung GPS)", ext_style, "uc_d06", "uc_d05"))
    nodes.append(add_edge("e_dinc_1", "«include»", inc_style, "uc_d09", "uc_d13"))

    return create_diagram_xml("So-do-Use-Case-Chi-tiet-Dashboard", nodes, w="1400", h="950")


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
    lane_style = "shape=swimlane;whiteSpace=wrap;html=1;startSize=30;fontStyle=1;fontSize=13;fontFamily=Helvetica;"
    nodes.append(add_cell("tier_mobile", "TẦNG THIẾT BỊ DI ĐỘNG BIÊN (EDGE MOBILE CLIENT - FLUTTER)", lane_style + "fillColor=#EBF3FA;strokeColor=#1976D2;", x=40, y=40, w=460, h=880))
    nodes.append(add_cell("tier_backend", "TẦNG MÁY CHỦ TIẾP NHẬN & XỬ LÝ LÕI (FASTAPI BACKEND CORE)", lane_style + "fillColor=#F3E5F5;strokeColor=#6A1B9A;", x=540, y=40, w=540, h=880))
    nodes.append(add_cell("tier_dashboard", "TẦNG ĐIỀU PHỐI & QUẢN TRỊ WEB (DISPATCH DASHBOARD)", lane_style + "fillColor=#FFF8E1;strokeColor=#F57C00;", x=1120, y=40, w=440, h=880))

    # Tier 1 Components
    nodes.append(add_cell("m_ui", "Giao diện Người dùng (Presentation):\n- Màn hình SOS khẩn cấp (1 chạm)\n- Biểu mẫu Báo cáo Cứu hộ chi tiết\n- Màn hình Tra cứu tiến trình Cứu hộ", STYLE_ACT, parent="tier_mobile", x=30, y=50, w=400, h=70))
    nodes.append(add_cell("m_ctrl", "Tầng Logic & Quản lý Trạng thái:\n- FormController, LocationController\n- ConnectivityMonitor & ThroughputEvaluator\n- StatusPollingController (15s polling)", STYLE_ACT, parent="tier_mobile", x=30, y=150, w=400, h=70))
    nodes.append(add_cell("m_ai_eng", "Bộ Suy luận On-device AI (Edge AI Engine):\n- MobileNetV3-Large Backbone (256x256)\n- Custom Head phân loại 4 mức ngập (non/low/med/high)\n- Runtime kép: ONNX Runtime Dart & ExecuTorch (.pte)", STYLE_AI, parent="tier_mobile", x=30, y=250, w=400, h=85))
    nodes.append(add_cell("m_hive_store", "Lưu trữ Ngoại tuyến Outbox (Hive Store-and-Forward):\n- Hàng đợi Outbox Box (JSON RFC 8785 Canonical SHA-256)\n- Cache bản ghi cứu hộ & tiến trình trạng thái cục bộ", STYLE_DB, parent="tier_mobile", x=30, y=365, w=400, h=75))
    nodes.append(add_cell("m_bridge", "Cầu nối Phần cứng & Nền tảng (Platform Channels):\n- Định vị GPS (Geolocator)\n- SMS Telephony Bridge (Android SMS Manager)\n- WorkManager (Lịch trình đồng bộ ngầm khi có mạng)", "rounded=1;whiteSpace=wrap;html=1;fillColor=#ECEFF1;strokeColor=#455A64;fontSize=11;fontFamily=Helvetica;", parent="tier_mobile", x=30, y=470, w=400, h=75))

    # Tier 2 Components
    nodes.append(add_cell("be_api", "API Ingestion & Webhook Endpoints:\n- POST /sync/messages (JSON batch <= 50, idempotency)\n- POST /api/reports (Multipart Image + JSON metadata)\n- GET /probe (64 KB Network Bandwidth Probe)\n- POST /api/sms/inbound (SMS Gateway Webhook)\n- GET /api/reports/status (Status polling endpoint)", STYLE_ACT, parent="tier_backend", x=30, y=50, w=480, h=95))
    nodes.append(add_cell("be_dedup_eng", "Xử lý Toàn vẹn & Chống trùng lặp (Dedup Engine):\n- Kiểm tra Contract Version & Kích thước\n- Chuẩn hóa RFC 8785 JSON & SHA-256 Hashing\n- Tra cứu messages_dedup (Phát hiện mất ACK sau commit)\n- Merge Policy gộp ảnh/trường bổ sung theo owner", STYLE_OK, parent="tier_backend", x=30, y=175, w=480, h=85))
    nodes.append(add_cell("be_core", "Lõi Xử lý & Phân tích Đồ thị (rescue_core):\n- Data Adapter (to_report_v2: [F, U, N, V])\n- Review Queue Manager (Tách ca thiếu tọa độ GPS)\n- Graph Construction (Ma trận tương đồng Haversine + F + U)\n- Louvain Community Detection (Phân cụm không gian)\n- Priority Scoring P(c) = w1*Nc + w2*Vc + w3*Fc + w4*Uc", "rounded=1;whiteSpace=wrap;html=1;fillColor=#EFEBE9;strokeColor=#5D4037;fontSize=11;fontFamily=Helvetica;", parent="tier_backend", x=30, y=290, w=480, h=105))
    nodes.append(add_cell("be_db_store", "Cơ sở Dữ liệu Quan hệ (SQLite / PostgreSQL WAL):\n- Bảng: reports, messages_dedup, report_events\n- Bảng: teams, operators, sessions, server_meta", STYLE_DB, parent="tier_backend", x=30, y=425, w=480, h=75))
    nodes.append(add_cell("be_upload_fs", "Lưu trữ Tệp Vật lý (Local File System Storage):\n- Thư mục uploads/: Lưu trữ ảnh gốc & ảnh nén hiện trường", STYLE_DB, parent="tier_backend", x=30, y=530, w=480, h=60))

    # Tier 3 Components
    nodes.append(add_cell("d_auth", "Xác thực & Bảo mật Điều phối:\n- Đăng nhập PBKDF2 Session Token\n- Phân quyền Admin / Dispatcher Operator", STYLE_ACT, parent="tier_dashboard", x=20, y=50, w=400, h=65))
    nodes.append(add_cell("d_gis_map", "Bản đồ Giám sát Không gian (Leaflet GIS):\n- Hiển thị vị trí sự cố, ranh giới cụm & mức ưu tiên\n- Chấm tọa độ thủ công cho ca thiếu vị trí", STYLE_ACT, parent="tier_dashboard", x=20, y=145, w=400, h=75))
    nodes.append(add_cell("d_cluster_board", "Bảng Điều phối Thứ tự Ưu tiên:\n- Danh sách cụm theo thứ bậc điểm P(c)\n- Drawer Quản lý Hàng xem xét (Review Queue)", STYLE_ACT, parent="tier_dashboard", x=20, y=250, w=400, h=70))
    nodes.append(add_cell("d_case_modal", "Modal Thao tác Chi tiết Ca Cứu hộ:\n- Xem ảnh hiện trường, nhãn AI, số nạn nhân\n- Điều động / Gán đội cứu hộ (Teams Assignment)\n- Chuyển trạng thái (dispatched -> resolved / cancelled)", STYLE_OK, parent="tier_dashboard", x=20, y=350, w=400, h=85))
    nodes.append(add_cell("d_admin_tools", "Công cụ Quản trị & Báo cáo:\n- Xuất dữ liệu thống kê CSV / GeoJSON\n- Quản lý tài khoản điều phối & Sao lưu CSDL", STYLE_ACT, parent="tier_dashboard", x=20, y=465, w=400, h=75))

    # Inter-tier Connections
    nodes.append(add_edge("sa_e1", "Sync & Upload (HTTP)", STYLE_EDGE, "m_hive_store", "be_api"))
    nodes.append(add_edge("sa_e2", "SMS Webhook", STYLE_EDGE, "m_bridge", "be_api"))
    nodes.append(add_edge("sa_e3", "Probe & Polling", STYLE_EDGE, "m_ctrl", "be_api"))
    nodes.append(add_edge("sa_e4", "Inference Tags", STYLE_EDGE, "m_ai_eng", "m_ctrl"))
    nodes.append(add_edge("sa_e5", "Verify & Dedup", STYLE_EDGE, "be_api", "be_dedup_eng"))
    nodes.append(add_edge("sa_e6", "Commit Data", STYLE_EDGE, "be_dedup_eng", "be_db_store"))
    nodes.append(add_edge("sa_e7", "Save Image", STYLE_EDGE, "be_api", "be_upload_fs"))
    nodes.append(add_edge("sa_e8", "Fetch Reports", STYLE_EDGE, "be_db_store", "be_core"))
    nodes.append(add_edge("sa_e9", "Clusters + ETag", STYLE_EDGE, "be_core", "d_cluster_board"))
    nodes.append(add_edge("sa_e10", "Poll Changes (5s)", STYLE_EDGE, "d_gis_map", "be_api"))
    nodes.append(add_edge("sa_e11", "Assign & Status", STYLE_EDGE, "d_case_modal", "be_api"))

    return create_diagram_xml("Kien-truc-Tong-the-He-thong", nodes, w="1620", h="980")


# =========================================================================
# 8. SƠ ĐỒ THỰC THỂ LIÊN KẾT CSDL (DATABASE ERD)
# =========================================================================
def generate_database_erd():
    nodes = []
    tbl_style = "shape=table;startSize=30;container=1;collapsible=0;childLayout=tableLayout;fixedRows=1;rowLines=1;fontStyle=1;align=center;fontSize=12;fontFamily=Helvetica;fillColor=#EDE7F6;strokeColor=#512DA8;"
    row_style = "shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;top=0;left=0;bottom=0;right=0;collapsible=0;dropTarget=0;fillColor=none;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;"
    cell_pk = "shape=partialRectangle;connectable=0;fillColor=#FFF9C4;top=0;left=0;bottom=0;right=0;align=left;spacingLeft=6;fontStyle=1;fontSize=10;fontFamily=Helvetica;"
    cell_fk = "shape=partialRectangle;connectable=0;fillColor=#E1F5FE;top=0;left=0;bottom=0;right=0;align=left;spacingLeft=6;fontStyle=2;fontSize=10;fontFamily=Helvetica;"
    cell_def = "shape=partialRectangle;connectable=0;fillColor=#FFFFFF;top=0;left=0;bottom=0;right=0;align=left;spacingLeft=6;fontSize=10;fontFamily=Helvetica;"

    # Table: reports
    nodes.append(add_cell("t_reports", "Table: reports (Báo cáo cứu hộ)", tbl_style, x=500, y=80, w=340, h=350))
    cols_reports = [
        ("r_c1", "PK  id", "VARCHAR(64)", cell_pk),
        ("r_c2", "    status", "VARCHAR(20) [processing, dispatched...]", cell_def),
        ("r_c3", "    status_version", "INTEGER DEFAULT 1", cell_def),
        ("r_c4", "    lat, lng", "REAL (Nullable GPS coordinates)", cell_def),
        ("r_c5", "    location_source", "VARCHAR(20) [gps, manual, cell]", cell_def),
        ("r_c6", "    image_url", "VARCHAR(255) (Nullable path)", cell_def),
        ("r_c7", "    image_hash", "VARCHAR(64) (SHA-256)", cell_def),
        ("r_c8", "    owner_client_id", "VARCHAR(64)", cell_def),
        ("r_c9", "    payload_json", "TEXT (Original canonical payload)", cell_def),
        ("r_c10", "    payload_hash", "VARCHAR(64) (RFC 8785 SHA-256)", cell_def),
        ("r_c11", "FK  team_id", "VARCHAR(32) [Ref: teams.id]", cell_fk),
        ("r_c12", "    created_at, updated_at", "TIMESTAMP", cell_def),
    ]
    for cid, name, dtype, cstyle in cols_reports:
        nodes.append(add_cell(cid, f"{name} : {dtype}", cstyle, parent="t_reports", w=340, h=25))

    # Table: messages_dedup
    nodes.append(add_cell("t_dedup", "Table: messages_dedup (Chống trùng lặp)", tbl_style, x=80, y=80, w=320, h=200))
    cols_dedup = [
        ("d_c1", "PK  message_id", "VARCHAR(64)", cell_pk),
        ("d_c2", "PK  client_id", "VARCHAR(64)", cell_pk),
        ("d_c3", "    sequence_number", "INTEGER", cell_def),
        ("d_c4", "    payload_hash", "VARCHAR(64)", cell_def),
        ("d_c5", "FK  report_id", "VARCHAR(64) [Ref: reports.id]", cell_fk),
        ("d_c6", "    received_at", "TIMESTAMP", cell_def),
    ]
    for cid, name, dtype, cstyle in cols_dedup:
        nodes.append(add_cell(cid, f"{name} : {dtype}", cstyle, parent="t_dedup", w=320, h=25))

    # Table: report_events
    nodes.append(add_cell("t_events", "Table: report_events (Nhật ký truy vết)", tbl_style, x=940, y=80, w=320, h=200))
    cols_events = [
        ("e_c1", "PK  id", "INTEGER AUTOINCREMENT", cell_pk),
        ("e_c2", "FK  report_id", "VARCHAR(64) [Ref: reports.id]", cell_fk),
        ("e_c3", "    actor", "VARCHAR(64) (operator/system/app)", cell_def),
        ("e_c4", "    action", "VARCHAR(32) (create/status/location)", cell_def),
        ("e_c5", "    metadata_json", "TEXT (Event snapshot)", cell_def),
        ("e_c6", "    created_at", "TIMESTAMP", cell_def),
    ]
    for cid, name, dtype, cstyle in cols_events:
        nodes.append(add_cell(cid, f"{name} : {dtype}", cstyle, parent="t_events", w=320, h=25))

    # Table: teams
    nodes.append(add_cell("t_teams", "Table: teams (Đội cứu hộ thực địa)", tbl_style, x=500, y=500, w=340, h=175))
    cols_teams = [
        ("tm_c1", "PK  id", "VARCHAR(32)", cell_pk),
        ("tm_c2", "    name", "VARCHAR(100)", cell_def),
        ("tm_c3", "    contact_phone", "VARCHAR(50)", cell_def),
        ("tm_c4", "    status", "VARCHAR(20) [available, dispatched...]", cell_def),
        ("tm_c5", "    members_count", "INTEGER", cell_def),
    ]
    for cid, name, dtype, cstyle in cols_teams:
        nodes.append(add_cell(cid, f"{name} : {dtype}", cstyle, parent="t_teams", w=340, h=25))

    # Table: operators
    nodes.append(add_cell("t_operators", "Table: operators (Tài khoản điều phối)", tbl_style, x=940, y=360, w=320, h=175))
    cols_operators = [
        ("op_c1", "PK  username", "VARCHAR(50)", cell_pk),
        ("op_c2", "    password_hash", "VARCHAR(255) (PBKDF2-SHA256)", cell_def),
        ("op_c3", "    role", "VARCHAR(20) [admin, operator]", cell_def),
        ("op_c4", "    full_name", "VARCHAR(100)", cell_def),
        ("op_c5", "    created_at", "TIMESTAMP", cell_def),
    ]
    for cid, name, dtype, cstyle in cols_operators:
        nodes.append(add_cell(cid, f"{name} : {dtype}", cstyle, parent="t_operators", w=320, h=25))

    # Table: sessions
    nodes.append(add_cell("t_sessions", "Table: sessions (Phiên đăng nhập)", tbl_style, x=940, y=600, w=320, h=150))
    cols_sessions = [
        ("s_c1", "PK  token_hash", "VARCHAR(64)", cell_pk),
        ("s_c2", "FK  username", "VARCHAR(50) [Ref: operators]", cell_fk),
        ("s_c3", "    created_at", "TIMESTAMP", cell_def),
        ("s_c4", "    expires_at", "TIMESTAMP", cell_def),
    ]
    for cid, name, dtype, cstyle in cols_sessions:
        nodes.append(add_cell(cid, f"{name} : {dtype}", cstyle, parent="t_sessions", w=320, h=25))

    # Table: server_meta
    nodes.append(add_cell("t_meta", "Table: server_meta (Metadata hệ thống)", tbl_style, x=80, y=360, w=320, h=150))
    cols_meta = [
        ("m_c1", "PK  key", "VARCHAR(50)", cell_pk),
        ("m_c2", "    value", "TEXT (Cluster version, epoch, seeds)", cell_def),
        ("m_c3", "    updated_at", "TIMESTAMP", cell_def),
    ]
    for cid, name, dtype, cstyle in cols_meta:
        nodes.append(add_cell(cid, f"{name} : {dtype}", cstyle, parent="t_meta", w=320, h=25))

    # Relationships
    erd_edge = "endArrow=diamondThin;endFill=1;startArrow=none;html=1;strokeColor=#455A64;strokeWidth=1.5;fontSize=10;"
    nodes.append(add_edge("erd_e1", "1 : N (Dedup -> Report)", erd_edge, "t_reports", "t_dedup"))
    nodes.append(add_edge("erd_e2", "1 : N (Report -> Events)", erd_edge, "t_reports", "t_events"))
    nodes.append(add_edge("erd_e3", "1 : N (Team -> Reports)", erd_edge, "t_teams", "t_reports"))
    nodes.append(add_edge("erd_e4", "1 : N (Operator -> Sessions)", erd_edge, "t_operators", "t_sessions"))

    return create_diagram_xml("So-do-Thuc-the-Lien-ket-CSDL-ERD", nodes, w="1350", h="850")


# =========================================================================
# 9. KIẾN TRÚC PHÂN LỚP MOBILE FLUTTER (CLEAN ARCHITECTURE)
# =========================================================================
def generate_mobile_architecture():
    nodes = []
    layer_style = "shape=swimlane;whiteSpace=wrap;html=1;startSize=28;fontStyle=1;fontSize=12;fontFamily=Helvetica;"

    nodes.append(add_cell("l_pres", "1. PRESENTATION LAYER (GIAO DIỆN & TRẠNG THÁI)", layer_style + "fillColor=#E3F2FD;strokeColor=#1976D2;", x=40, y=40, w=1120, h=180))
    nodes.append(add_cell("l_dom", "2. DOMAIN LAYER (NGHIỆP VỤ & QUY TẮC CỐT LÕI)", layer_style + "fillColor=#EDE7F6;strokeColor=#512DA8;", x=40, y=250, w=1120, h=180))
    nodes.append(add_cell("l_data", "3. DATA LAYER (DỮ LIỆU & REPOSITORY IMPLEMENTATION)", layer_style + "fillColor=#E8F5E9;strokeColor=#2E7D32;", x=40, y=460, w=1120, h=200))
    nodes.append(add_cell("l_plat", "4. PLATFORM CHANNELS & NATIVE HARDWARE BRIDGES", layer_style + "fillColor=#ECEFF1;strokeColor=#455A64;", x=40, y=690, w=1120, h=150))

    # Presentation Layer
    nodes.append(add_cell("p_views", "UI Views / Screens:\n- SosScreen (Gửi SOS 1 chạm)\n- CreateReportScreen (Biểu mẫu kèm ảnh)\n- RescueTimelineScreen (Tra cứu tiến trình)\n- MapOverviewScreen (Bản đồ offline)", STYLE_ACT, parent="l_pres", x=40, y=50, w=480, h=95))
    nodes.append(add_cell("p_ctrl", "Controllers / State Management:\n- SosController & ReportFormController\n- ConnectivityController & ProbeEvaluator\n- StatusPollingController (15s Timer)", STYLE_ACT, parent="l_pres", x=580, y=50, w=480, h=95))

    # Domain Layer
    nodes.append(add_cell("d_ent", "Entities & Models:\n- RescueRecord (id, status, gps, urgency)\n- AiTag (label, confidence)\n- SendMode (smsFallback, metadataOnly, compressedImage, originalImage)", STYLE_ACT, parent="l_dom", x=40, y=50, w=480, h=95))
    nodes.append(add_cell("d_uc", "Use Cases & Business Policies:\n- AnalyzeImageUseCase (Khởi chạy mô hình AI)\n- DeliverRecordUseCase (Chính sách thích ứng)\n- ProbeNetworkUseCase & PollStatusUseCase", STYLE_ACT, parent="l_dom", x=580, y=50, w=480, h=95))

    # Data Layer
    nodes.append(add_cell("dt_repo", "Repository Implementations:\n- RescueRepositoryImpl\n- InferenceRepositoryImpl (Conditional export)\n- NetworkProbeRepositoryImpl", STYLE_ACT, parent="l_data", x=40, y=45, w=340, h=120))
    nodes.append(add_cell("dt_local", "Local DataSources:\n- HiveBoxLocalDataSource (Outbox store-and-forward)\n- RFC 8785 Canonical JSON Encoder & SHA-256 Hasher", STYLE_DB, parent="l_data", x=420, y=45, w=330, h=120))
    nodes.append(add_cell("dt_remote", "Remote & Native DataSources:\n- HttpRemoteDataSource (FastAPI REST Client)\n- SmsRemoteDataSource (Android SMS Bridge)\n- OnnxInferenceDataSource (onnxruntime package)\n- ExecutorchMethodChannel (C++ Android Runner)", STYLE_ACT, parent="l_data", x=780, y=45, w=310, h=120))

    # Platform Layer
    nodes.append(add_cell("pl_gps", "Geolocator (GPS Sensor)", STYLE_ACT, parent="l_plat", x=60, y=50, w=220, h=60))
    nodes.append(add_cell("pl_cam", "Camera & Gallery Picker", STYLE_ACT, parent="l_plat", x=320, y=50, w=220, h=60))
    nodes.append(add_cell("pl_sms", "Android SMS Telephony Manager", STYLE_WARN, parent="l_plat", x=580, y=50, w=240, h=60))
    nodes.append(add_cell("pl_wm", "WorkManager (Background Tasks)", STYLE_ACT, parent="l_plat", x=860, y=50, w=220, h=60))

    # Connectors
    nodes.append(add_edge("ma_e1", "Calls", STYLE_EDGE, "p_ctrl", "d_uc"))
    nodes.append(add_edge("ma_e2", "Implements", STYLE_EDGE, "dt_repo", "d_uc"))
    nodes.append(add_edge("ma_e3", "Uses", STYLE_EDGE, "dt_repo", "dt_local"))
    nodes.append(add_edge("ma_e4", "Uses", STYLE_EDGE, "dt_repo", "dt_remote"))
    nodes.append(add_edge("ma_e5", "Hardware Channel", STYLE_EDGE, "dt_remote", "pl_sms"))

    return create_diagram_xml("Kien-truc-Phan-lop-Mobile-Flutter", nodes, w="1220", h="900")


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
