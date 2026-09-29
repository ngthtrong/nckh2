// Tài khoản: đổi mật khẩu của chính mình; quản trị viên thêm, sửa, khóa, đặt lại mật khẩu.
import { api } from './api.js';
import { state } from './store.js';
import { esc, fmtTime, openDialog, toast } from './util.js';

const ROLE_LABEL = { admin: 'Quản trị viên', operator: 'Điều phối viên' };
let operators = [];

export function isAdmin() { return state.session?.role === 'admin'; }

/** Đổi mật khẩu. ``forced``: tài khoản đang dùng mật khẩu tạm, phải đổi mới được dùng tiếp. */
export function changePassword({ forced = false } = {}) {
    return openDialog({
        title: forced ? 'Đặt mật khẩu mới' : 'Đổi mật khẩu',
        body: `${forced ? '<p>Tài khoản đang dùng mật khẩu tạm do quản trị viên cấp. Đặt mật khẩu của riêng bạn để tiếp tục.</p>' : ''}
            <label class="field">Mật khẩu hiện tại<input name="current" type="password" autocomplete="current-password" required></label>
            <label class="field">Mật khẩu mới <span class="hint">(ít nhất 8 ký tự)</span><input name="next" type="password" autocomplete="new-password" minlength="8" maxlength="200" required></label>
            <label class="field">Nhập lại mật khẩu mới<input name="again" type="password" autocomplete="new-password" required></label>
            <p class="muted small">Các phiên đăng nhập khác của tài khoản này sẽ bị đăng xuất.</p>`,
        okLabel: 'Lưu mật khẩu',
        onSubmit: async form => {
            const data = new FormData(form);
            if (data.get('next') !== data.get('again')) throw new Error('Hai lần nhập mật khẩu mới không khớp');
            await api('/api/auth/password', {
                method: 'POST', body: { currentPassword: data.get('current'), newPassword: data.get('next') },
            });
            if (state.session) state.session.mustChangePassword = false;
            toast('Đã đổi mật khẩu.', 'success');
        },
    });
}

export function initAccounts() {
    const dialog = document.getElementById('operators-dialog');
    document.getElementById('btn-operators').addEventListener('click', async () => {
        await loadOperators();
        dialog.showModal();
    });
    document.getElementById('operators-close').addEventListener('click', () => dialog.close());
    const body = document.getElementById('operators-body');
    body.addEventListener('click', async event => {
        const button = event.target.closest('[data-op]');
        if (!button) return;
        const op = operators.find(o => o.id === Number(button.dataset.id));
        if (!op) return;
        if (button.dataset.op === 'edit') await editOperator(op);
        if (button.dataset.op === 'reset') await resetPassword(op);
        if (button.dataset.op === 'toggle') await patchOperator(op, { active: !op.active },
            `${op.active ? 'Đã khóa' : 'Đã mở khóa'} tài khoản ${op.username}.`);
    });
    body.addEventListener('submit', async event => {
        event.preventDefault();
        const data = new FormData(event.target);
        const payload = {
            username: (data.get('username') || '').trim().toLowerCase(),
            displayName: (data.get('displayName') || '').trim(),
            password: data.get('password'),
            role: data.get('role'),
        };
        try {
            await api('/api/operators', { method: 'POST', body: payload });
            toast(`Đã tạo tài khoản ${payload.username}. Người dùng phải đổi mật khẩu khi đăng nhập lần đầu.`, 'success');
            await loadOperators();
        } catch (err) {
            const box = document.getElementById('operator-error');
            box.textContent = err.message;
            box.hidden = false;
        }
    });
}

async function loadOperators() {
    try {
        operators = (await api('/api/operators')).operators;
    } catch (err) {
        toast(err.message, 'error');
    }
    renderOperators();
}

async function patchOperator(op, body, message) {
    try {
        await api(`/api/operators/${op.id}`, { method: 'PATCH', body });
        toast(message, 'success');
        await loadOperators();
        return true;
    } catch (err) {
        toast(err.message, 'error');
        return false;
    }
}

function editOperator(op) {
    return openDialog({
        title: `Sửa tài khoản ${op.username}`,
        body: `<label class="field">Tên hiển thị <span class="hint">(ghi vào nhật ký thao tác)</span>
                <input name="displayName" required maxlength="60" value="${esc(op.displayName)}"></label>
            <label class="field">Vai trò<select name="role">${Object.entries(ROLE_LABEL).map(([k, v]) =>
                `<option value="${k}" ${op.role === k ? 'selected' : ''}>${esc(v)}</option>`).join('')}</select></label>`,
        okLabel: 'Lưu',
        onSubmit: async form => {
            const data = new FormData(form);
            await api(`/api/operators/${op.id}`, {
                method: 'PATCH', body: { displayName: data.get('displayName').trim(), role: data.get('role') },
            });
            toast(`Đã lưu tài khoản ${op.username}.`, 'success');
            await loadOperators();
        },
    });
}

function resetPassword(op) {
    return openDialog({
        title: `Đặt lại mật khẩu cho ${op.username}`,
        body: `<p>Người dùng bị đăng xuất khỏi mọi máy và phải đổi mật khẩu tạm này ở lần đăng nhập sau.</p>
            <label class="field">Mật khẩu tạm <span class="hint">(ít nhất 8 ký tự; báo riêng cho người dùng)</span>
                <input name="password" type="text" minlength="8" maxlength="200" required autocomplete="off"></label>`,
        okLabel: 'Đặt lại',
        okClass: 'btn-warning',
        onSubmit: async form => {
            await api(`/api/operators/${op.id}`, { method: 'PATCH', body: { password: new FormData(form).get('password') } });
            toast(`Đã đặt lại mật khẩu cho ${op.username}.`, 'success');
            await loadOperators();
        },
    });
}

function renderOperators() {
    const rows = operators.map(o => `
        <tr class="${o.active ? '' : 'inactive'}">
            <td><b>${esc(o.displayName)}</b><div class="muted small mono">${esc(o.username)}</div></td>
            <td>${esc(ROLE_LABEL[o.role] || o.role)}</td>
            <td>${o.active ? (o.mustChangePassword ? 'Chờ đổi mật khẩu' : 'Hoạt động') : 'Đã khóa'}</td>
            <td>${o.lastLoginAt ? fmtTime(o.lastLoginAt) : '–'}</td>
            <td class="nowrap">
                <button class="btn btn-small" data-op="edit" data-id="${o.id}">Sửa</button>
                <button class="btn btn-small" data-op="reset" data-id="${o.id}">Đặt lại mật khẩu</button>
                ${o.id === state.session?.operatorId ? '' : `<button class="btn btn-small" data-op="toggle" data-id="${o.id}">${o.active ? 'Khóa' : 'Mở khóa'}</button>`}
            </td>
        </tr>`).join('');
    document.getElementById('operators-body').innerHTML = `
        <div class="table-wrap"><table class="team-table">
            <thead><tr><th>Người dùng</th><th>Vai trò</th><th>Trạng thái</th><th>Đăng nhập gần nhất</th><th></th></tr></thead>
            <tbody>${rows}</tbody></table></div>
        <form class="team-form operator-form" autocomplete="off">
            <label class="field">Tên đăng nhập<input name="username" required minlength="3" maxlength="32" pattern="[a-z0-9][a-z0-9._\\-]{2,31}" placeholder="vd: nguyenvana"></label>
            <label class="field">Tên hiển thị<input name="displayName" required maxlength="60" placeholder="Nguyễn Văn A — Trực ban xã"></label>
            <label class="field">Mật khẩu tạm<input name="password" type="text" required minlength="8" maxlength="200"></label>
            <label class="field">Vai trò<select name="role">${Object.entries(ROLE_LABEL).map(([k, v]) =>
                `<option value="${k}" ${k === 'operator' ? 'selected' : ''}>${esc(v)}</option>`).join('')}</select></label>
            <div class="action-row"><button class="btn btn-primary" type="submit">Tạo tài khoản</button></div>
        </form>
        <p class="muted small">Tên đăng nhập: chữ thường không dấu, số, “.”, “_”, “-”. Quản trị viên được quản lý tài khoản và tải sao lưu.</p>
        <p id="operator-error" class="form-error" hidden></p>`;
}
