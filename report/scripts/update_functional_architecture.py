#!/usr/bin/env python3
"""
Tạo sơ đồ functional_architecture.drawio và xuất ra functional_architecture.pdf
Sơ đồ luồng chức năng và tương tác giữa các phân hệ trong hệ thống cứu hộ (Hình 3.1).
Thiết kế tinh gọn, súc tích (cắt giảm chữ rườm rà), chuẩn mỹ thuật IEEE/Springer.
"""

import os
from pathlib import Path
import fitz  # PyMuPDF

DIAGRAM_DIR = Path("/mnt/d/NCKH2/report/assets/diagrams")

def build_svg() -> str:
    # Canvas width: 1080, height: 500
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 500" width="1080" height="500">
  <defs>
    <style>
      .sectitle { font-family: 'Roboto', 'DejaVu Sans', 'Arial', sans-serif; font-size: 12.5px; font-weight: bold; }
      .boxbold { font-family: 'Roboto', 'DejaVu Sans', 'Arial', sans-serif; font-size: 11.5px; font-weight: bold; }
      .boxsub { font-family: 'Roboto', 'DejaVu Sans', 'Arial', sans-serif; font-size: 10px; fill: #37474F; }
      .actorbold { font-family: 'Roboto', 'DejaVu Sans', 'Arial', sans-serif; font-size: 11.5px; font-weight: bold; fill: #BF360C; }
      .actorsub { font-family: 'Roboto', 'DejaVu Sans', 'Arial', sans-serif; font-size: 10.5px; fill: #E65100; }
      .lblbold { font-family: 'Roboto', 'DejaVu Sans', 'Arial', sans-serif; font-size: 9.5px; font-weight: bold; }
      .lblsub { font-family: 'Roboto', 'DejaVu Sans', 'Arial', sans-serif; font-size: 8.5px; fill: #546E7A; }
    </style>
    <marker id="arrow-blue" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#1976D2" />
    </marker>
    <marker id="arrow-orange" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#E65100" />
    </marker>
    <marker id="arrow-purple" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#7B1FA2" />
    </marker>
    <marker id="arrow-teal" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#00695C" />
    </marker>
    <marker id="arrow-actor" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#E65100" />
    </marker>
    <marker id="arrow-green" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#2E7D32" />
    </marker>
  </defs>

  <!-- Background Canvas -->
  <rect x="0" y="0" width="1080" height="500" fill="#FFFFFF" />

  <!-- ==================== CỘT 1: PHÂN HỆ DI ĐỘNG BIÊN (TRÁI) ==================== -->
  <rect x="20" y="16" width="275" height="468" rx="8" fill="#F8FAFC" stroke="#90CAF9" stroke-width="1.5" />
  <rect x="20" y="16" width="275" height="32" rx="8" fill="#E3F2FD" stroke="#90CAF9" stroke-width="1.5" />
  <text x="157" y="37" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="12px" font-weight="bold" fill="#0D47A1">PHÂN HỆ DI ĐỘNG BIÊN (EDGE)</text>

  <!-- Actor Mobile -->
  <rect x="36" y="58" width="242" height="52" rx="6" fill="#FFF3E0" stroke="#FF9800" stroke-width="1.2" />
  <text x="157" y="79" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="11px" font-weight="bold" fill="#BF360C">Người dân / Nạn nhân</text>
  <text x="157" y="97" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="10.5px" font-weight="bold" fill="#E65100">&amp; Đội cứu hộ thực địa</text>

  <!-- Mũi tên Actor <-> Flutter Client -->
  <line x1="157" y1="110" x2="157" y2="132" stroke="#FF9800" stroke-width="1.5" marker-start="url(#arrow-actor)" marker-end="url(#arrow-actor)" />
  <text x="166" y="124" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="8.5px" fill="#D84315">Tương tác App</text>

  <!-- Ứng dụng Di động Flutter -->
  <rect x="36" y="132" width="242" height="336" rx="8" fill="#FFFFFF" stroke="#1976D2" stroke-width="1.8" />
  <rect x="36" y="132" width="242" height="32" rx="8" fill="#E8F1FB" stroke="#1976D2" stroke-width="1.8" />
  <text x="157" y="153" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="11.5px" font-weight="bold" fill="#0D47A1">Ứng dụng Di động (Flutter Client)</text>

  <!-- Module 1: SOS & Báo cứu nạn -->
  <rect x="47" y="174" width="220" height="64" rx="5" fill="#F4F8FD" stroke="#BBDEFB" stroke-width="1" />
  <text x="58" y="193" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="10.5px" font-weight="bold" fill="#1565C0">SOS Khẩn cấp &amp; Báo cáo</text>
  <text x="58" y="210" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#455A64">• SOS 1 chạm gửi tọa độ GPS tức thời</text>
  <text x="58" y="226" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#455A64">• Báo ngập đa phương thức (Ảnh, N, V)</text>

  <!-- Module 2: Edge AI -->
  <rect x="47" y="248" width="220" height="86" rx="5" fill="#FDF2F8" stroke="#F8BBD0" stroke-width="1" />
  <text x="58" y="267" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="10.5px" font-weight="bold" fill="#AD1457">Suy luận On-device Edge AI</text>
  <text x="58" y="285" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#455A64">• Phân loại mức ngập F (MobileNetV3)</text>
  <text x="58" y="301" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#880E4F">• Runtime: ExecuTorch (chính), ONNX</text>
  <text x="58" y="317" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#455A64">• Tính điểm khẩn cấp biên E_i</text>

  <!-- Module 3: Outbox & Sync -->
  <rect x="47" y="344" width="220" height="112" rx="5" fill="#F5F5F5" stroke="#CFD8DC" stroke-width="1" />
  <text x="58" y="363" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="10.5px" font-weight="bold" fill="#37474F">Hive Outbox &amp; Ngoại tuyến</text>
  <text x="58" y="381" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#455A64">• Store-and-Forward chống mất tin</text>
  <text x="58" y="397" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#455A64">• Chuẩn hóa băm JCS (RFC 8785)</text>
  <text x="58" y="413" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#1565C0">• Tra cứu tiến độ ca (/reports/status)</text>
  <text x="58" y="429" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#455A64">• Tiếp nhận nhiệm vụ cứu hộ thực địa</text>


  <!-- ==================== CỘT 2: MÁY CHỦ XỬ LÝ TRUNG TÂM (GIỮA) ==================== -->
  <rect x="415" y="16" width="290" height="468" rx="8" fill="#FAF5FB" stroke="#7B1FA2" stroke-width="1.6" stroke-dasharray="6,4" />
  <rect x="415" y="16" width="290" height="32" rx="8" fill="#F3E5F5" stroke="#7B1FA2" stroke-width="1.6" />
  <text x="560" y="37" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="12px" font-weight="bold" fill="#6A1B9A">MÁY CHỦ XỬ LÝ TRUNG TÂM (BACKEND CORE)</text>

  <!-- Box 1: FastAPI Ingestion & Service -->
  <rect x="428" y="58" width="264" height="110" rx="7" fill="#FFFFFF" stroke="#7B1FA2" stroke-width="1.8" />
  <rect x="428" y="58" width="264" height="26" rx="7" fill="#EDE7F6" stroke="#7B1FA2" stroke-width="1.8" />
  <text x="560" y="75" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="10.5px" font-weight="bold" fill="#4A148C">Cổng Tiếp nhận &amp; REST API (FastAPI)</text>
  <text x="439" y="99" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#37474F">• Hợp đồng JCS (RFC 8785) &amp; Header v1</text>
  <text x="439" y="115" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#37474F">• Chống trùng lặp Idempotency (messages_dedup)</text>
  <text x="439" y="131" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#37474F">• Tiếp nhận SMS Webhook (/api/sms/inbound)</text>
  <text x="439" y="147" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#37474F">• Xác thực phiên &amp; REST API cho Mobile, Web</text>

  <!-- Mũi tên Gateway <-> Storage (Ghi nhận tức thời) -->
  <line x1="560" y1="168" x2="560" y2="198" stroke="#00695C" stroke-width="1.6" marker-start="url(#arrow-teal)" marker-end="url(#arrow-teal)" />
  <rect x="475" y="175" width="170" height="16" rx="3" fill="#FFFFFF" stroke="#B2DFDB" stroke-width="0.8" />
  <text x="560" y="187" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="8.5px" font-weight="bold" fill="#00695C">Ghi nhận tức thời &amp; Đọc ca (SQLite WAL)</text>

  <!-- Box 2: Lưu trữ Bền vững -->
  <rect x="428" y="198" width="264" height="96" rx="7" fill="#FFFFFF" stroke="#00695C" stroke-width="1.8" />
  <rect x="428" y="198" width="264" height="26" rx="7" fill="#E0F2F1" stroke="#00695C" stroke-width="1.8" />
  <text x="560" y="215" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="10.5px" font-weight="bold" fill="#004D40">Kho Lưu trữ Bền vững (SQLite &amp; Files)</text>
  <text x="439" y="239" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#37474F">• CSDL SQLite WAL (reports, teams, meta)</text>
  <text x="439" y="255" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#37474F">• Nhật ký kiểm toán phân công report_events</text>
  <text x="439" y="271" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#37474F">• Thư mục lưu trữ ảnh hiện trường (uploads/)</text>

  <!-- Mũi tên Storage <-> rescue_core -->
  <line x1="560" y1="294" x2="560" y2="324" stroke="#4E342E" stroke-width="1.6" marker-start="url(#arrow-purple)" marker-end="url(#arrow-purple)" />
  <rect x="472" y="301" width="176" height="16" rx="3" fill="#FFFFFF" stroke="#D7CCC8" stroke-width="0.8" />
  <text x="560" y="313" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="8.5px" font-weight="bold" fill="#4E342E">Đọc active reports ↔ Cache RAM (ETag)</text>

  <!-- Box 3: Lõi thuật toán rescue_core & ClusterService -->
  <rect x="428" y="324" width="264" height="144" rx="7" fill="#FFFFFF" stroke="#4E342E" stroke-width="1.8" />
  <rect x="428" y="324" width="264" height="26" rx="7" fill="#EFEBE9" stroke="#4E342E" stroke-width="1.8" />
  <text x="560" y="341" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="10.5px" font-weight="bold" fill="#3E2723">Lõi Thuật toán &amp; Phân cụm (rescue_core)</text>
  <text x="439" y="365" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#37474F">• Ma trận đồ thị C_ij &amp; Phân cụm Louvain đa tỉ lệ</text>
  <text x="439" y="381" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#37474F">• Điểm ưu tiên cụm P(c) đa tiêu chí (E, F, N, V)</text>
  <text x="439" y="397" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#37474F">• Khóa clusterKey duy trì lựa chọn khi tải</text>
  <text x="439" y="413" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#37474F">• Hàng xem xét (Review Queue) thiếu GPS/giờ</text>
  <text x="439" y="429" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#37474F">• Bộ nhớ đệm phân cụm trên RAM (ETag)</text>


  <!-- ==================== CỘT 3: BÀN ĐIỀU PHỐI WEB GIS (PHẢI) ==================== -->
  <rect x="795" y="16" width="265" height="468" rx="8" fill="#FFFDF8" stroke="#FFE082" stroke-width="1.5" />
  <rect x="795" y="16" width="265" height="32" rx="8" fill="#FFF8E1" stroke="#FFE082" stroke-width="1.5" />
  <text x="927" y="37" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="12px" font-weight="bold" fill="#E65100">PHÂN HỆ ĐIỀU PHỐI WEB (DASHBOARD)</text>

  <!-- Actor Dispatcher -->
  <rect x="810" y="58" width="235" height="52" rx="6" fill="#FFF3E0" stroke="#FF9800" stroke-width="1.2" />
  <text x="927" y="80" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="11.5px" font-weight="bold" fill="#BF360C">Điều phối viên cứu nạn</text>
  <text x="927" y="96" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="10px" fill="#E65100">(Dispatcher Web Client)</text>

  <!-- Mũi tên Actor <-> Dashboard -->
  <line x1="927" y1="110" x2="927" y2="132" stroke="#FF9800" stroke-width="1.5" marker-start="url(#arrow-actor)" marker-end="url(#arrow-actor)" />
  <text x="936" y="124" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="8.5px" fill="#D84315">Vận hành Web</text>

  <!-- Bàn điều phối Web GIS Leaflet -->
  <rect x="810" y="132" width="235" height="336" rx="8" fill="#FFFFFF" stroke="#F57C00" stroke-width="1.8" />
  <rect x="810" y="132" width="235" height="32" rx="8" fill="#FFF3E0" stroke="#F57C00" stroke-width="1.8" />
  <text x="927" y="153" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="11.5px" font-weight="bold" fill="#E65100">Bàn điều phối Web (Leaflet GIS)</text>

  <!-- Module 1: Bản đồ giám sát -->
  <rect x="821" y="174" width="213" height="64" rx="5" fill="#FFFDE7" stroke="#FFF59D" stroke-width="1" />
  <text x="832" y="193" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="10.5px" font-weight="bold" fill="#F57F17">Bản đồ Giám sát Leaflet GIS</text>
  <text x="832" y="210" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#455A64">• Ranh giới cụm &amp; màu ưu tiên theo P(c)</text>
  <text x="832" y="226" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#455A64">• Chấm gán tọa độ ca thiếu GPS/thời gian</text>

  <!-- Module 2: Quản lý cụm & Ca -->
  <rect x="821" y="248" width="213" height="86" rx="5" fill="#FFF8E1" stroke="#FFE082" stroke-width="1" />
  <text x="832" y="267" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="10.5px" font-weight="bold" fill="#E65100">Bảng Cụm &amp; Thẩm tra (Review)</text>
  <text x="832" y="285" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#455A64">• Danh sách xếp hạng ưu tiên giảm dần P(c)</text>
  <text x="832" y="301" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#455A64">• Hàng xem xét (Review Queue) thẩm tra SOS</text>
  <text x="832" y="317" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#455A64">• Khóa clusterKey giữ ổn định hiển thị</text>

  <!-- Module 3: Phân công & Quản trị -->
  <rect x="821" y="344" width="213" height="112" rx="5" fill="#FAFAFA" stroke="#CFD8DC" stroke-width="1" />
  <text x="832" y="363" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="10.5px" font-weight="bold" fill="#37474F">Phân công Đội &amp; Quản trị</text>
  <text x="832" y="381" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#455A64">• Giao đội cứu trợ &amp; đổi 4 trạng thái ca</text>
  <text x="832" y="397" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#455A64">• Quản lý đội cứu hộ (/api/teams)</text>
  <text x="832" y="413" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#455A64">• Nhật ký kiểm toán ca (report_events)</text>
  <text x="832" y="429" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#455A64">• Quản lý tài khoản điều phối &amp; sao lưu DB</text>


  <!-- ==================== CÁC TUYẾN KẾT NỐI LIÊN PHÂN HỆ ==================== -->
  
  <!-- 1. KÊNH IP TRỰC TIẾP (REST API) MOBILE <-> FASTAPI -->
  <rect x="306" y="66" width="98" height="52" rx="4" fill="#FFFFFF" stroke="#90CAF9" stroke-width="1" />
  <text x="355" y="80" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9px" font-weight="bold" fill="#0D47A1">KÊNH IP (REST)</text>
  <text x="355" y="93" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="8px" fill="#1565C0">• POST /sync, /reports</text>
  <text x="355" y="105" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="8px" fill="#1565C0">• GET /reports/status</text>

  <!-- Mũi tên từ Flutter Client sang Hộp Kênh IP -->
  <line x1="278" y1="92" x2="306" y2="92" stroke="#1976D2" stroke-width="1.6" marker-start="url(#arrow-blue)" marker-end="url(#arrow-blue)" />
  <!-- Mũi tên từ Hộp Kênh IP sang FastAPI -->
  <line x1="404" y1="92" x2="428" y2="92" stroke="#1976D2" stroke-width="1.6" marker-start="url(#arrow-blue)" marker-end="url(#arrow-blue)" />


  <!-- 2. KÊNH GSM & SMS GATEWAY TRUNG GIAN -->
  <rect x="306" y="132" width="98" height="52" rx="5" fill="#FFFDE7" stroke="#FBC02D" stroke-width="1.2" />
  <text x="355" y="147" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9px" font-weight="bold" fill="#F57F17">SMS GATEWAY</text>
  <text x="355" y="160" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="8px" fill="#6D4C41">Thiết bị / Tổng đài GSM</text>
  <text x="355" y="172" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="7.5px" fill="#D84315">Thu nhận tin SMS SOS</text>

  <!-- Mũi tên từ Flutter Client sang SMS Gateway (GSM SMS) -->
  <line x1="278" y1="158" x2="306" y2="158" stroke="#F57C00" stroke-width="1.5" stroke-dasharray="3,2" marker-end="url(#arrow-orange)" />
  <text x="292" y="152" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="7.5px" font-weight="bold" fill="#E65100">GSM</text>

  <!-- Mũi tên từ SMS Gateway sang FastAPI Webhook -->
  <line x1="404" y1="158" x2="428" y2="158" stroke="#2E7D32" stroke-width="1.5" marker-end="url(#arrow-green)" />
  <text x="416" y="151" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="7px" font-weight="bold" fill="#2E7D32">HTTP</text>

  <rect x="306" y="188" width="98" height="18" rx="3" fill="#E8F5E9" stroke="#81C784" stroke-width="0.8" />
  <text x="355" y="200" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="7.5px" font-weight="bold" fill="#2E7D32">POST /api/sms/inbound</text>


  <!-- 3. KẾT NỐI FASTAPI GATEWAY <-> WEB DASHBOARD -->
  <rect x="702" y="76" width="94" height="74" rx="4" fill="#FFFFFF" stroke="#FFCC80" stroke-width="1" />
  <text x="749" y="90" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9px" font-weight="bold" fill="#E65100">HTTP REST API</text>
  <text x="749" y="103" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="7.8px" fill="#BF360C">• Poll: /changes, /clusters</text>
  <text x="749" y="115" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="7.8px" fill="#BF360C">• Điều phối: /team, /status</text>
  <text x="749" y="127" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="7.8px" fill="#BF360C">• Quản lý: /api/teams</text>
  <text x="749" y="139" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="7.2px" fill="#546E7A">(Cookie Session Auth)</text>

  <!-- Mũi tên từ FastAPI sang Hộp REST API Dashboard -->
  <line x1="692" y1="113" x2="702" y2="113" stroke="#E65100" stroke-width="1.6" marker-start="url(#arrow-orange)" marker-end="url(#arrow-orange)" />
  <!-- Mũi tên từ Hộp REST API sang Web Dashboard -->
  <line x1="796" y1="113" x2="810" y2="113" stroke="#E65100" stroke-width="1.6" marker-start="url(#arrow-orange)" marker-end="url(#arrow-orange)" />

</svg>'''
    return svg

def build_drawio_xml() -> str:
    # Sơ đồ Draw.io tương ứng hoàn chỉnh với bố cục tinh gọn
    return '''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" agent="Antigravity" version="24.0.0">
  <diagram id="diag-func-arch" name="Kien-truc-chuc-nang-he-thong">
    <mxGraphModel dx="1200" dy="700" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1080" pageHeight="500" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        
        <!-- Cột 1: Di động biên -->
        <mxCell id="c1_frame" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F8FAFC;strokeColor=#90CAF9;strokeWidth=1.5;arcSize=4;" vertex="1" parent="1">
          <mxGeometry x="20" y="16" width="275" height="468" as="geometry" />
        </mxCell>
        <mxCell id="c1_title" value="&lt;b&gt;PHÂN HỆ DI ĐỘNG BIÊN (EDGE)&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E3F2FD;strokeColor=#90CAF9;strokeWidth=1.5;fontColor=#0D47A1;fontSize=12;fontFamily=Helvetica;" vertex="1" parent="1">
          <mxGeometry x="20" y="16" width="275" height="32" as="geometry" />
        </mxCell>
        <mxCell id="act_mob" value="&lt;b&gt;Người dân / Nạn nhân&lt;/b&gt;&lt;br&gt;&lt;b&gt;&amp;amp; Đội cứu hộ thực địa&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF3E0;strokeColor=#FF9800;strokeWidth=1.2;fontSize=11;fontColor=#BF360C;fontFamily=Helvetica;" vertex="1" parent="1">
          <mxGeometry x="36" y="58" width="242" height="52" as="geometry" />
        </mxCell>
        <mxCell id="app_flutter" value="&lt;b&gt;Ứng dụng Di động (Flutter Client)&lt;/b&gt;&lt;hr&gt;&lt;div align=&quot;left&quot; style=&quot;font-size:10px;color:#37474F;&quot;&gt;&lt;b&gt;• SOS &amp;amp; Báo cáo:&lt;/b&gt; 1 chạm GPS, Ảnh, N, V&lt;br&gt;&lt;b&gt;• On-device Edge AI:&lt;/b&gt; MobileNetV3 (F); ExecuTorch, ONNX; Điểm khẩn cấp E_i&lt;br&gt;&lt;b&gt;• Hive Outbox &amp;amp; Ngoại tuyến:&lt;/b&gt; Store-and-Forward, JCS RFC 8785&lt;br&gt;&lt;b&gt;• Tiến độ ca:&lt;/b&gt; Tra cứu /reports/status &amp;amp; Tác nghiệp thực địa&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1976D2;strokeWidth=1.8;fontSize=11.5;fontFamily=Helvetica;align=center;verticalAlign=top;spacingTop=6;" vertex="1" parent="1">
          <mxGeometry x="36" y="132" width="242" height="336" as="geometry" />
        </mxCell>

        <!-- Trung gian: SMS Gateway -->
        <mxCell id="sms_gw" value="&lt;b&gt;SMS GATEWAY&lt;/b&gt;&lt;br&gt;&lt;font style=&quot;font-size:9px;color:#5D4037;&quot;&gt;Thiết bị / Tổng đài GSM&lt;br&gt;Nhận SMS SOS &amp;amp; Chuyển tiếp Webhook&lt;/font&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFDE7;strokeColor=#FBC02D;strokeWidth=1.2;fontSize=9.5;fontFamily=Helvetica;align=center;" vertex="1" parent="1">
          <mxGeometry x="306" y="132" width="98" height="52" as="geometry" />
        </mxCell>
        
        <!-- Cột 2: Máy chủ trung tâm -->
        <mxCell id="c2_frame" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FAF5FB;strokeColor=#7B1FA2;strokeWidth=1.6;dashed=1;dashPattern=6 4;arcSize=4;" vertex="1" parent="1">
          <mxGeometry x="415" y="16" width="290" height="468" as="geometry" />
        </mxCell>
        <mxCell id="c2_title" value="&lt;b&gt;MÁY CHỦ XỬ LÝ TRUNG TÂM (BACKEND CORE)&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F3E5F5;strokeColor=#7B1FA2;strokeWidth=1.6;fontColor=#6A1B9A;fontSize=12;fontFamily=Helvetica;" vertex="1" parent="1">
          <mxGeometry x="415" y="16" width="290" height="32" as="geometry" />
        </mxCell>
        <mxCell id="gw_api" value="&lt;b&gt;Cổng Tiếp nhận &amp;amp; REST API (FastAPI)&lt;/b&gt;&lt;hr&gt;&lt;div align=&quot;left&quot; style=&quot;font-size:9.5px;color:#37474F;&quot;&gt;• Hợp đồng JCS (RFC 8785) &amp;amp; Header v1&lt;br&gt;• Chống trùng lặp Idempotency (messages_dedup)&lt;br&gt;• Tiếp nhận SMS Webhook (/api/sms/inbound)&lt;br&gt;• Xác thực phiên &amp;amp; REST API cho Mobile, Web&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#7B1FA2;strokeWidth=1.8;fontSize=10.5;fontFamily=Helvetica;align=center;verticalAlign=top;spacingTop=6;" vertex="1" parent="1">
          <mxGeometry x="428" y="58" width="264" height="110" as="geometry" />
        </mxCell>
        <mxCell id="db_storage" value="&lt;b&gt;Kho Lưu trữ Bền vững (SQLite &amp;amp; Files)&lt;/b&gt;&lt;hr&gt;&lt;div align=&quot;left&quot; style=&quot;font-size:9.5px;color:#37474F;&quot;&gt;• CSDL SQLite WAL (reports, teams, meta)&lt;br&gt;• Nhật ký kiểm toán phân công report_events&lt;br&gt;• Thư mục lưu trữ ảnh hiện trường (uploads/)&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#00695C;strokeWidth=1.8;fontSize=10.5;fontFamily=Helvetica;align=center;verticalAlign=top;spacingTop=6;" vertex="1" parent="1">
          <mxGeometry x="428" y="198" width="264" height="96" as="geometry" />
        </mxCell>
        <mxCell id="core_rescue" value="&lt;b&gt;Lõi Thuật toán &amp;amp; Phân cụm (rescue_core)&lt;/b&gt;&lt;hr&gt;&lt;div align=&quot;left&quot; style=&quot;font-size:9.5px;color:#37474F;&quot;&gt;• Ma trận đồ thị C_ij &amp;amp; Phân cụm Louvain đa tỉ lệ&lt;br&gt;• Điểm ưu tiên cụm P(c) đa tiêu chí (E, F, N, V)&lt;br&gt;• Khóa clusterKey duy trì lựa chọn khi tải&lt;br&gt;• Hàng xem xét (Review Queue) thiếu GPS/giờ&lt;br&gt;• Bộ nhớ đệm phân cụm trên RAM (ETag)&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#4E342E;strokeWidth=1.8;fontSize=10.5;fontFamily=Helvetica;align=center;verticalAlign=top;spacingTop=6;" vertex="1" parent="1">
          <mxGeometry x="428" y="324" width="264" height="144" as="geometry" />
        </mxCell>

        <!-- Cột 3: Web Dashboard -->
        <mxCell id="c3_frame" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFDF8;strokeColor=#FFE082;strokeWidth=1.5;arcSize=4;" vertex="1" parent="1">
          <mxGeometry x="795" y="16" width="265" height="468" as="geometry" />
        </mxCell>
        <mxCell id="c3_title" value="&lt;b&gt;PHÂN HỆ ĐIỀU PHỐI WEB (DASHBOARD)&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF8E1;strokeColor=#FFE082;strokeWidth=1.5;fontColor=#E65100;fontSize=12;fontFamily=Helvetica;" vertex="1" parent="1">
          <mxGeometry x="795" y="16" width="265" height="32" as="geometry" />
        </mxCell>
        <mxCell id="act_disp" value="&lt;b&gt;Điều phối viên cứu nạn&lt;/b&gt;&lt;br&gt;(Dispatcher Web Client)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF3E0;strokeColor=#FF9800;strokeWidth=1.2;fontSize=11;fontColor=#BF360C;fontFamily=Helvetica;" vertex="1" parent="1">
          <mxGeometry x="810" y="58" width="235" height="52" as="geometry" />
        </mxCell>
        <mxCell id="dash_web" value="&lt;b&gt;Bàn điều phối Web (Leaflet GIS)&lt;/b&gt;&lt;hr&gt;&lt;div align=&quot;left&quot; style=&quot;font-size:9.5px;color:#37474F;&quot;&gt;&lt;b&gt;• Bản đồ Leaflet GIS:&lt;/b&gt; Ranh giới cụm, màu P(c), gán tọa độ&lt;br&gt;&lt;b&gt;• Bảng Cụm &amp;amp; Thẩm tra:&lt;/b&gt; Xếp hạng P(c), Review Queue, clusterKey&lt;br&gt;&lt;b&gt;• Phân công &amp;amp; Đội:&lt;/b&gt; Giao đội, đổi 4 trạng thái, API /teams&lt;br&gt;&lt;b&gt;• Kiểm toán &amp;amp; Xuất dữ liệu:&lt;/b&gt; Nhật ký report_events, CSV, GeoJSON&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#F57C00;strokeWidth=1.8;fontSize=11.5;fontFamily=Helvetica;align=center;verticalAlign=top;spacingTop=6;" vertex="1" parent="1">
          <mxGeometry x="810" y="132" width="235" height="336" as="geometry" />
        </mxCell>
        
        <!-- Các đường nối -->
        <mxCell id="e_act_mob" value="Tương tác App" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeWidth=1.5;strokeColor=#FF9800;endArrow=classic;startArrow=classic;fontSize=9;fontColor=#D84315;" edge="1" parent="1" source="act_mob" target="app_flutter">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e_act_disp" value="Vận hành Web" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeWidth=1.5;strokeColor=#FF9800;endArrow=classic;startArrow=classic;fontSize=9;fontColor=#D84315;" edge="1" parent="1" source="act_disp" target="dash_web">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <!-- Kênh IP: App -> FastAPI -->
        <mxCell id="e_mob_gw_ip" value="KÊNH IP (REST)&lt;br&gt;POST /sync, /reports&lt;br&gt;GET /status" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeWidth=1.6;strokeColor=#1976D2;endArrow=classic;startArrow=classic;fontSize=8.5;fontColor=#0D47A1;labelBackgroundColor=#FFFFFF;" edge="1" parent="1" source="app_flutter" target="gw_api">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="355" y="92" />
            </Array>
          </mxGeometry>
        </mxCell>

        <!-- Kênh SMS: App -> SMS Gateway -> FastAPI -->
        <mxCell id="e_mob_sms" value="GSM SMS" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeWidth=1.5;strokeColor=#F57C00;dashed=1;endArrow=classic;fontSize=8;fontColor=#E65100;labelBackgroundColor=#FFFFFF;" edge="1" parent="1" source="app_flutter" target="sms_gw">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e_sms_gw" value="POST /api/sms/inbound" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeWidth=1.5;strokeColor=#2E7D32;endArrow=classic;fontSize=8;fontColor=#2E7D32;labelBackgroundColor=#FFFFFF;" edge="1" parent="1" source="sms_gw" target="gw_api">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <!-- Nội bộ Server -->
        <mxCell id="e_gw_db" value="Ghi nhận tức thời &amp;amp; Đọc ca (SQLite WAL)" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeWidth=1.6;strokeColor=#00695C;endArrow=classic;startArrow=classic;fontSize=8.5;fontColor=#00695C;labelBackgroundColor=#FFFFFF;" edge="1" parent="1" source="gw_api" target="db_storage">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e_db_core" value="Đọc active reports ↔ Cache RAM (ETag)" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeWidth=1.6;strokeColor=#4E342E;endArrow=classic;startArrow=classic;fontSize=8.5;fontColor=#4E342E;labelBackgroundColor=#FFFFFF;" edge="1" parent="1" source="db_storage" target="core_rescue">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <!-- FastAPI <-> Dashboard -->
        <mxCell id="e_gw_dash" value="HTTP REST API&lt;br&gt;Poll: /changes, /clusters&lt;br&gt;Điều phối: /team, /status" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeWidth=1.6;strokeColor=#E65100;endArrow=classic;startArrow=classic;fontSize=8.5;fontColor=#E65100;labelBackgroundColor=#FFFFFF;" edge="1" parent="1" source="gw_api" target="dash_web">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="750" y="113" />
            </Array>
          </mxGeometry>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''

def main():
    print("Generating streamlined functional_architecture diagram...")
    
    # 1. Tạo SVG
    svg_str = build_svg()
    svg_path = DIAGRAM_DIR / "functional_architecture.svg"
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_str)
    print(f"Saved SVG to {svg_path}")

    # 2. Tạo XML Draw.io
    drawio_str = build_drawio_xml()
    drawio_path = DIAGRAM_DIR / "functional_architecture.drawio"
    with open(drawio_path, "w", encoding="utf-8") as f:
        f.write(drawio_str)
    print(f"Saved Draw.io to {drawio_path}")

    # 3. Xuất vector PDF
    pdf_path = DIAGRAM_DIR / "functional_architecture.pdf"
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
    preview_path = DIAGRAM_DIR / "functional_architecture_preview.png"
    doc_render = fitz.open(pdf_path)
    page = doc_render[0]
    pix = page.get_pixmap(dpi=200)
    pix.save(preview_path)
    doc_render.close()
    print(f"Exported PNG Preview to {preview_path}")

if __name__ == "__main__":
    main()
