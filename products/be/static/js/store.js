// Trạng thái phía trình duyệt và lịch vẽ lại theo từng phần giao diện.
import { CLOSED, STATUS_ORDER, eventTime, hasLocation, loadPref, people, topTag } from './util.js';

export const state = {
    operator: null,
    config: {},
    reports: new Map(),          // id -> báo cáo (cập nhật dần qua /api/reports/changes)
    cursor: 0,
    epoch: null,
    loaded: false,
    clusterData: { clusters: [], review: [] },
    session: null,               // phiên đăng nhập: operator, username, role, operatorId...
    clusterStale: false,         // server trả kết quả phân cụm cũ trong lúc tính lại nền
    clusterEtag: null,
    clusterOf: new Map(),        // id báo cáo -> cụm
    teams: [],
    teamById: new Map(),
    stats: null,
    // Cụm đang chọn: giữ theo clusterKey + danh sách thành viên lúc chọn (clusterId đổi giữa các lần phân cụm).
    selection: null,             // { key, ids: Set }
    filters: { q: '', statuses: new Set(), time: '', since: '', until: '', team: '', location: '', vulnerable: '', label: '', sendMode: '' },
    sort: { field: 'priority', dir: 'asc' },
    page: 1,
    pageSize: loadPref('pageSize', 50),
    checked: new Set(),
    newIds: new Set(),
    unseen: 0,
    colorMode: loadPref('colorMode', 'cluster'),
    showClosed: loadPref('showClosed', false),
    heat: loadPref('heat', false),
    tab: 'clusters',
    openReportId: null,
};

// ---------------------------------------------------------------- Lịch vẽ lại
const renderers = {};
const dirty = new Set();
let frame = 0;
export function registerRenderer(part, fn) { renderers[part] = fn; }
export function invalidate(...parts) {
    parts.forEach(p => dirty.add(p));
    if (!frame) {
        frame = requestAnimationFrame(() => {
            frame = 0;
            const todo = [...dirty];
            dirty.clear();
            for (const part of todo) {
                try { renderers[part]?.(); } catch (err) { console.error('render', part, err); }
            }
        });
    }
}
export const ALL_PARTS = ['kpis', 'map', 'clusters', 'review', 'table', 'drawer', 'filters'];

// ---------------------------------------------------------------- Truy vấn trên state
export function getReport(id) { return state.reports.get(id); }
export function clusterFor(id) { return state.clusterOf.get(id); }
export function selectedCluster() {
    const sel = state.selection;
    return sel ? state.clusterData.clusters.find(c => c.clusterKey === sel.key) || null : null;
}

function timeRange() {
    const f = state.filters;
    if (!f.time) return [null, null];
    if (f.time === 'custom') {
        return [f.since ? new Date(f.since) : null, f.until ? new Date(f.until) : null];
    }
    return [new Date(Date.now() - Number(f.time) * 3600 * 1000), null];
}

/** Lọc phía trình duyệt, cùng ngữ nghĩa với tham số lọc của GET /api/reports. */
export function matchesFilters(r) {
    const f = state.filters;
    if (f.statuses.size && !f.statuses.has(r.status)) return false;
    if (f.q) {
        const q = f.q.toLowerCase();
        if (!String(r.id).toLowerCase().includes(q) && !String(r.description || '').toLowerCase().includes(q)) return false;
    }
    const [since, until] = timeRange();
    if (since || until) {
        const t = eventTime(r);
        if (!t || (since && t < since) || (until && t > until)) return false;
    }
    if (f.location === 'true' && !hasLocation(r)) return false;
    if (f.location === 'false' && hasLocation(r)) return false;
    if (f.team === 'none' && r.assignedTeamId !== null && r.assignedTeamId !== undefined) return false;
    if (f.team && f.team !== 'none' && String(r.assignedTeamId) !== f.team) return false;
    if (f.sendMode && r.sendMode !== f.sendMode) return false;
    if (f.label && topTag(r)?.label !== f.label) return false;
    if (f.vulnerable) {
        const groups = r.vulnerableGroups || [];
        if (!groups.length || (f.vulnerable !== 'any' && !groups.includes(f.vulnerable))) return false;
    }
    return true;
}

export function visibleReports() {
    const sel = state.selection;
    const base = sel ? [...sel.ids].map(getReport).filter(Boolean) : [...state.reports.values()];
    const rows = base.filter(matchesFilters);
    const { field, dir } = state.sort;
    const sign = dir === 'asc' ? 1 : -1;
    const time = r => eventTime(r)?.getTime() ?? 0;
    const rank = r => clusterFor(r.id)?.rank ?? Infinity;
    const cmp = {
        createdAt: (a, b) => time(a) - time(b),
        people: (a, b) => people(a) - people(b),
        status: (a, b) => STATUS_ORDER[a.status] - STATUS_ORDER[b.status],
        // Cụm hạng cao trước; báo cáo chưa kết thúc trước; mới nhất trước.
        priority: (a, b) => (rank(a) - rank(b)) || (CLOSED.has(a.status) - CLOSED.has(b.status)) || (time(b) - time(a)) * sign,
    }[field];
    return rows.sort((a, b) => sign * cmp(a, b) || String(a.id).localeCompare(String(b.id)));
}

/** Tham số query tương ứng bộ lọc hiện tại (dùng cho xuất dữ liệu). */
export function filterQuery() {
    const f = state.filters;
    const params = new URLSearchParams();
    if (f.statuses.size) params.set('status', [...f.statuses].join(','));
    if (f.q) params.set('q', f.q);
    const [since, until] = timeRange();
    if (since) params.set('since', since.toISOString());
    if (until) params.set('until', until.toISOString());
    if (f.team) params.set('teamId', f.team);
    if (f.location) params.set('hasLocation', f.location);
    if (f.vulnerable) params.set('vulnerable', f.vulnerable);
    if (f.label) params.set('label', f.label);
    if (f.sendMode) params.set('sendMode', f.sendMode);
    if (state.selection) params.set('ids', [...state.selection.ids].join(','));
    return params;
}
