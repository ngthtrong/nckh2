#!/usr/bin/env python3
"""
Tạo sơ đồ functional_architecture.drawio và xuất ra functional_architecture.pdf
Sơ đồ luồng chức năng và tương tác giữa các phân hệ trong hệ thống cứu hộ (Hình 3.1).
Chuẩn hóa bố cục 3 phân hệ (Mobile Client - Backend Core - Web GIS Dashboard),
phản ánh chính xác 100% hiện trạng mã nguồn hệ thống.
"""

import os
from pathlib import Path
import fitz  # PyMuPDF

DIAGRAM_DIR = Path("/mnt/d/NCKH2/report/assets/diagrams")

def build_svg() -> str:
    # Canvas width: 1140, height: 560
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1140 560" width="1140" height="560">
  <defs>
    <style>
      .title { font-family: 'Roboto', 'DejaVu Sans', 'Arial', sans-serif; font-size: 14px; font-weight: bold; fill: #0D47A1; }
      .sectitle { font-family: 'Roboto', 'DejaVu Sans', 'Arial', sans-serif; font-size: 13px; font-weight: bold; }
      .boxbold { font-family: 'Roboto', 'DejaVu Sans', 'Arial', sans-serif; font-size: 12px; font-weight: bold; }
      .boxsub { font-family: 'Roboto', 'DejaVu Sans', 'Arial', sans-serif; font-size: 10px; fill: #37474F; }
      .actorbold { font-family: 'Roboto', 'DejaVu Sans', 'Arial', sans-serif; font-size: 12px; font-weight: bold; fill: #BF360C; }
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
  <rect x="0" y="0" width="1140" height="560" fill="#FFFFFF" />

  <!-- ==================== CỘT 1: PHÂN HỆ DI ĐỘNG BIÊN (TRÁI) ==================== -->
  <!-- Khung nhóm Cột 1 -->
  <rect x="25" y="18" width="290" height="524" rx="8" fill="#F8FAFC" stroke="#90CAF9" stroke-width="1.5" />
  <rect x="25" y="18" width="290" height="34" rx="8" fill="#E3F2FD" stroke="#90CAF9" stroke-width="1.5" />
  <text x="170" y="40" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="12.5px" font-weight="bold" fill="#0D47A1">PHÂN HỆ DI ĐỘNG BIÊN (EDGE)</text>

  <!-- Actor Mobile -->
  <rect x="45" y="64" width="250" height="58" rx="6" fill="#FFF3E0" stroke="#FF9800" stroke-width="1.2" />
  <text x="170" y="87" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="11.5px" font-weight="bold" fill="#BF360C">Người dân / Nạn nhân</text>
  <text x="170" y="106" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="11px" font-weight="bold" fill="#E65100">&amp; Đội cứu hộ thực địa</text>

  <!-- Mũi tên Actor <-> Flutter Client -->
  <line x1="170" y1="122" x2="170" y2="146" stroke="#FF9800" stroke-width="1.5" marker-start="url(#arrow-actor)" marker-end="url(#arrow-actor)" />
  <text x="180" y="137" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9px" fill="#D84315">Tương tác App</text>

  <!-- Ứng dụng Di động Flutter -->
  <rect x="45" y="148" width="250" height="380" rx="8" fill="#FFFFFF" stroke="#1976D2" stroke-width="1.8" />
  <rect x="45" y="148" width="250" height="36" rx="8" fill="#E8F1FB" stroke="#1976D2" stroke-width="1.8" />
  <text x="170" y="171" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="12px" font-weight="bold" fill="#0D47A1">Ứng dụng Di động (Flutter Client)</text>

  <!-- Module 1: SOS & Báo cứu nạn -->
  <rect x="56" y="192" width="228" height="62" rx="5" fill="#F4F8FD" stroke="#BBDEFB" stroke-width="1" />
  <text x="68" y="210" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="10.5px" font-weight="bold" fill="#1565C0">SOS Khẩn cấp &amp; Báo cáo Sự cố</text>
  <text x="68" y="226" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#455A64">• SOS 1 chạm gửi định vị GPS tức thời</text>
  <text x="68" y="241" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" fill="#455A64">• Báo cáo đa phương thức (Ảnh, N, V)</text>

  <!-- Module 2: Edge AI -->
  <rect x="56" y="260" width="228" height="98" rx="5" fill="#FDF2F8" stroke="#F8BBD0" stroke-width="1" />
  <text x="68" y="278" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="10.5px" font-weight="bold" fill="#AD1457">Suy luận On-device Edge AI</text>
  <text x="68" y="295" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#455A64">• MobileNetV3 phân loại mức ngập (F)</text>
  <text x="68" y="310" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#880E4F">• ExecuTorch mặc định; ONNX so sánh</text>
  <text x="68" y="325" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#455A64">• Điểm khẩn cấp E_i (Logistic Regression)</text>
  <text x="68" y="340" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="8.8px" fill="#C2185B">* Backend tạm đọc urgency/mô tả cho P(c)</text>

  <!-- Module 3: Outbox & Sync -->
  <rect x="56" y="365" width="228" height="150" rx="5" fill="#F5F5F5" stroke="#CFD8DC" stroke-width="1" />
  <text x="68" y="383" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="10.5px" font-weight="bold" fill="#37474F">Hive Outbox &amp; Đồng bộ Ngoại tuyến</text>
  <text x="68" y="401" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#455A64">• Store-and-Forward chống mất mát tin</text>
  <text x="68" y="416" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#455A64">• Băm payload chuẩn tắc JCS RFC 8785</text>
  <text x="68" y="431" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#455A64">• Tra cứu tiến độ ca gửi qua API status:</text>
  <text x="76" y="446" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9px" font-weight="bold" fill="#1565C0">  GET /api/reports/status?ids=...</text>
  <text x="68" y="462" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9px" fill="#455A64">• Tiếp nhận nhiệm vụ cứu hộ tại chỗ</text>
  <text x="68" y="477" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="8.8px" fill="#D32F2F">* Cập nhật trạng thái cần quyền điều phối</text>


  <!-- ==================== CỘT 2: MÁY CHỦ XỬ LÝ TRUNG TÂM (GIỮA) ==================== -->
  <!-- Khung nét đứt Máy chủ Trung tâm -->
  <rect x="425" y="18" width="315" height="524" rx="8" fill="#FAF5FB" stroke="#7B1FA2" stroke-width="1.6" stroke-dasharray="6,4" />
  <rect x="425" y="18" width="315" height="34" rx="8" fill="#F3E5F5" stroke="#7B1FA2" stroke-width="1.6" />
  <text x="582" y="40" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="12px" font-weight="bold" fill="#6A1B9A">MÁY CHỦ XỬ LÝ TRUNG TÂM (BACKEND CORE)</text>

  <!-- Box 1: FastAPI Ingestion & Service -->
  <rect x="440" y="64" width="285" height="128" rx="7" fill="#FFFFFF" stroke="#7B1FA2" stroke-width="1.8" />
  <rect x="440" y="64" width="285" height="28" rx="7" fill="#EDE7F6" stroke="#7B1FA2" stroke-width="1.8" />
  <text x="582" y="83" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="11px" font-weight="bold" fill="#4A148C">API tiếp nhận &amp; dịch vụ backend (FastAPI)</text>
  <text x="452" y="107" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#37474F">• Kiểm tra X-Message-Contract-Version: 1</text>
  <text x="452" y="122" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#37474F">• Kiểm tra hash payload JCS RFC 8785 (sync batch)</text>
  <text x="452" y="137" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#37474F">• Chống trùng lặp Idempotency (messages_dedup)</text>
  <text x="452" y="152" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#37474F">• Xác thực phiên &amp; phân quyền admin/operator</text>
  <text x="452" y="167" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#37474F">• Nhận SMS Webhook POST /api/sms/inbound (Token)</text>
  <text x="452" y="182" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#37474F">• Cung cấp REST API cho Mobile &amp; Web Dashboard</text>

  <!-- Mũi tên Gateway <-> Storage (Ghi nhận tức thời) -->
  <line x1="582" y1="192" x2="582" y2="224" stroke="#00695C" stroke-width="1.8" marker-start="url(#arrow-teal)" marker-end="url(#arrow-teal)" />
  <rect x="492" y="200" width="180" height="16" rx="3" fill="#FFFFFF" stroke="#B2DFDB" stroke-width="0.8" />
  <text x="582" y="212" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="8.8px" font-weight="bold" fill="#00695C">Ghi nhận tức thời &amp; Đọc ca (SQLite WAL)</text>

  <!-- Box 2: Lưu trữ Bền vững -->
  <rect x="440" y="224" width="285" height="112" rx="7" fill="#FFFFFF" stroke="#00695C" stroke-width="1.8" />
  <rect x="440" y="224" width="285" height="28" rx="7" fill="#E0F2F1" stroke="#00695C" stroke-width="1.8" />
  <text x="582" y="243" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="11px" font-weight="bold" fill="#004D40">Lưu trữ Bền vững (SQLite &amp; Files)</text>
  <text x="452" y="267" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#37474F">• SQLite WAL: reports, messages_dedup, teams, meta</text>
  <text x="452" y="282" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#37474F">• Nhật ký kiểm toán phân công report_events</text>
  <text x="452" y="297" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#37474F">• Thư mục uploads/: Tệp ảnh hiện trường JPEG/PNG</text>
  <text x="452" y="312" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#37474F">• Đối soát toàn vẹn mã băm SHA-256</text>
  <text x="452" y="327" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="8.8px" fill="#00695C">• WAL: Ghi nhận độc lập, không bị khóa bởi tính toán</text>

  <!-- Mũi tên Storage <-> rescue_core -->
  <line x1="582" y1="336" x2="582" y2="368" stroke="#4E342E" stroke-width="1.8" marker-start="url(#arrow-purple)" marker-end="url(#arrow-purple)" />
  <rect x="487" y="344" width="190" height="16" rx="3" fill="#FFFFFF" stroke="#D7CCC8" stroke-width="0.8" />
  <text x="582" y="356" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="8.8px" font-weight="bold" fill="#4E342E">Đọc active reports ↔ Cache Snapshot RAM</text>

  <!-- Box 3: Lõi thuật toán rescue_core & ClusterService -->
  <rect x="440" y="368" width="285" height="164" rx="7" fill="#FFFFFF" stroke="#4E342E" stroke-width="1.8" />
  <rect x="440" y="368" width="285" height="28" rx="7" fill="#EFEBE9" stroke="#4E342E" stroke-width="1.8" />
  <text x="582" y="387" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="11px" font-weight="bold" fill="#3E2723">Lõi Thuật toán &amp; Dịch vụ Cụm (rescue_core)</text>
  <text x="452" y="411" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#37474F">• Ma trận đồ thị C_ij &amp; Phân cụm Louvain đa tỉ lệ</text>
  <text x="452" y="426" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#37474F">• Điểm ưu tiên cụm P(c) đa tiêu chí (E từ urgency/mô tả)</text>
  <text x="452" y="441" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#37474F">• clusterKey: duy trì lựa chọn cụm giữa các lần tải</text>
  <text x="452" y="456" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#37474F">• Hàng xem xét (Review Queue): thiếu vị trí hoặc thời gian</text>
  <text x="452" y="471" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#37474F">• Loại bỏ bản trùng lặp &amp; gộp bản gần trùng khi tính P(c)</text>
  <text x="452" y="486" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#37474F">• ClusterSnapshot trên RAM (ETag) — Không ghi CSDL</text>
  <text x="452" y="501" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="8.8px" fill="#5D4037">• Cập nhật gia tăng nền theo epoch/version dữ liệu</text>


  <!-- ==================== CỘT 3: BÀN ĐIỀU PHỐI WEB GIS (PHẢI) ==================== -->
  <!-- Khung nhóm Cột 3 -->
  <rect x="845" y="18" width="270" height="524" rx="8" fill="#FFFDF8" stroke="#FFE082" stroke-width="1.5" />
  <rect x="845" y="18" width="270" height="34" rx="8" fill="#FFF8E1" stroke="#FFE082" stroke-width="1.5" />
  <text x="980" y="40" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="12px" font-weight="bold" fill="#E65100">PHÂN HỆ ĐIỀU PHỐI &amp; QUẢN TRỊ WEB</text>

  <!-- Actor Dispatcher / Admin -->
  <rect x="860" y="64" width="240" height="58" rx="6" fill="#FFF3E0" stroke="#FF9800" stroke-width="1.2" />
  <text x="980" y="87" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="11.5px" font-weight="bold" fill="#BF360C">Điều phối viên cứu nạn</text>
  <text x="980" y="106" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="11px" font-weight="bold" fill="#E65100">&amp; Quản trị viên (Admin)</text>

  <!-- Mũi tên Actor <-> Dashboard -->
  <line x1="980" y1="122" x2="980" y2="146" stroke="#FF9800" stroke-width="1.5" marker-start="url(#arrow-actor)" marker-end="url(#arrow-actor)" />
  <text x="990" y="137" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9px" fill="#D84315">Vận hành Web</text>

  <!-- Bàn điều phối Web GIS Leaflet -->
  <rect x="860" y="148" width="240" height="380" rx="8" fill="#FFFFFF" stroke="#F57C00" stroke-width="1.8" />
  <rect x="860" y="148" width="240" height="36" rx="8" fill="#FFF3E0" stroke="#F57C00" stroke-width="1.8" />
  <text x="980" y="171" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="12px" font-weight="bold" fill="#E65100">Bàn điều phối Web (Leaflet GIS)</text>

  <!-- Module 1: Bản đồ giám sát -->
  <rect x="872" y="192" width="216" height="68" rx="5" fill="#FFFDE7" stroke="#FFF59D" stroke-width="1" />
  <text x="884" y="210" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="10.5px" font-weight="bold" fill="#F57F17">Bản đồ Giám sát Sự cố Leaflet</text>
  <text x="884" y="226" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#455A64">• Leaflet GIS đóng gói cục bộ không CDN</text>
  <text x="884" y="241" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#455A64">• Ranh giới cụm &amp; màu ưu tiên theo P(c)</text>
  <text x="884" y="254" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9px" fill="#455A64">• Chấm gán tọa độ ca thiếu vị trí/thời gian</text>

  <!-- Module 2: Quản lý cụm & Ca -->
  <rect x="872" y="268" width="216" height="92" rx="5" fill="#FFF8E1" stroke="#FFE082" stroke-width="1" />
  <text x="884" y="286" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="10.5px" font-weight="bold" fill="#E65100">Bảng Cụm &amp; Thẩm tra Yêu cầu</text>
  <text x="884" y="303" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#455A64">• Danh sách ưu tiên giảm dần theo P(c)</text>
  <text x="884" y="318" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#455A64">• clusterKey: giữ ổn định hiển thị khi poll</text>
  <text x="884" y="333" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#455A64">• Hàng xem xét (Review Queue) thẩm tra SOS</text>
  <text x="884" y="348" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#455A64">• Xác minh thông tin, tránh suy diễn GPS sai</text>

  <!-- Module 3: Phân công & Quản trị -->
  <rect x="872" y="368" width="216" height="147" rx="5" fill="#FAFAFA" stroke="#CFD8DC" stroke-width="1" />
  <text x="884" y="386" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="10.5px" font-weight="bold" fill="#37474F">Phân công Đội &amp; Quản trị Hệ thống</text>
  <text x="884" y="403" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#455A64">• Giao đội: PUT /api/reports/{id}/team</text>
  <text x="884" y="418" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#455A64">• Đổi 4 trạng thái: PATCH .../status</text>
  <text x="884" y="433" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#455A64">• Quản lý đội: GET/POST/PATCH /teams</text>
  <text x="884" y="448" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#455A64">• Nhật ký kiểm toán ca: report_events</text>
  <text x="884" y="463" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.2px" fill="#455A64">• Quản lý tài khoản điều phối viên</text>
  <text x="884" y="478" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9px" fill="#37474F">• Sao lưu SQLite DB &amp; uploads/ định kỳ</text>


  <!-- ==================== CÁC TUYẾN ĐƯỜNG KẾT NỐI LIÊN PHÂN HỆ ==================== -->
  
  <!-- 1. KÊNH IP TRỰC TIẾP (REST API) MOBILE <-> FASTAPI -->
  <!-- Hộp chú thích Kênh IP nằm ở giữa x: 318..422 -->
  <rect x="318" y="72" width="104" height="66" rx="4" fill="#FFFFFF" stroke="#90CAF9" stroke-width="1" />
  <text x="370" y="86" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" font-weight="bold" fill="#0D47A1">KÊNH IP (REST)</text>
  <text x="370" y="99" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="8.2px" fill="#1565C0">• POST /sync/messages</text>
  <text x="370" y="111" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="8.2px" fill="#1565C0">• Multipart /api/reports</text>
  <text x="370" y="123" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="8.2px" font-weight="bold" fill="#1565C0">• GET /reports/status</text>
  <text x="370" y="134" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="7.8px" fill="#546E7A">(Hỏi trạng thái điều phối)</text>

  <!-- Mũi tên từ Flutter Client sang Hộp Kênh IP -->
  <line x1="295" y1="105" x2="318" y2="105" stroke="#1976D2" stroke-width="1.8" marker-start="url(#arrow-blue)" marker-end="url(#arrow-blue)" />
  <!-- Mũi tên từ Hộp Kênh IP sang FastAPI -->
  <line x1="422" y1="105" x2="440" y2="105" stroke="#1976D2" stroke-width="1.8" marker-start="url(#arrow-blue)" marker-end="url(#arrow-blue)" />


  <!-- 2. KÊNH GSM & SMS GATEWAY TRUNG GIAN -->
  <!-- Hộp SMS Gateway trung gian -->
  <rect x="316" y="152" width="108" height="52" rx="5" fill="#FFFDE7" stroke="#FBC02D" stroke-width="1.2" />
  <text x="370" y="167" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" font-weight="bold" fill="#F57F17">SMS GATEWAY</text>
  <text x="370" y="180" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="8px" fill="#6D4C41">Thiết bị / Tổng đài GSM</text>
  <text x="370" y="191" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="7.8px" fill="#6D4C41">SIM nhận SMS tự do</text>
  <text x="370" y="201" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="7.5px" fill="#D84315">&amp; tin SOS|id:... từ App</text>

  <!-- Mũi tên từ Flutter Client sang SMS Gateway (qua sóng GSM) -->
  <line x1="295" y1="178" x2="316" y2="178" stroke="#F57C00" stroke-width="1.5" stroke-dasharray="3,2" marker-end="url(#arrow-orange)" />
  <text x="305" y="172" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="7.5px" font-weight="bold" fill="#E65100">GSM</text>

  <!-- Mũi tên từ SMS Gateway sang FastAPI Webhook -->
  <line x1="424" y1="178" x2="440" y2="178" stroke="#2E7D32" stroke-width="1.5" marker-end="url(#arrow-green)" />
  <text x="432" y="171" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="7.2px" font-weight="bold" fill="#2E7D32">HTTP</text>

  <!-- Hộp chú thích Webhook SMS Token -->
  <rect x="318" y="210" width="104" height="22" rx="3" fill="#E8F5E9" stroke="#81C784" stroke-width="0.8" />
  <text x="370" y="221" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="7.5px" font-weight="bold" fill="#2E7D32">POST /api/sms/inbound</text>
  <text x="370" y="229" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="7px" fill="#388E3C">(kèm X-Gateway-Token)</text>


  <!-- 3. KẾT NỐI FASTAPI GATEWAY <-> WEB DASHBOARD -->
  <!-- Hộp chú thích API Dashboard <-> Gateway (x: 744..842) -->
  <rect x="744" y="68" width="98" height="112" rx="4" fill="#FFFFFF" stroke="#FFCC80" stroke-width="1" />
  <text x="793" y="82" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="9.5px" font-weight="bold" fill="#E65100">HTTP REST API</text>
  <text x="793" y="96" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="8px" fill="#BF360C">• Poll 5s: /changes</text>
  <text x="793" y="108" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="8px" fill="#BF360C">• ETag: /clusters</text>
  <text x="793" y="122" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="8px" font-weight="bold" fill="#D84315">• PUT /reports/{id}/team</text>
  <text x="793" y="134" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="8px" font-weight="bold" fill="#D84315">• PATCH .../status</text>
  <text x="793" y="147" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="7.8px" fill="#BF360C">• GET/POST /teams</text>
  <text x="793" y="159" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="7.8px" fill="#BF360C">• PATCH /teams/{id}</text>
  <text x="793" y="172" text-anchor="middle" font-family="Roboto, DejaVu Sans, Arial, sans-serif" font-size="7.5px" fill="#455A64">(Session Cookie Auth)</text>

  <!-- Mũi tên từ FastAPI sang Hộp REST API Dashboard -->
  <line x1="725" y1="124" x2="744" y2="124" stroke="#E65100" stroke-width="1.8" marker-start="url(#arrow-orange)" marker-end="url(#arrow-orange)" />
  <!-- Mũi tên từ Hộp REST API sang Web Dashboard -->
  <line x1="842" y1="124" x2="860" y2="124" stroke="#E65100" stroke-width="1.8" marker-start="url(#arrow-orange)" marker-end="url(#arrow-orange)" />

</svg>'''
    return svg

def build_drawio_xml() -> str:
    # Sơ đồ Draw.io tương ứng hoàn chỉnh với bố cục chuẩn hóa
    return '''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" agent="Antigravity" version="24.0.0">
  <diagram id="diag-func-arch" name="Kien-truc-chuc-nang-he-thong">
    <mxGraphModel dx="1200" dy="700" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1140" pageHeight="560" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        
        <!-- Cột 1: Di động biên -->
        <mxCell id="c1_frame" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F8FAFC;strokeColor=#90CAF9;strokeWidth=1.5;arcSize=4;" vertex="1" parent="1">
          <mxGeometry x="25" y="18" width="290" height="524" as="geometry" />
        </mxCell>
        <mxCell id="c1_title" value="&lt;b&gt;PHÂN HỆ DI ĐỘNG BIÊN (EDGE)&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E3F2FD;strokeColor=#90CAF9;strokeWidth=1.5;fontColor=#0D47A1;fontSize=13;fontFamily=Helvetica;" vertex="1" parent="1">
          <mxGeometry x="25" y="18" width="290" height="34" as="geometry" />
        </mxCell>
        <mxCell id="act_mob" value="&lt;b&gt;Người dân / Nạn nhân&lt;/b&gt;&lt;br&gt;&lt;b&gt;&amp;amp; Đội cứu hộ thực địa&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF3E0;strokeColor=#FF9800;strokeWidth=1.2;fontSize=12;fontColor=#BF360C;fontFamily=Helvetica;" vertex="1" parent="1">
          <mxGeometry x="45" y="64" width="250" height="58" as="geometry" />
        </mxCell>
        <mxCell id="app_flutter" value="&lt;b&gt;Ứng dụng Di động (Flutter Client)&lt;/b&gt;&lt;hr&gt;&lt;div align=&quot;left&quot; style=&quot;font-size:10px;color:#37474F;&quot;&gt;&lt;b&gt;• SOS &amp;amp; Báo cáo Sự cố:&lt;/b&gt; 1 chạm GPS, Ảnh, N, V&lt;br&gt;&lt;b&gt;• On-device Edge AI:&lt;/b&gt; MobileNetV3 (F); ExecuTorch mặc định, ONNX so sánh; Điểm khẩn cấp E_i (Logistic Regression từ dấu hiệu nặng; backend tạm đọc urgency/mô tả)&lt;br&gt;&lt;b&gt;• Hive Outbox:&lt;/b&gt; Ngoại tuyến Store-and-Forward, JCS RFC 8785&lt;br&gt;&lt;b&gt;• Tiến độ ca cứu hộ:&lt;/b&gt; GET /api/reports/status?ids=... (Đổi trạng thái nghiệp vụ yêu cầu quyền điều phối)&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1976D2;strokeWidth=1.8;fontSize=11.5;fontFamily=Helvetica;align=center;verticalAlign=top;spacingTop=6;" vertex="1" parent="1">
          <mxGeometry x="45" y="148" width="250" height="380" as="geometry" />
        </mxCell>

        <!-- Thành phần trung gian: SMS Gateway -->
        <mxCell id="sms_gw" value="&lt;b&gt;SMS GATEWAY&lt;/b&gt;&lt;br&gt;&lt;font style=&quot;font-size:9px;color:#5D4037;&quot;&gt;Thiết bị / Tổng đài GSM&lt;br&gt;Nhận SMS SOS | Chuyển tiếp POST /api/sms/inbound (Token)&lt;/font&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFDE7;strokeColor=#FBC02D;strokeWidth=1.2;fontSize=10;fontFamily=Helvetica;align=center;" vertex="1" parent="1">
          <mxGeometry x="316" y="152" width="108" height="52" as="geometry" />
        </mxCell>
        
        <!-- Cột 2: Máy chủ trung tâm -->
        <mxCell id="c2_frame" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FAF5FB;strokeColor=#7B1FA2;strokeWidth=1.6;dashed=1;dashPattern=6 4;arcSize=4;" vertex="1" parent="1">
          <mxGeometry x="425" y="18" width="315" height="524" as="geometry" />
        </mxCell>
        <mxCell id="c2_title" value="&lt;b&gt;MÁY CHỦ XỬ LÝ TRUNG TÂM (BACKEND CORE)&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F3E5F5;strokeColor=#7B1FA2;strokeWidth=1.6;fontColor=#6A1B9A;fontSize=12.5;fontFamily=Helvetica;" vertex="1" parent="1">
          <mxGeometry x="425" y="18" width="315" height="34" as="geometry" />
        </mxCell>
        <mxCell id="gw_api" value="&lt;b&gt;API tiếp nhận &amp;amp; dịch vụ backend (FastAPI)&lt;/b&gt;&lt;hr&gt;&lt;div align=&quot;left&quot; style=&quot;font-size:10px;color:#37474F;&quot;&gt;• Kiểm tra X-Message-Contract-Version: 1&lt;br&gt;• Kiểm tra hash payload JCS RFC 8785 (sync batch)&lt;br&gt;• Chống trùng lặp Idempotency (messages_dedup)&lt;br&gt;• Xác thực phiên &amp;amp; phân quyền admin/operator&lt;br&gt;• Nhận Webhook POST /api/sms/inbound (Token)&lt;br&gt;• REST API cho Mobile &amp;amp; Web Dashboard&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#7B1FA2;strokeWidth=1.8;fontSize=11.5;fontFamily=Helvetica;align=center;verticalAlign=top;spacingTop=6;" vertex="1" parent="1">
          <mxGeometry x="440" y="64" width="285" height="128" as="geometry" />
        </mxCell>
        <mxCell id="db_storage" value="&lt;b&gt;Lưu trữ Bền vững (SQLite &amp;amp; Files)&lt;/b&gt;&lt;hr&gt;&lt;div align=&quot;left&quot; style=&quot;font-size:10px;color:#37474F;&quot;&gt;• SQLite WAL: reports, messages_dedup, teams, meta&lt;br&gt;• Nhật ký kiểm toán phân công report_events&lt;br&gt;• Thư mục uploads/: Tệp ảnh hiện trường JPEG/PNG (SHA-256)&lt;br&gt;• Ghi nhận tức thời, không bị khóa bởi phân cụm&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#00695C;strokeWidth=1.8;fontSize=11.5;fontFamily=Helvetica;align=center;verticalAlign=top;spacingTop=6;" vertex="1" parent="1">
          <mxGeometry x="440" y="224" width="285" height="112" as="geometry" />
        </mxCell>
        <mxCell id="core_rescue" value="&lt;b&gt;Lõi Thuật toán &amp;amp; Dịch vụ Cụm (rescue_core)&lt;/b&gt;&lt;hr&gt;&lt;div align=&quot;left&quot; style=&quot;font-size:10px;color:#37474F;&quot;&gt;• Ma trận đồ thị C_ij &amp;amp; Phân cụm Louvain đa tỉ lệ&lt;br&gt;• Điểm ưu tiên cụm P(c) đa tiêu chí (E từ urgency/mô tả)&lt;br&gt;• clusterKey: duy trì lựa chọn cụm giữa các lần tải&lt;br&gt;• Hàng xem xét (Review Queue): thiếu vị trí hoặc thời gian&lt;br&gt;• Snapshot Cache trên RAM (ETag) — Không ghi SQLite&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#4E342E;strokeWidth=1.8;fontSize=11.5;fontFamily=Helvetica;align=center;verticalAlign=top;spacingTop=6;" vertex="1" parent="1">
          <mxGeometry x="440" y="368" width="285" height="164" as="geometry" />
        </mxCell>

        <!-- Cột 3: Web Dashboard -->
        <mxCell id="c3_frame" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFDF8;strokeColor=#FFE082;strokeWidth=1.5;arcSize=4;" vertex="1" parent="1">
          <mxGeometry x="845" y="18" width="270" height="524" as="geometry" />
        </mxCell>
        <mxCell id="c3_title" value="&lt;b&gt;PHÂN HỆ ĐIỀU PHỐI &amp;amp; QUẢN TRỊ WEB&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF8E1;strokeColor=#FFE082;strokeWidth=1.5;fontColor=#E65100;fontSize=12.5;fontFamily=Helvetica;" vertex="1" parent="1">
          <mxGeometry x="845" y="18" width="270" height="34" as="geometry" />
        </mxCell>
        <mxCell id="act_disp" value="&lt;b&gt;Điều phối viên cứu nạn&lt;/b&gt;&lt;br&gt;&lt;b&gt;&amp;amp; Quản trị viên (Admin)&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF3E0;strokeColor=#FF9800;strokeWidth=1.2;fontSize=12;fontColor=#BF360C;fontFamily=Helvetica;" vertex="1" parent="1">
          <mxGeometry x="860" y="64" width="240" height="58" as="geometry" />
        </mxCell>
        <mxCell id="dash_web" value="&lt;b&gt;Bàn điều phối Web (Leaflet GIS)&lt;/b&gt;&lt;hr&gt;&lt;div align=&quot;left&quot; style=&quot;font-size:10px;color:#37474F;&quot;&gt;&lt;b&gt;• Bản đồ số Leaflet GIS:&lt;/b&gt; Ranh giới cụm &amp;amp; màu ưu tiên; Chấm gán tọa độ ca thiếu vị trí/thời gian&lt;br&gt;&lt;b&gt;• Quản lý Ca &amp;amp; Cụm:&lt;/b&gt; Thứ bậc P(c); Khóa clusterKey giữ ổn định khi poll; Review Queue thẩm tra SOS&lt;br&gt;&lt;b&gt;• Phân công &amp;amp; Đội:&lt;/b&gt; PUT /api/reports/{id}/team; PATCH .../status; Quản lý đội GET/POST/PATCH /teams&lt;br&gt;&lt;b&gt;• Quản trị:&lt;/b&gt; Nhật ký report_events; tài khoản &amp;amp; sao lưu&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#F57C00;strokeWidth=1.8;fontSize=11.5;fontFamily=Helvetica;align=center;verticalAlign=top;spacingTop=6;" vertex="1" parent="1">
          <mxGeometry x="860" y="148" width="240" height="380" as="geometry" />
        </mxCell>
        
        <!-- Các đường nối -->
        <mxCell id="e_act_mob" value="Tương tác App" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeWidth=1.5;strokeColor=#FF9800;endArrow=classic;startArrow=classic;fontSize=9.5;fontColor=#D84315;" edge="1" parent="1" source="act_mob" target="app_flutter">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e_act_disp" value="Vận hành Web" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeWidth=1.5;strokeColor=#FF9800;endArrow=classic;startArrow=classic;fontSize=9.5;fontColor=#D84315;" edge="1" parent="1" source="act_disp" target="dash_web">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <!-- Kênh IP: App -> FastAPI -->
        <mxCell id="e_mob_gw_ip" value="KÊNH IP (REST)&lt;br&gt;POST /sync/messages (Batch)&lt;br&gt;Multipart /api/reports&lt;br&gt;GET /api/reports/status" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeWidth=1.8;strokeColor=#1976D2;endArrow=classic;startArrow=classic;fontSize=9;fontColor=#0D47A1;labelBackgroundColor=#FFFFFF;" edge="1" parent="1" source="app_flutter" target="gw_api">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="370" y="105" />
            </Array>
          </mxGeometry>
        </mxCell>

        <!-- Kênh SMS: App -> SMS Gateway -> FastAPI -->
        <mxCell id="e_mob_sms" value="GSM SMS" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeWidth=1.5;strokeColor=#F57C00;dashed=1;endArrow=classic;fontSize=8.5;fontColor=#E65100;labelBackgroundColor=#FFFFFF;" edge="1" parent="1" source="app_flutter" target="sms_gw">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e_sms_gw" value="POST /api/sms/inbound&lt;br&gt;(X-Gateway-Token)" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeWidth=1.5;strokeColor=#2E7D32;endArrow=classic;fontSize=8.5;fontColor=#2E7D32;labelBackgroundColor=#FFFFFF;" edge="1" parent="1" source="sms_gw" target="gw_api">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <!-- Nội bộ Server -->
        <mxCell id="e_gw_db" value="Ghi nhận tức thời &amp;amp; Đọc ca (SQLite WAL)" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeWidth=1.8;strokeColor=#00695C;endArrow=classic;startArrow=classic;fontSize=9;fontColor=#00695C;labelBackgroundColor=#FFFFFF;" edge="1" parent="1" source="gw_api" target="db_storage">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e_db_core" value="Đọc active reports ↔ Cache Snapshot RAM" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeWidth=1.8;strokeColor=#4E342E;endArrow=classic;startArrow=classic;fontSize=9;fontColor=#4E342E;labelBackgroundColor=#FFFFFF;" edge="1" parent="1" source="db_storage" target="core_rescue">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <!-- FastAPI <-> Dashboard -->
        <mxCell id="e_gw_dash" value="HTTP REST API&lt;br&gt;Poll 5s: /changes&lt;br&gt;ETag: /clusters&lt;br&gt;PUT /reports/{id}/team&lt;br&gt;PATCH .../status&lt;br&gt;GET/POST/PATCH /teams" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeWidth=1.8;strokeColor=#E65100;endArrow=classic;startArrow=classic;fontSize=8.5;fontColor=#E65100;labelBackgroundColor=#FFFFFF;" edge="1" parent="1" source="gw_api" target="dash_web">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="790" y="124" />
            </Array>
          </mxGeometry>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''

def main():
    print("Generating functional_architecture diagram...")
    
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
