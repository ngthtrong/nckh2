from __future__ import annotations


def get_dashboard_html() -> str:
    return """<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Demo Louvain Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="anonymous" />
  <style>
    :root {
      color-scheme: dark;
      --bg: #07111f;
      --panel: rgba(13, 20, 33, 0.88);
      --panel-strong: #0d1726;
      --text: #ecf4ff;
      --muted: #9cafcc;
      --line: rgba(151, 183, 233, 0.15);
      --accent: #66e3ff;
      --accent-2: #8bffbe;
      --danger: #ff738f;
      --warn: #ffd166;
      --info: #7aa2ff;
      --shadow: 0 24px 80px rgba(0, 0, 0, 0.34);
      --radius: 22px;
    }

    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      margin: 0;
      font-family: "Inter", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(102, 227, 255, 0.16), transparent 28%),
        radial-gradient(circle at top right, rgba(139, 255, 190, 0.12), transparent 24%),
        linear-gradient(180deg, #06101b 0%, #02050a 100%);
    }

    .app {
      display: grid;
      grid-template-columns: 430px 1fr;
      height: 100vh;
      min-height: 100vh;
    }

    .sidebar {
      padding: 18px;
      overflow: auto;
      border-right: 1px solid var(--line);
      background: linear-gradient(180deg, rgba(10, 17, 29, 0.96), rgba(6, 10, 18, 0.92));
    }

    .brand {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 18px;
      border-radius: 20px;
      background: linear-gradient(135deg, rgba(102, 227, 255, 0.12), rgba(139, 255, 190, 0.08));
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
      margin-bottom: 14px;
    }

    .brand h1 {
      margin: 0;
      font-size: 21px;
      line-height: 1.15;
      letter-spacing: -0.03em;
    }

    .brand p {
      margin: 4px 0 0;
      font-size: 12px;
      color: var(--muted);
      line-height: 1.55;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 10px;
      border-radius: 999px;
      background: rgba(102, 227, 255, 0.12);
      color: var(--accent);
      font-size: 12px;
      font-weight: 600;
      white-space: nowrap;
    }

    .panel {
      margin-top: 12px;
      padding: 16px;
      border-radius: var(--radius);
      background: var(--panel);
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
      backdrop-filter: blur(16px);
    }

    .panel h2 {
      margin: 0 0 12px;
      font-size: 16px;
      letter-spacing: -0.02em;
    }

    .grid-2 {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }

    .metric {
      padding: 14px;
      border-radius: 16px;
      background: rgba(255,255,255,0.05);
      border: 1px solid var(--line);
    }

    .metric .label {
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }

    .metric .value {
      font-size: 28px;
      font-weight: 800;
      letter-spacing: -0.04em;
    }

    .metric .foot {
      margin-top: 6px;
      color: var(--muted);
      font-size: 12px;
    }

    .controls {
      display: grid;
      gap: 10px;
    }

    .row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }

    .input, select, button {
      width: 100%;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.05);
      color: var(--text);
      padding: 11px 12px;
      font: inherit;
      outline: none;
    }

    button {
      cursor: pointer;
      background: linear-gradient(135deg, var(--accent), var(--accent-2));
      color: #08111f;
      font-weight: 800;
      border: 0;
      box-shadow: 0 10px 26px rgba(102, 227, 255, 0.16);
    }

    button.secondary {
      color: var(--text);
      background: rgba(255,255,255,0.06);
      border: 1px solid var(--line);
      box-shadow: none;
    }

    .legend {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }

    .legend-item {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 7px 10px;
      border-radius: 999px;
      background: rgba(255,255,255,0.05);
      color: var(--muted);
      font-size: 12px;
      border: 1px solid var(--line);
    }

    .dot {
      width: 10px;
      height: 10px;
      border-radius: 999px;
      display: inline-block;
    }

    .list {
      display: grid;
      gap: 10px;
      max-height: 260px;
      overflow: auto;
      padding-right: 2px;
    }

    .item {
      padding: 12px;
      border-radius: 16px;
      background: rgba(255,255,255,0.05);
      border: 1px solid var(--line);
      cursor: pointer;
      transition: transform 120ms ease, border-color 120ms ease;
    }

    .item:hover { transform: translateY(-1px); border-color: rgba(102, 227, 255, 0.38); }

    .item-head {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: center;
      margin-bottom: 6px;
    }

    .title {
      font-weight: 700;
      line-height: 1.3;
    }

    .subtle {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 6px 10px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }

    .pill.red { background: rgba(255, 115, 143, 0.14); color: var(--danger); }
    .pill.yellow { background: rgba(255, 209, 102, 0.14); color: var(--warn); }
    .pill.green { background: rgba(139, 255, 190, 0.14); color: var(--accent-2); }
    .pill.blue { background: rgba(122, 162, 255, 0.14); color: var(--info); }

    .map-wrap {
      position: relative;
      overflow: hidden;
    }

    #map {
      width: 100%;
      height: 100vh;
    }

    .map-overlay {
      position: absolute;
      top: 16px;
      left: 16px;
      z-index: 500;
      width: min(460px, calc(100% - 32px));
      pointer-events: none;
    }

    .map-card {
      pointer-events: auto;
      padding: 14px 16px;
      border-radius: 18px;
      background: rgba(8, 14, 24, 0.78);
      border: 1px solid rgba(255,255,255,0.12);
      box-shadow: var(--shadow);
      backdrop-filter: blur(18px);
    }

    .map-card h2 {
      margin: 0 0 6px;
      font-size: 15px;
    }

    .map-card p {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }

    .map-stats {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 10px;
    }

    .map-stat {
      padding: 7px 10px;
      border-radius: 999px;
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.08);
      font-size: 12px;
      color: var(--text);
    }

    .leaflet-container { background: #08111f; }
    .leaflet-popup-content-wrapper,
    .leaflet-popup-tip {
      background: #0b1424;
      color: #edf4ff;
      box-shadow: var(--shadow);
    }

    .leaflet-popup-content {
      margin: 12px 14px;
      font: inherit;
      line-height: 1.45;
    }

    .popup-title {
      font-weight: 800;
      margin-bottom: 4px;
    }

    .popup-meta {
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 6px;
    }

    .popup-text {
      font-size: 13px;
    }

    @media (max-width: 1100px) {
      .app { grid-template-columns: 1fr; }
      .sidebar { height: auto; max-height: 48vh; }
      #map { height: 52vh; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="brand">
        <div>
          <h1>Dashboard Louvain</h1>
          <p>Trực quan hóa sự kiện cứu hộ và cộng đồng trên bản đồ thật.</p>
        </div>
        <div class="badge">Leaflet + OSM</div>
      </div>

      <div class="panel">
        <h2>Tổng quan</h2>
        <div class="grid-2">
          <div class="metric"><div class="label">Reports</div><div class="value" id="metricReports">-</div><div class="foot">Bản ghi đầu vào</div></div>
          <div class="metric"><div class="label">Communities</div><div class="value" id="metricCommunities">-</div><div class="foot">Cụm Louvain</div></div>
          <div class="metric"><div class="label">Edges</div><div class="value" id="metricEdges">-</div><div class="foot">Cạnh đồ thị</div></div>
          <div class="metric"><div class="label">Modularity</div><div class="value" id="metricModularity">-</div><div class="foot">Chất lượng cụm</div></div>
        </div>
        <div class="legend">
          <div class="legend-item"><span class="dot" style="background:#ff738f"></span>Đỏ: khẩn cấp</div>
          <div class="legend-item"><span class="dot" style="background:#ffd166"></span>Vàng: cần hỗ trợ</div>
          <div class="legend-item"><span class="dot" style="background:#8bffbe"></span>Xanh: theo dõi</div>
          <div class="legend-item"><span class="dot" style="background:#66e3ff"></span>Tâm cụm</div>
        </div>
      </div>

      <div class="panel">
        <h2>Bộ lọc & Tương tác</h2>
        <div class="controls">
          <input class="input" id="searchInput" placeholder="Lọc theo tên / tỉnh / nhãn" />
          <div class="row">
            <select id="priorityFilter">
              <option value="all">Tất cả mức</option>
              <option value="red">Đỏ</option>
              <option value="yellow">Vàng</option>
              <option value="green">Xanh</option>
            </select>
            <select id="communitySelect"></select>
          </div>
          <div class="row">
            <button id="btnRefresh">Làm mới</button>
            <button class="secondary" id="btnFitAll">Hiển thị toàn bộ</button>
          </div>
          <div class="row">
            <button class="secondary" id="btnToggleEdges">Ẩn/hiện cạnh</button>
            <button class="secondary" id="btnToggleCommunities">Ẩn/hiện cụm</button>
          </div>
        </div>
      </div>

      <div class="panel">
        <h2>Cộng đồng</h2>
        <div class="list" id="communityList"></div>
      </div>

      <div class="panel">
        <h2>Sự kiện gần nhất</h2>
        <div class="list" id="reportList"></div>
      </div>
    </aside>

    <main class="map-wrap">
      <div class="map-overlay">
        <div class="map-card">
          <h2>Bản đồ cứu hộ thời gian thực</h2>
          <p>
            Các điểm là báo cáo cứu hộ, vòng tròn lớn là tâm cụm Louvain. Chọn một cụm ở panel trái để zoom và
            thấy các sự kiện thành viên cùng đường nối từ tâm cụm.
          </p>
          <div class="map-stats">
            <div class="map-stat" id="mapStatReports">Reports: -</div>
            <div class="map-stat" id="mapStatCommunities">Communities: -</div>
            <div class="map-stat" id="mapStatSelected">Selected: -</div>
          </div>
        </div>
      </div>
      <div id="map"></div>
    </main>
  </div>

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin="anonymous"></script>
  <script>
    const state = {
      reports: [],
      communities: [],
      graph: { nodes: [], edges: [] },
      summary: { nodes: 0, edges: 0, community_count: 0, modularity: 0 },
      activeCommunityId: null,
      showEdges: true,
      showCommunities: true,
      map: null,
      layers: {
        reports: null,
        communities: null,
        edges: null,
        selectedCommunity: null,
      },
    };

    const els = {
      metricReports: document.getElementById('metricReports'),
      metricCommunities: document.getElementById('metricCommunities'),
      metricEdges: document.getElementById('metricEdges'),
      metricModularity: document.getElementById('metricModularity'),
      mapStatReports: document.getElementById('mapStatReports'),
      mapStatCommunities: document.getElementById('mapStatCommunities'),
      mapStatSelected: document.getElementById('mapStatSelected'),
      communitySelect: document.getElementById('communitySelect'),
      communityList: document.getElementById('communityList'),
      reportList: document.getElementById('reportList'),
      searchInput: document.getElementById('searchInput'),
      priorityFilter: document.getElementById('priorityFilter'),
    };

    const priorityMeta = {
      red: { label: 'Đỏ', fill: '#ff738f', border: '#ff8ea3' },
      yellow: { label: 'Vàng', fill: '#ffd166', border: '#ffe08f' },
      green: { label: 'Xanh', fill: '#8bffbe', border: '#b6ffd8' },
    };

    const communityPalette = [
      '#66e3ff', '#8bffbe', '#ffd166', '#7aa2ff', '#ff738f', '#c79cff', '#ff9f68', '#73ddff'
    ];

    function safeText(value) {
      return String(value ?? '').replace(/[&<>]/g, s => ({'&': '&amp;', '<': '&lt;', '>': '&gt;'}[s]));
    }

    function fmt(value, digits = 2) {
      return Number(value).toFixed(digits);
    }

    function priorityLevel(score) {
      if (score > 0.7) return 'red';
      if (score >= 0.4) return 'yellow';
      return 'green';
    }

    function priorityLabel(score) {
      const level = priorityLevel(score);
      return priorityMeta[level].label;
    }

    function colorForPriority(score) {
      return priorityMeta[priorityLevel(score)].fill;
    }

    function colorForCommunity(communityId) {
      return communityPalette[Math.abs(Number(communityId)) % communityPalette.length];
    }

    function priorityBadge(score) {
      const level = priorityLevel(score);
      return `<span class="pill ${level}">${priorityMeta[level].label}</span>`;
    }

    function initMap() {
      state.map = L.map('map', { zoomControl: true }).setView([16.5, 107.5], 7);

      const osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: '&copy; OpenStreetMap contributors',
      });

      const esriSat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 18,
        attribution: 'Tiles &copy; Esri',
      });

      const stamenToner = L.tileLayer('https://stamen-tiles.a.ssl.fastly.net/toner/{z}/{x}/{y}.png', {
        maxZoom: 20,
        attribution: 'Map tiles by Stamen Design (toner), CC-BY-SA',
      });

      const cartoLight = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; CartoDB',
      });

      const baseMaps = {
        'OSM (Standard)': osm,
        'Satellite (Esri)': esriSat,
        'Grayscale (Stamen Toner)': stamenToner,
        'Light (CartoDB)': cartoLight,
      };

      // restore last base layer selection when available
      const saved = (function(){ try { return localStorage.getItem('baseLayer'); } catch(e){ return null; } })() || 'OSM (Standard)';
      (baseMaps[saved] || osm).addTo(state.map);

      L.control.layers(baseMaps, null, { position: 'topright', collapsed: false }).addTo(state.map);

      state.layers.reports = L.layerGroup().addTo(state.map);
      state.layers.communities = L.layerGroup().addTo(state.map);
      state.layers.edges = L.layerGroup().addTo(state.map);
      state.layers.selectedCommunity = L.layerGroup().addTo(state.map);

      // persist user's base layer choice
      state.map.on('baselayerchange', function(e){
        try { localStorage.setItem('baseLayer', e.name); } catch(err) { /* ignore */ }
      });
    }

    function renderMetrics() {
      els.metricReports.textContent = state.reports.length;
      els.metricCommunities.textContent = state.communities.length;
      els.metricEdges.textContent = state.summary.edges;
      els.metricModularity.textContent = fmt(state.summary.modularity, 4);
      els.mapStatReports.textContent = `Reports: ${state.reports.length}`;
      els.mapStatCommunities.textContent = `Communities: ${state.communities.length}`;
      els.mapStatSelected.textContent = `Selected: ${state.activeCommunityId ?? '-'}`;
    }

    function renderCommunitySelect() {
      els.communitySelect.innerHTML = [
        `<option value="all">Tất cả cụm</option>`,
        ...state.communities.map(c => `<option value="${c.community_id}">Cụm #${c.community_id} (${c.report_count})</option>`),
      ].join('');
      els.communitySelect.value = state.activeCommunityId == null ? 'all' : String(state.activeCommunityId);
    }

    function applyReportFilter(reports) {
      const query = els.searchInput.value.trim().toLowerCase();
      const priority = els.priorityFilter.value;
      return reports.filter(item => {
        const haystack = [item.province, item.name, item.phone, item.image_label, item.text_label].join(' ').toLowerCase();
        const level = priorityLevel(item.urgency_score);
        return (!query || haystack.includes(query)) && (priority === 'all' || level === priority);
      });
    }

    function renderReportList() {
      const reports = applyReportFilter(state.reports).slice(0, 18);
      els.reportList.innerHTML = reports.map(item => `
        <div class="item" data-report-id="${safeText(item.report_id)}">
          <div class="item-head">
            <div class="title">${safeText(item.name)}</div>
            ${priorityBadge(item.urgency_score)}
          </div>
          <div class="subtle">${safeText(item.province)} · ${safeText(item.created_at)}</div>
          <div class="subtle" style="margin-top: 6px;">${safeText(item.text_content)}</div>
          <div class="subtle" style="margin-top: 6px;">Image: ${safeText(item.image_label)} · Text: ${safeText(item.text_label)} · ${fmt(item.urgency_score, 3)}</div>
        </div>
      `).join('') || '<div class="item"><div class="subtle">Không có dữ liệu khớp bộ lọc.</div></div>';

      els.reportList.querySelectorAll('.item[data-report-id]').forEach(el => {
        el.addEventListener('click', () => focusReport(el.dataset.reportId));
      });
    }

    function renderCommunityList() {
      els.communityList.innerHTML = state.communities.map(comm => {
        const color = colorForCommunity(comm.community_id);
        return `
          <div class="item" data-community-id="${comm.community_id}">
            <div class="item-head">
              <div class="title">Cụm #${comm.community_id}</div>
              <span class="pill blue">${comm.report_count} sự kiện</span>
            </div>
            <div class="subtle">Tâm: ${fmt(comm.center_lat, 4)}, ${fmt(comm.center_lng, 4)}</div>
            <div class="subtle">Cửa sổ: ${safeText(comm.time_window_start)} → ${safeText(comm.time_window_end)}</div>
            <div class="subtle">Max score: ${fmt(comm.max_urgency_score, 3)}</div>
            <div class="subtle" style="margin-top: 8px; color: ${color};">Nhấn để zoom và làm nổi bật cụm này</div>
          </div>
        `;
      }).join('');

      els.communityList.querySelectorAll('.item[data-community-id]').forEach(el => {
        el.addEventListener('click', () => selectCommunity(Number(el.dataset.communityId)));
      });
    }

    function clearLayers() {
      state.layers.reports.clearLayers();
      state.layers.communities.clearLayers();
      state.layers.edges.clearLayers();
      state.layers.selectedCommunity.clearLayers();
    }

    function reportPopupHtml(item) {
      return `
        <div class="popup-title">${safeText(item.name)}</div>
        <div class="popup-meta">${safeText(item.province)} · ${safeText(item.created_at)}</div>
        <div class="popup-text">${safeText(item.text_content)}</div>
        <div class="popup-meta" style="margin-top: 8px;">
          Image: ${safeText(item.image_label)} · Text: ${safeText(item.text_label)}<br/>
          Priority: ${priorityLabel(item.urgency_score)} · Score: ${fmt(item.urgency_score, 3)}<br/>
          GPS: ${fmt(item.lat, 5)}, ${fmt(item.lng, 5)}
        </div>
      `;
    }

    function communityById(id) {
      return state.communities.find(item => Number(item.community_id) === Number(id));
    }

    function nodesForCommunity(id) {
      return state.graph.nodes.filter(node => Number(node.community_id) === Number(id));
    }

    function communityMembersFromCommunityPayload(id) {
      const community = communityById(id);
      return community ? community.members || [] : [];
    }

    function renderMap() {
      clearLayers();
      const filteredReports = applyReportFilter(state.reports);
      const communityFilter = els.communitySelect.value;

      state.graph.edges.forEach(edge => {
        if (!state.showEdges) return;
        const source = state.graph.nodes.find(node => node.report_id === edge.source);
        const target = state.graph.nodes.find(node => node.report_id === edge.target);
        if (!source || !target) return;
        if (communityFilter !== 'all' && Number(source.community_id) !== Number(communityFilter)) return;
        const line = L.polyline([[source.lat, source.lng], [target.lat, target.lng]], {
          color: '#66e3ff',
          weight: 1,
          opacity: 0.22,
          dashArray: '4 8',
        });
        line.addTo(state.layers.edges);
      });

      state.communities.forEach(comm => {
        if (!state.showCommunities) return;
        const radius = 900 + (comm.report_count * 1400);
        const color = colorForCommunity(comm.community_id);
        const circle = L.circle([comm.center_lat, comm.center_lng], {
          radius,
          color,
          weight: 2,
          fillColor: color,
          fillOpacity: 0.10,
        });
        circle.bindPopup(`
          <div class="popup-title">Cụm #${comm.community_id}</div>
          <div class="popup-meta">${comm.report_count} sự kiện · Max score ${fmt(comm.max_urgency_score, 3)}</div>
          <div class="popup-text">Tâm cụm: ${fmt(comm.center_lat, 5)}, ${fmt(comm.center_lng, 5)}</div>
        `);
        circle.addTo(state.layers.communities);
      });

      filteredReports.forEach(item => {
        const isActive = state.activeCommunityId !== null && Number(item.community_id) === Number(state.activeCommunityId);
        const marker = L.circleMarker([item.lat, item.lng], {
          radius: isActive ? 9 : 6,
          color: isActive ? '#ffffff' : colorForPriority(item.urgency_score),
          weight: isActive ? 2.5 : 1.5,
          fillColor: colorForPriority(item.urgency_score),
          fillOpacity: isActive ? 0.95 : 0.82,
        });
        marker.bindPopup(reportPopupHtml(item));
        marker.addTo(state.layers.reports);
      });

      if (state.activeCommunityId !== null) {
        const members = communityMembersFromCommunityPayload(state.activeCommunityId);
        const community = communityById(state.activeCommunityId);
        if (community && members.length) {
          const center = [community.center_lat, community.center_lng];
          L.circle(center, {
            radius: 1300 + community.report_count * 900,
            color: '#66e3ff',
            weight: 3,
            fillColor: '#66e3ff',
            fillOpacity: 0.08,
          }).addTo(state.layers.selectedCommunity);

          L.circleMarker(center, {
            radius: 12,
            color: '#66e3ff',
            weight: 3,
            fillColor: '#ffffff',
            fillOpacity: 0.95,
          }).bindPopup(`<div class="popup-title">Tâm cụm #${community.community_id}</div><div class="popup-meta">${community.report_count} sự kiện</div>`).addTo(state.layers.selectedCommunity);

          members.forEach(member => {
            const memberPoint = L.circleMarker([member.lat, member.lng], {
              radius: 8,
              color: colorForPriority(member.urgency_score),
              weight: 2,
              fillColor: colorForPriority(member.urgency_score),
              fillOpacity: 0.95,
            }).bindPopup(reportPopupHtml(member));
            memberPoint.addTo(state.layers.selectedCommunity);

            L.polyline([[community.center_lat, community.center_lng], [member.lat, member.lng]], {
              color: '#66e3ff',
              weight: 1.5,
              opacity: 0.35,
            }).addTo(state.layers.selectedCommunity);
          });
        }
      }
    }

    function focusReport(reportId) {
      const item = state.reports.find(report => report.report_id === reportId);
      if (!item) return;
      state.map.setView([item.lat, item.lng], 12, { animate: true });
      const temp = L.popup().setLatLng([item.lat, item.lng]).setContent(reportPopupHtml(item)).openOn(state.map);
      if (item.community_id !== undefined) {
        selectCommunity(item.community_id, false);
      }
    }

    function selectCommunity(communityId, refit = true) {
      state.activeCommunityId = communityId;
      els.communitySelect.value = String(communityId);
      renderMetrics();
      renderMap();

      const community = communityById(communityId);
      if (community && refit) {
        state.map.setView([community.center_lat, community.center_lng], 12, { animate: true });
      }
    }

    function fitAll() {
      const latLngs = state.reports.map(item => [item.lat, item.lng]);
      if (!latLngs.length) return;
      const bounds = L.latLngBounds(latLngs);
      state.map.fitBounds(bounds.pad(0.18));
    }

    async function loadData() {
      const [reportsRes, communitiesRes, summaryRes, graphRes] = await Promise.all([
        fetch('/reports'),
        fetch('/louvain/communities'),
        fetch('/louvain/summary'),
        fetch('/louvain/graph'),
      ]);

      const reportsPayload = await reportsRes.json();
      const communitiesPayload = await communitiesRes.json();
      const summaryPayload = await summaryRes.json();
      const graphPayload = await graphRes.json();

      state.reports = (reportsPayload.items || []).map(report => ({
        ...report,
        community_id: null,
      }));
      state.communities = communitiesPayload.communities || [];
      state.summary = summaryPayload;
      state.graph = graphPayload.graph || { nodes: [], edges: [] };

      const communityIndex = new Map();
      state.communities.forEach(comm => {
        comm.members.forEach(member => communityIndex.set(member.report_id, comm.community_id));
      });

      state.reports = state.reports.map(report => ({
        ...report,
        community_id: communityIndex.get(report.report_id) ?? 0,
      }));

      state.graph.nodes = state.graph.nodes.map(node => ({
        ...node,
        community_id: communityIndex.get(node.report_id) ?? 0,
      }));

      state.activeCommunityId = state.communities[0]?.community_id ?? null;

      renderMetrics();
      renderCommunitySelect();
      renderCommunityList();
      renderReportList();
      renderMap();
      fitAll();

      if (state.activeCommunityId !== null) {
        selectCommunity(state.activeCommunityId, false);
      }
    }

    document.getElementById('btnRefresh').addEventListener('click', loadData);
    document.getElementById('btnFitAll').addEventListener('click', fitAll);
    document.getElementById('btnToggleEdges').addEventListener('click', () => {
      state.showEdges = !state.showEdges;
      renderMap();
    });
    document.getElementById('btnToggleCommunities').addEventListener('click', () => {
      state.showCommunities = !state.showCommunities;
      renderMap();
    });
    els.communitySelect.addEventListener('change', () => {
      const value = els.communitySelect.value;
      if (value === 'all') {
        state.activeCommunityId = null;
        renderMetrics();
        renderMap();
        fitAll();
        return;
      }
      selectCommunity(Number(value));
    });
    els.searchInput.addEventListener('input', () => {
      renderReportList();
      renderMap();
    });
    els.priorityFilter.addEventListener('change', () => {
      renderReportList();
      renderMap();
    });

    initMap();
    loadData().catch(error => {
      console.error(error);
      document.getElementById('reportList').innerHTML = `<div class="item"><div class="subtle">Không tải được dữ liệu: ${safeText(error.message)}</div></div>`;
    });
  </script>
</body>
</html>"""
