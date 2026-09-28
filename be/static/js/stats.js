// Tab thống kê: thời gian phản ứng, lưu lượng 24 giờ, khối lượng theo đội, cách gửi, lý do đóng.
import { state } from './store.js';
import { SEND_MODE_LABEL, esc, fmtMinutes } from './util.js';

let showTable = false;

function tile(label, s) {
    return `<div class="stat-tile"><div class="label">${esc(label)}</div>
        <div class="value">${s.count ? fmtMinutes(s.medianMin) : '–'}</div>
        <div class="sub">${s.count ? `p90 ${fmtMinutes(s.p90Min)} · n = ${s.count}` : 'chưa có dữ liệu'}</div></div>`;
}

function niceMax(v) {
    if (v <= 4) return 4;
    const step = Math.pow(10, Math.floor(Math.log10(v)));
    for (const m of [1, 2, 2.5, 5, 10]) if (m * step >= v) return m * step;
    return 10 * step;
}

function barPath(x, y, w, h) {
    if (h <= 0) return '';
    const r = Math.min(2, w / 2, h);
    return `M${x},${y + h}V${y + r}Q${x},${y} ${x + r},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h}Z`;
}

function hourLabel(iso) {
    return new Date(iso).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
}

function hourlyChart(hourly) {
    const W = 440, H = 170, L = 30, R = 6, T = 8, B = 22;
    const max = niceMax(Math.max(1, ...hourly.map(h => Math.max(h.received, h.resolved))));
    const plotW = W - L - R, plotH = H - T - B;
    const gw = plotW / hourly.length, bw = Math.max(2, (gw - 4) / 2);
    const y = v => T + plotH - (v / max) * plotH;
    const grid = [0, max / 2, max].map(v => `<line class="gridline" x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}"/>
        <text x="${L - 4}" y="${y(v) + 3}" text-anchor="end">${v}</text>`).join('');
    const bars = hourly.map((h, i) => {
        const x = L + i * gw + (gw - 2 * bw - 2) / 2;
        const label = i % 4 === 0 ? `<text x="${L + i * gw + gw / 2}" y="${H - 6}" text-anchor="middle">${hourLabel(h.hour)}</text>` : '';
        return `<path d="${barPath(x, y(h.received), bw, T + plotH - y(h.received))}" fill="var(--series-1)"/>
            <path d="${barPath(x + bw + 2, y(h.resolved), bw, T + plotH - y(h.resolved))}" fill="var(--series-2)"/>
            <rect class="hit" x="${L + i * gw}" y="${T}" width="${gw}" height="${plotH}" data-i="${i}"/>${label}`;
    }).join('');
    return `<div class="chart-legend">
            <span class="legend-item"><span class="swatch" style="background:var(--series-1)"></span>Tiếp nhận</span>
            <span class="legend-item"><span class="swatch" style="background:var(--series-2)"></span>Giải quyết</span>
        </div>
        <div class="chart" id="hourly-chart">
            <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Số báo cáo tiếp nhận và giải quyết theo giờ trong 24 giờ qua">
                <g class="axis">${grid}</g>${bars}
                <line x1="${L}" x2="${W - R}" y1="${T + plotH}" y2="${T + plotH}" stroke="var(--border-strong)"/>
            </svg>
            <div class="tooltip" id="hourly-tip" hidden></div>
        </div>`;
}

function hourlyTable(hourly) {
    return `<table class="mini-table"><thead><tr><th>Giờ</th><th class="num">Tiếp nhận</th><th class="num">Giải quyết</th></tr></thead><tbody>
        ${hourly.slice().reverse().map(h => `<tr><td>${hourLabel(h.hour)}</td><td class="num">${h.received}</td><td class="num">${h.resolved}</td></tr>`).join('')}
        </tbody></table>`;
}

function barTable(rows, head) {
    if (!rows.length) return '<p class="muted small">Chưa có dữ liệu.</p>';
    const max = Math.max(...rows.map(r => r[1]), 1);
    return `<table class="mini-table"><thead><tr><th>${esc(head)}</th><th></th><th class="num">Số</th></tr></thead><tbody>
        ${rows.map(([label, n]) => `<tr><td>${esc(label)}</td><td style="width:45%"><div class="inline-bar" style="width:${(100 * n / max).toFixed(1)}%"></div></td><td class="num">${n}</td></tr>`).join('')}
        </tbody></table>`;
}

export function renderStats() {
    const box = document.getElementById('stats-panel');
    const s = state.stats;
    if (!s) { box.innerHTML = '<div class="empty-panel">Đang tải thống kê…</div>'; return; }
    const r = s.response;
    const teams = s.teams.filter(t => t.active || t.activeAssignments || t.resolved);
    box.innerHTML = `<div class="stats">
        <div>
            <h4>Thời gian phản ứng (trung vị)</h4>
            <div class="stat-tiles">
                ${tile('Tiếp nhận → điều phối', r.receivedToDispatch)}
                ${tile('Điều phối → hoàn tất', r.dispatchToResolve)}
                ${tile('Tiếp nhận → hoàn tất', r.receivedToResolve)}
            </div>
            <p class="muted small">Tính từ lúc server nhận báo cáo lần đầu đến lần đổi trạng thái đầu tiên trong nhật ký.</p>
        </div>
        <div>
            <h4>24 giờ qua <button class="link-btn" id="toggle-hourly">${showTable ? 'Xem biểu đồ' : 'Xem dạng bảng'}</button></h4>
            ${showTable ? hourlyTable(s.hourly) : hourlyChart(s.hourly)}
        </div>
        <div>
            <h4>Khối lượng theo đội</h4>
            ${teams.length ? `<table class="mini-table"><thead><tr><th>Đội</th><th class="num">Đang nhận</th><th class="num">Đã xong</th></tr></thead><tbody>
                ${teams.map(t => `<tr><td>${esc(t.name)}${t.active ? '' : ' <span class="muted">(ngừng)</span>'}</td><td class="num">${t.activeAssignments}</td><td class="num">${t.resolved}</td></tr>`).join('')}
            </tbody></table>` : '<p class="muted small">Chưa có đội nào.</p>'}
        </div>
        <div><h4>Cách app gửi báo cáo</h4>
            ${barTable(Object.entries(s.sendModes).map(([k, n]) => [SEND_MODE_LABEL[k] || k, n]).sort((a, b) => b[1] - a[1]), 'Cách gửi')}</div>
        <div><h4>Lý do đóng báo cáo</h4>
            ${barTable(Object.entries(s.closeReasons).map(([k, n]) => [state.config.closeReasons?.[k] || k, n]).sort((a, b) => b[1] - a[1]), 'Lý do')}</div>
        <div><h4>Thao tác của điều phối viên</h4>
            ${barTable(s.operators.map(o => [o.actor, o.actions]), 'Điều phối viên')}</div>
        <p class="muted small">Cập nhật ${new Date(s.generatedAt).toLocaleTimeString('vi-VN')}.</p>
    </div>`;

    document.getElementById('toggle-hourly').onclick = () => { showTable = !showTable; renderStats(); };
    const chart = document.getElementById('hourly-chart');
    if (chart) {
        const tip = document.getElementById('hourly-tip');
        chart.addEventListener('mousemove', event => {
            const hit = event.target.closest('.hit');
            if (!hit) { tip.hidden = true; return; }
            const h = s.hourly[Number(hit.dataset.i)];
            const rect = chart.getBoundingClientRect();
            tip.innerHTML = `${hourLabel(h.hour)}: tiếp nhận <b>${h.received}</b> · giải quyết <b>${h.resolved}</b>`;
            tip.style.left = `${Math.min(Math.max(event.clientX - rect.left, 90), rect.width - 90)}px`;
            tip.style.top = `${event.clientY - rect.top}px`;
            tip.hidden = false;
        });
        chart.addEventListener('mouseleave', () => { tip.hidden = true; });
    }
}

export function renderResponseKpi() {
    const s = state.stats?.response?.receivedToDispatch;
    document.getElementById('kpi-response').textContent = s && s.count ? fmtMinutes(s.medianMin) : '–';
    document.getElementById('kpi-response-hint').textContent = s && s.count ? `trung vị · p90 ${fmtMinutes(s.p90Min)}` : 'trung vị (chưa có dữ liệu)';
}
