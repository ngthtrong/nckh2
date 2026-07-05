"""Chạy pipeline v2 và xuất một dashboard HTML tự chứa (self-contained).

Dashboard gồm:
  - Bản đồ Miền Trung VN (Leaflet + OSM) với các sự kiện tô màu theo cụm,
    kích thước điểm theo số người, trọng tâm cụm gắn nhãn hạng ưu tiên.
  - Bảng xếp hạng P(C_k) với đầy đủ thành phần (Ẽ, F̃, Ñ, V_agg, core, P).
  - Panel giải thích công thức tương ứng Mục 4.

Dữ liệu nhúng trực tiếp vào HTML nên chỉ cần mở file bằng trình duyệt.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

V2_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(V2_ROOT))

from data.generate import load_events  # noqa: E402
from pipeline.attributes import compute_confidence  # noqa: E402
from pipeline.config import DEFAULT_CONFIG as C  # noqa: E402
from pipeline.clustering import modularity, run_louvain  # noqa: E402
from pipeline.priority import score_clusters  # noqa: E402
from pipeline.weighting import build_weight_matrix, sparsify  # noqa: E402

DATASET = V2_ROOT / "data" / "dataset.json"
OUT_HTML = Path(__file__).resolve().parent / "dashboard.html"

# bảng màu phân biệt cụm (lặp lại nếu nhiều cụm)
PALETTE = [
    "#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4", "#46f0f0",
    "#f032e6", "#bcf60c", "#fabebe", "#008080", "#e6beff", "#9a6324",
    "#800000", "#aaffc3", "#808000", "#ffd8b1", "#000075", "#808080",
    "#ff6b6b", "#1abc9c", "#2c3e50", "#d35400", "#7f8c8d", "#c0392b",
    "#16a085", "#27ae60", "#2980b9", "#8e44ad",
]


def build_payload() -> dict:
    events = load_events(DATASET)
    compute_confidence(events, C.confidence)
    w = build_weight_matrix(events, C.weight, mode="gating")
    ws = sparsify(w, C.weight)
    labels = run_louvain(ws, C.cluster.resolution, C.cluster.random_state)
    mod = modularity(ws, labels)
    scores = score_clusters(events, labels, C.priority)

    # gán hạng ưu tiên (1 = cao nhất) cho từng cluster_id
    rank_of = {s.cluster_id: r + 1 for r, s in enumerate(scores)}

    nodes = []
    for ev, lab in zip(events, labels):
        nodes.append({
            "id": ev.event_id,
            "lat": ev.lat,
            "lng": ev.lng,
            "cluster": lab,
            "rank": rank_of.get(lab, 0),
            "flood": ev.flood,
            "urgency": ev.urgency,
            "n": ev.n_trapped,
            "vuln": ev.vulnerability,
            "conf": round(ev.confidence, 3),
            "province": ev.province,
            "note": ev.note,
            "fake": ev.is_fake,
        })

    clusters = []
    for r, s in enumerate(scores):
        clusters.append({
            "rank": r + 1,
            "cluster_id": s.cluster_id,
            "size": s.size,
            "e_agg": s.e_agg,
            "f_max": s.f_max,
            "n_norm": s.n_norm,
            "n_raw": s.n_total_raw,
            "v_agg": s.v_agg,
            "core": s.core,
            "priority": s.priority,
            "center_lat": s.center_lat,
            "center_lng": s.center_lng,
        })

    return {
        "meta": {
            "n_events": len(events),
            "n_clusters": len(scores),
            "modularity": round(mod, 4),
            "sigma_geo_m": C.weight.sigma_geo_m,
            "resolution": C.cluster.resolution,
            "v_scale": C.priority.v_scale,
        },
        "nodes": nodes,
        "clusters": clusters,
    }


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Demo v2 — Phân cụm & Ưu tiên Cứu hộ Bão lũ (Miền Trung VN)</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
      crossorigin="anonymous"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
        integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
        crossorigin="anonymous"></script>
<style>
  * { box-sizing: border-box; }
  body { margin:0; font-family: system-ui, "Segoe UI", Roboto, sans-serif; color:#1a1a1a; background:#f4f5f7; }
  header { background:#0b2545; color:#fff; padding:14px 20px; }
  header h1 { margin:0; font-size:18px; }
  header p { margin:4px 0 0; font-size:13px; color:#9fb3d1; }
  .stats { display:flex; gap:18px; padding:10px 20px; background:#13315c; color:#e6edf7; font-size:13px; flex-wrap:wrap; }
  .stats b { color:#ffd166; }
  .wrap { display:flex; gap:0; height:calc(100vh - 118px); }
  #map { flex:1.4; min-width:0; }
  .side { flex:1; overflow:auto; padding:14px 16px; background:#fff; border-left:1px solid #dfe3e8; }
  h2 { font-size:15px; margin:8px 0; }
  table { width:100%; border-collapse:collapse; font-size:12px; }
  th, td { padding:5px 6px; text-align:right; border-bottom:1px solid #eef0f2; }
  th:first-child, td:first-child { text-align:left; }
  thead th { position:sticky; top:0; background:#0b2545; color:#fff; font-weight:600; }
  tr.top1 td { background:#fff3cd; font-weight:600; }
  .swatch { display:inline-block; width:11px; height:11px; border-radius:2px; margin-right:5px; vertical-align:middle; }
  .legend { font-size:12px; line-height:1.6; }
  .formula { background:#f0f4f9; border-left:4px solid #4363d8; padding:8px 10px; margin:8px 0; font-size:12px; }
  .formula code { background:#e2e8f2; padding:1px 4px; border-radius:3px; }
  details { margin-top:10px; }
  summary { cursor:pointer; font-weight:600; font-size:13px; }
</style>
</head>
<body>
<header>
  <h1>Demo v2 — Phân cụm sự kiện & Ưu tiên cứu hộ bão lũ</h1>
  <p>Vùng Miền Trung Việt Nam (Huế · Quảng Trị · Quảng Nam · Đà Nẵng) — áp dụng công thức Mục 4 (PaperV2)</p>
</header>
<div class="stats" id="stats"></div>
<div class="wrap">
  <div id="map"></div>
  <div class="side">
    <h2>Bảng xếp hạng ưu tiên cụm  P(C_k)</h2>
    <table id="ptable">
      <thead><tr>
        <th>#</th><th>Cụm</th><th>N đv</th><th>Ẽ</th><th>F̃max</th><th>Ñ</th><th>V_agg</th><th>core</th><th>P</th>
      </tr></thead>
      <tbody></tbody>
    </table>

    <details open>
      <summary>Chú giải bản đồ</summary>
      <div class="legend" id="legend"></div>
    </details>

    <details>
      <summary>Công thức đang áp dụng (Mục 4)</summary>
      <div class="formula">
        <b>Trọng số cạnh (4.2)</b><br/>
        <code>w_ij = S_geo · (β·S_temp + γ·S_context)</code><br/>
        Địa lý là cổng chặn (gating) — cụm gắn kết không gian.
      </div>
      <div class="formula">
        <b>Phân cụm (4.3)</b><br/>
        Louvain tối ưu Modularity <code>Q</code>, tham số phân giải <code>λ</code>.
      </div>
      <div class="formula">
        <b>Ưu tiên cụm (4.4)</b><br/>
        <code>P(C_k) = V_agg · (ω₁·Ẽ + ω₂·F̃max + ω₃·Ñ)</code><br/>
        Chuẩn hóa thang đo; V_agg là thừa số nhân (khuếch đại công bằng).
      </div>
    </details>
  </div>
</div>

<script>
const DATA = __PAYLOAD__;
const PALETTE = __PALETTE__;

function colorFor(cluster) { return PALETTE[cluster % PALETTE.length]; }

// stats bar
const m = DATA.meta;
document.getElementById('stats').innerHTML =
  `Sự kiện: <b>${m.n_events}</b>` +
  ` &nbsp;|&nbsp; Số cụm: <b>${m.n_clusters}</b>` +
  ` &nbsp;|&nbsp; Modularity Q: <b>${m.modularity}</b>` +
  ` &nbsp;|&nbsp; σ_geo: <b>${m.sigma_geo_m} m</b>` +
  ` &nbsp;|&nbsp; λ: <b>${m.resolution}</b>` +
  ` &nbsp;|&nbsp; s: <b>${m.v_scale}</b>`;

// map
const map = L.map('map').setView([16.4, 107.8], 9);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 18, attribution: '© OpenStreetMap'
}).addTo(map);

const bounds = [];
DATA.nodes.forEach(nd => {
  const r = 4 + Math.sqrt(nd.n) * 1.6;
  const marker = L.circleMarker([nd.lat, nd.lng], {
    radius: r,
    color: nd.fake ? '#000' : colorFor(nd.cluster),
    weight: nd.fake ? 2 : 1,
    fillColor: colorFor(nd.cluster),
    fillOpacity: 0.7,
    dashArray: nd.fake ? '3' : null,
  }).addTo(map);
  marker.bindPopup(
    `<b>${nd.id}</b> ${nd.fake ? '⚠️ TIN GIẢ' : ''}<br/>` +
    `Cụm ${nd.cluster} (hạng ${nd.rank})<br/>` +
    `${nd.province}<br/>` +
    `Ngập F=${nd.flood} · Khẩn cấp E=${nd.urgency}<br/>` +
    `Số người N=${nd.n} · Tổn thương V=${nd.vuln}<br/>` +
    `Độ tin cậy C=${nd.conf}<br/><i>${nd.note}</i>`
  );
  bounds.push([nd.lat, nd.lng]);
});

// cluster centroids with rank label (top clusters emphasized)
DATA.clusters.forEach(c => {
  if (c.size < 2) return;
  const label = L.divIcon({
    className: '',
    html: `<div style="background:${colorFor(c.cluster_id)};color:#fff;border-radius:50%;`+
          `width:26px;height:26px;line-height:26px;text-align:center;font-weight:700;`+
          `border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.4);font-size:12px;">${c.rank}</div>`,
    iconSize: [26, 26], iconAnchor: [13, 13],
  });
  L.marker([c.center_lat, c.center_lng], {icon: label})
   .bindPopup(`<b>Cụm ${c.cluster_id}</b> — hạng ưu tiên ${c.rank}<br/>P(C_k)=${c.priority}`)
   .addTo(map);
});

if (bounds.length) map.fitBounds(bounds, {padding:[30,30]});

// priority table
const tb = document.querySelector('#ptable tbody');
DATA.clusters.forEach(c => {
  const tr = document.createElement('tr');
  if (c.rank === 1) tr.className = 'top1';
  tr.innerHTML =
    `<td>${c.rank}</td>` +
    `<td><span class="swatch" style="background:${colorFor(c.cluster_id)}"></span>${c.cluster_id}</td>` +
    `<td>${c.size}</td><td>${c.e_agg}</td><td>${c.f_max}</td>` +
    `<td>${c.n_norm}</td><td>${c.v_agg}</td><td>${c.core}</td><td><b>${c.priority}</b></td>`;
  tb.appendChild(tr);
});

// legend
const shown = [...new Set(DATA.clusters.map(c => c.cluster_id))].slice(0, 12);
document.getElementById('legend').innerHTML =
  shown.map(cid => `<span class="swatch" style="background:${colorFor(cid)}"></span>Cụm ${cid}`).join('<br/>') +
  '<br/><span class="swatch" style="background:#fff;border:2px dashed #000"></span>Viền đen nét đứt = tin giả (C_i thấp)' +
  '<br/>Kích thước điểm ∝ số người mắc kẹt · Số tròn = hạng ưu tiên cụm';
</script>
</body>
</html>
"""


def main():
    payload = build_payload()
    html = (HTML_TEMPLATE
            .replace("__PAYLOAD__", json.dumps(payload, ensure_ascii=False))
            .replace("__PALETTE__", json.dumps(PALETTE)))
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"Dashboard -> {OUT_HTML}")
    print(f"  {payload['meta']['n_events']} sự kiện, "
          f"{payload['meta']['n_clusters']} cụm, "
          f"Q={payload['meta']['modularity']}")
    print(f"  Mở bằng trình duyệt: file://{OUT_HTML}")


if __name__ == "__main__":
    main()
