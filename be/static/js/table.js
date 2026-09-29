// Bảng báo cáo: lọc/sắp xếp/phân trang phía trình duyệt, chọn nhiều để thao tác hàng loạt.
import { clusterColor } from './map.js';
import { clusterFor, selectedCluster, state, visibleReports } from './store.js';
import { SEND_MODE_LABEL, VULNERABLE_LABEL, aiText, esc, eventTime, fmtAgo, fmtDate, people, statusBadge } from './util.js';

let pageRows = [];

export function renderTable() {
    const rows = visibleReports();
    const pages = Math.max(1, Math.ceil(rows.length / state.pageSize));
    if (state.page > pages) state.page = pages;
    const start = (state.page - 1) * state.pageSize;
    pageRows = rows.slice(start, start + state.pageSize);

    const sel = state.selection;
    const cluster = selectedCluster();
    document.getElementById('table-title').textContent = sel
        ? (cluster ? `Cụm #${cluster.rank} — ${sel.ids.size} báo cáo` : `Cụm đã chọn — ${sel.ids.size} báo cáo`)
        : 'Tất cả báo cáo';
    document.getElementById('table-subtitle').textContent = cluster
        ? `Điểm ưu tiên ${cluster.priority.toFixed(3)}; đã gộp ${cluster.exactDuplicatesRemoved} bản trùng khớp và ${cluster.nearDuplicatesCoalesced} bản gần trùng.`
        : `${rows.length} báo cáo khớp bộ lọc trên tổng ${state.reports.size}. Chọn một cụm ở panel bên để lọc theo cụm.`;
    document.getElementById('cluster-actions').hidden = !sel;
    if (sel) {
        // Số báo cáo trong cụm còn chuyển được; nút bị vô hiệu khi không còn báo cáo nào.
        const members = [...sel.ids].map(id => state.reports.get(id)).filter(Boolean);
        const eligible = {
            dispatched: members.filter(r => r.status === 'processing').length,
            resolved: members.filter(r => r.status === 'processing' || r.status === 'dispatched').length,
        };
        const labels = { dispatched: 'Điều phối cả cụm', resolved: 'Hoàn tất cả cụm' };
        document.querySelectorAll('[data-cluster-action]').forEach(btn => {
            const n = eligible[btn.dataset.clusterAction];
            btn.textContent = `${labels[btn.dataset.clusterAction]} (${n})`;
            btn.disabled = n === 0;
        });
    }

    document.querySelectorAll('.sort').forEach(btn => {
        btn.dataset.dir = btn.dataset.sort === state.sort.field ? state.sort.dir : '';
    });

    const empty = document.getElementById('empty-state');
    empty.hidden = rows.length > 0;
    empty.innerHTML = state.reports.size
        ? 'Không có báo cáo khớp bộ lọc. <button class="link-btn" id="empty-reset">Xóa lọc</button>'
        : 'Chưa có báo cáo. Chạy app Flutter, <code>python test_client.py</code> hoặc <code>python seed_demo.py</code> để nạp dữ liệu mô phỏng.';

    document.getElementById('report-rows').innerHTML = pageRows.map(r => {
        const c = clusterFor(r.id);
        const team = r.assignedTeamId != null ? state.teamById.get(r.assignedTeamId) : null;
        const t = eventTime(r);
        const vuln = (r.vulnerableGroups || []).map(g => VULNERABLE_LABEL[g] || g).join(', ');
        return `<tr data-id="${esc(r.id)}" class="${state.checked.has(r.id) ? 'selected' : ''} ${state.newIds.has(r.id) ? 'is-new' : ''}">
            <td class="col-check"><input type="checkbox" data-check="${esc(r.id)}" ${state.checked.has(r.id) ? 'checked' : ''} aria-label="Chọn ${esc(r.id)}"></td>
            <td class="nowrap">${fmtDate(t)}<div class="pill-mini">${fmtAgo(t)}</div></td>
            <td class="mono">${esc(r.id)} ${state.newIds.has(r.id) ? '<span class="badge badge-new">MỚI</span>' : ''}
                ${r.lat == null ? '<div class="pill-mini">không có GPS</div>' : r.locationSource === 'manual' ? '<div class="pill-mini">vị trí nhập tay</div>' : ''}</td>
            <td>${c && c.size > 1 ? `<span class="cluster-dot"><span class="swatch" style="background:${clusterColor(c)}"></span>#${c.rank}</span>` : '<span class="muted">–</span>'}</td>
            <td>${people(r)}${vuln ? `<div class="pill-mini">${esc(vuln)}</div>` : ''}</td>
            <td class="desc-cell"><div class="text" title="${esc(r.description)}">${esc(r.description || '')}</div><div class="ai-text">${esc(aiText(r))}</div></td>
            <td>${r.imageUrl ? `<img class="thumb" src="${esc(r.imageUrl)}" alt="" loading="lazy">` : '<span class="muted">–</span>'}
                ${SEND_MODE_LABEL[r.sendMode] ? `<div class="pill-mini nowrap">${esc(SEND_MODE_LABEL[r.sendMode])}</div>` : ''}</td>
            <td>${team ? esc(team.name) : '<span class="muted">–</span>'}</td>
            <td>${statusBadge(r.status)}</td>
            <td class="col-actions"><button class="btn btn-small" data-open="${esc(r.id)}">Chi tiết</button></td>
        </tr>`;
    }).join('');

    const checkAll = document.getElementById('check-all');
    const onPage = pageRows.filter(r => state.checked.has(r.id)).length;
    checkAll.checked = pageRows.length > 0 && onPage === pageRows.length;
    checkAll.indeterminate = onPage > 0 && onPage < pageRows.length;

    document.getElementById('pager-info').textContent = rows.length
        ? `Hiển thị ${start + 1}–${start + pageRows.length} / ${rows.length}` : '';
    document.getElementById('page-label').textContent = `Trang ${state.page}/${pages}`;
    document.getElementById('page-prev').disabled = state.page <= 1;
    document.getElementById('page-next').disabled = state.page >= pages;
    renderBulkBar();
}

export function renderBulkBar() {
    // Chỉ tính các báo cáo còn tồn tại.
    for (const id of state.checked) if (!state.reports.has(id)) state.checked.delete(id);
    const n = state.checked.size;
    document.getElementById('bulk-bar').hidden = n === 0;
    document.getElementById('bulk-count').textContent = `Đã chọn ${n} báo cáo`;
}

export function currentPageIds() { return pageRows.map(r => r.id); }
