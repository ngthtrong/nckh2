# Phân tích RQ — bằng chứng đã lưu, không chạy lại campaign

Handoff P01/P02 đã đọc; giữ LR/runtime và data-scope. HEAD/dirty baseline ../run-baseline; source-hashes.json chốt input, protocol.json khóa unit/family/bootstrap/tolerance.

RQ1 hỏi ưu thế Product so với Additive độc lập; calibration20run, test40run041–080, development tách theo notebook. Không dùng test để chọn lại. RQ2/3 Candidate4.1 có development1000…, calibration2000…, test3000–3039, xem manifest/notebook gốc; không trộn với Generator3.0. Nhãn sự kiện, latent benefit/harm và mapping copy là evaluator-only; không được đưa vào inference.

| Claim | Kết luận | Δ cải thiện | CI95% | Holm p |
|---|---|---:|---|---:|
| RQ1-superiority | NOT_ESTABLISHED | -0.011843 | -0.022569038835731164;-0.0023996203485349586 | 0.25602277954717423 |
| RQ1-density | NOT_ESTABLISHED | 0.009890 | -0.0010047504945361167;0.020821217403933685 | 0.25602277954717423 |
| RQ1-copy5 | NOT_SUPPORTED | -0.610797 | -0.6317899170802675;-0.5880567073734004 |  |
| RQ2-alignment-legacy | NOT_ESTABLISHED | 0.012118 | -0.012156208756437498;0.03771246816868746 | 0.5881899675797937 |
| RQ2-alignment-random | NOT_ESTABLISHED | -0.009433 | -0.050301339091187496;0.03229436350506246 | 1.0 |
| RQ3-nearest-latent_harm | ADVERSE_COMPARISON | -69.884639 | -95.7691353756396;-45.03264847447709 | 4.091609844181221e-05 |
| RQ3-nearest-deadline_miss_rate | ADVERSE_COMPARISON | -0.177083 | -0.20833333333333331;-0.14479166666666665 | 1.17452841440164e-06 |

RQ1 Product/Additive ARI .9072205/.9190637, Δ−.0118432; 9thắng/19hòa/12thua, rawp.0987/Holm.2560. CI percentile chưa hiệu chỉnh không cùng kiểm định với Wilcoxon/Holm; không chọn phép có lợi, p>.05 không chứng minh tương đương. Matched-density retained fraction .03011/.03021, degree9.90/9.94; Leiden .9164883. Fake absorption/rejection0 nhưng false destinations16.49%, không gọi chống tin giả thành công. Stress primary/replication kiểm riêng300bootstrap rows/bundle; copy2x tăng nhẹ/copy5x giảm mạnh, không xác định threshold collapse. Cơ chế quantile/top-k là interpretation, chưa isolated.

RQ2 oracle grouping: revised NDCG.666889741, random.6763, legacy.65477; không chứng minh superiority/general benefit. Exact-copy2/5/10x score drift0 ở grouping cố định hỗ trợ bất biến hẹp. Tăng N/V và coordinated high-confidence attacks thất bại; boundedness không bảo đảm nguồn thật hoặc graph robustness. 21config×40seed sensitivity có mean span<.01; không validate dispatch constants.

RQ3: từ CSV raw, trung bình ba resource conditions theo seed trước paired inference; n40,14endpoint mỗi fixed contrast. Revised harm tăng14.34vslegacy, trễ hạn giảm1.875đpt nhưng không significant sau Holm. Nearest-first có harm/trễ thấp hơn; Δ oriented−69.8846/−.1770833. Product worse than matched-density Additive under fixed revised score (harm Holm.000168). Không gọi harm mô phỏng là số người thực. Cost/travel/scheduling mismatch là possible mechanism, chưa causal diagnosis.

## Sai lệch và phạm vi replay

- Original verifier base FAILED do CSV benchmark_test_40runs thiếu final LF; bytes khác historical commit, toàn bộ400records/fields bằng nhau. Không sửa source/manifest. verify_stress.py dùng adapter symlink src→thucnghiem, giữ historical git path, chứng minh record equality rồi gọi hàm stress chỉ đọc. Đây là stress replay có bounded base disposition, không full verifier PASS.
- RQ2 còn8discrepancies:3rawp Spearman (legacy/simple_linear/urgency_only) và5Holm liên quan. Đúng NumPy2.0.2/pandas2.2.2/SciPy1.16.3 cho cùng kết quả replay như env mới, nên không đổ lỗi phiên bản. CSV %.10g đã làm tròn có thể tác động tie ranks, chưa cô lập; không khôi phục độ chính xác bị mất bằng số tưởng tượng. Giữ cả original và replay. NDCG conclusion không đổi.
- Script exit0 chỉ nghĩa chạy xong, không chứng nhận mọi số khớp. validation.txt và discrepancies.json ghi coverage/thất bại cụ thể. RQ3 env pin theo provenance; tolerances tuyệt đối/relative, p dùng abs1e-12 để không che sai số ở p nhỏ.

Chưa tính lại clustering/predictions hoặc validate real-world labels. Không sửa historical CSV/notebook/checkpoint/model/config.

Phạm vi stress chính xác: mỗi bundle có 300 hàng hiệu ứng, gồm 288 CI bootstrap không rỗng được replay và 12 hàng n=0 được kiểm tra giữ trống. Tổng hai bundle: 576 CI tính lại và 24 hàng trống được kiểm.
