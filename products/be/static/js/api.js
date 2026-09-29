// Gọi API cùng origin; cookie phiên do server đặt (HttpOnly).

export class ApiError extends Error {
    constructor(status, code, message) {
        super(message || code || `HTTP ${status}`);
        this.status = status;
        this.code = code;
    }
}

const ERROR_TEXT = {
    INVALID_STATUS_VERSION: 'Báo cáo vừa được người khác cập nhật; tải lại và thử lại',
    INVALID_STATUS_TRANSITION: 'Không thể chuyển sang trạng thái này',
    REPORT_NOT_FOUND: 'Không tìm thấy báo cáo',
    TEAM_NOT_FOUND: 'Không tìm thấy đội',
    TEAM_INACTIVE: 'Đội đang ngừng hoạt động',
    TEAM_NAME_TAKEN: 'Tên đội đã tồn tại',
    REPORT_CLOSED: 'Báo cáo đã kết thúc',
    WIPE_DISABLED: 'Chức năng xóa dữ liệu đang tắt',
    UNAUTHENTICATED: 'Phiên đăng nhập đã hết hạn',
    FORBIDDEN: 'Chỉ quản trị viên được thực hiện thao tác này',
};
export function errorText(code, fallback) { return ERROR_TEXT[code] || fallback || code; }

let onUnauthorized = () => {};
export function setUnauthorizedHandler(fn) { onUnauthorized = fn; }

export async function api(path, { method = 'GET', body, headers = {}, raw = false } = {}) {
    const init = { method, headers: { ...headers }, credentials: 'same-origin' };
    if (body !== undefined) {
        init.headers['Content-Type'] = 'application/json';
        init.body = JSON.stringify(body);
    }
    const res = await fetch(path, init);
    if (res.status === 401 && !path.startsWith('/api/auth/')) {
        onUnauthorized();
        throw new ApiError(401, 'UNAUTHENTICATED', ERROR_TEXT.UNAUTHENTICATED);
    }
    if (res.status === 304) return { notModified: true, headers: res.headers };
    if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const detail = data.detail || {};
        const code = typeof detail === 'string' ? detail : detail.code;
        const message = typeof detail === 'string' ? detail : detail.error;
        throw new ApiError(res.status, code, errorText(code, message || res.statusText));
    }
    if (raw) return res;
    return res.json();
}
