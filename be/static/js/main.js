// Khởi động dashboard: đăng nhập, hỏi thay đổi định kỳ, chọn cụm, gắn sự kiện giao diện.
import { api, setUnauthorizedHandler } from './api.js';
import { changePassword, initAccounts, isAdmin } from './accounts.js';
import { assignTeam, changeStatus, createReport, setAfterChange } from './actions.js';
import { closeDrawer, openReport, pickLocation, renderDrawer } from './drawer.js';
import { cancelPick, fitAll, fitIds, initMap, invalidateMapSize, isPicking, renderMap, resetView } from './map.js';
import { renderClusters, renderReview } from './panels.js';
import { renderResponseKpi, renderStats } from './stats.js';
import { ALL_PARTS, getReport, invalidate, registerRenderer, selectedCluster, state, filterQuery } from './store.js';
import { currentPageIds, renderBulkBar, renderTable } from './table.js';
import { initTeams, renderTeams } from './teams.js';
import { CLOSED, esc, isSynthetic, loadPref, savePref, toast } from './util.js';

const POLL_MS = 5000;
const STATS_MS = 30000;
const TEAMS_MS = 60000;
const BASE_TITLE = document.title;

let pollTimer = 0;
let statsTimer = 0;
let teamsTimer = 0;
let polling = false;
let started = false;
let soundOn = loadPref('sound', false);

// ---------------------------------------------------------------- Đăng nhập
function showLogin(message) {
    stopPolling();
    document.getElementById('app-view').hidden = true;
    document.getElementById('login-view').hidden = false;
    const err = document.getElementById('login-error');
    err.hidden = !message;
    err.textContent = message || '';
    const user = document.getElementById('login-username');
    user.value = user.value || loadPref('username', '');
    (user.value ? document.getElementById('login-password') : user).focus();
}

async function startApp(session) {
    state.session = session;
    state.operator = session.operator;
    state.config = session.config || {};
    document.getElementById('operator-name').textContent = session.operator;
    document.getElementById('btn-operators').hidden = !isAdmin();
    document.querySelectorAll('[data-admin-only]').forEach(el => { el.hidden = !isAdmin(); });
    document.getElementById('login-view').hidden = true;
    document.getElementById('app-view').hidden = false;
    if (!started) {
        started = true;
        initMap(openReport, (cluster, pan) => selectCluster(cluster, pan));
        bindUi();
        initTeams(async () => { await loadTeams(); loadStats(); });
        initAccounts();
    }
    if (session.mustChangePassword && !(await changePassword({ forced: true }))) {
        await logout();
        return;
    }
    if (state.config.defaultAdminPassword) {
        toast('Tài khoản quản trị vẫn dùng mật khẩu mặc định. Đổi mật khẩu trước khi dùng thật.', 'error');
    }
    invalidateMapSize();
    await Promise.all([loadTeams(), poll(true)]);
    loadStats();
    pollTimer = setInterval(() => poll(false), POLL_MS);
    statsTimer = setInterval(loadStats, STATS_MS);
    teamsTimer = setInterval(loadTeams, TEAMS_MS);
}

async function logout() {
    try { await api('/api/auth/logout', { method: 'POST' }); } catch { /* vẫn thoát */ }
    state.session = null;
    closeDrawer();
    showLogin();
}

function stopPolling() {
    clearInterval(pollTimer);
    clearInterval(statsTimer);
    clearInterval(teamsTimer);
}

document.getElementById('login-form').addEventListener('submit', async event => {
    event.preventDefault();
    const username = document.getElementById('login-username').value.trim().toLowerCase();
    const password = document.getElementById('login-password').value;
    const btn = event.target.querySelector('button[type=submit]');
    btn.disabled = true;
    try {
        const session = await api('/api/auth/login', { method: 'POST', body: { username, password } });
        savePref('username', username);
        document.getElementById('login-password').value = '';
        await startApp(session);
    } catch (err) {
        showLogin(err.message);
    } finally {
        btn.disabled = false;
    }
});

setUnauthorizedHandler(() => showLogin('Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại.'));

// ---------------------------------------------------------------- Tải dữ liệu
function setLive(ok, text) {
    const el = document.getElementById('live-status');
    el.classList.toggle('error', !ok);
    el.querySelector('.text').textContent = text;
}

async function poll(first) {
    if (polling) return;
    polling = true;
    try {
        let changed = false;
        let more = true;
        while (more) {
            const data = await api(`/api/reports/changes?since=${state.cursor}&epoch=${encodeURIComponent(state.epoch || '')}`);
            if (data.reset) {
                if (state.loaded && state.epoch && data.epoch !== state.epoch) toast('Dữ liệu trên server đã được làm mới toàn bộ.');
                state.reports.clear();
                state.checked.clear();
                state.newIds.clear();
                state.unseen = 0;
                resetView();
            }
            let fresh = 0;
            for (const r of data.reports) {
                if (state.loaded && !data.reset && !state.reports.has(r.id)) {
                    state.newIds.add(r.id);
                    fresh += 1;
                }
                state.reports.set(r.id, r);
            }
            if (fresh) notifyNew(fresh);
            changed = changed || data.reports.length > 0 || data.reset;
            state.cursor = data.cursor;
            state.epoch = data.epoch;
            more = data.hasMore;
        }
        state.loaded = true;

        const res = await api('/api/clusters', { raw: true, headers: state.clusterEtag ? { 'If-None-Match': state.clusterEtag } : {} });
        if (!res.notModified) {
            const clusters = await res.json();
            state.clusterEtag = res.headers.get('ETag');
            state.clusterData = clusters;
            state.clusterStale = Boolean(clusters.stale);
            state.clusterOf = new Map();
            for (const c of clusters.clusters) for (const id of c.reportIds) state.clusterOf.set(id, c);
            reconcileSelection();
            changed = true;
        }
        if (changed || first) invalidate(...ALL_PARTS);
        const clusterNote = state.clusterStale ? ' · phân cụm đang tính lại' : '';
        setLive(true, `Cập nhật lúc ${new Date().toLocaleTimeString('vi-VN')} · tự làm mới ${POLL_MS / 1000} s${clusterNote}`);
    } catch (err) {
        if (err.status !== 401) setLive(false, `Mất kết nối server — đang thử lại (${err.message})`);
    } finally {
        polling = false;
    }
}

async function loadTeams() {
    try {
        const data = await api('/api/teams');
        state.teams = data.teams;
        state.teamById = new Map(data.teams.map(t => [t.id, t]));
        renderTeamFilter();
        renderTeams();
        invalidate('table', 'drawer', 'map');
    } catch (err) { /* hiện ở trạng thái kết nối */ }
}

async function loadStats() {
    try {
        state.stats = await api('/api/stats');
        renderResponseKpi();
        if (state.tab === 'stats') renderStats();
    } catch (err) { /* bỏ qua */ }
}

setAfterChange(async () => {
    await poll(false);
    loadStats();
    loadTeams();
});

// ---------------------------------------------------------------- Báo cáo mới
function notifyNew(count) {
    state.unseen += count;
    const btn = document.getElementById('new-reports');
    btn.hidden = false;
    btn.textContent = `${state.unseen} báo cáo mới`;
    document.title = `(${state.unseen}) ${BASE_TITLE}`;
    if (soundOn) beep();
}

function beep() {
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.frequency.value = 880;
        gain.gain.setValueAtTime(0.15, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
        osc.connect(gain).connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.5);
    } catch { /* trình duyệt chặn âm thanh */ }
}

function acknowledgeNew() {
    state.unseen = 0;
    document.getElementById('new-reports').hidden = true;
    document.title = BASE_TITLE;
    selectCluster(null);
    state.sort = { field: 'createdAt', dir: 'desc' };
    state.page = 1;
    invalidate('table');
    document.querySelector('.table-card').scrollIntoView({ behavior: 'smooth' });
}

// ---------------------------------------------------------------- Chọn cụm
function selectCluster(cluster, pan = true) {
    if (!cluster) {
        state.selection = null;
    } else {
        state.selection = { key: cluster.clusterKey, ids: new Set(cluster.reportIds) };
        if (pan) fitIds(cluster.reportIds);
    }
    state.page = 1;
    invalidate('map', 'clusters', 'table');
}

/**
 * Sau mỗi lần phân cụm lại: tìm lại cụm đang chọn theo clusterKey, nếu không có thì theo
 * số thành viên trùng nhiều nhất; báo cho điều phối viên khi thành viên cụm thay đổi.
 */
function reconcileSelection() {
    const sel = state.selection;
    if (!sel) return;
    const clusters = state.clusterData.clusters;
    let match = clusters.find(c => c.clusterKey === sel.key);
    if (!match) {
        let best = 0;
        for (const c of clusters) {
            const overlap = c.reportIds.filter(id => sel.ids.has(id)).length;
            if (overlap > best) { best = overlap; match = c; }
        }
    }
    const closedNow = id => CLOSED.has(getReport(id)?.status);
    if (!match) {
        const allClosed = [...sel.ids].every(closedNow);
        toast(allClosed ? 'Cụm đã chọn đã được xử lý xong.' : 'Cụm đã chọn không còn sau khi phân cụm lại; đã bỏ chọn.');
        state.selection = null;
        return;
    }
    const ids = new Set(match.reportIds);
    const added = [...ids].filter(id => !sel.ids.has(id)).length;
    const removed = [...sel.ids].filter(id => !ids.has(id) && !closedNow(id)).length;
    if (added || removed) toast(`Cụm #${match.rank} vừa được tính lại: thêm ${added}, bớt ${removed} báo cáo.`);
    state.selection = { key: match.clusterKey, ids };
}

// ---------------------------------------------------------------- KPI & bộ lọc
function renderKpis() {
    const counts = { processing: 0, dispatched: 0, resolved: 0, cancelled: 0 };
    let synthetic = 0;
    for (const r of state.reports.values()) {
        counts[r.status] = (counts[r.status] || 0) + 1;
        if (isSynthetic(r)) synthetic += 1;
    }
    for (const [k, v] of Object.entries(counts)) document.getElementById(`kpi-${k}`).textContent = v;
    document.getElementById('kpi-review').textContent = (state.clusterData.review || []).length;
    document.getElementById('kpi-clusters').textContent = state.clusterData.clusters.filter(c => c.size > 1).length;
    document.getElementById('synthetic-banner').hidden = synthetic === 0;
    document.getElementById('synthetic-count').textContent = synthetic;
}

function renderFilters() {
    const f = state.filters;
    document.querySelectorAll('.chip[data-status]').forEach(chip => chip.setAttribute('aria-pressed', String(f.statuses.has(chip.dataset.status))));
    document.getElementById('f-custom-time').hidden = f.time !== 'custom';
    document.querySelectorAll('[data-color-mode]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.colorMode === state.colorMode)));
    document.getElementById('toggle-closed').checked = state.showClosed;
    document.getElementById('toggle-heat').checked = state.heat;
}

function renderTeamFilter() {
    const select = document.getElementById('f-team');
    const value = select.value;
    select.innerHTML = '<option value="">Mọi đội</option><option value="none">Chưa giao đội</option>' +
        state.teams.map(t => `<option value="${t.id}">${esc(t.name)}${t.active ? '' : ' (ngừng)'}</option>`).join('');
    select.value = value;
}

function setTab(tab) {
    state.tab = tab;
    document.querySelectorAll('[role=tab]').forEach(b => b.setAttribute('aria-selected', String(b.dataset.tab === tab)));
    document.querySelectorAll('.tab-panel').forEach(p => { p.hidden = p.dataset.panel !== tab; });
    if (tab === 'stats') renderStats();
}

function resetFilters() {
    state.filters = { q: '', statuses: new Set(), time: '', since: '', until: '', team: '', location: '', vulnerable: '', label: '', sendMode: '' };
    for (const id of ['f-q', 'f-time', 'f-since', 'f-until', 'f-team', 'f-location', 'f-vulnerable', 'f-label', 'f-sendmode']) {
        document.getElementById(id).value = '';
    }
    state.page = 1;
    invalidate('filters', 'table');
}

function filtersChanged() {
    state.page = 1;
    invalidate('filters', 'table');
}

// ---------------------------------------------------------------- Gắn sự kiện
function bindUi() {
    registerRenderer('kpis', renderKpis);
    registerRenderer('map', renderMap);
    registerRenderer('clusters', renderClusters);
    registerRenderer('review', renderReview);
    registerRenderer('table', renderTable);
    registerRenderer('drawer', renderDrawer);
    registerRenderer('filters', renderFilters);

    document.getElementById('btn-logout').addEventListener('click', logout);
    document.getElementById('operator-name').addEventListener('click', () => changePassword());
    document.getElementById('new-reports').addEventListener('click', acknowledgeNew);
    document.getElementById('btn-new-report').addEventListener('click', async () => {
        const id = await createReport();
        if (id) openReport(id);
    });

    const soundBtn = document.getElementById('btn-sound');
    const renderSound = () => {
        soundBtn.textContent = `Âm báo: ${soundOn ? 'bật' : 'tắt'}`;
        soundBtn.setAttribute('aria-pressed', String(soundOn));
    };
    renderSound();
    soundBtn.addEventListener('click', () => { soundOn = !soundOn; savePref('sound', soundOn); renderSound(); if (soundOn) beep(); });

    // Xuất dữ liệu / sao lưu
    const exportBtn = document.getElementById('btn-export');
    const menu = document.getElementById('export-menu');
    exportBtn.addEventListener('click', event => {
        event.stopPropagation();
        menu.hidden = !menu.hidden;
        exportBtn.setAttribute('aria-expanded', String(!menu.hidden));
    });
    document.addEventListener('click', () => { menu.hidden = true; exportBtn.setAttribute('aria-expanded', 'false'); });
    menu.addEventListener('click', event => {
        const btn = event.target.closest('button');
        if (!btn) return;
        const link = document.createElement('a');
        if (btn.dataset.action === 'backup' || btn.dataset.action === 'backup-images') {
            link.href = `/api/admin/backup${btn.dataset.action === 'backup-images' ? '?images=1' : ''}`;
        } else {
            const params = filterQuery();
            params.set('format', btn.dataset.format);
            link.href = `/api/export?${params}`;
        }
        link.download = '';
        document.body.appendChild(link);
        link.click();
        link.remove();
    });

    // KPI → lọc/tab
    document.querySelectorAll('.kpi[data-status-filter]').forEach(k => k.addEventListener('click', () => {
        state.filters.statuses = new Set([k.dataset.statusFilter]);
        filtersChanged();
        document.querySelector('.table-card').scrollIntoView({ behavior: 'smooth' });
    }));
    document.querySelectorAll('.kpi[data-tab-target]').forEach(k => k.addEventListener('click', () => setTab(k.dataset.tabTarget)));
    document.querySelectorAll('[role=tab]').forEach(b => b.addEventListener('click', () => setTab(b.dataset.tab)));

    // Bản đồ
    document.querySelectorAll('[data-color-mode]').forEach(b => b.addEventListener('click', () => {
        state.colorMode = b.dataset.colorMode; savePref('colorMode', state.colorMode); invalidate('map', 'filters');
    }));
    document.getElementById('toggle-closed').addEventListener('change', e => {
        state.showClosed = e.target.checked; savePref('showClosed', state.showClosed); invalidate('map');
    });
    document.getElementById('toggle-heat').addEventListener('change', e => {
        state.heat = e.target.checked; savePref('heat', state.heat); invalidate('map');
    });
    document.getElementById('btn-fit').addEventListener('click', fitAll);

    // Panel cụm & hàng cần xem xét
    document.getElementById('cluster-list').addEventListener('click', event => {
        const row = event.target.closest('[data-cluster-key]');
        if (!row) return;
        const cluster = state.clusterData.clusters.find(c => c.clusterKey === row.dataset.clusterKey);
        const current = selectedCluster();
        selectCluster(current && cluster && current.clusterKey === cluster.clusterKey ? null : cluster);
    });
    document.getElementById('review-list').addEventListener('click', event => {
        const open = event.target.closest('[data-review-open]');
        const pick = event.target.closest('[data-review-pick]');
        if (open) openReport(open.dataset.reviewOpen);
        if (pick) pickLocation(pick.dataset.reviewPick);
    });
    document.getElementById('btn-clear-cluster').addEventListener('click', () => selectCluster(null));
    document.querySelectorAll('[data-cluster-action]').forEach(b => b.addEventListener('click', () => {
        const cluster = selectedCluster();
        if (!state.selection) return;
        changeStatus([...state.selection.ids], b.dataset.clusterAction, { contextLabel: cluster ? `Cụm #${cluster.rank}` : 'Cụm đã chọn' });
    }));

    // Bộ lọc
    let searchTimer = 0;
    document.getElementById('f-q').addEventListener('input', e => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => { state.filters.q = e.target.value.trim(); filtersChanged(); }, 200);
    });
    document.querySelectorAll('.chip[data-status]').forEach(chip => chip.addEventListener('click', () => {
        const s = chip.dataset.status;
        if (state.filters.statuses.has(s)) state.filters.statuses.delete(s); else state.filters.statuses.add(s);
        filtersChanged();
    }));
    const bindSelect = (id, key) => document.getElementById(id).addEventListener('change', e => { state.filters[key] = e.target.value; filtersChanged(); });
    bindSelect('f-time', 'time');
    bindSelect('f-since', 'since');
    bindSelect('f-until', 'until');
    bindSelect('f-team', 'team');
    bindSelect('f-location', 'location');
    bindSelect('f-vulnerable', 'vulnerable');
    bindSelect('f-label', 'label');
    bindSelect('f-sendmode', 'sendMode');
    document.getElementById('f-reset').addEventListener('click', resetFilters);
    document.getElementById('empty-state').addEventListener('click', e => { if (e.target.id === 'empty-reset') resetFilters(); });

    // Bảng
    document.querySelectorAll('.sort').forEach(btn => btn.addEventListener('click', () => {
        const field = btn.dataset.sort;
        state.sort = state.sort.field === field
            ? { field, dir: state.sort.dir === 'asc' ? 'desc' : 'asc' }
            : { field, dir: field === 'priority' ? 'asc' : 'desc' };
        invalidate('table');
    }));
    const rows = document.getElementById('report-rows');
    rows.addEventListener('click', event => {
        const check = event.target.closest('[data-check]');
        if (check) {
            if (check.checked) state.checked.add(check.dataset.check); else state.checked.delete(check.dataset.check);
            check.closest('tr').classList.toggle('selected', check.checked);
            renderBulkBar();
            return;
        }
        if (event.target.closest('a')) return;
        const tr = event.target.closest('tr[data-id]');
        if (tr) openReport(tr.dataset.id);
    });
    document.getElementById('check-all').addEventListener('change', e => {
        for (const id of currentPageIds()) { if (e.target.checked) state.checked.add(id); else state.checked.delete(id); }
        invalidate('table');
    });
    document.getElementById('bulk-bar').addEventListener('click', event => {
        const btn = event.target.closest('[data-bulk]');
        if (!btn) return;
        const ids = [...state.checked];
        if (btn.dataset.bulk === 'clear') { state.checked.clear(); invalidate('table'); return; }
        if (btn.dataset.bulk === 'team') { assignTeam(ids); return; }
        changeStatus(ids, btn.dataset.bulk, { contextLabel: 'Các báo cáo đã chọn' });
    });
    document.getElementById('page-size').value = String(state.pageSize);
    document.getElementById('page-size').addEventListener('change', e => {
        state.pageSize = Number(e.target.value); savePref('pageSize', state.pageSize); state.page = 1; invalidate('table');
    });
    document.getElementById('page-prev').addEventListener('click', () => { state.page -= 1; invalidate('table'); });
    document.getElementById('page-next').addEventListener('click', () => { state.page += 1; invalidate('table'); });

    // Ngăn chi tiết
    document.getElementById('drawer-close').addEventListener('click', () => { closeDrawer(); invalidate('table'); });
    document.addEventListener('keydown', event => {
        if (event.key !== 'Escape' || document.querySelector('dialog[open]')) return;
        if (isPicking()) cancelPick();
        else if (state.openReportId) { closeDrawer(); invalidate('table'); }
    });
}

// ---------------------------------------------------------------- Khởi động
(async () => {
    try {
        const session = await api('/api/auth/me');
        if (session.authenticated) await startApp(session);
        else showLogin();
    } catch {
        showLogin();
    }
})();
