// Ngăn chi tiết báo cáo: ảnh, thông tin, thao tác điều phối, ghi chú, nhật ký, JSON gốc.
import { api } from './api.js';
import { addNote, assignTeam, canMoveTo, changeStatus, setLocation } from './actions.js';
import { focusReport, startPick } from './map.js';
import { clusterFor, getReport, invalidate, state } from './store.js';
import {
    CLOSED, EVENT_LABEL, SEND_MODE_LABEL, SOURCE_LABEL, STATUS_LABEL, VULNERABLE_LABEL,
    aiText, esc, eventTime, fmtAgo, fmtDate, fmtTime, isSynthetic, people, statusBadge, toast,
} from './util.js';

let shownSeq = null;
let history = [];

export function openReport(id) {
    state.openReportId = id;
    state.newIds.delete(id);
    shownSeq = null;
    history = [];
    const drawer = document.getElementById('drawer');
    drawer.hidden = false;
    document.getElementById('drawer-body').innerHTML = `
        <div id="d-main"></div>
        <section>
            <h3>Thêm ghi chú</h3>
            <form id="d-note-form" class="inline-form">
                <textarea name="text" maxlength="1000" required placeholder="VD: đã gọi lại, người gửi xác nhận còn 3 người trên mái"></textarea>
                <button class="btn btn-small" type="submit">Lưu ghi chú</button>
            </form>
        </section>
        <section><h3>Nhật ký</h3><div id="d-history" class="muted small">Đang tải…</div></section>
        <section><details class="raw"><summary>Dữ liệu gốc (JSON)</summary><pre id="d-raw"></pre></details></section>`;
    document.getElementById('d-note-form').addEventListener('submit', async event => {
        event.preventDefault();
        const form = event.target;
        const text = form.text.value.trim();
        if (!text) return;
        form.querySelector('button').disabled = true;
        try {
            await addNote(id, text);
            form.reset();
            toast('Đã lưu ghi chú.', 'success');
        } catch (err) {
            toast(err.message, 'error');
        } finally {
            form.querySelector('button').disabled = false;
        }
    });
    renderDrawer();
    invalidate('table');
}

export function closeDrawer() {
    state.openReportId = null;
    document.getElementById('drawer').hidden = true;
}

async function loadHistory(id) {
    try {
        const data = await api(`/api/reports/${encodeURIComponent(id)}/history`);
        if (state.openReportId !== id) return;
        history = data.events;
        renderHistory();
    } catch (err) {
        document.getElementById('d-history').textContent = 'Không tải được nhật ký: ' + err.message;
    }
}

function renderHistory() {
    const box = document.getElementById('d-history');
    if (!box) return;
    if (!history.length) { box.textContent = 'Chưa có thao tác.'; return; }
    box.className = '';
    box.innerHTML = `<ul class="timeline">${history.slice().reverse().map(e => {
        let what = EVENT_LABEL[e.kind] || e.kind;
        if (e.kind === 'status') what = `${STATUS_LABEL[e.from] || e.from || '?'} → <b>${esc(STATUS_LABEL[e.to] || e.to)}</b> (v${e.statusVersion})`;
        if (e.kind === 'received') what = 'Tiếp nhận báo cáo';
        if (e.kind === 'assign') what = e.to ? `Giao đội <b>${esc(e.note || e.to)}</b>` : 'Bỏ giao đội';
        if (e.kind === 'image') what = `Nhận ảnh hiện trường${e.note ? ` (${esc(e.note)})` : ''}`;
        if (e.kind === 'location') what = `Đặt vị trí ${esc(e.to)}${e.from ? ` (trước: ${esc(e.from)})` : ''}`;
        const who = e.actor ? esc(e.actor) : esc(SOURCE_LABEL[e.source] || e.source);
        const note = e.kind === 'assign' || e.kind === 'image' ? '' : e.note;
        return `<li class="kind-${esc(e.kind)}"><div class="when">${fmtTime(e.at)} · ${who}</div>
            <div>${what}</div>${note ? `<div class="note">${esc(note)}</div>` : ''}</li>`;
    }).join('')}</ul>`;
}

export function renderDrawer() {
    const id = state.openReportId;
    if (!id) return;
    const r = getReport(id);
    const main = document.getElementById('d-main');
    if (!r) {
        main.innerHTML = '<p class="muted">Báo cáo không còn tồn tại.</p>';
        return;
    }
    if (shownSeq === r.updatedSeq) return;
    const firstRender = shownSeq === null;
    shownSeq = r.updatedSeq;

    document.getElementById('drawer-title').textContent = r.id;
    document.getElementById('drawer-sub').innerHTML = `${statusBadge(r.status)} · nhận ${fmtAgo(eventTime(r))}${isSynthetic(r) ? ' · <b>dữ liệu mô phỏng</b>' : ''}`;
    const c = clusterFor(r.id);
    const team = r.assignedTeamId != null ? state.teamById.get(r.assignedTeamId) : null;
    const vuln = (r.vulnerableGroups || []).map(g => VULNERABLE_LABEL[g] || g).join(', ');
    const closed = CLOSED.has(r.status);
    const location = r.lat == null
        ? '<b>Không có GPS</b> — cần xác minh'
        : `<span class="mono">${Number(r.lat).toFixed(5)}, ${Number(r.lng).toFixed(5)}</span> · ${r.locationSource === 'manual' ? 'nhập tay' : 'từ thiết bị'}`;

    const actions = closed
        ? `<p class="muted small">Báo cáo đã kết thúc${r.closeReason ? ` (${esc(state.config.closeReasons?.[r.closeReason] || r.closeReason)})` : ''}; không đổi trạng thái được nữa.</p>`
        : `<div class="action-row">
            ${canMoveTo(r, 'dispatched') ? '<button class="btn btn-warning" data-d-status="dispatched">Điều phối…</button>' : ''}
            ${canMoveTo(r, 'resolved') ? '<button class="btn btn-good" data-d-status="resolved">Hoàn tất…</button>' : ''}
            <button class="btn" data-d-team>Giao đội…</button>
            <button class="btn btn-danger" data-d-status="cancelled">Đóng báo cáo…</button>
          </div>`;

    main.innerHTML = `
        <section>${actions}</section>
        ${r.imageUrl ? `<section><a href="${esc(r.imageUrl)}" target="_blank" rel="noopener"><img class="detail-image" src="${esc(r.imageUrl)}" alt="Ảnh hiện trường"></a></section>` : ''}
        <section>
            <h3>Thông tin</h3>
            <dl class="facts">
                <dt>Thời điểm gửi</dt><dd>${fmtDate(eventTime(r))}</dd>
                <dt>Server nhận lần đầu</dt><dd>${fmtTime(r.firstReceivedAt)}</dd>
                <dt>Số người cần cứu</dt><dd>${people(r)}${r.trappedCount || r.injuredCount ? ` (mắc kẹt ${r.trappedCount || 0}, bị thương ${r.injuredCount || 0})` : ''}</dd>
                <dt>Nhóm yếu thế</dt><dd>${esc(vuln) || '–'}</dd>
                <dt>Mô tả</dt><dd>${esc(r.description) || '–'}</dd>
                ${r.contactPhone ? `<dt>Liên hệ người báo</dt><dd><a href="tel:${esc(r.contactPhone)}">${esc(r.contactPhone)}</a></dd>` : ''}
                <dt>Nhận diện AI</dt><dd>${esc(aiText(r)) || '–'}</dd>
                <dt>Cách gửi</dt><dd>${esc(SEND_MODE_LABEL[r.sendMode] || r.sendMode || '–')}</dd>
                <dt>Cụm</dt><dd>${c && c.size > 1 ? `#${c.rank} · P = ${c.priority.toFixed(3)} · ${c.size} báo cáo` : 'Điểm lẻ / chưa vào cụm'}</dd>
                <dt>Đội phụ trách</dt><dd>${team ? `${esc(team.name)}${team.phone ? ` · ${esc(team.phone)}` : ''}` : '–'}</dd>
                <dt>Vị trí</dt><dd>${location}
                    <div class="action-row" style="margin-top:6px">
                        ${r.lat != null ? '<button class="btn btn-small" data-d-focus>Xem trên bản đồ</button>' : ''}
                        <button class="btn btn-small" data-d-pick>Chọn trên bản đồ</button>
                        <button class="btn btn-small" data-d-coords>Nhập tọa độ</button>
                    </div></dd>
                <dt>Phiên bản trạng thái</dt><dd>v${r.statusVersion}${r.statusUpdatedAt ? ` · cập nhật ${fmtTime(r.statusUpdatedAt)}` : ''}</dd>
            </dl>
        </section>`;
    document.getElementById('d-raw').textContent = JSON.stringify(r, null, 2);

    main.querySelectorAll('[data-d-status]').forEach(btn => btn.addEventListener('click', () => changeStatus([r.id], btn.dataset.dStatus)));
    main.querySelector('[data-d-team]')?.addEventListener('click', () => assignTeam([r.id]));
    main.querySelector('[data-d-focus]')?.addEventListener('click', () => focusReport(r.id));
    main.querySelector('[data-d-coords]')?.addEventListener('click', () => setLocation(r.id));
    main.querySelector('[data-d-pick]')?.addEventListener('click', () => pickLocation(r.id));

    loadHistory(id);
    if (firstRender) document.getElementById('drawer-body').scrollTop = 0;
}

export function pickLocation(id) {
    // Ẩn ngăn chi tiết để thấy bản đồ; mở lại sau khi chọn xong hoặc hủy.
    const drawer = document.getElementById('drawer');
    const reopen = () => { if (state.openReportId === id) drawer.hidden = false; };
    if (state.openReportId === id) drawer.hidden = true;
    startPick(id, async (lat, lng) => { await setLocation(id, lat, lng); reopen(); }, reopen);
}
