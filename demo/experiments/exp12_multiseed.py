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

VÒNG 17 (phản biện §8, điểm 3): trước đây mỗi hạt giống chỉ jitter TOẠ ĐỘ ĐIỂM,
nên cả 20 hạt giống dùng lại đúng một bố cục liên nhóm (cùng mức chồng lấn, cùng
spread, cùng mật độ). Khi đó sd chỉ đo nhiễu trong nhóm, không đo độ bền trước
các cấu hình khó dễ khác nhau. Nay `GEOM_JITTER` buộc mỗi hạt giống sinh lại CẢ
hình học liên nhóm (khoảng cách tâm–tâm -> mức chồng lấn hiệu dụng, spread, số
điểm mỗi nhóm).

Ngoài ra mọi độ đo được kèm CI bootstrap 95% và kiểm định Wilcoxon GHÉP CẶP
(cùng hạt giống) — `wins_pct` một mình không nói được hiệu là thật hay là nhiễu.
Nếu CI của hiệu CHỨA 0 thì kết luận đúng là "không có bằng chứng khác biệt".
"""
from __future__ import annotations

import statistics as stats

from common import bootstrap_ci, paired_test, print_table, save_table
from data.generate import make_events
from pipeline.attributes import compute_confidence
from pipeline.clustering import modularity, run_louvain
from pipeline.config import DEFAULT_CONFIG as C
from pipeline.metrics import cluster_quality, geographic_spread, noise_handling
from pipeline.weighting import build_weight_matrix_vec, sparsify

N_SEEDS = 20
BASE_SEED = 1000

# Biến thiên hình học liên nhóm theo hạt giống (±25%): đổi khoảng cách tâm–tâm của
# các cặp chồng lấn, spread nội nhóm và số điểm mỗi nhóm. Đặt > 0 là điểm khác biệt
# chính so với bản trước (chỉ jitter điểm).
GEOM_JITTER = 0.25


def _one_seed(seed: int) -> dict:
    events = make_events(seed=seed, geom_jitter=GEOM_JITTER)
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
        # quy ước hình học chính của bài (P2.2): chỉ các cụm chứa >= 1 điểm có nhãn
        spl = geographic_spread(events, lab, gt_labels=gt)
        out[f"{tag}_mean_diam_labeled"] = spl["mean_diameter_km_labeled"]
        out[f"{tag}_max_diam_labeled"] = spl["max_diameter_km_labeled"]
        out[f"{tag}_n_clusters_noise_only"] = spl["n_clusters_noise_only"]
        out[f"{tag}_max_diam"] = sp["max_diameter_km"]
        out[f"{tag}_n_clusters"] = sp["n_clusters"]
        out[f"{tag}_n_singletons"] = sp["n_singletons"]
        out[f"{tag}_noise_absorbed_pct"] = nz["noise_absorbed_pct"]
        out[f"{tag}_modularity"] = round(modularity(ws, lab), 4)
        if tag == "gate":
            out["gate_errors"] = _error_structure(lab, gt)
    return out


def _error_structure(labels: list[int], gt: list[int]) -> dict:
    """Nhóm GT nào bị GỘP hoặc TÁCH — cấu trúc sai sót, không chỉ độ lớn sai sót.

    Trên dataset vòng 17, ARI KHÔNG còn bất biến theo hạt giống (sd > 0) vì mỗi
    hạt giống sinh lại cả hình học liên nhóm. Hàm này ghi lại sai sót nào lặp lại:
    nếu cùng một cặp nhãn bị gộp ở phần lớn hạt giống thì đó là giới hạn có hệ
    thống của cấu hình mặc định (một cặp chồng lấn mà ngữ cảnh không đủ tách),
    chứ không phải nhiễu ngẫu nhiên. Bài báo phải nêu đúng cặp đó thay vì chỉ báo
    cáo một con số ARI trung bình.
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
        # quy ước hình học chính của bài (P2.2) — đặt TRƯỚC các cột gộp
        ("mean_diam_labeled", "thấp hơn tốt"),
        ("max_diam_labeled", "thấp hơn tốt"),
        ("n_clusters_noise_only", "—"),
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
        # CI bootstrap của TRUNG BÌNH mỗi phương pháp + kiểm định ghép cặp trên hiệu.
        # `paired_test` luôn tính hiệu theo chiều (gating - additive); với độ đo
        # "thấp hơn tốt" thì hiệu ÂM mới là gating tốt hơn, nên ghi rõ chiều tốt.
        g_lo, g_hi = bootstrap_ci(g)
        a_lo, a_hi = bootstrap_ci(a)
        pt = paired_test(g, a)
        summary.append({
            "metric": key,
            "direction": direction,
            "gating_mean": gm,
            "gating_sd": gsd,
            "gating_ci95_lo": g_lo,
            "gating_ci95_hi": g_hi,
            "additive_a1_mean": am,
            "additive_a1_sd": asd,
            "additive_ci95_lo": a_lo,
            "additive_ci95_hi": a_hi,
            "mean_diff_gate_minus_add": pt["mean_diff"],
            "diff_ci95_lo": pt["diff_ci_lo"],
            "diff_ci95_hi": pt["diff_ci_hi"],
            "diff_ci_contains_zero": pt["contains_zero"],
            "wilcoxon_p": pt["wilcoxon_p"],
            "gating_wins_pct": (round(100.0 * wins / len(seeds), 1)
                                if wins is not None else None),
        })

    print_table(f"Exp12 — mean ± sd + CI 95% trên {N_SEEDS} hạt giống "
                f"(geom_jitter = {GEOM_JITTER})", summary)
    print("\n--- Diễn giải ---")
    print("Mọi con số tiêu đề trong bài phải được trích từ bảng này (dạng mean ± sd")
    print("kèm CI), KHÔNG phải từ một lần chạy seed = 42. Mỗi hạt giống sinh lại CẢ")
    print(f"hình học liên nhóm (±{GEOM_JITTER:.0%} trên khoảng cách tâm–tâm, spread và")
    print("số điểm mỗi nhóm), nên sd ở đây đo độ bền trước các cấu hình khó dễ khác")
    print("nhau — không chỉ nhiễu toạ độ trong nhóm như bản trước.")
    print("Cột diff_ci_contains_zero là điều kiện phát biểu: nếu True thì kết luận")
    print("đúng là KHÔNG có bằng chứng khác biệt, bất kể gating_wins_pct bằng bao")
    print("nhiêu. Lưu ý dạng cộng KHÔNG phải người rơm: alpha = 1,0 là cấu hình dạng")
    print("cộng đạt ARI cao nhất theo exp1A.")

    # Kết luận nào được phép phát biểu? Chỉ những độ đo có CI của hiệu KHÔNG chứa 0.
    sig_rows = [r for r in summary
                if r["direction"] != "—" and not r["diff_ci_contains_zero"]]
    ns_rows = [r for r in summary
               if r["direction"] != "—" and r["diff_ci_contains_zero"]]
    print("\n--- Độ đo có khác biệt được chứng minh (CI của hiệu không chứa 0) ---")
    for r in sig_rows:
        print(f"  {r['metric']}: hiệu = {r['mean_diff_gate_minus_add']} "
              f"[{r['diff_ci95_lo']}; {r['diff_ci95_hi']}], "
              f"Wilcoxon p = {r['wilcoxon_p']}")
    print("--- Độ đo KHÔNG có bằng chứng khác biệt (phải phát biểu là không kết luận) ---")
    for r in ns_rows or []:
        print(f"  {r['metric']}: hiệu = {r['mean_diff_gate_minus_add']} "
              f"[{r['diff_ci95_lo']}; {r['diff_ci95_hi']}] chứa 0")
    if not ns_rows:
        print("  (không có)")

    # CẤU TRÚC SAI SỐ: nhãn GT nào bị gộp/xé, và có ổn định qua hạt giống hay không.
    # Bản trước khẳng định sd(ARI) = 0 vì luôn cùng một cặp bị gộp; với dataset khó
    # + geom_jitter thì sd > 0, nên ở đây ta BÁO CÁO phân bố thay vì giả định.
    merge_sigs: dict[str, int] = {}
    for r in per_seed:
        sig = "; ".join("+".join(str(g) for g in grp)
                        for grp in r["gate_errors"]["merged_gt_groups"])
        merge_sigs[sig] = merge_sigs.get(sig, 0) + 1
    n_split = sum(r["gate_errors"]["n_gt_groups_split"] for r in per_seed)
    ari_sd = next(r["gating_sd"] for r in summary if r["metric"] == "ari")
    print(f"\n--- Cấu trúc sai số của gating (sd của ARI = {ari_sd}) ---")
    print(f"Tổng số nhãn GT bị xé nhỏ trên cả {N_SEEDS} hạt giống = {n_split}.")
    print("Phân bố các cấu hình GỘP nhãn (chữ ký = các nhóm GT bị gộp vào một cụm):")
    for sig, cnt in sorted(merge_sigs.items(), key=lambda kv: -kv[1]):
        print(f"  {sig or '(không gộp)'}: {cnt}/{N_SEEDS} hạt giống")
    print("Đọc bảng này cùng sd: sai số KHÔNG còn là một cặp cố định như dataset cũ.")
    print("Cặp bị gộp thường xuyên nhất là cặp chồng lấn không gian mà ngữ cảnh chưa")
    print("tách đủ — đây là giới hạn thật của cấu hình mặc định và phải nêu trong bài,")
    print("không phải bằng chứng về độ bền vững tuyệt đối.")

    save_table("exp12_multiseed_per_seed.json", per_seed)
    save_table("exp12_multiseed_summary.json", summary)
    print("\n[saved] exp12_multiseed_*.json -> results/tables/")


if __name__ == "__main__":
    main()
