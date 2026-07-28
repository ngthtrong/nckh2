# Loop 17 — Truy vết số liệu trong `paper/main.tex`

Mỗi hàng dưới đây ánh xạ một nhóm số thực nghiệm trong bài tới JSON nguồn và
khóa/selector tương ứng. Các năm trích dẫn, số thứ tự phương trình và cận giải
tích không phải kết quả thực nghiệm.

## Dataset và độ khó

| Số/nhóm số trong bài | JSON nguồn | Khóa hoặc selector |
|---|---|---|
| 485 tổng; 421 có nhãn; 60 noise; campaign 4; 13 sự kiện | `demo/data/dataset.json` | `meta.n_total`, `n_core`, `n_noise`, `n_campaign`, `n_gt_clusters` |
| Cỡ sự kiện 8–70; spread nguồn 120–900 m; lệch thời gian 3.5 h | `demo/data/dataset.json` | `meta.gt_event_size_min/max`, `source_blob_spread_m_min/max`, `same_location_time_gap_h` |
| Ba cặp chồng lấn có tâm 714–783 m | `demo/data/dataset.json` | `meta.spatial_overlap_pair_centroid_m.{0-1,2-3,4-5}` |
| 39 fake; 26 trong vùng; 66.7% | `demo/data/dataset.json` | `meta.n_fake`, `n_fake_in_cluster`, `frac_fake_in_cluster` |
| K-Means 0.6304; Haversine 0.4120 | `demo/results/tables/exp0_dataset_hardness.json` | `[0].geo_baselines.*_ari` |
| Bỏ context: 0.9515 → 0.7775, giảm 0.1740 | cùng file | `[0].context_ablation.ari_full_gating`, `ari_context_ablated`, `ari_drop` |
| Context sweep range 0.0706 | cùng file | `[0].tau_context_response.ari_range` |
| AUC đặc trưng đơn mạnh nhất 0.6903 | cùng file | `[0].single_feature_auc.max_single_feature_auc` |
| Năm cửa chặn đều đạt | cùng file | `[0].all_criteria_pass` và năm khóa `pass_*` |
| Gói JSON 105–111 byte | `demo/results/tables/exp10_packet_size.json` | `[0].min_bytes`, `max_bytes` |

## Kết quả phân cụm

| Số/nhóm số trong bài | JSON nguồn | Khóa hoặc selector |
|---|---|---|
| Product ARI 0.9616±0.0134, CI [0.9562,0.9675] | `demo/results/tables/exp12_multiseed_summary.json` | hàng `metric="ari"`, các khóa `gating_*` |
| Additive ARI 0.9348±0.0179, CI [0.9272,0.9426] | cùng file | hàng `metric="ari"`, các khóa `additive_*` |
| Hiệu ARI 0.0268, CI [0.0198,0.0345], p=0.000132 | cùng file | hàng `metric="ari"`, `mean_diff_gate_minus_add`, `diff_ci95_*`, `wilcoxon_p` |
| NMI và CI ở Bảng multi-seed | cùng file | hàng `metric="nmi"` |
| Đường kính trung bình 1.54/98.53 km và CI hiệu | cùng file | hàng `metric="mean_diam_labeled"` |
| Đường kính cực đại 4.44/192.27 km và CI hiệu | cùng file | hàng `metric="max_diam_labeled"` |
| Louvain/Leiden ARI 0.9515, đường kính TB 1.4985 km, K=52 | `demo/results/tables/exp4_baselines.json` | hàng `method="Louvain (gating graph)"` và `method="Leiden (gating graph)"` |
| HDBSCAN ARI 0.9508; 15 cụm có nhãn; 6.5809/79.857 km; 3 cụm noise | cùng file | hàng `method="HDBSCAN (dist=1-w gating)"` |
| K-Means tọa độ ARI 0.6304 | cùng file | hàng `method="K-Means (K=13, coords only)"` |
| Context overlap 0.9379→0.5419, giảm 0.396; ranking τ=0.9774 | `demo/results/tables/exp6_context_ablation.json` | `[0].overlap_subset_*`, `kendall_tau_ranking` |
| Sweep context 0.8809–0.9515; sigma range 0.1817; resolution range 0.1320 | `demo/results/tables/exp2_sensitivity_diagnosis.json` | hàng `sweep="tau_context"`, `"sigma_geo"`, `"resolution"` |

## Ngưỡng và Bổ đề 1

| Số/nhóm số trong bài | JSON nguồn | Khóa hoặc selector |
|---|---|---|
| Tỷ lệ cặp tại θ=0.05: product 0.1085; additive 0.9569–0.9797 | `demo/results/tables/exp13_theta_ranges.json` | `frac_pairs_above_0.05` theo `form` |
| Product: best ARI 0.9731; θ=0.39; 34 điểm dùng được; cửa sổ chuẩn hóa [0.0327,0.7531] | `demo/results/tables/exp13_theta_calibration_best.json` | hàng `form="gating"` |
| Additive α=.5: ARI 0.9768; θ=.90; cửa sổ [0.6697,0.8511]; retained [0.0057,0.0403] | cùng file | hàng `form="additive (alpha=0.5)"` |
| Additive α=1: ARI 0.9652; θ=1.34; max 3.1698 km; 37 điểm; cửa sổ [0.5011,0.8768] | cùng file | hàng `form="additive (alpha=1.0)"` |
| Product 0/38 vi phạm; additive α=.5 71/79; α=1 95/99 | `demo/results/tables/exp13_lemma1_check.json` | `n_lemma1_violations`, `n_theta_checked` theo `form` |

Giá trị 1.713 km tại `σ=700 m, θ=.05` là phép thế trực tiếp vào Bổ đề 1, không
phải ước lượng thực nghiệm.

## Ưu tiên, confidence và scaling

| Số/nhóm số trong bài | JSON nguồn | Khóa hoặc selector |
|---|---|---|
| Perturb ω ±.10: τ mean 0.9665, min 0.9276; top-3 giữ 87%; 200 lần | `demo/results/tables/exp5_ranking_stability.json` | hàng `omega_perturbation="+/-0.10"`, `mean_kendall_tau`, `min_kendall_tau`, `top3_set_preserved_pct`, `n_trials` |
| Perturb σ có τ≥0.989 | `demo/results/tables/exp5_structural_stability.json` | `kendall_tau_matched` trên mọi hàng |
| Static τ=1/drift=0; dynamic τ=0.9111/drift=0.1265 | `demo/results/tables/exp5_nref_stability.json` | hàng cuối `[41]`, các khóa `*_tau_anchor`, `*_max_abs_priority_drift` |
| Dispatch: 3 boats, 3 depots, 20 seeds, min size 2, confidence .5 | `demo/results/tables/exp7_equity_outcome.json` | `[0].config.*` |
| Product vs no-V: −14.8168 min, CI [−26.6803,−3.7257], p=.026642 | cùng file | `[0].paired_comparisons[0]` |
| Product vs additive-V: −1.4295 min, CI [−10.9079,7.8816], p=.756166 | cùng file | `[0].paired_comparisons[1]` |
| Combined confidence: AUC/CI .6919/[.6095,.7693], AP/CI .1546/[.1135,.2267], random AP .0804 | `demo/results/tables/exp8_confidence_detector.json` | `[0].marginal_detector.*` |
| `-n_corrob`: AUC .6903, AP .1680 | cùng file | `[0].single_features`, hàng `feature="-n_corrob"` |
| Conditional AUC .4212/.4680/.6234 | cùng file | `[0].conditional_by_density[*].auc` |
| Campaign 4, mean C=.9273; real mean C=.9035 | cùng file | `[0].fake_campaign`, hàng `scenario="fake_campaign"` và `"real_reports"` |
| 7,200 sự kiện: tổng 46.0644 s, dựng ma trận 33.7583 s | `demo/results/tables/exp11_scaling.json` | hàng `n_events=7200`, `total_vec_s`, `build_vec_s` |

## Tham số phương pháp

Các giá trị mặc định `σ=700`, `τ_t=45`, `(τ_F,τ_E)=(.25,.35)`,
`(β,γ)=(.5,.5)`, `θ=.05`, `k=12`, resolution 1, `ω=(.34,.33,.33)`, `s=10`,
`μ=2`, `N_ref=500` được định nghĩa duy nhất trong
`demo/pipeline/config.py`. Chúng là đặc tả phương pháp, không phải kết quả chọn
sau khi xem nhãn.
