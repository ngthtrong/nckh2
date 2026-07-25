"""Thí nghiệm 7 — Thước đo KẾT QUẢ (outcome) cho equity (phản biện 1.2).

Phản biện: exp1C mới chứng minh V_agg (nhân) *đổi* thứ hạng, CHƯA chứng minh
thứ hạng mới *tốt hơn* về mặt cứu hộ. Đây là lập luận mô tả, chưa chuẩn tắc.

Cách khắc phục (hướng (a) của phản biện): định nghĩa một metric vận hành —
"thời gian mô phỏng đến nạn nhân yếu thế" dưới chính sách điều phối THAM LAM
theo thứ hạng P — rồi so 3 chính sách ranking:
    (a) P đầy đủ  : V_agg dạng NHÂN (đề xuất)
    (b) P không V : bỏ hoàn toàn yếu tố tổn thương (omega thuần lõi)
    (c) P cộng V  : V_agg dạng CỘNG (offset)

Mô hình điều phối (đơn giản, minh bạch):
  - Có R đội ca nô, mỗi đội tốc độ VBOAT km/h, xuất phát từ một depot chung.
  - Phục vụ các cụm LẦN LƯỢT theo thứ hạng P giảm dần; mỗi đội bốc cụm kế tiếp
    trong hàng đợi khi rảnh, di chuyển từ vị trí hiện tại tới trọng tâm cụm
    (Haversine), cộng thời gian phục vụ cố định TSERVE mỗi cụm.
  - "Thời gian đến" của một cụm = thời điểm đội tới trọng tâm cụm đó.

Metric equity: thời gian-đến trung bình CÓ TRỌNG SỐ theo tổng tổn thương ΣV của
cụm (nạn nhân yếu thế càng nhiều thì việc tới trễ càng bị phạt nặng). Chính sách
tốt hơn về equity => metric này NHỎ hơn.

VỀ TÍNH TUẦN HOÀN CỦA THƯỚC ĐO (phản biện 1.2b): không tồn tại thước đo trung
lập tuyệt đối ở đây, nên ta báo cáo CẢ BA và nói rõ thiên vị của từng cái thay vì
chọn cái có lợi rồi biện minh sau:
  1. `time_to_vulnerable_min`  — trọng số ΣV thuần. THIÊN VỊ dạng CỘNG: dạng cộng
     tối ưu đúng hàm mục tiêu này (offset phẳng theo ΣV).
  2. `harm_weighted_time_min`  — trọng số ΣV × core. THIÊN VỊ dạng NHÂN: định
     nghĩa 'thiệt hại' là tương tác yếu-thế × nghiêm-trọng, tức chính giả thuyết
     mà dạng nhân mã hoá. Đây là thước đo bản trước chọn, nên không thể dùng nó
     làm bằng chứng độc lập.
  3. `severe_reach_time_min`   — trọng số 1[F_max > 0,7], KHÔNG chứa V và KHÔNG
     chứa core. Định nghĩa trước bằng ngưỡng vận hành (ngập > 0,7 là nguy hiểm
     tới tính mạng) nên không thiên vị dạng nào. Đây là thước đo trọng tài.

Trung thực: nếu (a) KHÔNG nhỏ hơn (b)/(c) trên thước đo trọng tài, ta báo cáo
đúng như vậy và đóng khung V_agg là *lựa chọn giá trị chuẩn tắc* (triage ưu tiên
người dễ tổn thương) thay vì tuyên bố tối ưu khách quan.
"""
from __future__ import annotations

import heapq

from common import prepared_events, print_table, save_table
from pipeline.config import DEFAULT_CONFIG as C
from pipeline.clustering import run_louvain
from pipeline.priority import score_clusters
from pipeline.attributes import haversine_m
from pipeline.weighting import build_weight_matrix, sparsify

# Tham số mô phỏng điều phối (đặt theo miền, minh bạch)
N_BOATS = 3          # số đội ca nô
V_BOAT_KMH = 30.0    # tốc độ ca nô (km/h) — cỡ ca nô cứu hộ
T_SERVE_MIN = 15.0   # thời gian phục vụ mỗi cụm (phút)

# Ngưỡng "ngập nặng" cho metric trung lập thứ ba. Đặt trước khi xem kết quả;
# đây là tiêu chí vận hành (ngập tới mái, phải cứu hộ bằng ca nô), KHÔNG lấy từ
# bất kỳ thành phần nào của công thức P.
SEVERE_FLOOD_THRESHOLD = 0.7


def _depot(scores):
    """Depot = trọng tâm hình học của tất cả các cụm (trung tâm chiến dịch)."""
    lat = sum(s.center_lat for s in scores) / len(scores)
    lng = sum(s.center_lng for s in scores) / len(scores)
    return lat, lng


def _simulate_arrival_times(ordered, depot):
    """Mô phỏng R đội phục vụ các cụm theo thứ tự `ordered`.

    Trả về dict {cluster_id: arrival_time_min}.
    Heap các đội: (thời điểm rảnh, lat hiện tại, lng hiện tại).
    """
    dlat, dlng = depot
    boats = [(0.0, dlat, dlng) for _ in range(N_BOATS)]
    heapq.heapify(boats)
    arrival = {}
    for s in ordered:
        free_t, blat, blng = heapq.heappop(boats)
        dist_km = haversine_m(blat, blng, s.center_lat, s.center_lng) / 1000.0
        travel_min = (dist_km / V_BOAT_KMH) * 60.0
        arr = free_t + travel_min
        arrival[s.cluster_id] = arr
        # đội bận tới arr + phục vụ, và đứng tại trọng tâm cụm vừa phục vụ
        heapq.heappush(boats, (arr + T_SERVE_MIN, s.center_lat, s.center_lng))
    return arrival


def _vulnerable_weight(score, events_by_cluster):
    """Tổng tổn thương ΣV của cụm (trọng số cho metric equity thuần)."""
    return sum(e.vulnerability for e in events_by_cluster.get(score.cluster_id, []))


def _harm_weight(score, events_by_cluster):
    """Trọng số THIỆT HẠI = ΣV * mức nghiêm trọng lõi (đã chuẩn hóa).

    Đây là điểm mấu chốt để phân biệt dạng nhân với dạng cộng: một nạn nhân
    yếu thế trong cụm ngập nặng/khẩn cấp cao chịu rủi ro sinh tồn lớn hơn cùng
    nạn nhân đó trong cụm nhẹ. Dạng NHÂN được thiết kế đúng để ưu tiên giao của
    'yếu thế' VÀ 'nghiêm trọng'; dạng cộng chỉ thưởng một offset phẳng theo ΣV
    nên không nắm được tương tác này. Trọng số = ΣV * core (core in [0,1])."""
    v = sum(e.vulnerability for e in events_by_cluster.get(score.cluster_id, []))
    return v * score.core


def _severe_vulnerable_weight(score, events_by_cluster):
    """Trọng số TRUNG LẬP, đăng ký trước: ΣV của các cụm ngập nặng (F_max > 0,7).

    Vì sao cần metric thứ ba: metric ΣV-thuần (`_vulnerable_weight`) tối ưu đúng
    cho dạng CỘNG, còn metric thiệt-hại (`_harm_weight`) dùng chính `score.core`
    — đại lượng nằm trong công thức P đang được đánh giá — nên có lợi cho dạng
    NHÂN. Chấm điểm bằng bất kỳ metric nào trong hai cái đó rồi tuyên bố người
    thắng là lập luận vòng tròn (phản biện 1.2).

    Metric này dùng một tiêu chí NGOÀI công thức P: ngưỡng ngập nặng F > 0,7 là
    tiêu chí phân loại vận hành (nhà cửa ngập tới mái, cần cứu hộ đường thuỷ),
    xác định trước khi xem kết quả và không phụ thuộc omega, V_agg hay core.
    Trọng số = ΣV nếu cụm ngập nặng, 0 nếu không: "tới muộn ở nơi có người yếu
    thế TRONG vùng ngập nặng" là thiệt hại ta thực sự muốn giảm.
    """
    mem = events_by_cluster.get(score.cluster_id, [])
    if not mem:
        return 0.0
    f_max = max(e.flood for e in mem)
    if f_max <= SEVERE_FLOOD_THRESHOLD:
        return 0.0
    return sum(e.vulnerability for e in mem)


def _weighted_time(scores, arrival, weight_fn, events_by_cluster):
    """Thời gian-đến trung bình có trọng số. Nhỏ = tốt.

    scores dùng để lấy TRỌNG SỐ (cố định theo cụm), arrival lấy từ chính sách
    đang đánh giá. Tách bạch để mọi chính sách được chấm bằng cùng bộ trọng số."""
    num = 0.0
    den = 0.0
    for s in scores:
        w = weight_fn(s, events_by_cluster)
        if w <= 0:
            continue
        num += w * arrival[s.cluster_id]
        den += w
    return (num / den) if den > 0 else 0.0


def main():
    events = prepared_events()
    w = build_weight_matrix(events, C.weight, mode="gating")
    ws = sparsify(w, C.weight)
    lab = run_louvain(ws, C.cluster.resolution, C.cluster.random_state)

    events_by_cluster = {}
    for e, l in zip(events, lab):
        events_by_cluster.setdefault(l, []).append(e)

    # Ba chính sách ranking (cùng tập cụm & trọng tâm, chỉ khác cách tính P)
    sc_full = score_clusters(events, lab, C.priority, normalize_v=True)   # (a) V nhân
    sc_add = score_clusters(events, lab, C.priority, normalize_v=False)   # (c) V cộng

    # (b) P không V: đặt V_agg=1 bằng cách chấm điểm rồi sắp theo `core` (bỏ V)
    sc_noV = sorted(sc_full, key=lambda s: s.core, reverse=True)

    depot = _depot(sc_full)

    policies = {
        "P_full_multiplicative": sc_full,
        "P_no_vulnerability": sc_noV,
        "P_additive_V": sorted(sc_add, key=lambda s: s.priority, reverse=True),
    }

    rows = []
    twv_by_policy = {}
    harm_by_policy = {}
    severe_by_policy = {}
    for name, ordered in policies.items():
        arrival = _simulate_arrival_times(ordered, depot)
        # metric 1: thời gian đến yếu thế, trọng số ΣV thuần (thiên vị dạng CỘNG)
        twv = _weighted_time(sc_full, arrival, _vulnerable_weight, events_by_cluster)
        # metric 2: trọng số THIỆT HẠI = ΣV * core (thiên vị dạng NHÂN vì dùng core)
        harm = _weighted_time(sc_full, arrival, _harm_weight, events_by_cluster)
        # metric 3: TRUNG LẬP — ΣV trong cụm ngập nặng F>0,7 (ngoài công thức P)
        severe = _weighted_time(sc_full, arrival, _severe_vulnerable_weight, events_by_cluster)
        # thời gian-đến TB không trọng số (để đối chiếu công bằng tổng thể)
        mean_arr = sum(arrival.values()) / len(arrival)
        rows.append({
            "policy": name,
            "time_to_vulnerable_min": round(twv, 2),
            "harm_weighted_time_min": round(harm, 2),
            "severe_flood_vulnerable_time_min": round(severe, 2),
            "mean_arrival_all_min": round(mean_arr, 2),
        })
        twv_by_policy[name] = twv
        harm_by_policy[name] = harm
        severe_by_policy[name] = severe

    def _impr(metric, base_key="P_no_vulnerability", full_key="P_full_multiplicative"):
        base, full = metric[base_key], metric[full_key]
        return round(100 * (base - full) / base, 2) if base else 0.0

    impr_twv = _impr(twv_by_policy)
    impr_harm = _impr(harm_by_policy)
    impr_severe = _impr(severe_by_policy)
    # so với chính sách dạng CỘNG (đối thủ thật, không phải 'bỏ V')
    impr_severe_vs_add = _impr(severe_by_policy, base_key="P_additive_V")

    print_table("Exp7 — Outcome metric cho equity (thời gian đến nạn nhân yếu thế)", rows)
    print(f"\nCấu hình: {N_BOATS} ca nô, {V_BOAT_KMH} km/h, phục vụ {T_SERVE_MIN} phút/cụm.")
    print("\n--- Ba metric, và THIÊN VỊ đã biết của từng cái (khai báo trước) ---")
    print(f"[1. ΣV thuần   ] V nhân giảm {impr_twv}% so với bỏ V. "
          "THIÊN VỊ dạng CỘNG: trọng số phẳng theo ΣV chính là cái dạng cộng tối ưu hoá.")
    print(f"[2. ΣV × core  ] V nhân giảm {impr_harm}% so với bỏ V. "
          "THIÊN VỊ dạng NHÂN: dùng lại `core` của chính công thức P (lập luận vòng).")
    print(f"[3. ΣV | F>0,7 ] V nhân giảm {impr_severe}% so với bỏ V; "
          f"{impr_severe_vs_add}% so với dạng CỘNG.")
    print("     TRUNG LẬP: ngưỡng ngập F > 0,7 là tiêu chí ngoài công thức P, không dùng")
    print("     core, không dùng omega. Đây là metric duy nhất trong ba cái nên dùng để")
    print("     KẾT LUẬN; hai metric đầu chỉ để cho thấy kết quả phụ thuộc cách chọn metric.")
    if impr_severe_vs_add <= 0:
        print("\nKẾT LUẬN TRUNG THỰC: trên metric trung lập, dạng NHÂN KHÔNG tốt hơn dạng CỘNG.")
        print("Vậy V_agg dạng nhân phải được đóng khung là LỰA CHỌN GIÁ TRỊ CHUẨN TẮC")
        print("(triage ưu tiên người dễ tổn thương), không phải tối ưu khách quan đã chứng minh.")
    else:
        print(f"\nTrên metric trung lập, dạng NHÂN tốt hơn dạng CỘNG {impr_severe_vs_add}%.")

    out = {
        "config": {
            "n_boats": N_BOATS,
            "v_boat_kmh": V_BOAT_KMH,
            "t_serve_min": T_SERVE_MIN,
        },
        "policies": rows,
        "improvement_pct_vulnerable_full_vs_noV": impr_twv,
        "improvement_pct_harm_full_vs_noV": impr_harm,
        "improvement_pct_severe_full_vs_noV": impr_severe,
        "improvement_pct_severe_full_vs_additive": impr_severe_vs_add,
        "metric_bias_note": {
            "time_to_vulnerable_min": "thiên vị dạng CỘNG (trọng số phẳng theo ΣV)",
            "harm_weighted_time_min": "thiên vị dạng NHÂN (dùng lại core của P)",
            "severe_flood_vulnerable_time_min": "TRUNG LẬP (ngưỡng F>0,7 ngoài công thức P)",
        },
        "primary_metric": "severe_flood_vulnerable_time_min",
    }
    save_table("exp7_equity_outcome.json", [out])
    print("\n[saved] exp7_equity_outcome.json -> results/tables/")


if __name__ == "__main__":
    main()
