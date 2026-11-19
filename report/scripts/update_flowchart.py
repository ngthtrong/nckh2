#!/usr/bin/env python3
"""
Tạo sơ đồ flowchart.drawio và xuất ra flowchart.pdf, flowchart.svg, flowchart_preview.png.
Lưu đồ quy trình phối hợp tổng thể 4 làn giữa các tác nhân và phân hệ trong hệ thống (Hình 3.2).
Chuẩn hóa:
1. Dòng thời gian tuần tự từ trên xuống dưới (Top-Down Monotonic Timeline), TUYỆT ĐỐI không có mũi tên đi ngược từ dưới lên trên.
2. Hoàn toàn không có đường cắt chéo (Planar flow):
   - Review Queue tách ca thiếu GPS và đóng gói cùng cụm Louvain trong JSON của GET /api/clusters.
   - Nhánh SMS đi vòng có đệm khoảng cách thoáng đãng.
3. Đúng 100% kiến trúc thực tế:
   - Dashboard kích hoạt phân cụm qua GET /api/clusters (ETag), không tự động chạy Louvain khi nạp tin.
   - Giao đội và cập nhật trạng thái gọi đúng API: PUT /api/reports/{id}/team và PATCH /api/reports/{id}/status.
   - Backend tự ghi nhật ký kiểm toán report_events trong SQLite WAL.
"""

import os
from pathlib import Path
import fitz  # PyMuPDF

DIAGRAM_DIR = Path("/mnt/d/NCKH2/report/assets/diagrams")

def build_svg() -> str:
    # Canvas dimensions: 1820 x 1360
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1820 1360" width="1820" height="1360">
  <defs>
    <style>
      .lanetitle { font-family: 'Roboto', 'DejaVu Sans', 'Arial', sans-serif; font-size: 13px; font-weight: bold; }
      .nodetitle { font-family: 'Roboto', 'DejaVu Sans', 'Arial', sans-serif; font-size: 11px; font-weight: bold; }
      .nodesub { font-family: 'Roboto', 'DejaVu Sans', 'Arial', sans-serif; font-size: 9.5px; fill: #37474F; }
      .edgelbl { font-family: 'Roboto', 'DejaVu Sans', 'Arial', sans-serif; font-size: 9px; font-weight: bold; fill: #455A64; }
      .phasebadge { font-family: 'Roboto', 'DejaVu Sans', 'Arial', sans-serif; font-size: 10.5px; font-weight: bold; fill: #455A64; }
    </style>
    <marker id="arr-gray" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#546E7A" />
    </marker>
    <marker id="arr-blue" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#1976D2" />
    </marker>
    <marker id="arr-purple" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#7B1FA2" />
    </marker>
    <marker id="arr-orange" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#E65100" />
    </marker>
    <marker id="arr-green" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#2E7D32" />
    </marker>
    <marker id="arr-brown" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#4E342E" />
    </marker>
    <marker id="arr-red" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#C62828" />
    </marker>
  </defs>

  <!-- Background Canvas -->
  <rect x="0" y="0" width="1820" height="1360" fill="#FFFFFF" />

  <!-- ==================== 4 SWIMLANES ==================== -->
  <!-- Lane 1: Mobile (w=410, x=30) -->
  <rect x="30" y="25" width="410" height="1310" rx="8" fill="#F8FAFC" stroke="#90CAF9" stroke-width="1.8" />
  <rect x="30" y="25" width="410" height="36" rx="8" fill="#E3F2FD" stroke="#90CAF9" stroke-width="1.8" />
  <text x="235" y="48" text-anchor="middle" class="lanetitle" fill="#0D47A1">1. ỨNG DỤNG DI ĐỘNG BIÊN (FLUTTER EDGE APP)</text>

  <!-- Lane 2: Server Ingestion & DB (w=420, x=470) -->
  <rect x="470" y="25" width="420" height="1310" rx="8" fill="#FAF5FB" stroke="#BA68C8" stroke-width="1.8" />
  <rect x="470" y="25" width="420" height="36" rx="8" fill="#F3E5F5" stroke="#BA68C8" stroke-width="1.8" />
  <text x="680" y="48" text-anchor="middle" class="lanetitle" fill="#6A1B9A">2. MÁY CHỦ TIẾP NHẬN &amp; DEDUP (FASTAPI / SQLITE)</text>

  <!-- Lane 3: Core Clustering (w=420, x=920) -->
  <rect x="920" y="25" width="420" height="1310" rx="8" fill="#FBF8F5" stroke="#BCAAA4" stroke-width="1.8" />
  <rect x="920" y="25" width="420" height="36" rx="8" fill="#EFEBE9" stroke="#BCAAA4" stroke-width="1.8" />
  <text x="1130" y="48" text-anchor="middle" class="lanetitle" fill="#4E342E">3. LÕI PHÂN CỤM &amp; ƯU TIÊN (RESCUE_CORE)</text>

  <!-- Lane 4: Dashboard (w=420, x=1370) -->
  <rect x="1370" y="25" width="420" height="1310" rx="8" fill="#FFFDF8" stroke="#FFE082" stroke-width="1.8" />
  <rect x="1370" y="25" width="420" height="36" rx="8" fill="#FFF8E1" stroke="#FFE082" stroke-width="1.8" />
  <text x="1580" y="48" text-anchor="middle" class="lanetitle" fill="#E65100">4. BÀN ĐIỀU PHỐI TRUNG TÂM (WEB GIS DASHBOARD)</text>

  <!-- ==================== PHASE DIVIDERS ==================== -->
  <!-- Phase 1 Header -->
  <rect x="35" y="66" width="310" height="20" rx="4" fill="#ECEFF1" />
  <text x="45" y="80" class="phasebadge">GIAI ĐOẠN 1: BÁO CÁO KHẨN CẤP &amp; ĐỒNG BỘ BIÊN</text>

  <!-- Phase 2 Header -->
  <line x1="30" y1="365" x2="1790" y2="365" stroke="#CFD8DC" stroke-width="1.2" stroke-dasharray="6 4" />
  <rect x="925" y="372" width="375" height="20" rx="4" fill="#ECEFF1" />
  <text x="935" y="386" class="phasebadge">GIAI ĐOẠN 2: PHÂN CỤM ĐỒ THỊ LOUVAIN (THEO NHU CẦU POLLING)</text>

  <!-- Phase 3 Header -->
  <line x1="30" y1="895" x2="1790" y2="895" stroke="#CFD8DC" stroke-width="1.2" stroke-dasharray="6 4" />
  <rect x="1375" y="902" width="350" height="20" rx="4" fill="#ECEFF1" />
  <text x="1385" y="916" class="phasebadge">GIAI ĐOẠN 3: GIÁM SÁT, THẨM TRA &amp; TÁC NGHIỆP CỨU NẠN</text>

  <!-- ==================== GIAI ĐOẠN 1: BÁO CÁO & ĐỒNG BỘ BIÊN (y = 90 .. 350) ==================== -->
  
  <!-- m_start -->
  <ellipse cx="235" cy="110" rx="65" ry="18" fill="#E8F5E9" stroke="#2E7D32" stroke-width="1.5" />
  <text x="235" y="114" text-anchor="middle" class="nodetitle" fill="#1B5E20">Bắt đầu (Mở App)</text>

  <!-- m_choose -->
  <rect x="135" y="146" width="200" height="40" rx="6" fill="#FFFFFF" stroke="#1976D2" stroke-width="1.4" />
  <text x="235" y="162" text-anchor="middle" class="nodetitle" fill="#0D47A1">Chọn: Gửi SOS 1 chạm</text>
  <text x="235" y="176" text-anchor="middle" class="nodesub">hoặc Tạo báo cáo chi tiết</text>

  <!-- m_ai -->
  <rect x="120" y="204" width="230" height="46" rx="6" fill="#FCE4EC" stroke="#D81B60" stroke-width="1.5" />
  <text x="235" y="221" text-anchor="middle" class="nodetitle" fill="#880E4F">Chụp ảnh -&gt; Edge AI MobileNetV3</text>
  <text x="235" y="236" text-anchor="middle" class="nodesub">Phân loại 4 mức ngập F &amp; Confidence</text>

  <!-- m_form -->
  <rect x="120" y="268" width="230" height="46" rx="6" fill="#FFFFFF" stroke="#1976D2" stroke-width="1.4" />
  <text x="235" y="284" text-anchor="middle" class="nodetitle" fill="#0D47A1">Nhập GPS (hoặc để trống), N, V</text>
  <text x="235" y="299" text-anchor="middle" class="nodesub">Ghi Outbox (Hive) &amp; Canonical JCS Hash</text>

  <!-- m_net_dec -->
  <polygon points="235,328 325,350 235,372 145,350" fill="#FFF9C4" stroke="#FBC02D" stroke-width="1.5" />
  <text x="235" y="353" text-anchor="middle" font-family="Roboto, Arial, sans-serif" font-size="10px" font-weight="bold" fill="#F57F17">Đánh giá mạng?</text>

  <!-- m_sms -->
  <rect x="45" y="410" width="160" height="44" rx="6" fill="#FFEBEE" stroke="#E53935" stroke-width="1.4" />
  <text x="125" y="426" text-anchor="middle" class="nodetitle" fill="#B71C1C">Mất mạng: Gửi SMS SOS</text>
  <text x="125" y="441" text-anchor="middle" class="nodesub">Dự phòng GSM (chờ sync)</text>

  <!-- m_rest -->
  <rect x="225" y="410" width="195" height="44" rx="6" fill="#E3F2FD" stroke="#1976D2" stroke-width="1.4" />
  <text x="322" y="426" text-anchor="middle" class="nodetitle" fill="#0D47A1">Có mạng: REST / Multipart</text>
  <text x="322" y="441" text-anchor="middle" class="nodesub">POST /sync batch hoặc /api/reports</text>

  <!-- Lane 2: s_recv (API Gateway) -->
  <rect x="495" y="410" width="220" height="44" rx="6" fill="#FFFFFF" stroke="#7B1FA2" stroke-width="1.6" />
  <text x="605" y="426" text-anchor="middle" class="nodetitle" fill="#6A1B9A">Cổng Tiếp nhận (API Gateway)</text>
  <text x="605" y="441" text-anchor="middle" class="nodesub">Sync Batch / Multipart / SMS Webhook</text>

  <!-- Lane 2: s_val (Validate Contract & Hash) -->
  <rect x="495" y="490" width="220" height="44" rx="6" fill="#FFFFFF" stroke="#7B1FA2" stroke-width="1.4" />
  <text x="605" y="506" text-anchor="middle" class="nodetitle" fill="#6A1B9A">Xác thực Hợp đồng &amp; Hash</text>
  <text x="605" y="521" text-anchor="middle" class="nodesub">Header v1, Canonical JCS SHA-256</text>

  <!-- Lane 2: s_dedup_dec -->
  <polygon points="605,550 705,572 605,594 505,572" fill="#FFF9C4" stroke="#FBC02D" stroke-width="1.5" />
  <text x="605" y="575" text-anchor="middle" font-family="Roboto, Arial, sans-serif" font-size="10px" font-weight="bold" fill="#F57F17">Tra cứu messages_dedup?</text>

  <!-- Lane 2: s_dup (Idempotent ACK) -->
  <rect x="740" y="550" width="135" height="44" rx="6" fill="#E8F5E9" stroke="#2E7D32" stroke-width="1.3" />
  <text x="807" y="567" text-anchor="middle" class="nodetitle" fill="#1B5E20">Trùng ID &amp; Hash</text>
  <text x="807" y="582" text-anchor="middle" class="nodesub">Trả ACK cũ (Idempotent)</text>

  <!-- Lane 2: s_tx (Valid Transaction) -->
  <rect x="495" y="618" width="220" height="46" rx="6" fill="#FFFFFF" stroke="#00695C" stroke-width="1.5" />
  <text x="605" y="634" text-anchor="middle" class="nodetitle" fill="#004D40">Giao dịch SQLite (WAL Mode)</text>
  <text x="605" y="650" text-anchor="middle" class="nodesub">Lưu reports, dedup, files uploads/</text>

  <!-- Lane 2: s_meta (Update server_meta & ACK) -->
  <rect x="495" y="682" width="220" height="44" rx="6" fill="#FFFFFF" stroke="#7B1FA2" stroke-width="1.5" />
  <text x="605" y="698" text-anchor="middle" class="nodetitle" fill="#6A1B9A">Tăng cluster_version</text>
  <text x="605" y="713" text-anchor="middle" class="nodesub">server_meta &amp; Trả HTTP Response</text>

  <!-- Lane 1: m_wait_ack -->
  <rect x="135" y="682" width="200" height="44" rx="6" fill="#E8F5E9" stroke="#2E7D32" stroke-width="1.4" />
  <text x="235" y="698" text-anchor="middle" class="nodetitle" fill="#1B5E20">Nhận phản hồi ACK</text>
  <text x="235" y="713" text-anchor="middle" class="nodesub">Cập nhật Outbox synced=true</text>

  <!-- ==================== GIAI ĐOẠN 2: POLLING & PHÂN CỤM LOUVAIN (y = 400 .. 860) ==================== -->
  
  <!-- Lane 4: d_login -->
  <rect x="1480" y="340" width="200" height="40" rx="6" fill="#FFFFFF" stroke="#E65100" stroke-width="1.4" />
  <text x="1580" y="356" text-anchor="middle" class="nodetitle" fill="#E65100">Đăng nhập Bàn Điều phối</text>
  <text x="1580" y="370" text-anchor="middle" class="nodesub">Khởi tạo phiên làm việc Dispatcher</text>

  <!-- Lane 4: d_poll -->
  <rect x="1465" y="410" width="230" height="44" rx="6" fill="#FFF8E1" stroke="#FFA000" stroke-width="1.5" />
  <text x="1580" y="426" text-anchor="middle" class="nodetitle" fill="#E65100">Polling định kỳ 5s</text>
  <text x="1580" y="441" text-anchor="middle" class="nodesub">GET /api/reports/changes &amp; /api/clusters</text>

  <!-- Lane 3: c_recv (Check ETag & version) -->
  <rect x="945" y="410" width="220" height="44" rx="6" fill="#FFFFFF" stroke="#4E342E" stroke-width="1.5" />
  <text x="1055" y="426" text-anchor="middle" class="nodetitle" fill="#4E342E">Tiếp nhận GET /api/clusters</text>
  <text x="1055" y="441" text-anchor="middle" class="nodesub">Kiểm tra header If-None-Match ETag</text>

  <!-- Lane 3: c_etag_dec -->
  <polygon points="1055,476 1150,498 1055,520 960,498" fill="#FFF9C4" stroke="#FBC02D" stroke-width="1.5" />
  <text x="1055" y="501" text-anchor="middle" font-family="Roboto, Arial, sans-serif" font-size="10px" font-weight="bold" fill="#F57F17">cluster_version đổi?</text>

  <!-- Lane 3: c_304 (Not Modified) -->
  <rect x="1195" y="476" width="130" height="44" rx="6" fill="#F5F5F5" stroke="#757575" stroke-width="1.3" />
  <text x="1260" y="493" text-anchor="middle" class="nodetitle" fill="#424242">304 Not Modified</text>
  <text x="1260" y="508" text-anchor="middle" class="nodesub">Giữ nguyên cụm cũ</text>

  <!-- Lane 3: c_fetch (Extract active reports) -->
  <rect x="945" y="542" width="220" height="44" rx="6" fill="#FFFFFF" stroke="#4E342E" stroke-width="1.4" />
  <text x="1055" y="558" text-anchor="middle" class="nodetitle" fill="#4E342E">Lấy báo cáo active_only</text>
  <text x="1055" y="574" text-anchor="middle" class="nodesub">Trích xuất [F, U, N, V] qua to_report_v2</text>

  <!-- Lane 3: c_split_dec -->
  <polygon points="1055,608 1145,630 1055,652 965,630" fill="#FFF9C4" stroke="#FBC02D" stroke-width="1.5" />
  <text x="1055" y="633" text-anchor="middle" font-family="Roboto, Arial, sans-serif" font-size="10px" font-weight="bold" fill="#F57F17">Tọa độ GPS hợp lệ?</text>

  <!-- Lane 3: c_rev (Review Queue) -->
  <rect x="1190" y="608" width="140" height="44" rx="6" fill="#FFF3E0" stroke="#FB8C00" stroke-width="1.4" />
  <text x="1260" y="625" text-anchor="middle" class="nodetitle" fill="#E65100">Review Queue</text>
  <text x="1260" y="640" text-anchor="middle" class="nodesub">Tách riêng ca thiếu GPS</text>

  <!-- Lane 3: c_graph (Louvain Community Detection) -->
  <rect x="945" y="674" width="220" height="46" rx="6" fill="#FFFFFF" stroke="#4E342E" stroke-width="1.5" />
  <text x="1055" y="690" text-anchor="middle" class="nodetitle" fill="#4E342E">Ma trận C_ij &amp; Cụm Louvain</text>
  <text x="1055" y="706" text-anchor="middle" class="nodesub">Khoảng cách Haversine, ngập, khẩn cấp</text>

  <!-- Lane 3: c_score (Calculate P(c)) -->
  <rect x="945" y="742" width="220" height="46" rx="6" fill="#FFFFFF" stroke="#4E342E" stroke-width="1.5" />
  <text x="1055" y="758" text-anchor="middle" class="nodetitle" fill="#4E342E">Tính điểm ưu tiên cụm P(c)</text>
  <text x="1055" y="774" text-anchor="middle" class="nodesub">Khóa clusterKey &amp; Cập nhật ETag mới</text>

  <!-- Lane 3: c_resp -->
  <rect x="945" y="810" width="220" height="44" rx="6" fill="#E8F5E9" stroke="#2E7D32" stroke-width="1.4" />
  <text x="1055" y="826" text-anchor="middle" class="nodetitle" fill="#1B5E20">Trả JSON Clusters &amp; Review</text>
  <text x="1055" y="841" text-anchor="middle" class="nodesub">Kèm header ETag cho Dashboard</text>

  <!-- ==================== GIAI ĐOẠN 3: GIÁM SÁT, ĐIỀU PHỐI & HOÀN TẤT (y = 810 .. 1320) ==================== -->
  
  <!-- Lane 4: d_view -->
  <rect x="1465" y="810" width="230" height="44" rx="6" fill="#FFFFFF" stroke="#E65100" stroke-width="1.5" />
  <text x="1580" y="826" text-anchor="middle" class="nodetitle" fill="#E65100">Cập nhật Leaflet GIS &amp; Bảng Cụm</text>
  <text x="1580" y="841" text-anchor="middle" class="nodesub">Hiển thị ranh giới cụm &amp; Hàng xem xét</text>

  <!-- Lane 4: d_branch_dec -->
  <polygon points="1580,935 1675,957 1580,979 1485,957" fill="#FFF9C4" stroke="#FBC02D" stroke-width="1.5" />
  <text x="1580" y="960" text-anchor="middle" font-family="Roboto, Arial, sans-serif" font-size="10px" font-weight="bold" fill="#F57F17">Phân loại ca xử lý?</text>

  <!-- Lane 4: d_geocode (Manual GPS Assignment) -->
  <rect x="1385" y="1000" width="175" height="44" rx="6" fill="#FFF3E0" stroke="#FB8C00" stroke-width="1.4" />
  <text x="1472" y="1016" text-anchor="middle" class="nodetitle" fill="#E65100">Ca thiếu GPS (Review)</text>
  <text x="1472" y="1031" text-anchor="middle" class="nodesub">Thẩm tra, gọi &amp; Gán tọa độ</text>

  <!-- Lane 4: d_pick (Pick Highest Priority Cluster) -->
  <rect x="1595" y="1000" width="180" height="44" rx="6" fill="#FFFFFF" stroke="#E65100" stroke-width="1.4" />
  <text x="1685" y="1016" text-anchor="middle" class="nodetitle" fill="#E65100">Ca đã gom cụm P(c)</text>
  <text x="1685" y="1031" text-anchor="middle" class="nodesub">Chọn cụm có độ khẩn cấp cao</text>

  <!-- Lane 4: d_assign (Dispatch Team) -->
  <rect x="1465" y="1066" width="230" height="46" rx="6" fill="#FFF8E1" stroke="#FFA000" stroke-width="1.6" />
  <text x="1580" y="1083" text-anchor="middle" class="nodetitle" fill="#E65100">Giao đội cứu hộ (PUT /team)</text>
  <text x="1580" y="1098" text-anchor="middle" class="nodesub">Đổi status -&gt; dispatched (tăng version)</text>

  <!-- Lane 2: s_status_tx (Server Record Event) -->
  <rect x="495" y="1066" width="220" height="46" rx="6" fill="#FFFFFF" stroke="#00695C" stroke-width="1.5" />
  <text x="605" y="1083" text-anchor="middle" class="nodetitle" fill="#004D40">Cập nhật DB &amp; Ghi report_events</text>
  <text x="605" y="1098" text-anchor="middle" class="nodesub">Nhật ký kiểm toán (actor, action, time)</text>

  <!-- Lane 4: d_rescue -->
  <rect x="1465" y="1134" width="230" height="44" rx="6" fill="#FFFFFF" stroke="#1976D2" stroke-width="1.4" />
  <text x="1580" y="1150" text-anchor="middle" class="nodetitle" fill="#0D47A1">Đội Cứu hộ Thực địa Tác nghiệp</text>
  <text x="1580" y="1165" text-anchor="middle" class="nodesub">Tiếp cận hiện trường &amp; Triển khai ứng cứu</text>

  <!-- Lane 4: d_result_dec -->
  <polygon points="1580,1200 1675,1222 1580,1244 1485,1222" fill="#FFF9C4" stroke="#FBC02D" stroke-width="1.5" />
  <text x="1580" y="1225" text-anchor="middle" font-family="Roboto, Arial, sans-serif" font-size="10px" font-weight="bold" fill="#F57F17">Kết quả cứu hộ?</text>

  <!-- Lane 4: d_ok (Resolved) -->
  <rect x="1385" y="1268" width="180" height="42" rx="6" fill="#E8F5E9" stroke="#2E7D32" stroke-width="1.4" />
  <text x="1475" y="1284" text-anchor="middle" class="nodetitle" fill="#1B5E20">Thành công: resolved</text>
  <text x="1475" y="1299" text-anchor="middle" class="nodesub">Cập nhật cứu hộ hoàn tất</text>

  <!-- Lane 4: d_cancel (Cancelled) -->
  <rect x="1595" y="1268" width="180" height="42" rx="6" fill="#FFEBEE" stroke="#E53935" stroke-width="1.4" />
  <text x="1685" y="1284" text-anchor="middle" class="nodetitle" fill="#B71C1C">Hủy / Giả: cancelled</text>
  <text x="1685" y="1299" text-anchor="middle" class="nodesub">Bắt buộc nhập lý do đóng</text>

  <!-- Lane 1: m_poll_status -->
  <rect x="120" y="1066" width="230" height="46" rx="6" fill="#FFFFFF" stroke="#1976D2" stroke-width="1.4" />
  <text x="235" y="1083" text-anchor="middle" class="nodetitle" fill="#0D47A1">Polling GET /api/reports/status</text>
  <text x="235" y="1098" text-anchor="middle" class="nodesub">Nhận cập nhật tiến trình điều phối</text>

  <!-- Lane 1: m_end -->
  <ellipse cx="235" cy="1289" rx="75" ry="20" fill="#E8F5E9" stroke="#2E7D32" stroke-width="1.6" />
  <text x="235" y="1293" text-anchor="middle" class="nodetitle" fill="#1B5E20">Kết thúc (Được cứu)</text>

  <!-- ==================== ARROWS / CONNECTORS ==================== -->
  
  <!-- Phase 1: Lane 1 Downwards -->
  <line x1="235" y1="128" x2="235" y2="146" stroke="#1976D2" stroke-width="1.4" marker-end="url(#arr-blue)" />
  <line x1="235" y1="186" x2="235" y2="204" stroke="#1976D2" stroke-width="1.4" marker-end="url(#arr-blue)" />
  <line x1="235" y1="250" x2="235" y2="268" stroke="#1976D2" stroke-width="1.4" marker-end="url(#arr-blue)" />
  <line x1="235" y1="314" x2="235" y2="328" stroke="#1976D2" stroke-width="1.4" marker-end="url(#arr-blue)" />

  <!-- Net decision branches -->
  <path d="M 145 350 L 125 350 L 125 410" fill="none" stroke="#E53935" stroke-width="1.3" marker-end="url(#arr-red)" />
  <text x="110" y="375" text-anchor="middle" class="edgelbl" fill="#C62828">Mất sóng</text>

  <path d="M 325 350 L 322 350 L 322 410" fill="none" stroke="#1976D2" stroke-width="1.3" marker-end="url(#arr-blue)" />
  <text x="345" y="375" text-anchor="start" class="edgelbl" fill="#0D47A1">Có IP data</text>

  <!-- Cross Lane 1 -> Lane 2: Send Request (Clean Horizontal Bridges without text collisions) -->
  <!-- SMS route: goes generously under m_rest (y=472) to reach s_recv -->
  <path d="M 125 454 L 125 472 L 460 472 L 460 432 L 495 432" fill="none" stroke="#E53935" stroke-width="1.3" stroke-dasharray="4 3" marker-end="url(#arr-purple)" />
  <text x="210" y="485" class="edgelbl" fill="#C62828">SMS Gateway Webhook</text>

  <!-- REST route -->
  <line x1="420" y1="432" x2="495" y2="432" stroke="#1976D2" stroke-width="1.4" marker-end="url(#arr-purple)" />
  <text x="440" y="425" class="edgelbl" fill="#0D47A1">HTTP REST</text>

  <!-- Lane 2 Downwards -->
  <line x1="605" y1="454" x2="605" y2="490" stroke="#7B1FA2" stroke-width="1.4" marker-end="url(#arr-purple)" />
  <line x1="605" y1="534" x2="605" y2="550" stroke="#7B1FA2" stroke-width="1.4" marker-end="url(#arr-purple)" />

  <line x1="705" y1="572" x2="740" y2="572" stroke="#2E7D32" stroke-width="1.3" marker-end="url(#arr-green)" />
  <text x="715" y="565" class="edgelbl" fill="#2E7D32">Trùng</text>

  <line x1="605" y1="594" x2="605" y2="618" stroke="#00695C" stroke-width="1.4" marker-end="url(#arr-green)" />
  <text x="615" y="609" class="edgelbl" fill="#00695C">Hợp lệ</text>

  <line x1="605" y1="664" x2="605" y2="682" stroke="#7B1FA2" stroke-width="1.4" marker-end="url(#arr-purple)" />

  <!-- Lane 2 -> Lane 1: ACK Response (Horizontal Left) -->
  <line x1="495" y1="704" x2="335" y2="704" stroke="#2E7D32" stroke-width="1.5" marker-end="url(#arr-green)" />
  <text x="415" y="697" text-anchor="middle" class="edgelbl" fill="#2E7D32">Trả HTTP 201 / ACK</text>

  <!-- Lane 1 ACK downwards to poll status -->
  <line x1="235" y1="726" x2="235" y2="1066" stroke="#1976D2" stroke-width="1.3" stroke-dasharray="4 3" marker-end="url(#arr-blue)" />
  <text x="245" y="890" class="edgelbl" fill="#1976D2">Chờ điều phối</text>

  <line x1="235" y1="1112" x2="235" y2="1269" stroke="#2E7D32" stroke-width="1.4" marker-end="url(#arr-green)" />

  <!-- Phase 2: Lane 4 Polling -> Lane 3 -->
  <line x1="1580" y1="380" x2="1580" y2="410" stroke="#E65100" stroke-width="1.4" marker-end="url(#arr-orange)" />
  
  <line x1="1465" y1="432" x2="1165" y2="432" stroke="#E65100" stroke-width="1.4" marker-end="url(#arr-brown)" />
  <text x="1315" y="425" text-anchor="middle" class="edgelbl" fill="#E65100">GET /api/clusters (ETag)</text>

  <!-- Lane 3 Downwards -->
  <line x1="1055" y1="454" x2="1055" y2="476" stroke="#4E342E" stroke-width="1.4" marker-end="url(#arr-brown)" />
  
  <line x1="1150" y1="498" x2="1195" y2="498" stroke="#757575" stroke-width="1.3" marker-end="url(#arr-gray)" />
  <text x="1160" y="491" class="edgelbl" fill="#757575">Không</text>

  <line x1="1055" y1="520" x2="1055" y2="542" stroke="#4E342E" stroke-width="1.4" marker-end="url(#arr-brown)" />
  <text x="1065" y="534" class="edgelbl" fill="#4E342E">Đổi</text>

  <line x1="1055" y1="586" x2="1055" y2="608" stroke="#4E342E" stroke-width="1.4" marker-end="url(#arr-brown)" />

  <!-- GPS Split -->
  <line x1="1145" y1="630" x2="1190" y2="630" stroke="#FB8C00" stroke-width="1.3" marker-end="url(#arr-orange)" />
  <text x="1155" y="623" class="edgelbl" fill="#E65100">Thiếu</text>

  <!-- Review Queue packages into response -->
  <path d="M 1260 652 L 1260 832 L 1165 832" fill="none" stroke="#FB8C00" stroke-width="1.3" stroke-dasharray="3 3" marker-end="url(#arr-brown)" />
  <text x="1268" y="740" class="edgelbl" fill="#E65100">Gộp Review</text>

  <line x1="1055" y1="652" x2="1055" y2="674" stroke="#4E342E" stroke-width="1.4" marker-end="url(#arr-brown)" />
  <text x="1065" y="665" class="edgelbl" fill="#4E342E">Có GPS</text>

  <line x1="1055" y1="720" x2="1055" y2="742" stroke="#4E342E" stroke-width="1.4" marker-end="url(#arr-brown)" />
  <line x1="1055" y1="788" x2="1055" y2="810" stroke="#2E7D32" stroke-width="1.4" marker-end="url(#arr-green)" />

  <!-- Lane 3 -> Lane 4: Return JSON Clusters + Review (Horizontal Right) -->
  <line x1="1165" y1="832" x2="1465" y2="832" stroke="#2E7D32" stroke-width="1.5" marker-end="url(#arr-orange)" />
  <text x="1315" y="825" text-anchor="middle" class="edgelbl" fill="#2E7D32">JSON: Cụm P(c) &amp; Review Queue</text>

  <!-- Phase 3: Lane 4 Downwards -->
  <line x1="1580" y1="854" x2="1580" y2="935" stroke="#E65100" stroke-width="1.4" marker-end="url(#arr-orange)" />

  <path d="M 1485 957 L 1472 957 L 1472 1000" fill="none" stroke="#FB8C00" stroke-width="1.3" marker-end="url(#arr-orange)" />
  <path d="M 1675 957 L 1685 957 L 1685 1000" fill="none" stroke="#E65100" stroke-width="1.3" marker-end="url(#arr-orange)" />

  <path d="M 1472 1044 L 1472 1056 L 1580 1056 L 1580 1066" fill="none" stroke="#E65100" stroke-width="1.3" marker-end="url(#arr-orange)" />
  <path d="M 1685 1044 L 1685 1056 L 1580 1056 L 1580 1066" fill="none" stroke="#E65100" stroke-width="1.3" />

  <!-- Dispatch Action: Horizontal Left to Lane 2 Server DB -->
  <line x1="1465" y1="1089" x2="715" y2="1089" stroke="#00695C" stroke-width="1.5" marker-end="url(#arr-green)" />
  <text x="1090" y="1082" text-anchor="middle" class="edgelbl" fill="#00695C">PUT /api/reports/{id}/team &amp; PATCH /status</text>

  <line x1="1580" y1="1112" x2="1580" y2="1134" stroke="#1976D2" stroke-width="1.4" marker-end="url(#arr-blue)" />
  <line x1="1580" y1="1178" x2="1580" y2="1200" stroke="#1976D2" stroke-width="1.4" marker-end="url(#arr-blue)" />

  <path d="M 1485 1222 L 1475 1222 L 1475 1268" fill="none" stroke="#2E7D32" stroke-width="1.3" marker-end="url(#arr-green)" />
  <text x="1455" y="1248" text-anchor="middle" class="edgelbl" fill="#2E7D32">Đạt</text>

  <path d="M 1675 1222 L 1685 1222 L 1685 1268" fill="none" stroke="#E53935" stroke-width="1.3" marker-end="url(#arr-red)" />
  <text x="1705" y="1248" text-anchor="middle" class="edgelbl" fill="#C62828">Hủy</text>

</svg>'''
    return svg

def build_drawio_xml() -> str:
    """Tạo tệp Draw.io XML tương ứng với sơ đồ 4 làn."""
    xml = '''<mxfile host="Electron" agent="Antigravity">
  <diagram id="diag-flowchart-clean" name="Luu-do-Quy-trinh-He-thong-4-Lan">
    <mxGraphModel dx="1600" dy="1100" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1820" pageHeight="1360" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        
        <!-- SWIMLANES -->
        <mxCell id="lane_mob" value="1. ỨNG DỤNG DI ĐỘNG BIÊN (FLUTTER EDGE APP)" style="shape=swimlane;whiteSpace=wrap;html=1;startSize=36;fontStyle=1;fontSize=13;fontFamily=Helvetica;fillColor=#F8FAFC;strokeColor=#90CAF9;strokeWidth=1.8;fontColor=#0D47A1;" vertex="1" parent="1">
          <mxGeometry x="30" y="25" width="410" height="1310" as="geometry" />
        </mxCell>
        <mxCell id="lane_srv" value="2. MÁY CHỦ TIẾP NHẬN &amp; DEDUP (FASTAPI / SQLITE)" style="shape=swimlane;whiteSpace=wrap;html=1;startSize=36;fontStyle=1;fontSize=13;fontFamily=Helvetica;fillColor=#FAF5FB;strokeColor=#BA68C8;strokeWidth=1.8;fontColor=#6A1B9A;" vertex="1" parent="1">
          <mxGeometry x="470" y="25" width="420" height="1310" as="geometry" />
        </mxCell>
        <mxCell id="lane_core" value="3. LÕI PHÂN CỤM &amp; ƯU TIÊN (RESCUE_CORE)" style="shape=swimlane;whiteSpace=wrap;html=1;startSize=36;fontStyle=1;fontSize=13;fontFamily=Helvetica;fillColor=#FBF8F5;strokeColor=#BCAAA4;strokeWidth=1.8;fontColor=#4E342E;" vertex="1" parent="1">
          <mxGeometry x="920" y="25" width="420" height="1310" as="geometry" />
        </mxCell>
        <mxCell id="lane_dash" value="4. BÀN ĐIỀU PHỐI TRUNG TÂM (WEB GIS DASHBOARD)" style="shape=swimlane;whiteSpace=wrap;html=1;startSize=36;fontStyle=1;fontSize=13;fontFamily=Helvetica;fillColor=#FFFDF8;strokeColor=#FFE082;strokeWidth=1.8;fontColor=#E65100;" vertex="1" parent="1">
          <mxGeometry x="1370" y="25" width="420" height="1310" as="geometry" />
        </mxCell>

        <!-- LANE 1 NODES -->
        <mxCell id="m_start" value="Bắt đầu (Mở App)" style="ellipse;whiteSpace=wrap;html=1;fillColor=#E8F5E9;strokeColor=#2E7D32;strokeWidth=1.5;fontFamily=Helvetica;fontStyle=1;fontColor=#1B5E20;fontSize=11.5;" vertex="1" parent="lane_mob">
          <mxGeometry x="140" y="70" width="130" height="36" as="geometry" />
        </mxCell>
        <mxCell id="m_choose" value="Chọn: Gửi SOS 1 chạm&#xa;hoặc Tạo báo cáo chi tiết" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1976D2;strokeWidth=1.4;fontFamily=Helvetica;fontSize=11;fontColor=#0D47A1;fontStyle=1;" vertex="1" parent="lane_mob">
          <mxGeometry x="105" y="121" width="200" height="40" as="geometry" />
        </mxCell>
        <mxCell id="m_ai" value="Chụp ảnh -&gt; Edge AI MobileNetV3&#xa;Phân loại 4 mức ngập F &amp; Confidence" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FCE4EC;strokeColor=#D81B60;strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontColor=#880E4F;fontStyle=1;" vertex="1" parent="lane_mob">
          <mxGeometry x="90" y="179" width="230" height="46" as="geometry" />
        </mxCell>
        <mxCell id="m_form" value="Nhập GPS (hoặc để trống), N, V&#xa;Ghi Outbox (Hive) &amp; Canonical JCS Hash" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1976D2;strokeWidth=1.4;fontFamily=Helvetica;fontSize=11;fontColor=#0D47A1;fontStyle=1;" vertex="1" parent="lane_mob">
          <mxGeometry x="90" y="243" width="230" height="46" as="geometry" />
        </mxCell>
        <mxCell id="m_net_dec" value="Đánh giá mạng?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#FFF9C4;strokeColor=#FBC02D;strokeWidth=1.5;fontFamily=Helvetica;fontSize=10;fontStyle=1;fontColor=#F57F17;" vertex="1" parent="lane_mob">
          <mxGeometry x="145" y="303" width="120" height="44" as="geometry" />
        </mxCell>
        <mxCell id="m_sms" value="Mất mạng: Gửi SMS SOS&#xa;Dự phòng GSM (chờ sync)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFEBEE;strokeColor=#E53935;strokeWidth=1.4;fontFamily=Helvetica;fontSize=10.5;fontColor=#B71C1C;fontStyle=1;" vertex="1" parent="lane_mob">
          <mxGeometry x="15" y="385" width="160" height="44" as="geometry" />
        </mxCell>
        <mxCell id="m_rest" value="Có mạng: REST / Multipart&#xa;POST /sync batch hoặc /api/reports" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E3F2FD;strokeColor=#1976D2;strokeWidth=1.4;fontFamily=Helvetica;fontSize=10.5;fontColor=#0D47A1;fontStyle=1;" vertex="1" parent="lane_mob">
          <mxGeometry x="195" y="385" width="195" height="44" as="geometry" />
        </mxCell>
        <mxCell id="m_wait_ack" value="Nhận phản hồi ACK&#xa;Cập nhật Outbox synced=true" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F5E9;strokeColor=#2E7D32;strokeWidth=1.4;fontFamily=Helvetica;fontSize=11;fontColor=#1B5E20;fontStyle=1;" vertex="1" parent="lane_mob">
          <mxGeometry x="105" y="657" width="200" height="44" as="geometry" />
        </mxCell>
        <mxCell id="m_poll_status" value="Polling GET /api/reports/status&#xa;Nhận cập nhật tiến trình điều phối" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1976D2;strokeWidth=1.4;fontFamily=Helvetica;fontSize=11;fontColor=#0D47A1;fontStyle=1;" vertex="1" parent="lane_mob">
          <mxGeometry x="90" y="1041" width="230" height="46" as="geometry" />
        </mxCell>
        <mxCell id="m_end" value="Kết thúc (Được cứu)" style="ellipse;whiteSpace=wrap;html=1;fillColor=#E8F5E9;strokeColor=#2E7D32;strokeWidth=1.6;fontFamily=Helvetica;fontStyle=1;fontColor=#1B5E20;fontSize=11.5;" vertex="1" parent="lane_mob">
          <mxGeometry x="130" y="1264" width="150" height="40" as="geometry" />
        </mxCell>

        <!-- LANE 2 NODES -->
        <mxCell id="s_recv" value="Cổng Tiếp nhận (API Gateway)&#xa;Sync Batch / Multipart / SMS Webhook" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#7B1FA2;strokeWidth=1.6;fontFamily=Helvetica;fontSize=11;fontColor=#6A1B9A;fontStyle=1;" vertex="1" parent="lane_srv">
          <mxGeometry x="25" y="385" width="220" height="44" as="geometry" />
        </mxCell>
        <mxCell id="s_val" value="Xác thực Hợp đồng &amp; Hash&#xa;Header v1, Canonical JCS SHA-256" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#7B1FA2;strokeWidth=1.4;fontFamily=Helvetica;fontSize=11;fontColor=#6A1B9A;fontStyle=1;" vertex="1" parent="lane_srv">
          <mxGeometry x="25" y="465" width="220" height="44" as="geometry" />
        </mxCell>
        <mxCell id="s_dedup_dec" value="Tra cứu messages_dedup?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#FFF9C4;strokeColor=#FBC02D;strokeWidth=1.5;fontFamily=Helvetica;fontSize=10;fontStyle=1;fontColor=#F57F17;" vertex="1" parent="lane_srv">
          <mxGeometry x="35" y="525" width="200" height="44" as="geometry" />
        </mxCell>
        <mxCell id="s_dup" value="Trùng ID &amp; Hash&#xa;Trả ACK cũ (Idempotent)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F5E9;strokeColor=#2E7D32;strokeWidth=1.3;fontFamily=Helvetica;fontSize=10.5;fontColor=#1B5E20;fontStyle=1;" vertex="1" parent="lane_srv">
          <mxGeometry x="270" y="525" width="135" height="44" as="geometry" />
        </mxCell>
        <mxCell id="s_tx" value="Giao dịch SQLite (WAL Mode)&#xa;Lưu reports, dedup, files uploads/" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#00695C;strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontColor=#004D40;fontStyle=1;" vertex="1" parent="lane_srv">
          <mxGeometry x="25" y="593" width="220" height="46" as="geometry" />
        </mxCell>
        <mxCell id="s_meta" value="Tăng cluster_version&#xa;server_meta &amp; Trả HTTP Response" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#7B1FA2;strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontColor=#6A1B9A;fontStyle=1;" vertex="1" parent="lane_srv">
          <mxGeometry x="25" y="657" width="220" height="44" as="geometry" />
        </mxCell>
        <mxCell id="s_status_tx" value="Cập nhật DB &amp; Ghi report_events&#xa;Nhật ký kiểm toán (actor, action, time)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#00695C;strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontColor=#004D40;fontStyle=1;" vertex="1" parent="lane_srv">
          <mxGeometry x="25" y="1041" width="220" height="46" as="geometry" />
        </mxCell>

        <!-- LANE 3 NODES -->
        <mxCell id="c_recv" value="Tiếp nhận GET /api/clusters&#xa;Kiểm tra header If-None-Match ETag" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#4E342E;strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontColor=#4E342E;fontStyle=1;" vertex="1" parent="lane_core">
          <mxGeometry x="25" y="385" width="220" height="44" as="geometry" />
        </mxCell>
        <mxCell id="c_etag_dec" value="cluster_version đổi?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#FFF9C4;strokeColor=#FBC02D;strokeWidth=1.5;fontFamily=Helvetica;fontSize=10;fontStyle=1;fontColor=#F57F17;" vertex="1" parent="lane_core">
          <mxGeometry x="40" y="451" width="190" height="44" as="geometry" />
        </mxCell>
        <mxCell id="c_304" value="304 Not Modified&#xa;Giữ nguyên cụm cũ" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F5F5F5;strokeColor=#757575;strokeWidth=1.3;fontFamily=Helvetica;fontSize=10.5;fontColor=#424242;fontStyle=1;" vertex="1" parent="lane_core">
          <mxGeometry x="275" y="451" width="130" height="44" as="geometry" />
        </mxCell>
        <mxCell id="c_fetch" value="Lấy báo cáo active_only&#xa;Trích xuất [F, U, N, V] qua to_report_v2" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#4E342E;strokeWidth=1.4;fontFamily=Helvetica;fontSize=11;fontColor=#4E342E;fontStyle=1;" vertex="1" parent="lane_core">
          <mxGeometry x="25" y="517" width="220" height="44" as="geometry" />
        </mxCell>
        <mxCell id="c_split_dec" value="Tọa độ GPS hợp lệ?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#FFF9C4;strokeColor=#FBC02D;strokeWidth=1.5;fontFamily=Helvetica;fontSize=10;fontStyle=1;fontColor=#F57F17;" vertex="1" parent="lane_core">
          <mxGeometry x="45" y="583" width="180" height="44" as="geometry" />
        </mxCell>
        <mxCell id="c_rev" value="Review Queue&#xa;Tách riêng ca thiếu GPS" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF3E0;strokeColor=#FB8C00;strokeWidth=1.4;fontFamily=Helvetica;fontSize=10.5;fontColor=#E65100;fontStyle=1;" vertex="1" parent="lane_core">
          <mxGeometry x="270" y="583" width="140" height="44" as="geometry" />
        </mxCell>
        <mxCell id="c_graph" value="Ma trận C_ij &amp; Cụm Louvain&#xa;Khoảng cách Haversine, ngập, khẩn cấp" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#4E342E;strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontColor=#4E342E;fontStyle=1;" vertex="1" parent="lane_core">
          <mxGeometry x="25" y="649" width="220" height="46" as="geometry" />
        </mxCell>
        <mxCell id="c_score" value="Tính điểm ưu tiên cụm P(c)&#xa;Khóa clusterKey &amp; Cập nhật ETag mới" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#4E342E;strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontColor=#4E342E;fontStyle=1;" vertex="1" parent="lane_core">
          <mxGeometry x="25" y="717" width="220" height="46" as="geometry" />
        </mxCell>
        <mxCell id="c_resp" value="Trả JSON Clusters &amp; Review&#xa;Kèm header ETag cho Dashboard" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F5E9;strokeColor=#2E7D32;strokeWidth=1.4;fontFamily=Helvetica;fontSize=11;fontColor=#1B5E20;fontStyle=1;" vertex="1" parent="lane_core">
          <mxGeometry x="25" y="785" width="220" height="44" as="geometry" />
        </mxCell>

        <!-- LANE 4 NODES -->
        <mxCell id="d_login" value="Đăng nhập Bàn Điều phối&#xa;Khởi tạo phiên làm việc Dispatcher" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#E65100;strokeWidth=1.4;fontFamily=Helvetica;fontSize=11;fontColor=#E65100;fontStyle=1;" vertex="1" parent="lane_dash">
          <mxGeometry x="110" y="315" width="200" height="40" as="geometry" />
        </mxCell>
        <mxCell id="d_poll" value="Polling định kỳ 5s&#xa;GET /api/reports/changes &amp; /api/clusters" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF8E1;strokeColor=#FFA000;strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontColor=#E65100;fontStyle=1;" vertex="1" parent="lane_dash">
          <mxGeometry x="95" y="385" width="230" height="44" as="geometry" />
        </mxCell>
        <mxCell id="d_view" value="Cập nhật Leaflet GIS &amp; Bảng Cụm&#xa;Hiển thị ranh giới cụm &amp; Hàng xem xét" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#E65100;strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontColor=#E65100;fontStyle=1;" vertex="1" parent="lane_dash">
          <mxGeometry x="95" y="785" width="230" height="44" as="geometry" />
        </mxCell>
        <mxCell id="d_branch_dec" value="Phân loại ca xử lý?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#FFF9C4;strokeColor=#FBC02D;strokeWidth=1.5;fontFamily=Helvetica;fontSize=10;fontStyle=1;fontColor=#F57F17;" vertex="1" parent="lane_dash">
          <mxGeometry x="115" y="910" width="190" height="44" as="geometry" />
        </mxCell>
        <mxCell id="d_geocode" value="Ca thiếu GPS (Review)&#xa;Thẩm tra, gọi &amp; Gán tọa độ" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF3E0;strokeColor=#FB8C00;strokeWidth=1.4;fontFamily=Helvetica;fontSize=10.5;fontColor=#E65100;fontStyle=1;" vertex="1" parent="lane_dash">
          <mxGeometry x="15" y="975" width="175" height="44" as="geometry" />
        </mxCell>
        <mxCell id="d_pick" value="Ca đã gom cụm P(c)&#xa;Chọn cụm có độ khẩn cấp cao" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#E65100;strokeWidth=1.4;fontFamily=Helvetica;fontSize=10.5;fontColor=#E65100;fontStyle=1;" vertex="1" parent="lane_dash">
          <mxGeometry x="225" y="975" width="180" height="44" as="geometry" />
        </mxCell>
        <mxCell id="d_assign" value="Giao đội cứu hộ (PUT /team)&#xa;Đổi status -&gt; dispatched (tăng version)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF8E1;strokeColor=#FFA000;strokeWidth=1.6;fontFamily=Helvetica;fontSize=11;fontColor=#E65100;fontStyle=1;" vertex="1" parent="lane_dash">
          <mxGeometry x="95" y="1041" width="230" height="46" as="geometry" />
        </mxCell>
        <mxCell id="d_rescue" value="Đội Cứu hộ Thực địa Tác nghiệp&#xa;Tiếp cận hiện trường &amp; Triển khai ứng cứu" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1976D2;strokeWidth=1.4;fontFamily=Helvetica;fontSize=11;fontColor=#0D47A1;fontStyle=1;" vertex="1" parent="lane_dash">
          <mxGeometry x="95" y="1109" width="230" height="44" as="geometry" />
        </mxCell>
        <mxCell id="d_result_dec" value="Kết quả cứu hộ?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#FFF9C4;strokeColor=#FBC02D;strokeWidth=1.5;fontFamily=Helvetica;fontSize=10;fontStyle=1;fontColor=#F57F17;" vertex="1" parent="lane_dash">
          <mxGeometry x="115" y="1175" width="190" height="44" as="geometry" />
        </mxCell>
        <mxCell id="d_ok" value="Thành công: resolved&#xa;Cập nhật cứu hộ hoàn tất" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F5E9;strokeColor=#2E7D32;strokeWidth=1.4;fontFamily=Helvetica;fontSize=10.5;fontColor=#1B5E20;fontStyle=1;" vertex="1" parent="lane_dash">
          <mxGeometry x="15" y="1243" width="180" height="42" as="geometry" />
        </mxCell>
        <mxCell id="d_cancel" value="Hủy / Giả: cancelled&#xa;Bắt buộc nhập lý do đóng" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFEBEE;strokeColor=#E53935;strokeWidth=1.4;fontFamily=Helvetica;fontSize=10.5;fontColor=#B71C1C;fontStyle=1;" vertex="1" parent="lane_dash">
          <mxGeometry x="225" y="1243" width="180" height="42" as="geometry" />
        </mxCell>

        <!-- CONNECTING EDGES -->
        <mxCell id="e_m1" edge="1" parent="1" source="m_start" target="m_choose" style="endArrow=classic;html=1;strokeColor=#1976D2;strokeWidth=1.4;" />
        <mxCell id="e_m2" edge="1" parent="1" source="m_choose" target="m_ai" style="endArrow=classic;html=1;strokeColor=#1976D2;strokeWidth=1.4;" />
        <mxCell id="e_m3" edge="1" parent="1" source="m_ai" target="m_form" style="endArrow=classic;html=1;strokeColor=#1976D2;strokeWidth=1.4;" />
        <mxCell id="e_m4" edge="1" parent="1" source="m_form" target="m_net_dec" style="endArrow=classic;html=1;strokeColor=#1976D2;strokeWidth=1.4;" />
        <mxCell id="e_m5" value="Mất sóng" edge="1" parent="1" source="m_net_dec" target="m_sms" style="endArrow=classic;html=1;strokeColor=#E53935;strokeWidth=1.3;fontSize=9;fontColor=#C62828;" />
        <mxCell id="e_m6" value="Có IP data" edge="1" parent="1" source="m_net_dec" target="m_rest" style="endArrow=classic;html=1;strokeColor=#1976D2;strokeWidth=1.3;fontSize=9;fontColor=#0D47A1;" />

        <!-- Cross Lane 1 -> Lane 2: Clean Non-overlapping bridges -->
        <mxCell id="e_x1" value="SMS Gateway Webhook" edge="1" parent="1" source="m_sms" target="s_recv" style="endArrow=classic;html=1;strokeColor=#E53935;strokeWidth=1.3;dashed=1;fontSize=9;fontColor=#C62828;edgeStyle=orthogonalEdgeStyle;rounded=0;" />
        <mxCell id="e_x2" value="HTTP REST" edge="1" parent="1" source="m_rest" target="s_recv" style="endArrow=classic;html=1;strokeColor=#1976D2;strokeWidth=1.4;fontSize=9;fontColor=#0D47A1;" />

        <!-- Lane 2 Downwards -->
        <mxCell id="e_s1" edge="1" parent="1" source="s_recv" target="s_val" style="endArrow=classic;html=1;strokeColor=#7B1FA2;strokeWidth=1.4;" />
        <mxCell id="e_s2" edge="1" parent="1" source="s_val" target="s_dedup_dec" style="endArrow=classic;html=1;strokeColor=#7B1FA2;strokeWidth=1.4;" />
        <mxCell id="e_s3" value="Trùng" edge="1" parent="1" source="s_dedup_dec" target="s_dup" style="endArrow=classic;html=1;strokeColor=#2E7D32;strokeWidth=1.3;fontSize=9;fontColor=#2E7D32;" />
        <mxCell id="e_s4" value="Hợp lệ" edge="1" parent="1" source="s_dedup_dec" target="s_tx" style="endArrow=classic;html=1;strokeColor=#00695C;strokeWidth=1.4;fontSize=9;fontColor=#00695C;" />
        <mxCell id="e_s5" edge="1" parent="1" source="s_tx" target="s_meta" style="endArrow=classic;html=1;strokeColor=#7B1FA2;strokeWidth=1.4;" />

        <!-- Lane 2 -> Lane 1 ACK -->
        <mxCell id="e_s6" value="Trả HTTP 201 / ACK" edge="1" parent="1" source="s_meta" target="m_wait_ack" style="endArrow=classic;html=1;strokeColor=#2E7D32;strokeWidth=1.5;fontSize=9;fontColor=#2E7D32;" />
        <mxCell id="e_m7" value="Chờ điều phối" edge="1" parent="1" source="m_wait_ack" target="m_poll_status" style="endArrow=classic;html=1;strokeColor=#1976D2;strokeWidth=1.3;dashed=1;fontSize=9;fontColor=#1976D2;" />
        <mxCell id="e_m8" edge="1" parent="1" source="m_poll_status" target="m_end" style="endArrow=classic;html=1;strokeColor=#2E7D32;strokeWidth=1.4;" />

        <!-- Phase 2: Lane 4 Polling -> Lane 3 -->
        <mxCell id="e_d1" edge="1" parent="1" source="d_login" target="d_poll" style="endArrow=classic;html=1;strokeColor=#E65100;strokeWidth=1.4;" />
        <mxCell id="e_d2" value="GET /api/clusters (ETag)" edge="1" parent="1" source="d_poll" target="c_recv" style="endArrow=classic;html=1;strokeColor=#E65100;strokeWidth=1.4;fontSize=9;fontColor=#E65100;" />

        <!-- Lane 3 Downwards -->
        <mxCell id="e_c1" edge="1" parent="1" source="c_recv" target="c_etag_dec" style="endArrow=classic;html=1;strokeColor=#4E342E;strokeWidth=1.4;" />
        <mxCell id="e_c2" value="Không đổi" edge="1" parent="1" source="c_etag_dec" target="c_304" style="endArrow=classic;html=1;strokeColor=#757575;strokeWidth=1.3;fontSize=9;fontColor=#757575;" />
        <mxCell id="e_c3" value="Đổi" edge="1" parent="1" source="c_etag_dec" target="c_fetch" style="endArrow=classic;html=1;strokeColor=#4E342E;strokeWidth=1.4;fontSize=9;fontColor=#4E342E;" />
        <mxCell id="e_c4" edge="1" parent="1" source="c_fetch" target="c_split_dec" style="endArrow=classic;html=1;strokeColor=#4E342E;strokeWidth=1.4;" />
        <mxCell id="e_c5" value="Thiếu GPS" edge="1" parent="1" source="c_split_dec" target="c_rev" style="endArrow=classic;html=1;strokeColor=#FB8C00;strokeWidth=1.3;fontSize=9;fontColor=#E65100;" />
        <mxCell id="e_c5b" value="Gộp Review" edge="1" parent="1" source="c_rev" target="c_resp" style="endArrow=classic;html=1;strokeColor=#FB8C00;strokeWidth=1.3;dashed=1;fontSize=9;fontColor=#E65100;edgeStyle=orthogonalEdgeStyle;rounded=0;" />
        <mxCell id="e_c6" value="Có GPS" edge="1" parent="1" source="c_split_dec" target="c_graph" style="endArrow=classic;html=1;strokeColor=#4E342E;strokeWidth=1.4;fontSize=9;fontColor=#4E342E;" />
        <mxCell id="e_c7" edge="1" parent="1" source="c_graph" target="c_score" style="endArrow=classic;html=1;strokeColor=#4E342E;strokeWidth=1.4;" />
        <mxCell id="e_c8" edge="1" parent="1" source="c_score" target="c_resp" style="endArrow=classic;html=1;strokeColor=#2E7D32;strokeWidth=1.4;" />

        <!-- Lane 3 -> Lane 4 Result -->
        <mxCell id="e_c9" value="JSON: Cụm P(c) &amp; Review Queue" edge="1" parent="1" source="c_resp" target="d_view" style="endArrow=classic;html=1;strokeColor=#2E7D32;strokeWidth=1.5;fontSize=9;fontColor=#2E7D32;" />

        <!-- Phase 3: Lane 4 Downwards -->
        <mxCell id="e_d3" edge="1" parent="1" source="d_view" target="d_branch_dec" style="endArrow=classic;html=1;strokeColor=#E65100;strokeWidth=1.4;" />
        <mxCell id="e_d4" edge="1" parent="1" source="d_branch_dec" target="d_geocode" style="endArrow=classic;html=1;strokeColor=#FB8C00;strokeWidth=1.3;" />
        <mxCell id="e_d5" edge="1" parent="1" source="d_branch_dec" target="d_pick" style="endArrow=classic;html=1;strokeColor=#E65100;strokeWidth=1.3;" />
        <mxCell id="e_d6" edge="1" parent="1" source="d_geocode" target="d_assign" style="endArrow=classic;html=1;strokeColor=#E65100;strokeWidth=1.3;" />
        <mxCell id="e_d7" edge="1" parent="1" source="d_pick" target="d_assign" style="endArrow=classic;html=1;strokeColor=#E65100;strokeWidth=1.3;" />

        <!-- Dispatch Team -> Lane 2 Server DB -->
        <mxCell id="e_d8" value="PUT /team &amp; PATCH /status" edge="1" parent="1" source="d_assign" target="s_status_tx" style="endArrow=classic;html=1;strokeColor=#00695C;strokeWidth=1.5;fontSize=9;fontColor=#00695C;" />

        <mxCell id="e_d9" edge="1" parent="1" source="d_assign" target="d_rescue" style="endArrow=classic;html=1;strokeColor=#1976D2;strokeWidth=1.4;" />
        <mxCell id="e_d10" edge="1" parent="1" source="d_rescue" target="d_result_dec" style="endArrow=classic;html=1;strokeColor=#1976D2;strokeWidth=1.4;" />
        <mxCell id="e_d11" value="Đạt" edge="1" parent="1" source="d_result_dec" target="d_ok" style="endArrow=classic;html=1;strokeColor=#2E7D32;strokeWidth=1.3;fontSize=9;fontColor=#2E7D32;" />
        <mxCell id="e_d12" value="Hủy" edge="1" parent="1" source="d_result_dec" target="d_cancel" style="endArrow=classic;html=1;strokeColor=#E53935;strokeWidth=1.3;fontSize=9;fontColor=#C62828;" />

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''
    return xml

def main():
    # 1. Tạo SVG
    svg_str = build_svg()
    svg_path = DIAGRAM_DIR / "flowchart.svg"
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_str)
    print(f"Saved SVG to {svg_path}")

    # 2. Tạo Draw.io XML
    drawio_str = build_drawio_xml()
    drawio_path = DIAGRAM_DIR / "flowchart.drawio"
    with open(drawio_path, "w", encoding="utf-8") as f:
        f.write(drawio_str)
    print(f"Saved Draw.io to {drawio_path}")

    # 3. Xuất vector PDF bằng PyMuPDF (fitz)
    pdf_path = DIAGRAM_DIR / "flowchart.pdf"
    doc = fitz.open()
    svg_bytes = svg_str.encode("utf-8")
    svg_doc = fitz.open(stream=svg_bytes, filetype="svg")
    pdf_bytes = svg_doc.convert_to_pdf()
    svg_doc.close()

    pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    doc.insert_pdf(pdf_doc)
    doc.save(pdf_path)
    doc.close()
    pdf_doc.close()
    print(f"Exported Vector PDF to {pdf_path}")

    # 4. Xuất PNG preview
    preview_path = DIAGRAM_DIR / "flowchart_preview.png"
    doc_render = fitz.open(pdf_path)
    page = doc_render[0]
    pix = page.get_pixmap(dpi=150)
    pix.save(preview_path)
    doc_render.close()
    print(f"Exported PNG Preview to {preview_path}")

if __name__ == "__main__":
    main()
