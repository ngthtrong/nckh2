// Tiện ích dùng chung: định dạng, nhãn tiếng Việt, thông báo, hộp thoại.

export const STATUS_LABEL = {
    processing: 'Chờ xử lý', dispatched: 'Đã điều phối', resolved: 'Đã giải quyết', cancelled: 'Đã đóng',
};
export const STATUS_ORDER = { processing: 0, dispatched: 1, resolved: 2, cancelled: 3 };
export const CLOSED = new Set(['resolved', 'cancelled']);
export const SEND_MODE_LABEL = {
    fullImage: 'Ảnh gốc', compressedImage: 'Ảnh nén', textOnly: 'Chỉ thông tin',
    smsFallback: 'SMS', queuedOffline: 'Gửi muộn (offline)', hotline: 'Tổng đài nhập', synthetic: 'Mô phỏng', unknown: 'Không rõ',
};
export const VULNERABLE_LABEL = {
    elderly: 'Người già', children: 'Trẻ em', pregnant: 'Phụ nữ mang thai', disabled: 'Người khuyết tật',
};
export const AI_LABEL = { high: 'Ngập cao', medium: 'Ngập trung bình', low: 'Ngập thấp', non_flood: 'Không ngập' };
export const EVENT_LABEL = {
    received: 'Tiếp nhận', status: 'Đổi trạng thái', assign: 'Giao đội', note: 'Ghi chú', location: 'Cập nhật vị trí',
    image: 'Nhận ảnh hiện trường', sms: 'Nhận thêm SMS',
};
export const SOURCE_LABEL = { app: 'app', sync: 'app (đồng bộ)', sms: 'SMS', dashboard: 'dashboard', seed: 'nạp mô phỏng' };

export function esc(value) {
    return String(value ?? '').replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
}

/** Thời điểm từ ISO (có/không múi giờ; không múi = UTC như server) hoặc epoch ms. */
export function parseTime(raw) {
    if (raw === null || raw === undefined || raw === '') return null;
    let d;
    if (typeof raw === 'number' || /^\d+$/.test(String(raw))) d = new Date(Number(raw));
    else {
        const text = String(raw);
        d = new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(text) ? text : text + 'Z');
    }
    return isNaN(d) ? null : d;
}
export function eventTime(r) {
    return parseTime(r.createdAt) || parseTime(r.firstReceivedAt) || parseTime(r.serverReceivedAt);
}
export function fmtDate(d) {
    return d ? d.toLocaleString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit', year: 'numeric' }) : '–';
}
export function fmtTime(raw) { return fmtDate(parseTime(raw)); }
export function fmtAgo(d) {
    if (!d) return '';
    const s = Math.round((Date.now() - d.getTime()) / 1000);
    if (s < 0) return 'sắp tới';
    if (s < 60) return 'vừa xong';
    if (s < 3600) return `${Math.floor(s / 60)} phút trước`;
    if (s < 86400) return `${Math.floor(s / 3600)} giờ trước`;
    return `${Math.floor(s / 86400)} ngày trước`;
}
export function fmtMinutes(min) {
    if (min === null || min === undefined) return '–';
    if (min < 60) return `${Math.round(min)} phút`;
    const h = Math.floor(min / 60), m = Math.round(min % 60);
    return m ? `${h} giờ ${m} phút` : `${h} giờ`;
}

export function people(r) {
    const p = r.payload || {};
    if (p.n_trapped !== undefined && p.n_trapped !== null) return Number(p.n_trapped);
    return (r.trappedCount || 0) + (r.injuredCount || 0);
}
export function topTag(r) {
    const tags = r.aiTags || [];
    return tags.reduce((best, t) => (!best || (t.confidence || 0) > (best.confidence || 0) ? t : best), null);
}
export function aiText(r) {
    const tag = topTag(r);
    if (tag) return `${AI_LABEL[tag.label] || tag.label} (${Math.round((tag.confidence || 0) * 100)}%)`;
    const p = r.payload || {};
    if (p.flood !== undefined && p.flood !== null) return `mức ngập ${Number(p.flood).toFixed(2)}`;
    return '';
}
export function hasLocation(r) { return r.lat !== null && r.lat !== undefined && r.lng !== null && r.lng !== undefined; }
export function isSynthetic(r) { return (r.payload || {}).source === 'synthetic'; }
export function statusBadge(status) {
    return `<span class="badge badge-${esc(status)}">${esc(STATUS_LABEL[status] || status)}</span>`;
}

// ---------------------------------------------------------------- Thông báo nổi
export function toast(message, type = '', details = []) {
    const box = document.getElementById('toasts');
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.innerHTML = esc(message) + (details.length ? `<ul>${details.map(d => `<li>${esc(d)}</li>`).join('')}</ul>` : '');
    box.appendChild(el);
    setTimeout(() => el.remove(), type === 'error' ? 9000 : 4500);
}

// ---------------------------------------------------------------- Hộp thoại dùng chung
/**
 * Mở hộp thoại xác nhận. `onSubmit(form)` trả Promise; ném Error để hiện lỗi và giữ hộp thoại.
 * Trả về Promise<boolean> (true nếu đã xác nhận thành công).
 */
export function openDialog({ title, body, okLabel = 'Xác nhận', okClass = 'btn-primary', onSubmit }) {
    const dialog = document.getElementById('dialog');
    const form = document.getElementById('dialog-form');
    const ok = document.getElementById('dialog-ok');
    const error = document.getElementById('dialog-error');
    document.getElementById('dialog-title').textContent = title;
    document.getElementById('dialog-body').innerHTML = body;
    ok.textContent = okLabel;
    ok.className = `btn ${okClass}`;
    error.hidden = true;

    return new Promise(resolve => {
        const cleanup = result => {
            form.onsubmit = null;
            document.getElementById('dialog-cancel').onclick = null;
            dialog.onclose = null;
            if (dialog.open) dialog.close();
            resolve(result);
        };
        form.onsubmit = async event => {
            event.preventDefault();
            ok.disabled = true;
            try {
                await onSubmit?.(form);
                cleanup(true);
            } catch (err) {
                error.textContent = err.message || String(err);
                error.hidden = false;
            } finally {
                ok.disabled = false;
            }
        };
        document.getElementById('dialog-cancel').onclick = () => cleanup(false);
        dialog.onclose = () => resolve(false);
        dialog.showModal();
        form.querySelector('input, select, textarea')?.focus();
    });
}

// ---------------------------------------------------------------- Lưu tùy chọn cục bộ
export function loadPref(key, fallback) {
    try {
        const raw = localStorage.getItem('rescue-dashboard:' + key);
        return raw === null ? fallback : JSON.parse(raw);
    } catch { return fallback; }
}
export function savePref(key, value) {
    try { localStorage.setItem('rescue-dashboard:' + key, JSON.stringify(value)); } catch { /* bỏ qua */ }
}
