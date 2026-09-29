// Bản đồ Leaflet: cập nhật điểm theo id (không xóa/vẽ lại nên popup đang mở không bị đóng),
// tô màu theo cụm hoặc trạng thái, bản đồ nhiệt, chế độ chọn vị trí thủ công.
import { clusterFor, selectedCluster, state } from './store.js';
import { CLOSED, STATUS_LABEL, esc, fmtDate, eventTime, hasLocation, people } from './util.js';

// 8 cụm ưu tiên cao nhất có màu riêng (thứ tự bảng màu phân loại cố định); các cụm khác màu trung tính,
// nhận diện bằng nhãn hạng.
const CLUSTER_COLORS = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948'];
const OTHER_CLUSTER = '#5b6b82';
const SINGLE = '#9aa3af';
const STATUS_COLORS = { processing: '#d03b3b', dispatched: '#fab219', resolved: '#0ca30c', cancelled: '#8a8f98' };

let map, pointLayer, labelLayer, heatLayer, tileLayer;
const markers = new Map();   // id -> { marker, sig }
let fitted = false;
let pick = null;             // { onPick }
let lastLabelSig = '';

export function clusterColor(cluster) {
    if (!cluster || cluster.size < 2) return SINGLE;
    return cluster.rank <= CLUSTER_COLORS.length ? CLUSTER_COLORS[cluster.rank - 1] : OTHER_CLUSTER;
}

export function initMap(onOpenReport, onSelectCluster) {
    map = L.map('map', { preferCanvas: true }).setView([16.05, 108.2], 11);
    tileLayer = L.tileLayer(state.config.tileUrl || 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19, attribution: state.config.tileAttribution || '&copy; OpenStreetMap contributors',
    }).addTo(map);
    pointLayer = L.layerGroup().addTo(map);
    labelLayer = L.layerGroup().addTo(map);
    if (L.heatLayer) heatLayer = L.heatLayer([], { radius: 22, blur: 18, maxZoom: 15, minOpacity: 0.35 });

    document.getElementById('map').addEventListener('click', event => {
        const btn = event.target.closest('[data-open-id]');
        if (btn) { event.preventDefault(); onOpenReport(btn.dataset.openId); }
    });
    map.on('click', event => { if (pick) pickAt(event.latlng); });
    initMap.onSelectCluster = onSelectCluster;
    setTimeout(() => map.invalidateSize(), 0);
}

// Khi đang chọn vị trí, bấm trúng điểm/nhãn cụm có sẵn cũng lấy tọa độ (marker chặn sự kiện click của bản đồ).
function pickAt(latlng) {
    const done = pick.onPick;
    pick.onCancel = null;
    cancelPick();
    done(Number(latlng.lat.toFixed(6)), Number(latlng.lng.toFixed(6)));
}

function markerStyle(r, cluster, dimmed) {
    const closed = CLOSED.has(r.status);
    const fill = state.colorMode === 'status' ? STATUS_COLORS[r.status] : closed ? SINGLE : clusterColor(cluster);
    return {
        radius: 4 + Math.min(10, Math.sqrt(people(r))),
        color: closed ? fill : '#ffffff',
        weight: closed ? 2 : 1,
        fillColor: fill,
        fillOpacity: dimmed ? 0.12 : closed ? 0.25 : 0.88,
        opacity: dimmed ? 0.3 : 1,
    };
}

function popupHtml(r, cluster) {
    const team = r.assignedTeamId != null ? state.teamById.get(r.assignedTeamId)?.name : null;
    return `<b class="mono">${esc(r.id)}</b><br>${fmtDate(eventTime(r))}<br>
        Cụm: ${cluster && cluster.size > 1 ? '#' + cluster.rank : '–'} · ${people(r)} người · ${esc(STATUS_LABEL[r.status] || r.status)}
        ${team ? `<br>Đội: ${esc(team)}` : ''}
        ${r.locationSource === 'manual' ? '<br><i>Vị trí nhập tay</i>' : ''}
        <br>${esc((r.description || '').slice(0, 160))}
        <div class="popup-actions"><a href="#" data-open-id="${esc(r.id)}">Xem chi tiết</a></div>`;
}

export function renderMap() {
    if (!map) return;
    const sel = state.selection;
    const seen = new Set();
    const bounds = [];
    for (const r of state.reports.values()) {
        if (!hasLocation(r) || (!state.showClosed && CLOSED.has(r.status))) continue;
        const cluster = clusterFor(r.id);
        const dimmed = !!sel && !sel.ids.has(r.id);
        const style = markerStyle(r, cluster, dimmed);
        const sig = JSON.stringify([r.lat, r.lng, style, r.status, r.updatedSeq, cluster?.rank, cluster?.size]);
        seen.add(r.id);
        bounds.push([r.lat, r.lng]);
        const existing = markers.get(r.id);
        if (existing) {
            if (existing.sig === sig) continue;
            existing.marker.setLatLng([r.lat, r.lng]);
            existing.marker.setStyle(style);
            existing.marker.setRadius(style.radius);
            existing.marker.setPopupContent(popupHtml(r, cluster));
            existing.sig = sig;
        } else {
            const marker = L.circleMarker([r.lat, r.lng], style).bindPopup(popupHtml(r, cluster));
            marker.on('click', event => {
                if (pick) { marker.closePopup(); pickAt(event.latlng); return; }
                const c = clusterFor(r.id);
                if (c && c.size > 1) initMap.onSelectCluster?.(c, false);
            });
            marker.addTo(pointLayer);
            markers.set(r.id, { marker, sig });
        }
    }
    for (const [id, entry] of markers) {
        if (!seen.has(id)) { pointLayer.removeLayer(entry.marker); markers.delete(id); }
    }
    renderLabels();
    renderHeat();
    renderLegend();
    if (!fitted && bounds.length) {
        map.fitBounds(bounds, { padding: [20, 20] });
        fitted = true;
    }
}

function renderLabels() {
    const selected = selectedCluster();
    const clusters = state.clusterData.clusters.filter(c => c.size >= 2 && c.centroid);
    const sig = JSON.stringify([clusters.map(c => [c.clusterKey, c.rank, c.centroid]), selected?.clusterKey]);
    if (sig === lastLabelSig) return;
    lastLabelSig = sig;
    labelLayer.clearLayers();
    for (const c of clusters) {
        const isSel = selected && selected.clusterKey === c.clusterKey;
        L.marker([c.centroid.lat, c.centroid.lng], {
            icon: L.divIcon({ className: '', html: `<span class="rank-label${isSel ? ' selected' : ''}">#${c.rank}</span>`, iconSize: null }),
            zIndexOffset: isSel ? 2000 : 1000 - c.rank,
            keyboard: false,
        }).on('click', event => (pick ? pickAt(event.latlng) : initMap.onSelectCluster?.(c, true))).addTo(labelLayer);
    }
}

function renderHeat() {
    if (!heatLayer) return;
    if (!state.heat) {
        if (map.hasLayer(heatLayer)) map.removeLayer(heatLayer);
        return;
    }
    const points = [];
    for (const r of state.reports.values()) {
        if (hasLocation(r) && !CLOSED.has(r.status)) points.push([r.lat, r.lng, Math.min(1, 0.3 + people(r) / 20)]);
    }
    heatLayer.setLatLngs(points);
    if (!map.hasLayer(heatLayer)) heatLayer.addTo(map);
}

function renderLegend() {
    const el = document.getElementById('map-legend');
    const size = '<span class="legend-item">Kích thước điểm = số người cần cứu</span>';
    if (state.colorMode === 'status') {
        el.innerHTML = Object.entries(STATUS_COLORS)
            .filter(([s]) => state.showClosed || !CLOSED.has(s))
            .map(([s, c]) => `<span class="legend-item"><span class="swatch" style="background:${c}"></span>${esc(STATUS_LABEL[s])}</span>`)
            .join('') + size;
    } else {
        el.innerHTML = `<span class="legend-item"><span class="swatch" style="background:${CLUSTER_COLORS[0]}"></span>Màu = cụm (8 cụm ưu tiên cao nhất)</span>
            <span class="legend-item"><span class="swatch" style="background:${OTHER_CLUSTER}"></span>Cụm khác</span>
            <span class="legend-item"><span class="swatch" style="background:${SINGLE}"></span>Điểm lẻ</span>
            <span class="legend-item"><span class="rank-label">#1</span> hạng ưu tiên tại trọng tâm cụm</span>${size}`;
    }
}

export function fitAll() {
    const pts = [...state.reports.values()].filter(r => hasLocation(r) && (state.showClosed || !CLOSED.has(r.status))).map(r => [r.lat, r.lng]);
    if (pts.length) map.fitBounds(pts, { padding: [20, 20] });
}

export function fitIds(ids) {
    const pts = [...ids].map(id => state.reports.get(id)).filter(r => r && hasLocation(r)).map(r => [r.lat, r.lng]);
    if (pts.length) map.fitBounds(pts, { padding: [60, 60], maxZoom: 16 });
}

export function focusReport(id) {
    const r = state.reports.get(id);
    if (!r || !hasLocation(r)) return;
    map.setView([r.lat, r.lng], Math.max(map.getZoom(), 15));
    const entry = markers.get(id);
    if (entry) entry.marker.openPopup();
    document.querySelector('.map-card').scrollIntoView({ behavior: 'smooth', block: 'center' });
}

export function resetView() { fitted = false; }

/** Chế độ chọn vị trí: bấm lên bản đồ để lấy tọa độ; Esc hoặc nút Hủy để thoát. */
export function startPick(label, onPick, onCancel) {
    pick = { onPick, onCancel };
    const banner = document.getElementById('pick-banner');
    banner.innerHTML = `<span>Bấm lên bản đồ để đặt vị trí cho <b>${esc(label)}</b></span><button class="btn btn-small" id="pick-cancel">Hủy (Esc)</button>`;
    banner.hidden = false;
    document.querySelector('.map-card').classList.add('picking');
    document.getElementById('pick-cancel').onclick = cancelPick;
    document.querySelector('.map-card').scrollIntoView({ behavior: 'smooth', block: 'center' });
}
export function cancelPick() {
    const onCancel = pick?.onCancel;
    pick = null;
    onCancel?.();
    document.getElementById('pick-banner').hidden = true;
    document.querySelector('.map-card').classList.remove('picking');
}
export function isPicking() { return !!pick; }
export function invalidateMapSize() { map?.invalidateSize(); }
