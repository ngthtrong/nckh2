// Panel bên: danh sách cụm ưu tiên và hàng đợi "Cần xem xét" (thiếu vị trí/thời gian).
import { clusterColor } from './map.js';
import { getReport, selectedCluster, state } from './store.js';
import { STATUS_LABEL, esc, eventTime, fmtAgo, fmtDate, people } from './util.js';

const PRIORITY_MAX = 2.0; // mu = 2 (Eq. 4)

export function renderClusters() {
    const box = document.getElementById('cluster-list');
    const rows = state.clusterData.clusters;
    document.getElementById('tab-count-clusters').textContent = rows.filter(c => c.size > 1).length || '';
    if (!rows.length) {
        box.innerHTML = '<div class="empty-panel">Chưa có cụm nào (không có báo cáo đang mở có vị trí).</div>';
        return;
    }
    const selected = selectedCluster();
    box.innerHTML = rows.map(c => {
        const pct = Math.min(100, 100 * c.priority / PRIORITY_MAX);
        const k = c.components;
        const members = c.reportIds.map(getReport).filter(Boolean);
        const counts = {};
        let total = 0;
        for (const r of members) { counts[r.status] = (counts[r.status] || 0) + 1; total += people(r); }
        const mix = Object.entries(counts).map(([s, n]) => `<span class="badge badge-${esc(s)}">${n} ${esc((STATUS_LABEL[s] || s).toLowerCase())}</span>`).join('');
        return `<button class="cluster-row ${selected && selected.clusterKey === c.clusterKey ? 'active' : ''}" data-cluster-key="${esc(c.clusterKey)}">
            <div class="cluster-top">
                <div class="left">
                    <span class="swatch" style="background:${clusterColor(c)}"></span>
                    <span class="cluster-rank">#${c.rank}</span>
                    <span class="cluster-meta">${c.size} báo cáo · ~${Math.round(total)} người</span>
                </div>
                <span class="cluster-score" title="Điểm ưu tiên P">${c.priority.toFixed(3)}</span>
            </div>
            <div class="meter"><span style="width:${pct}%"></span></div>
            <div class="status-mix">${mix}</div>
            <div class="cluster-components">E ${k.E.toFixed(2)} · F ${k.F.toFixed(2)} · N ${k.N.toFixed(2)} · V ${k.V.toFixed(2)} · tin cậy ${k.provenance.toFixed(2)}
                ${c.exactDuplicatesRemoved || c.nearDuplicatesCoalesced ? ` · gộp ${c.exactDuplicatesRemoved + c.nearDuplicatesCoalesced} bản trùng` : ''}</div>
        </button>`;
    }).join('');
}

export function renderReview() {
    const box = document.getElementById('review-list');
    const ids = state.clusterData.review || [];
    document.getElementById('tab-count-review').textContent = ids.length || '';
    const rows = ids.map(getReport).filter(Boolean).sort((a, b) => (eventTime(b)?.getTime() ?? 0) - (eventTime(a)?.getTime() ?? 0));
    if (!rows.length) {
        box.innerHTML = '<div class="empty-panel">Không có báo cáo nào cần xem xét thủ công.</div>';
        return;
    }
    box.innerHTML = rows.map(r => `
        <div class="review-row">
            <div>
                <div><b class="mono">${esc(r.id)}</b> <span class="badge badge-${esc(r.status)}">${esc(STATUS_LABEL[r.status] || r.status)}</span></div>
                <div class="muted small">${fmtDate(eventTime(r))} · ${fmtAgo(eventTime(r))} · ${people(r)} người · ${r.lat == null ? 'không có GPS' : 'thiếu thời gian'}</div>
                <div class="desc">${esc((r.description || '(không có mô tả)').slice(0, 140))}</div>
            </div>
            <div class="action-row">
                <button class="btn btn-small" data-review-open="${esc(r.id)}">Chi tiết</button>
                <button class="btn btn-small btn-primary" data-review-pick="${esc(r.id)}">Đặt vị trí</button>
            </div>
        </div>`).join('');
}
