// Quản lý đội cứu hộ: thêm, sửa, ngừng/kích hoạt; xem số báo cáo đang giao.
import { api } from './api.js';
import { state } from './store.js';
import { esc, toast } from './util.js';

let editing = null;   // id đội đang sửa
let reload = async () => {};

export function initTeams(reloadTeams) {
    reload = reloadTeams;
    const dialog = document.getElementById('teams-dialog');
    document.getElementById('btn-teams').addEventListener('click', () => { editing = null; renderTeams(true); dialog.showModal(); });
    document.getElementById('teams-close').addEventListener('click', () => dialog.close());
    document.getElementById('teams-body').addEventListener('click', async event => {
        const edit = event.target.closest('[data-team-edit]');
        const toggle = event.target.closest('[data-team-toggle]');
        if (edit) { editing = Number(edit.dataset.teamEdit); renderTeams(); }
        if (event.target.closest('[data-team-cancel]')) { editing = null; renderTeams(); }
        if (toggle) {
            const team = state.teamById.get(Number(toggle.dataset.teamToggle));
            try {
                await api(`/api/teams/${team.id}`, { method: 'PATCH', body: { active: !team.active } });
                toast(`${team.active ? 'Đã ngừng' : 'Đã kích hoạt lại'} đội ${team.name}.`, 'success');
                await reload();
            } catch (err) { toast(err.message, 'error'); }
        }
    });
    document.getElementById('teams-body').addEventListener('submit', async event => {
        event.preventDefault();
        const data = new FormData(event.target);
        const members = data.get('members');
        const body = {
            name: (data.get('name') || '').trim(),
            phone: (data.get('phone') || '').trim() || null,
            members: members === '' ? null : Number(members),
            note: (data.get('note') || '').trim() || null,
        };
        try {
            if (editing) await api(`/api/teams/${editing}`, { method: 'PATCH', body });
            else await api('/api/teams', { method: 'POST', body });
            toast(editing ? 'Đã lưu thông tin đội.' : `Đã thêm đội ${body.name}.`, 'success');
            editing = null;
            await reload();
        } catch (err) {
            const box = document.getElementById('team-error');
            box.textContent = err.message;
            box.hidden = false;
        }
    });
}

export function renderTeams(force = false) {
    const body = document.getElementById('teams-body');
    if (!force && !document.getElementById('teams-dialog').open) return;
    const team = editing ? state.teamById.get(editing) : null;
    const rows = state.teams.map(t => `
        <tr class="${t.active ? '' : 'inactive'}">
            <td><b>${esc(t.name)}</b>${t.note ? `<div class="muted small">${esc(t.note)}</div>` : ''}</td>
            <td>${esc(t.phone || '–')}</td>
            <td>${t.members ?? '–'}</td>
            <td>${t.activeAssignments}</td>
            <td>${t.active ? 'Hoạt động' : 'Ngừng'}</td>
            <td class="nowrap">
                <button class="btn btn-small" data-team-edit="${t.id}">Sửa</button>
                <button class="btn btn-small" data-team-toggle="${t.id}">${t.active ? 'Ngừng' : 'Kích hoạt'}</button>
            </td>
        </tr>`).join('');
    body.innerHTML = `
        ${state.teams.length ? `<div class="table-wrap"><table class="team-table">
            <thead><tr><th>Đội</th><th>Điện thoại</th><th>Số người</th><th>Đang nhận</th><th>Trạng thái</th><th></th></tr></thead>
            <tbody>${rows}</tbody></table></div>` : '<p class="muted">Chưa có đội nào. Thêm đội để giao báo cáo khi điều phối.</p>'}
        <form class="team-form" autocomplete="off">
            <label class="field">${team ? `Sửa đội “${esc(team.name)}”` : 'Tên đội mới'}<input name="name" required maxlength="80" value="${esc(team?.name || '')}"></label>
            <label class="field">Điện thoại<input name="phone" maxlength="30" value="${esc(team?.phone || '')}"></label>
            <label class="field">Số người<input name="members" type="number" min="0" max="1000" value="${team?.members ?? ''}"></label>
            <label class="field">Ghi chú<input name="note" maxlength="1000" placeholder="Phương tiện, khu vực phụ trách" value="${esc(team?.note || '')}"></label>
            <div class="action-row">
                <button class="btn btn-primary" type="submit">${team ? 'Lưu' : 'Thêm đội'}</button>
                ${team ? '<button class="btn" type="button" data-team-cancel>Hủy</button>' : ''}
            </div>
        </form>
        <p id="team-error" class="form-error" hidden></p>`;
}
