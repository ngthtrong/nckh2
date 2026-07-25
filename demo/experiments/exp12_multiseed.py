"""Thí nghiệm 12 — Đa hạt giống: mọi số tiêu đề phải có trung bình ± lệch chuẩn.

Phản biện 2.6: toàn bộ kết quả trước đây được báo cáo trên MỘT bộ dữ liệu duy
nhất (seed = 42). Một con số đơn lẻ không cho biết nó là quy luật hay là may mắn
của một lần rút thăm. Không có thanh sai số thì không thể nói "gating tốt hơn
additive" một cách có ý nghĩa thống kê.

Ở đây ta sinh lại dữ liệu với N_SEEDS hạt giống độc lập (mỗi hạt giống cho một
bố cục nhiễu, một jitter lõi và một jitter nhóm kịch bản khác nhau) rồi báo cáo
trung bình ± lệch chuẩn cho:
  - ARI / NMI của gating và của additive (alpha = 1,0 — cấu hình MẠNH NHẤT của
    dạng cộng theo exp1A, để so sánh không bị dựng người rơm),
  - đường kính cụm (mean trên cụm >= 2 thành viên, và max),
  - số cụm, số singleton,
  - modularity.

Ngoài ra đếm tỉ lệ hạt giống mà gating THẮNG additive trên từng độ đo — đây là
phát biểu vững hơn trung bình đơn thuần (không phụ thuộc phân phối).
"""
from __future__ import annotations

import statistics as stats

from common import print_table, save_table
from data.generate import make_events
from pipeline.attributes import compute_confidence
from pipeline.clustering import modularity, run_louvain
from pipeline.config import DEFAULT_CONFIG as C
from pipeline.metrics import cluster_quality, geographic_spread, noise_handling
from pipeline.weighting import build_weight_matrix_vec, sparsify

N_SEEDS = 20
BASE_SEED = 1000


def _one_seed(seed: int) -> dict:
    events = make_events(seed=seed)
    compute_confidence(events, C.confidence)
    gt = [e.gt_cluster for e in events]

    out = {"seed": seed, "n_events": len(events)}
    for tag, mode, alpha in (("gate", "gating", None), ("add", "additive", 1.0)):
        w = build_weight_matrix_vec(events, C.weight, mode=mode, alpha=alpha)
        ws = sparsify(w, C.weight)
        lab = run_louvain(ws, C.cluster.resolution, C.cluster.random_state)
        q = cluster_quality(lab, gt)
        sp = geographic_spread(events, lab)
        nz = noise_handling(lab, gt)
        out[f"{tag}_ari"] = q["ari"]
        out[f"{tag}_nmi"] = q["nmi"]
        out[f"{tag}_mean_diam_multi"] = sp["mean_diameter_km_multi"]
        out[f"{tag}_max_diam"] = sp["max_diameter_km"]
        out[f"{tag}_n_clusters"] = sp["n_clusters"]
        out[f"{tag}_n_singletons"] = sp["n_singletons"]
        out[f"{tag}_noise_absorbed_pct"] = nz["noise_absorbed_pct"]
        out[f"{tag}_modularity"] = round(modularity(ws, lab), 4)
        if tag == "gate":
            out["gate_errors"] = _error_structure(lab, gt)
    return out


def _error_structure(labels: list[int], gt: list[int]) -> dict:
    """Nhóm GT nào bị GỘP hoặc TÁCH — giải thích tại sao sd của ARI bằng 0.

    ARI = 0,9957 lặp lại y hệt trên mọi hạt giống KHÔNG phải vì dữ liệu không
    đổi (toạ độ có jitter theo seed), mà vì cấu trúc SAI SÓT luôn giống nhau:
    đúng một cặp nhóm bị gộp — cặp S5 (gt 106/107) cách nhau 900 m, vốn được
    thiết kế làm ca đối chứng khó. Hàm này ghi lại cấu trúc đó để bài báo nêu
    nguyên nhân thay vì để một sd = 0 không giải thích.
    """
    by_gt: dict[int, set[int]] = {}
    for lab, g in zip(labels, gt):
        if g >= 0:
            by_gt.setdefault(g, set()).add(lab)
    # nhóm GT bị TÁCH: một nhãn GT rơi vào nhiều cụm
    split = sorted(g for g, labs in by_gt.items() if len(labs) > 1)
    # nhóm GT bị GỘP: một cụm chứa nhiều nhãn GT
    inv: dict[int, set[int]] = {}
    for g, labs in by_gt.items():
        for l in labs:
            inv.setdefault(l, set()).add(g)
    merged = sorted([sorted(gs) for l, gs in inv.items() if len(gs) > 1])
    return {
        "n_gt_groups_split": len(split),
        "gt_groups_split": split,
        "n_cluster_merges": len(merged),
        "merged_gt_groups": merged,
    }


def _mean_sd(values: list[float]) -> tuple[float, float]:
    m = stats.mean(values)
    sd = stats.stdev(values) if len(values) > 1 else 0.0
    return round(m, 4), round(sd, 4)


def main() -> None:
    seeds = [BASE_SEED + i for i in range(N_SEEDS)]
    per_seed = []
    for s in seeds:
        per_seed.append(_one_seed(s))
        print(f"  seed {s}: gate ARI={per_seed[-1]['gate_ari']:.4f} "
              f"add ARI={per_seed[-1]['add_ari']:.4f}")

    metrics = [
        ("ari", "cao hơn tốt"),
        ("nmi", "cao hơn tốt"),
        ("mean_diam_multi", "thấp hơn tốt"),
        ("max_diam", "thấp hơn tốt"),
        ("n_clusters", "—"),
        ("n_singletons", "—"),
        ("noise_absorbed_pct", "thấp hơn tốt"),
        ("modularity", "cao hơn tốt"),
    ]

    summary = []
    for key, direction in metrics:
        g = [r[f"gate_{key}"] for r in per_seed]
        a = [r[f"add_{key}"] for r in per_seed]
        gm, gsd = _mean_sd(g)
        am, asd = _mean_sd(a)
        # tỉ lệ hạt giống gating thắng (theo hướng tốt của độ đo)
        if direction == "cao hơn tốt":
            wins = sum(1 for x, y in zip(g, a) if x > y)
        elif direction == "thấp hơn tốt":
            wins = sum(1 for x, y in zip(g, a) if x < y)
        else:
            wins = None
        summary.append({
            "metric": key,
            "direction": direction,
            "gating_mean": gm,
            "gating_sd": gsd,
            "additive_a1_mean": am,
            "additive_a1_sd": asd,
            "gating_wins_pct": (round(100.0 * wins / len(seeds), 1)
                                if wins is not None else None),
        })

    print_table(f"Exp12 — Trung bình ± lệch chuẩn trên {N_SEEDS} hạt giống", summary)
    print("\n--- Diễn giải ---")
    print("Mọi con số tiêu đề trong bài phải được trích từ bảng này (dạng mean ± sd),")
    print("KHÔNG phải từ một lần chạy seed = 42. Cột gating_wins_pct cho phát biểu")
    print("không phụ thuộc phân phối: tỉ lệ hạt giống mà gating thắng additive")
    print("(alpha = 1,0 — cấu hình mạnh nhất của dạng cộng) trên từng độ đo.")
    print("Lưu ý: dạng cộng ở đây KHÔNG phải người rơm; alpha = 1,0 được chọn vì")
    print("exp1A cho thấy đó là cấu hình dạng cộng đạt ARI cao nhất.")

    # Vì sao sd(ARI) của gating = 0? Phải giải thích, không để con số 0 tự nói.
    merge_sigs = {}
    for r in per_seed:
        sig = "; ".join("+".join(str(g) for g in grp)
                        for grp in r["gate_errors"]["merged_gt_groups"])
        merge_sigs[sig] = merge_sigs.get(sig, 0) + 1
    n_split = sum(r["gate_errors"]["n_gt_groups_split"] for r in per_seed)
    print("\n--- Vì sao lệch chuẩn ARI của gating bằng 0? ---")
    print(f"Cấu trúc SAI SỐ giống nhau ở mọi hạt giống: tổng số nhãn GT bị xé nhỏ")
    print(f"trên cả {N_SEEDS} hạt giống = {n_split}; các nhóm GT bị gộp:")
    for sig, cnt in sorted(merge_sigs.items(), key=lambda kv: -kv[1]):
        print(f"  {sig or '(không gộp)'}: {cnt}/{N_SEEDS} hạt giống")
    print("Nghĩa là ARI không đổi KHÔNG phải vì dữ liệu không đổi (toạ độ, thời gian,")
    print("nhiễu đều sinh lại theo hạt giống) mà vì sai số duy nhất luôn là cùng một")
    print("cặp: hai nhóm S5 cách nhau 900 m được cố ý dựng để CHỈ S_context tách được.")
    print("Đây là giới hạn đã biết của cấu hình mặc định, không phải bằng chứng về")
    print("độ bền vững tuyệt đối — phải nêu đúng như vậy trong bài.")

    save_table("exp12_multiseed_per_seed.json", per_seed)
    save_table("exp12_multiseed_summary.json", summary)
    print("\n[saved] exp12_multiseed_*.json -> results/tables/")


if __name__ == "__main__":
    main()
