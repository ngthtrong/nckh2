// Thao tác điều phối: đổi trạng thái (một hoặc nhiều báo cáo), giao đội, ghi chú, vị trí.
// Mọi thao tác hàng loạt gửi đúng danh sách id + statusVersion mà điều phối viên đã xác nhận.
import { api, errorText } from './api.js';
import { getReport, state } from './store.js';
import { CLOSED, STATUS_LABEL, STATUS_ORDER, VULNERABLE_LABEL, esc, openDialog, toast } from './util.js';

let afterChange = () => {};
export function setAfterChange(fn) { afterChange = fn; }

const ACTION_TEXT = {
    dispatched: { title: 'Điều phối', ok: 'Điều phối', cls: 'btn-warning' },
    resolved: { title: 'Hoàn tất', ok: 'Đánh dấu đã giải quyết', cls: 'btn-good' },
    cancelled: { title: 'Đóng báo cáo', ok: 'Đóng báo cáo', cls: 'btn-danger' },
};

/** Báo cáo có thể chuyển sang `status` không (chỉ tiến; trạng thái kết thúc không đổi). */
export function canMoveTo(report, status) {
    if (!report || CLOSED.has(report.status)) return false;
    if (status === 'cancelled') return true;
    return STATUS_ORDER[status] > STATUS_ORDER[report.status];
}

function teamOptions(selected) {
    const active = state.teams.filter(t => t.active);
    return `<option value="">— Không giao đội —</option>` + active.map(t =>
        `<option value="${t.id}" ${String(selected) === String(t.id) ? 'selected' : ''}>${esc(t.name)}${t.activeAssignments ? ` · đang nhận ${t.activeAssignments}` : ''}</option>`
    ).join('');
}

function idList(reports) {
    const shown = reports.slice(0, 40).map(r => `${esc(r.id)} · ${esc(STATUS_LABEL[r.status])}`).join('<br>');
    const more = reports.length > 40 ? `<br>… và ${reports.length - 40} báo cáo khác` : '';
    return `<div class="id-list">${shown}${more}</div>`;
}

/**
 * Mở hộp thoại đổi trạng thái cho danh sách id. Báo cáo không chuyển được bị loại
 * và được liệt kê riêng để điều phối viên biết.
 */
export async function changeStatus(ids, status, { contextLabel = '' } = {}) {
    const all = ids.map(getReport).filter(Boolean);
    const targets = all.filter(r => canMoveTo(r, status));
    const skipped = all.length - targets.length;
    const text = ACTION_TEXT[status];
    if (!targets.length) {
        toast(`Không có báo cáo nào có thể chuyển sang “${STATUS_LABEL[status]}”.`, 'error');
        return false;
    }
    const reasons = Object.entries(state.config.closeReasons || {});
    const firstTeam = targets.length === 1 ? targets[0].assignedTeamId : '';
    const body = `
        <p>${contextLabel ? esc(contextLabel) + ': ' : ''}chuyển <b>${targets.length}</b> báo cáo sang <b>${esc(STATUS_LABEL[status])}</b>.
        ${skipped ? `<br><span class="muted small">Bỏ qua ${skipped} báo cáo đã ở trạng thái này hoặc đã kết thúc.</span>` : ''}</p>
        ${idList(targets)}
        ${status === 'dispatched' ? `<label class="field">Giao cho đội<select name="teamId">${teamOptions(firstTeam)}</select>
            ${state.teams.length ? '' : '<span class="hint">Chưa có đội nào — thêm ở mục “Đội cứu hộ”.</span>'}</label>` : ''}
        ${status === 'cancelled' ? `<label class="field">Lý do đóng (bắt buộc)<select name="reason" required>
            <option value="">— Chọn lý do —</option>${reasons.map(([k, v]) => `<option value="${esc(k)}">${esc(v)}</option>`).join('')}</select></label>` : ''}
        <label class="field">Ghi chú <span class="hint">(tùy chọn, lưu vào nhật ký)</span><textarea name="note" maxlength="1000"></textarea></label>
        ${status === 'resolved' || status === 'cancelled' ? '<p class="muted small">Trạng thái kết thúc không thể hoàn tác; người gửi sẽ thấy cập nhật trên app.</p>' : ''}`;

    let outcome = null;
    const ok = await openDialog({
        title: `${text.title} ${targets.length > 1 ? `${targets.length} báo cáo` : targets[0].id}`,
        body, okLabel: text.ok, okClass: text.cls,
        onSubmit: async form => {
            const data = new FormData(form);
            const payload = {
                status,
                items: targets.map(r => ({ id: r.id, statusVersion: (r.statusVersion || 1) + 1 })),
                note: (data.get('note') || '').trim() || null,
            };
            if (status === 'cancelled') {
                payload.reason = data.get('reason');
                if (!payload.reason) throw new Error('Chọn lý do đóng báo cáo');
            }
            if (data.get('teamId')) payload.teamId = Number(data.get('teamId'));
            outcome = await api('/api/reports/bulk-status', { method: 'POST', body: payload });
        },
    });
    if (!ok || !outcome) return false;
    const failures = outcome.results.filter(r => !r.ok).map(r => `${r.id}: ${errorText(r.code, r.error)}`);
    if (failures.length) {
        toast(`${outcome.ok}/${outcome.results.length} báo cáo đã chuyển sang “${STATUS_LABEL[status]}”; ${failures.length} lỗi:`, 'error', failures.slice(0, 8));
    } else {
        toast(`Đã chuyển ${outcome.ok} báo cáo sang “${STATUS_LABEL[status]}”.`, 'success');
    }
    for (const id of ids) state.checked.delete(id);
    await afterChange();
    return true;
}

export async function assignTeam(ids) {
    const targets = ids.map(getReport).filter(r => r && !CLOSED.has(r.status));
    if (!targets.length) { toast('Chỉ giao đội cho báo cáo chưa kết thúc.', 'error'); return; }
    let failures = [];
    const ok = await openDialog({
        title: `Giao đội cho ${targets.length} báo cáo`,
        body: `${idList(targets)}<label class="field">Đội<select name="teamId">${teamOptions(targets.length === 1 ? targets[0].assignedTeamId : '')}</select>
               <span class="hint">Chọn “Không giao đội” để bỏ giao.</span></label>`,
        okLabel: 'Lưu',
        onSubmit: async form => {
            const value = new FormData(form).get('teamId');
            const teamId = value ? Number(value) : null;
            failures = [];
            for (const r of targets) {
                try { await api(`/api/reports/${encodeURIComponent(r.id)}/team`, { method: 'PUT', body: { teamId } }); }
                catch (err) { failures.push(`${r.id}: ${err.message}`); }
            }
        },
    });
    if (!ok) return;
    if (failures.length) toast(`${failures.length} báo cáo chưa giao được đội:`, 'error', failures.slice(0, 8));
    else toast('Đã cập nhật đội phụ trách.', 'success');
    await afterChange();
}

export async function addNote(id, text) {
    await api(`/api/reports/${encodeURIComponent(id)}/notes`, { method: 'POST', body: { text } });
    await afterChange();
}

export async function setLocation(id, lat, lng) {
    const report = getReport(id);
    const ok = await openDialog({
        title: `Vị trí cho ${id}`,
        body: `<p class="muted small">Chỉ nhập vị trí đã xác minh (gọi lại người gửi, hỏi địa phương). Báo cáo có vị trí sẽ được đưa vào phân cụm và điều phối.</p>
            <div class="inline-form">
                <label class="field">Vĩ độ<input name="lat" type="number" step="any" min="-90" max="90" required value="${lat ?? report?.lat ?? ''}"></label>
                <label class="field">Kinh độ<input name="lng" type="number" step="any" min="-180" max="180" required value="${lng ?? report?.lng ?? ''}"></label>
            </div>
            <label class="field">Nguồn xác minh / ghi chú<textarea name="note" maxlength="1000" placeholder="VD: gọi lại số 09xx, nhà ở tổ 5 thôn Phú Sơn"></textarea></label>`,
        okLabel: 'Lưu vị trí',
        onSubmit: async form => {
            const data = new FormData(form);
            const body = { lat: Number(data.get('lat')), lng: Number(data.get('lng')), note: (data.get('note') || '').trim() || null };
            if (!Number.isFinite(body.lat) || !Number.isFinite(body.lng)) throw new Error('Nhập vĩ độ và kinh độ hợp lệ');
            await api(`/api/reports/${encodeURIComponent(id)}/location`, { method: 'PUT', body });
        },
    });
    if (ok) {
        toast(`Đã cập nhật vị trí cho ${id}.`, 'success');
        await afterChange();
    }
    return ok;
}

/** Nhập báo cáo nhận qua điện thoại/tổng đài. Trả về id báo cáo mới, hoặc null nếu hủy. */
export async function createReport() {
    let created = null;
    const groups = Object.entries(VULNERABLE_LABEL).map(([value, label]) =>
        `<label class="check"><input type="checkbox" name="vulnerableGroups" value="${esc(value)}"> ${esc(label)}</label>`).join(' ');
    const ok = await openDialog({
        title: 'Báo cáo mới (tổng đài)',
        body: `<label class="field">Tình huống (bắt buộc)<textarea name="description" maxlength="2000" required
                placeholder="VD: 2 người già mắc kẹt trên mái nhà, nước vẫn lên"></textarea></label>
            <label class="field">Số điện thoại người báo<input name="contactPhone" type="tel" maxlength="30"></label>
            <div class="inline-form">
                <label class="field">Mắc kẹt<input name="trappedCount" type="number" min="0" max="10000" value="0"></label>
                <label class="field">Bị thương<input name="injuredCount" type="number" min="0" max="10000" value="0"></label>
            </div>
            <div class="field">Nhóm yếu thế<div>${groups}</div></div>
            <div class="inline-form">
                <label class="field">Vĩ độ<input name="lat" type="number" step="any" min="-90" max="90"></label>
                <label class="field">Kinh độ<input name="lng" type="number" step="any" min="-180" max="180"></label>
            </div>
            <p class="muted small">Chưa rõ vị trí thì để trống: báo cáo vào hàng cần xác minh, có thể chọn trên bản đồ sau.</p>`,
        okLabel: 'Tạo báo cáo',
        onSubmit: async form => {
            const data = new FormData(form);
            const number = name => (data.get(name) === '' ? null : Number(data.get(name)));
            const body = {
                description: (data.get('description') || '').trim(),
                contactPhone: (data.get('contactPhone') || '').trim() || null,
                trappedCount: number('trappedCount') || 0,
                injuredCount: number('injuredCount') || 0,
                vulnerableGroups: data.getAll('vulnerableGroups'),
                lat: number('lat'),
                lng: number('lng'),
            };
            if (!body.description) throw new Error('Nhập mô tả tình huống');
            if ((body.lat === null) !== (body.lng === null)) throw new Error('Nhập đủ cả vĩ độ và kinh độ, hoặc để trống cả hai');
            created = await api('/api/reports/manual', { method: 'POST', body });
        },
    });
    if (!ok || !created) return null;
    state.reports.set(created.id, created);  // báo cáo tự nhập không tính là "báo cáo mới"
    toast(`Đã tạo báo cáo ${created.id}.`, 'success');
    await afterChange();
    return created.id;
}
