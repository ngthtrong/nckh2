#!/usr/bin/env python3
"""Sinh trọn bộ sơ đồ Draw.io (native XML) cho báo cáo NCKH THS2026-68.
Tạo các tệp tại report/assets/diagrams/:
  - usecase.drawio (Tổng thể)
  - usecase_mobile.drawio (Chi tiết Mobile App)
  - usecase_dashboard.drawio (Chi tiết Dashboard & Admin)
  - flowchart.drawio (Tổng thể 4 làn End-to-End)
  - flowchart_adaptive_mobile.drawio (Chi tiết thích ứng mạng & Edge AI)
  - flowchart_backend_dedup.drawio (Chi tiết Idempotency & Dedup)
"""
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "report" / "assets" / "diagrams"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def create_diagram_xml(title: str, elements: list, w="1654", h="1169") -> str:
    mxfile = ET.Element("mxfile", host="app.diagrams.net", agent="Antigravity", version="24.0.0")
    diagram = ET.SubElement(mxfile, "diagram", id="diag-1", name=title)
    model = ET.SubElement(diagram, "mxGraphModel", dx="1422", dy="800", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth=w, pageHeight=h, math="0", shadow="0")
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")

    for elem in elements:
        root.append(elem)

    return ET.tostring(mxfile, encoding="utf-8", xml_declaration=True).decode("utf-8")


def add_cell(cell_id, value, style, parent="1", vertex="1", x=0, y=0, w=120, h=60):
    cell = ET.Element("mxCell", {"id": str(cell_id), "value": value, "style": style, "parent": str(parent), "vertex": str(vertex)})
    ET.SubElement(cell, "mxGeometry", {"x": str(x), "y": str(y), "width": str(w), "height": str(h), "as": "geometry"})
    return cell


def add_edge(edge_id, value, style, source, target, parent="1"):
    cell = ET.Element("mxCell", {"id": str(edge_id), "value": value, "style": style, "parent": str(parent), "edge": "1", "source": str(source), "target": str(target)})
    ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
    return cell


# -------------------------------------------------------------------------
# 1. USE CASE TỔNG THỂ
# -------------------------------------------------------------------------
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


# -------------------------------------------------------------------------
# 2. FLOWCHART TỔNG THỂ 4 LÀN (END-TO-END)
# -------------------------------------------------------------------------
def generate_flowchart():
    nodes = []
    lane_style = "shape=swimlane;whiteSpace=wrap;html=1;startSize=28;fontStyle=1;fontSize=12;fontFamily=Helvetica;"
    nodes.append(add_cell("lane_mobile", "ỨNG DỤNG DI ĐỘNG (EDGE MOBILE APP)", lane_style + "fillColor=#E3F2FD;strokeColor=#1976D2;", x=40, y=40, w=420, h=1060))
    nodes.append(add_cell("lane_server", "MÁY CHỦ TIẾP NHẬN & DEDUP (FASTAPI / SQLITE)", lane_style + "fillColor=#EDE7F6;strokeColor=#512DA8;", x=500, y=40, w=450, h=1060))
    nodes.append(add_cell("lane_core", "LÕI PHÂN CỤM & ƯU TIÊN (RESCUE_CORE)", lane_style + "fillColor=#EFEBE9;strokeColor=#5D4037;", x=990, y=40, w=420, h=1060))
    nodes.append(add_cell("lane_dash", "ĐIỀU PHỐI VIÊN & ĐỘI CỨU HỘ (DASHBOARD)", lane_style + "fillColor=#FFF8E1;strokeColor=#F57C00;", x=1450, y=40, w=420, h=1060))

    start_style = "ellipse;whiteSpace=wrap;html=1;fillColor=#4CAF50;strokeColor=#2E7D32;fontColor=#FFFFFF;fontStyle=1;"
    end_style = "ellipse;whiteSpace=wrap;html=1;fillColor=#607D8B;strokeColor=#37474F;fontColor=#FFFFFF;fontStyle=1;"
    act_style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1E88E5;fontSize=11;fontFamily=Helvetica;"
    dec_style = "rhombus;whiteSpace=wrap;html=1;fillColor=#FFF3E0;strokeColor=#FB8C00;fontSize=10;fontFamily=Helvetica;"
    db_style = "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;fillColor=#ECEFF1;strokeColor=#455A64;fontSize=10;"

    # Lane 1: Mobile Flow
    nodes.append(add_cell("m_start", "Bắt đầu\n(Mở App)", start_style, parent="lane_mobile", x=160, y=50, w=100, h=40))
    nodes.append(add_cell("m_choose", "Chọn: Gửi SOS 1 chạm\nhoặc Báo cáo chi tiết", act_style, parent="lane_mobile", x=120, y=110, w=180, h=45))
    nodes.append(add_cell("m_ai", "Chụp ảnh -> On-device AI\n(MobileNetV3 ONNX/ExecuTorch)\n-> Mức ngập & Confidence", act_style + "fillColor=#FCE4EC;strokeColor=#D81B60;", parent="lane_mobile", x=120, y=180, w=180, h=55))
    nodes.append(add_cell("m_form", "Nhập tọa độ (GPS/tay),\nsố người kẹt, bị thương,\nnhóm yếu thế -> Urgency score", act_style, parent="lane_mobile", x=120, y=260, w=180, h=50))
    nodes.append(add_cell("m_hive", "Ghi Outbox (Hive)\nStore-and-Forward\n(RFC 8785 SHA-256 hash)", db_style, parent="lane_mobile", x=135, y=335, w=150, h=55))
    nodes.append(add_cell("m_probe", "Đo throughput\n(GET /probe 64 KB)", act_style, parent="lane_mobile", x=135, y=415, w=150, h=40))
    nodes.append(add_cell("m_net_dec", "Đánh giá mạng\n& Confidence AI", dec_style, parent="lane_mobile", x=140, y=480, w=140, h=65))
    
    nodes.append(add_cell("m_sms", "Gửi SMS dự phòng\ntới Gateway\n(kèm pending Outbox)", act_style + "fillColor=#FFEBEE;strokeColor=#E53935;", parent="lane_mobile", x=20, y=575, w=130, h=50))
    nodes.append(add_cell("m_meta_only", "Gửi chỉ Metadata JSON\n(POST /sync/messages)", act_style, parent="lane_mobile", x=160, y=575, w=140, h=50))
    nodes.append(add_cell("m_img_post", "Nén/giữ ảnh + Meta\n(POST /api/reports multipart)", act_style, parent="lane_mobile", x=280, y=650, w=130, h=50))
    
    nodes.append(add_cell("m_wait_ack", "Nhận phản hồi ACK\n& cập nhật synced=true", act_style, parent="lane_mobile", x=135, y=730, w=150, h=45))
    nodes.append(add_cell("m_poll", "Polling 15s trạng thái\n(GET /api/reports/status)\nnhận tiến trình cứu hộ", act_style, parent="lane_mobile", x=135, y=805, w=150, h=50))
    nodes.append(add_cell("m_end", "Kết thúc\n(Được cứu / Hoàn tất)", end_style, parent="lane_mobile", x=160, y=890, w=100, h=40))

    # Lane 2: Server Flow
    nodes.append(add_cell("s_recv", "Tiếp nhận Request\n(Sync batch / Reports / SMS)", act_style, parent="lane_server", x=140, y=180, w=170, h=45))
    nodes.append(add_cell("s_val", "Kiểm tra Header version,\nbounds size & tính canonical\nSHA-256 payload", act_style, parent="lane_server", x=140, y=250, w=170, h=55))
    nodes.append(add_cell("s_dedup_dec", "Tra cứu messages_dedup\n(message_id, hash, seq)", dec_style, parent="lane_server", x=145, y=330, w=160, h=70))
    
    nodes.append(add_cell("s_dup", "Trùng id & hash:\nTrả ACK duplicate cũ\n(Idempotent, không ghi đè)", act_style + "fillColor=#E8F5E9;strokeColor=#4CAF50;", parent="lane_server", x=20, y=430, w=135, h=55))
    nodes.append(add_cell("s_rej", "Trùng id khác hash /\ntái sử dụng sequence:\nTừ chối 409 Conflict", act_style + "fillColor=#FFEBEE;strokeColor=#E53935;", parent="lane_server", x=295, y=430, w=135, h=55))
    nodes.append(add_cell("s_tx", "Thao tác hợp lệ:\nMở DB Transaction,\nKiểm tra report_owner\n(Merge ảnh/trường trống)", act_style, parent="lane_server", x=140, y=515, w=170, h=65))
    
    nodes.append(add_cell("s_db", "Lưu SQLite: reports,\nmessages_dedup, files ảnh;\nGhi log report_events", db_style, parent="lane_server", x=145, y=610, w=160, h=60))
    nodes.append(add_cell("s_meta", "Tăng version dữ liệu\ntrong server_meta\n(đánh dấu cụm stale)", act_style, parent="lane_server", x=145, y=700, w=160, h=45))
    nodes.append(add_cell("s_ack", "Trả HTTP Response\n(accepted / 201 Created)", act_style, parent="lane_server", x=145, y=770, w=160, h=40))

    # Lane 3: Core Flow
    nodes.append(add_cell("c_trig", "Kích hoạt phân cụm\n(Polling Dashboard /\nbackground warmup)", act_style, parent="lane_core", x=130, y=200, w=160, h=45))
    nodes.append(add_cell("c_ver_dec", "Kiểm tra ETag /\ncluster_version đổi?", dec_style, parent="lane_core", x=140, y=275, w=140, h=60))
    nodes.append(add_cell("c_304", "Không đổi: Trả 304\nNot Modified (ETag)", act_style, parent="lane_core", x=20, y=360, w=120, h=45))
    nodes.append(add_cell("c_fetch", "Có đổi: Lấy danh sách\nbáo cáo active_only\n(bỏ resolved/cancelled)", act_style, parent="lane_core", x=140, y=360, w=160, h=50))
    nodes.append(add_cell("c_adapt", "Adapter to_report_v2:\nTrích xuất [F, U, N, V],\nTách ca thiếu tọa độ", act_style, parent="lane_core", x=140, y=435, w=160, h=50))
    
    nodes.append(add_cell("c_rev", "Đưa ca thiếu GPS vào\nHàng xem xét (Review Queue)", act_style + "fillColor=#FFF3E0;strokeColor=#FB8C00;", parent="lane_core", x=20, y=515, w=140, h=50))
    nodes.append(add_cell("c_graph", "Xây dựng ma trận tương đồng\nC_ij (khoảng cách Haversine,\nmức ngập, độ khẩn cấp)", act_style, parent="lane_core", x=180, y=515, w=170, h=55))
    nodes.append(add_cell("c_louvain", "Phân cụm cộng đồng Louvain\n& Xác định clusterKey\n(ID nhỏ nhất trong cụm)", act_style, parent="lane_core", x=180, y=595, w=170, h=55))
    nodes.append(add_cell("c_score", "Tính điểm ưu tiên P(c)\ncho từng cụm -> Xếp hạng cụm\n& Ghi cache Snapshot", act_style, parent="lane_core", x=140, y=675, w=160, h=50))
    nodes.append(add_cell("c_resp", "Trả JSON cụm + ETag\ncho Dashboard", act_style, parent="lane_core", x=140, y=750, w=160, h=40))

    # Lane 4: Dashboard Flow
    nodes.append(add_cell("d_login", "Đăng nhập Dashboard\n(Phiên làm việc Operator)", act_style, parent="lane_dash", x=130, y=100, w=160, h=45))
    nodes.append(add_cell("d_poll", "Polling 5s (/changes)\n& Cập nhật bản đồ Leaflet\n+ Hàng xem xét / Cụm", act_style, parent="lane_dash", x=130, y=170, w=160, h=50))
    nodes.append(add_cell("d_view", "Chọn cụm/báo cáo:\nXem ảnh, nhãn AI, vị trí,\nsố nạn nhân, gọi xác minh", act_style, parent="lane_dash", x=130, y=245, w=160, h=55))
    nodes.append(add_cell("d_loc_sup", "Bổ sung vị trí thủ công\n(nếu ca thuộc Review Queue)", act_style, parent="lane_dash", x=130, y=325, w=160, h=45))
    nodes.append(add_cell("d_assign", "Giao đội cứu hộ (teams)\n& Chuyển status -> dispatched\n(tăng statusVersion)", act_style + "fillColor=#E8F5E9;strokeColor=#2E7D32;", parent="lane_dash", x=130, y=395, w=160, h=55))
    nodes.append(add_cell("d_field", "Đội cứu hộ nhận lệnh,\ntiếp cận hiện trường,\ntriển khai ứng cứu", act_style, parent="lane_dash", x=130, y=475, w=160, h=50))
    nodes.append(add_cell("d_res_dec", "Kết quả cứu hộ\ntại hiện trường?", dec_style, parent="lane_dash", x=145, y=550, w=130, h=60))
    
    nodes.append(add_cell("d_ok", "Thành công: Cập nhật\nstatus -> resolved", act_style + "fillColor=#E8F5E9;strokeColor=#4CAF50;", parent="lane_dash", x=40, y=635, w=140, h=45))
    nodes.append(add_cell("d_cancel", "Hủy / Tin giả: Cập nhật\nstatus -> cancelled\n(bắt buộc chọn reason)", act_style + "fillColor=#FFEBEE;strokeColor=#E53935;", parent="lane_dash", x=210, y=635, w=140, h=50))
    nodes.append(add_cell("d_log", "Hệ thống ghi report_events\n(actor, action, timestamp);\nLoại khỏi active clusters", act_style, parent="lane_dash", x=130, y=715, w=160, h=50))
    nodes.append(add_cell("d_export", "Xuất báo cáo tổng kết\n(CSV / GeoJSON / Stats)", act_style, parent="lane_dash", x=130, y=790, w=160, h=45))

    edge_style = "endArrow=classic;html=1;strokeColor=#37474F;strokeWidth=1.3;fontSize=10;"
    lbl_style = edge_style + "fontColor=#0D47A1;"

    nodes.append(add_edge("fl_m1", "", edge_style, "m_start", "m_choose"))
    nodes.append(add_edge("fl_m2", "", edge_style, "m_choose", "m_ai"))
    nodes.append(add_edge("fl_m3", "", edge_style, "m_ai", "m_form"))
    nodes.append(add_edge("fl_m4", "", edge_style, "m_form", "m_hive"))
    nodes.append(add_edge("fl_m5", "", edge_style, "m_hive", "m_probe"))
    nodes.append(add_edge("fl_m6", "", edge_style, "m_probe", "m_net_dec"))
    nodes.append(add_edge("fl_m7", "Mất mạng", lbl_style, "m_net_dec", "m_sms"))
    nodes.append(add_edge("fl_m8", "Yếu / conf cao", lbl_style, "m_net_dec", "m_meta_only"))
    nodes.append(add_edge("fl_m9", "Tốt / ảnh nén", lbl_style, "m_net_dec", "m_img_post"))
    
    nodes.append(add_edge("fl_x1", "Gửi tin", edge_style, "m_sms", "s_recv"))
    nodes.append(add_edge("fl_x2", "Sync", edge_style, "m_meta_only", "s_recv"))
    nodes.append(add_edge("fl_x3", "Upload", edge_style, "m_img_post", "s_recv"))

    nodes.append(add_edge("fl_s1", "", edge_style, "s_recv", "s_val"))
    nodes.append(add_edge("fl_s2", "", edge_style, "s_val", "s_dedup_dec"))
    nodes.append(add_edge("fl_s3", "Duplicate", lbl_style, "s_dedup_dec", "s_dup"))
    nodes.append(add_edge("fl_s4", "Xung đột", lbl_style, "s_dedup_dec", "s_rej"))
    nodes.append(add_edge("fl_s5", "Hợp lệ", lbl_style, "s_dedup_dec", "s_tx"))
    nodes.append(add_edge("fl_s6", "", edge_style, "s_tx", "s_db"))
    nodes.append(add_edge("fl_s7", "", edge_style, "s_db", "s_meta"))
    nodes.append(add_edge("fl_s8", "", edge_style, "s_meta", "s_ack"))
    nodes.append(add_edge("fl_s9", "ACK", edge_style, "s_ack", "m_wait_ack"))
    nodes.append(add_edge("fl_s10", "", edge_style, "m_wait_ack", "m_poll"))
    nodes.append(add_edge("fl_s11", "", edge_style, "m_poll", "m_end"))

    nodes.append(add_edge("fl_sc1", "Dữ liệu mới", edge_style, "s_meta", "c_trig"))
    nodes.append(add_edge("fl_c1", "", edge_style, "c_trig", "c_ver_dec"))
    nodes.append(add_edge("fl_c2", "Không đổi", lbl_style, "c_ver_dec", "c_304"))
    nodes.append(add_edge("fl_c3", "Đổi", lbl_style, "c_ver_dec", "c_fetch"))
    nodes.append(add_edge("fl_c4", "", edge_style, "c_fetch", "c_adapt"))
    nodes.append(add_edge("fl_c5", "Thiếu GPS", lbl_style, "c_adapt", "c_rev"))
    nodes.append(add_edge("fl_c6", "Có GPS", lbl_style, "c_adapt", "c_graph"))
    nodes.append(add_edge("fl_c7", "", edge_style, "c_graph", "c_louvain"))
    nodes.append(add_edge("fl_c8", "", edge_style, "c_louvain", "c_score"))
    nodes.append(add_edge("fl_c9", "", edge_style, "c_score", "c_resp"))

    nodes.append(add_edge("fl_cd1", "Cụm & ETag", edge_style, "c_resp", "d_poll"))
    nodes.append(add_edge("fl_d1", "", edge_style, "d_login", "d_poll"))
    nodes.append(add_edge("fl_d2", "", edge_style, "d_poll", "d_view"))
    nodes.append(add_edge("fl_d3", "Cần bổ sung vị trí", lbl_style, "d_view", "d_loc_sup"))
    nodes.append(add_edge("fl_d4", "", edge_style, "d_loc_sup", "d_assign"))
    nodes.append(add_edge("fl_d5", "Đã đủ vị trí", lbl_style, "d_view", "d_assign"))
    nodes.append(add_edge("fl_d6", "", edge_style, "d_assign", "d_field"))
    nodes.append(add_edge("fl_d7", "", edge_style, "d_field", "d_res_dec"))
    nodes.append(add_edge("fl_d8", "Thành công", lbl_style, "d_res_dec", "d_ok"))
    nodes.append(add_edge("fl_d9", "Hủy / Lỗi", lbl_style, "d_res_dec", "d_cancel"))
    nodes.append(add_edge("fl_d10", "", edge_style, "d_ok", "d_log"))
    nodes.append(add_edge("fl_d11", "", edge_style, "d_cancel", "d_log"))
    nodes.append(add_edge("fl_d12", "", edge_style, "d_log", "d_export"))

    nodes.append(add_edge("fl_ds1", "PATCH /status", edge_style, "d_assign", "s_recv"))
    nodes.append(add_edge("fl_ds2", "Update status", edge_style, "d_log", "s_recv"))

    return create_diagram_xml("Luu-do-Quy-trinh-He-thong", nodes)


# -------------------------------------------------------------------------
# 3. FLOWCHART CHI TIẾT ADAPTIVE MOBILE
# -------------------------------------------------------------------------
def generate_flowchart_adaptive_mobile():
    nodes = []
    start_style = "ellipse;whiteSpace=wrap;html=1;fillColor=#4CAF50;strokeColor=#2E7D32;fontColor=#FFFFFF;fontStyle=1;"
    end_style = "ellipse;whiteSpace=wrap;html=1;fillColor=#607D8B;strokeColor=#37474F;fontColor=#FFFFFF;fontStyle=1;"
    act_style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1E88E5;fontSize=11;fontFamily=Helvetica;"
    dec_style = "rhombus;whiteSpace=wrap;html=1;fillColor=#FFF3E0;strokeColor=#FB8C00;fontSize=10;fontFamily=Helvetica;"
    db_style = "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;fillColor=#ECEFF1;strokeColor=#455A64;fontSize=10;"
    edge_style = "endArrow=classic;html=1;strokeColor=#37474F;strokeWidth=1.3;fontSize=10;"

    nodes.append(add_cell("am_start", "Khởi tạo Báo cáo\n(SOS / Post)", start_style, x=340, y=40, w=160, h=45))
    nodes.append(add_cell("am_img_dec", "Người dùng có\nđính kèm ảnh?", dec_style, x=350, y=115, w=140, h=65))
    nodes.append(add_cell("am_ai", "Edge AI MobileNetV3 suy luận:\n- Nhãn ngập: non/low/med/high\n- Confidence score", act_style + "fillColor=#FCE4EC;strokeColor=#D81B60;", x=160, y=210, w=200, h=55))
    nodes.append(add_cell("am_no_img", "Không có ảnh:\nGán nhãn non_flood mặc định", act_style, x=480, y=215, w=180, h=45))
    nodes.append(add_cell("am_fields", "Nhập thông tin cứu hộ:\n- Tọa độ GPS (hoặc để trống/nhập tay)\n- Số người kẹt, số người bị thương\n- Nhóm yếu thế (người già, trẻ nhỏ...)\n- Tự động tính Urgency Score", act_style, x=310, y=295, w=220, h=75))
    nodes.append(add_cell("am_hive", "Ghi ngay vào Hive Outbox\n(Store-and-forward cục bộ)\nTrạng thái: pending", db_style, x=345, y=395, w=150, h=60))
    nodes.append(add_cell("am_probe", "Gọi GET /probe (64 KB)\nĐo thông lượng mạng thực tế (kbps)", act_style, x=330, y=485, w=180, h=45))
    nodes.append(add_cell("am_net_eval", "Phân loại thông lượng\n& Điều kiện gửi?", dec_style, x=330, y=560, w=180, h=75))

    # Branches
    nodes.append(add_cell("am_sms", "MẤT MẠNG HOÀN TOÀN:\n- Kiểm tra số hotline SMS Android\n- Gửi tin SOS|id:... qua SMS\n- Giữ bản ghi trong Outbox chờ mạng", act_style + "fillColor=#FFEBEE;strokeColor=#E53935;", x=40, y=670, w=200, h=65))
    nodes.append(add_cell("am_meta", "MẠNG YẾU (<50 kbps)\nhoặc (Mạnh & Conf >= 0.90):\n- Gửi metadata JSON qua\n  POST /sync/messages (<=256 KB)", act_style, x=265, y=670, w=190, h=65))
    nodes.append(add_cell("am_comp", "MẠNG TRUNG BÌNH (50-1000 kbps):\n- Nén JPEG (max 1024px, q=60)\n- Gửi multipart qua POST /api/reports", act_style + "fillColor=#FFF8E1;strokeColor=#F57C00;", x=480, y=670, w=200, h=65))
    nodes.append(add_cell("am_orig", "MẠNG MẠNH (>=1000 kbps & Conf<0.9):\n- Giữ nguyên ảnh gốc\n- Gửi multipart POST /api/reports", act_style + "fillColor=#E8F5E9;strokeColor=#4CAF50;", x=705, y=670, w=210, h=65))

    nodes.append(add_cell("am_res", "Nhận phản hồi từ Server:\n- accepted: Xóa khỏi Outbox, synced=true\n- duplicate: Dùng kết quả cũ, synced=true\n- retry_later / lỗi mạng: Backoff retry\n- rejected: Chuyển dead-letter", act_style, x=330, y=775, w=220, h=75))
    nodes.append(add_cell("am_poll", "Khởi động Timer Polling 15s:\nGọi GET /api/reports/status\nđể nhận cập nhật tiến trình điều phối", act_style, x=330, y=875, w=220, h=50))
    nodes.append(add_cell("am_end", "Hoàn tất luồng client", end_style, x=390, y=950, w=100, h=40))

    # Edges
    nodes.append(add_edge("ae_1", "", edge_style, "am_start", "am_img_dec"))
    nodes.append(add_edge("ae_2", "Có ảnh", edge_style, "am_img_dec", "am_ai"))
    nodes.append(add_edge("ae_3", "Không ảnh", edge_style, "am_img_dec", "am_no_img"))
    nodes.append(add_edge("ae_4", "", edge_style, "am_ai", "am_fields"))
    nodes.append(add_edge("ae_5", "", edge_style, "am_no_img", "am_fields"))
    nodes.append(add_edge("ae_6", "", edge_style, "am_fields", "am_hive"))
    nodes.append(add_edge("ae_7", "", edge_style, "am_hive", "am_probe"))
    nodes.append(add_edge("ae_8", "", edge_style, "am_probe", "am_net_eval"))

    nodes.append(add_edge("ae_9", "Mất data", edge_style, "am_net_eval", "am_sms"))
    nodes.append(add_edge("ae_10", "<50 kbps", edge_style, "am_net_eval", "am_meta"))
    nodes.append(add_edge("ae_11", "50-1000 kbps", edge_style, "am_net_eval", "am_comp"))
    nodes.append(add_edge("ae_12", ">=1000 kbps", edge_style, "am_net_eval", "am_orig"))

    nodes.append(add_edge("ae_13", "", edge_style, "am_sms", "am_res"))
    nodes.append(add_edge("ae_14", "", edge_style, "am_meta", "am_res"))
    nodes.append(add_edge("ae_15", "", edge_style, "am_comp", "am_res"))
    nodes.append(add_edge("ae_16", "", edge_style, "am_orig", "am_res"))

    nodes.append(add_edge("ae_17", "", edge_style, "am_res", "am_poll"))
    nodes.append(add_edge("ae_18", "", edge_style, "am_poll", "am_end"))

    return create_diagram_xml("Luu-do-Gui-Bao-cao-Thich-ung-App", nodes, w="1000", h="1100")


# -------------------------------------------------------------------------
# 4. FLOWCHART CHI TIẾT BACKEND INGESTION & DEDUP
# -------------------------------------------------------------------------
def generate_flowchart_backend_dedup():
    nodes = []
    start_style = "ellipse;whiteSpace=wrap;html=1;fillColor=#4CAF50;strokeColor=#2E7D32;fontColor=#FFFFFF;fontStyle=1;"
    end_style = "ellipse;whiteSpace=wrap;html=1;fillColor=#607D8B;strokeColor=#37474F;fontColor=#FFFFFF;fontStyle=1;"
    act_style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#512DA8;fontSize=11;fontFamily=Helvetica;"
    dec_style = "rhombus;whiteSpace=wrap;html=1;fillColor=#FFF3E0;strokeColor=#FB8C00;fontSize=10;fontFamily=Helvetica;"
    db_style = "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;fillColor=#ECEFF1;strokeColor=#455A64;fontSize=10;"
    edge_style = "endArrow=classic;html=1;strokeColor=#37474F;strokeWidth=1.3;fontSize=10;"

    nodes.append(add_cell("bd_start", "Nhận Request tới Backend\n(Sync batch / Multipart / SMS)", start_style, x=330, y=40, w=180, h=45))
    nodes.append(add_cell("bd_header", "Kiểm tra header bắt buộc:\nX-Message-Contract-Version: 1", dec_style, x=340, y=110, w=160, h=65))
    nodes.append(add_cell("bd_bounds", "Kiểm tra giới hạn kích thước:\n- Batch <= 50 messages\n- Tổng request <= 256 KiB\n- Meta <= 64 KiB, Ảnh <= 15 MB", dec_style, x=330, y=200, w=180, h=70))
    nodes.append(add_cell("bd_jcs", "Chuẩn tắc hóa JSON theo RFC 8785\n& Tính mã băm SHA-256 payload", act_style, x=325, y=295, w=190, h=50))
    nodes.append(add_cell("bd_lookup", "Tra cứu bảng messages_dedup\ntheo message_id & client_id", act_style + "fillColor=#EDE7F6;", x=325, y=370, w=190, h=50))
    nodes.append(add_cell("bd_dedup_check", "Kết quả đối chiếu\nchống trùng lặp?", dec_style, x=335, y=445, w=170, h=70))

    # Branches
    nodes.append(add_cell("bd_dup_ok", "TRÙNG MESSAGE_ID & HASH:\n- Phát hiện mất ACK sau commit\n- Trả duplicate + kết quả cũ\n- Không sửa đổi CSDL (Idempotent)", act_style + "fillColor=#E8F5E9;strokeColor=#4CAF50;", x=40, y=545, w=210, h=65))
    nodes.append(add_cell("bd_err_conflict", "TRÙNG ID KHÁC HASH HOẶC TÁI DÙNG SEQ:\n- Trả lỗi 409 Conflict\n- Mã ID_REUSED_WITH_DIFFERENT_PAYLOAD\n  hoặc SEQUENCE_REUSED", act_style + "fillColor=#FFEBEE;strokeColor=#E53935;", x=600, y=545, w=230, h=65))
    
    nodes.append(add_cell("bd_new_tx", "THAO TÁC HỢP LỆ (MỚI):\nMở SQLite Database Transaction\nKiểm tra quyền sở hữu report_owner", act_style, x=325, y=545, w=190, h=65))
    nodes.append(add_cell("bd_merge_check", "Báo cáo đã có trong DB?", dec_style, x=345, y=635, w=150, h=65))
    
    nodes.append(add_cell("bd_merge_apply", "Báo cáo cũ (gộp dữ liệu):\n- Chỉ bổ sung trường còn trống\n- Gắn ảnh nếu trước đó chưa có ảnh\n- Giữ nguyên ảnh đầu tiên và ngày tạo", act_style, x=150, y=725, w=220, h=65))
    nodes.append(add_cell("bd_create_apply", "Báo cáo mới hoàn toàn:\n- Tạo bản ghi mới trong bảng reports\n- Trạng thái khởi tạo: processing\n- Lưu file ảnh vật lý (nếu có)", act_style, x=470, y=725, w=220, h=65))

    nodes.append(add_cell("bd_commit", "Commit Transaction:\n- Ghi vết bảng messages_dedup\n- Ghi nhật ký vào report_events\n- Tăng server_meta version (báo cụm stale)", db_style, x=320, y=820, w=200, h=70))
    nodes.append(add_cell("bd_ack", "Trả phản hồi HTTP cho Client\n(accepted / 201 Created)", act_style + "fillColor=#E8F5E9;strokeColor=#2E7D32;", x=340, y=915, w=160, h=45))
    nodes.append(add_cell("bd_end", "Kết thúc xử lý", end_style, x=370, y=985, w=100, h=40))

    # Error terminal
    nodes.append(add_cell("bd_err_bad", "Trả lỗi 400 Bad Request\n(UNSUPPORTED_CONTRACT_VERSION\nhoặc REQUEST_TOO_LARGE)", act_style + "fillColor=#FFEBEE;strokeColor=#E53935;", x=600, y=155, w=230, h=60))

    # Edges
    nodes.append(add_edge("bde_1", "", edge_style, "bd_start", "bd_header"))
    nodes.append(add_edge("bde_2", "Sai version", edge_style, "bd_header", "bd_err_bad"))
    nodes.append(add_edge("bde_3", "Đúng version", edge_style, "bd_header", "bd_bounds"))
    nodes.append(add_edge("bde_4", "Vượt kích thước", edge_style, "bd_bounds", "bd_err_bad"))
    nodes.append(add_edge("bde_5", "Hợp lệ", edge_style, "bd_bounds", "bd_jcs"))
    nodes.append(add_edge("bde_6", "", edge_style, "bd_jcs", "bd_lookup"))
    nodes.append(add_edge("bde_7", "", edge_style, "bd_lookup", "bd_dedup_check"))

    nodes.append(add_edge("bde_8", "Duplicate", edge_style, "bd_dedup_check", "bd_dup_ok"))
    nodes.append(add_edge("bde_9", "Xung đột", edge_style, "bd_dedup_check", "bd_err_conflict"))
    nodes.append(add_edge("bde_10", "Hợp lệ", edge_style, "bd_dedup_check", "bd_new_tx"))

    nodes.append(add_edge("bde_11", "", edge_style, "bd_new_tx", "bd_merge_check"))
    nodes.append(add_edge("bde_12", "Đã có id", edge_style, "bd_merge_check", "bd_merge_apply"))
    nodes.append(add_edge("bde_13", "Chưa có", edge_style, "bd_merge_check", "bd_create_apply"))

    nodes.append(add_edge("bde_14", "", edge_style, "bd_merge_apply", "bd_commit"))
    nodes.append(add_edge("bde_15", "", edge_style, "bd_create_apply", "bd_commit"))
    nodes.append(add_edge("bde_16", "", edge_style, "bd_commit", "bd_ack"))
    nodes.append(add_edge("bde_17", "", edge_style, "bd_ack", "bd_end"))
    nodes.append(add_edge("bde_18", "", edge_style, "bd_dup_ok", "bd_end"))
    nodes.append(add_edge("bde_19", "", edge_style, "bd_err_conflict", "bd_end"))
    nodes.append(add_edge("bde_20", "", edge_style, "bd_err_bad", "bd_end"))

    return create_diagram_xml("Luu-do-Tiep-nhan-va-Chong-trung-Backend", nodes, w="900", h="1080")


def main():
    usecase_xml = generate_usecase()
    flowchart_xml = generate_flowchart()
    flowchart_adaptive_mobile_xml = generate_flowchart_adaptive_mobile()
    flowchart_backend_dedup_xml = generate_flowchart_backend_dedup()

    files = {
        "usecase.drawio": usecase_xml,
        "flowchart.drawio": flowchart_xml,
        "flowchart_adaptive_mobile.drawio": flowchart_adaptive_mobile_xml,
        "flowchart_backend_dedup.drawio": flowchart_backend_dedup_xml,
    }

    for name, content in files.items():
        p = OUT_DIR / name
        p.write_text(content, encoding="utf-8")
        print(f"Generated: {p} ({len(content)} bytes)")


if __name__ == "__main__":
    main()
