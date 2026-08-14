
Để điền Table 3, cần chạy một thực nghiệm mới: “RQ2 parameter sensitivity”. Không cần chạy lại RQ1 clustering, vì toàn bộ tham số trong Table 3 thuộc \(Q_i\) và priority score \(P_k\), không tác động đến đồ thị clustering. Metric chính phải là NDCG@5, không phải ARI.

## 1. Dữ liệu và cấu hình phải dùng

Chạy trên đúng artifact RQ2 hiện tại:

- Candidate generator: `4.1.0`
- Test seeds: `3000–3039`
- Số test runs: 40
- Bundle SHA-256 bắt buộc:
  ```text
  a7c7a3f7ea63e57f1d98bd42f21c02aa04a69eaa37c824584a2be65f00f2d7e1
  ```
- Source snapshot:
  ```text
  a6be3e988dad1aa442c8c8e158c2bba96b2b7fb9
  ```
- Baseline mean NDCG@5 phải tái lập:
  ```text
  0.666889741
  ```

Để điền Table 3, cần chạy một thực nghiệm mới: “RQ2 parameter sensitivity”. Không cần chạy lại RQ1 clustering, vì toàn bộ tham số trong Table 3 thuộc \(Q_i\) và priority score \(P_k\), không tác động đến đồ thị clustering. Metric chính phải là NDCG@5, không phải ARI.

## 1. Dữ liệu và cấu hình phải dùng

Chạy trên đúng artifact RQ2 hiện tại:

- Candidate generator: `4.1.0`
- Test seeds: `3000–3039`
- Số test runs: 40
- Bundle SHA-256 bắt buộc:
  ```text
  a7c7a3f7ea63e57f1d98bd42f21c02aa04a69eaa37c824584a2be65f00f2d7e1
  ```
- Source snapshot:
  ```text
  a6be3e988dad1aa442c8c8e158c2bba96b2b7fb9
  ```
- Baseline mean NDCG@5 phải tái lập:
  ```text
  0.666889741
  ```

Source Candidate 4.1 đã bị xóa khỏi branch hiện tại nhưng vẫn khôi phục được từ commit trên. Notebook nên checkout đúng commit, tái sinh candidate bundle và dừng nếu SHA không khớp.

Không dùng bundle RQ1 generator 3.0.0 để điền bảng này, vì như vậy Table 3 sẽ không còn giải thích kết quả RQ2/RQ3 trong bài.

## 2. Thực nghiệm cần chạy

Nên tạo notebook riêng:

```text
RQ2_Parameter_Sensitivity_Colab.ipynb
```

hoặc bổ sung một section độc lập vào `RQ2_Priority_Robustness_Colab.ipynb`.

Thiết kế là one-at-a-time:

1. Chỉ thay đổi một tham số.
2. Giữ nguyên toàn bộ tham số khác.
3. Chạy lại ranking trên 40 test seeds.
4. Tính NDCG@5 cho từng seed.
5. Tính mean NDCG@5 của từng mức tham số.
6. Lấy min–max của các mean để điền `Metric range`.

## 3. Các mức tham số cần chạy

### Confidence heuristic

| Tham số | Các giá trị        |
| -------- | --------------------- |
| \(b_0\)  | \(-0.24,-0.20,-0.16\) |
| \(b_1\)  | \(1.12,1.40,1.68\)    |
| \(b_2\)  | \(0.72,0.90,1.08\)    |

Khi thay \(b_0,b_1,b_2\), bắt buộc tính lại toàn bộ \(Q_i\), không chỉ thay số trực tiếp trong priority score.

Điều này cũng có thể làm thay đổi near-duplicate family, vì code dùng chênh lệch confidence trong điều kiện near-duplicate. Đây là full-pipeline sensitivity hợp lệ và cần được ghi rõ.

### Priority weights

Không nên để một hàng chung \(\omega\). Tách thành:

- \(\omega_E\)
- \(\omega_F\)
- \(\omega_N\)

Với mỗi trọng số:

1. Nhân riêng thành phần đang xét với \(0.8\) hoặc \(1.2\).
2. Giữ hai thành phần còn lại ở giá trị gốc.
3. Chuẩn hóa lại cả vector để:
   \[
   \omega_E+\omega_F+\omega_N=1.
   \]

Ví dụ khi giảm \(\omega_E\):

\[
(.8\times .34,\ .33,\ .33)
\]

sau đó chuẩn hóa tổng về 1.

Nếu không chuẩn hóa, tổng trọng số thay đổi và miền bounded priority cũng thay đổi, làm sensitivity không còn chỉ phản ánh cơ cấu trọng số.

### Các hằng số còn lại

| Tham số        | Các giá trị  |
| --------------- | --------------- |
| \(\mu\)         | \(1.6,1.8,2.0\) |
| \(s\)           | \(8,10,12\)     |
| \(N_{\rm ref}\) | \(400,500,600\) |
| \(V_{\rm cap}\) | \(40,50,60\)    |

Không chạy \(\mu=2.4\). Implementation hiện quy định:

\[
1\leq\mu\leq2
\]

và sẽ từ chối 2.4. Vì baseline \(\mu=2\) nằm ngay tại trần policy, sensitivity của \(\mu\) phải là one-sided trong miền hợp lệ. Table 3 cần đổi khoảng \([1.6,2.4]\) thành \([1.6,2.0]\).

Lưu ý:

- Thay \(N_{\rm ref}\) phải đồng thời thay cap của \(N_i\) và mẫu số chuẩn hóa log.
- \(V_{\rm cap}\) nằm trong `RobustEstimatorPolicy.v_claim_cap`, không nằm trong `PriorityParams`; cần tạo estimator với policy mới thì thay đổi mới có hiệu lực.

## 4. Tổng số lần chạy

Sau khi gộp một baseline dùng chung:

- 6 cấu hình cho \(b_0,b_1,b_2\)
- 6 cấu hình cho ba thành phần \(\omega\)
- 2 cấu hình dưới baseline cho \(\mu\)
- 6 cấu hình cho \(s,N_{\rm ref},V_{\rm cap}\)
- 1 baseline

Tổng cộng:

\[
21\text{ configurations}\times40\text{ seeds}=840
\]

lượt đánh giá ranking.

## 5. Cách sửa notebook

Hàm tính ranking cần nhận cấu hình thay vì luôn dùng `DEFAULT_CONFIG`:

```python
method_scores(
    data,
    events,
    seed,
    confidence_params,
    priority_params,
    robust_policy,
)
```

Với mỗi configuration:

1. Load lại dataset/events mới.
2. Không tái sử dụng events từ configuration trước vì `compute_confidence()` thay đổi object tại chỗ.
3. Tạo oracle incident groups giống RQ2 gốc.
4. Tính lại confidence.
5. Chạy `score_clusters()` bằng revised estimator.
6. Tính relevance bằng `independent_benefit()` như notebook gốc.
7. Tính NDCG@5.
8. Ghi kết quả cùng provenance.

Pseudo-workflow:

```python
for config in sensitivity_registry:
    for seed in range(3000, 3040):
        data = load_candidate_dataset(seed)
        events = candidate_inference_events(data)

        compute_confidence(events, config.confidence_params)

        scores = revised_scores(
            data,
            events,
            priority_params=config.priority_params,
            robust_policy=config.robust_policy,
        )

        ndcg = compute_ndcg_at_5(scores, independent_benefit(data))
        save_row(config, seed, ndcg)
```

## 6. File kết quả cần xuất

### Kết quả từng seed

```text
rq2_parameter_sensitivity_test.csv
```

Nên có các cột:

```text
seed
parameter
level
b0
b1
b2
omega_e
omega_f
omega_n
mu
s
n_ref
v_cap
ndcg_at_5
spearman
top5_overlap
generator_version
candidate_bundle_sha256
source_commit
package_versions
```

### Kết quả tổng hợp

```text
rq2_parameter_sensitivity_summary.csv
```

Mỗi parameter/level nên có:

```text
parameter
tested_value
mean_ndcg_at_5
std_ndcg_at_5
median_ndcg_at_5
ci95_low
ci95_high
paired_delta_from_baseline
paired_delta_ci95_low
paired_delta_ci95_high
n_test_seeds
```

Sensitivity này là post-hoc exploratory analysis, nên không cần thêm Holm test. Không được dùng kết quả để chọn lại tham số tốt nhất.

## 7. Cách tính `Metric range`

Giả sử \(b_1\) cho kết quả:

| \(b_1\) | Mean NDCG@5 |
| ------: | ----------: |
|    1.12 |      0.6601 |
|    1.40 |      0.6669 |
|    1.68 |      0.6635 |

Khi đó:

\[
\text{Metric range}=[0.6601,0.6669].
\]

Công thức tổng quát:

\[
\left[
\min_{\ell}\overline{\operatorname{NDCG@5}}_{\ell},
\max_{\ell}\overline{\operatorname{NDCG@5}}_{\ell}
\right].
\]

Tiêu chí ổn định trong bài hiện là:

\[
\max-\min < 0.01.
\]

## 8. Table 3 cần thay đổi

Bảng hiện tại nên sửa từ 8 thành 10 hàng:

- \(b_0,b_1,b_2\)
- \(\omega_E,\omega_F,\omega_N\)
- \(\mu,s,N_{\rm ref},V_{\rm cap}\)

Đồng thời:

- `Calibrated value` → `Reference value`
- `Perturbed range` → `Tested values`
- Ghi rõ metric là mean NDCG@5 trên 40 Candidate-4.1 test seeds.
- Ghi rõ \(\omega\) được renormalize.
- Ghi rõ \(\mu\) là one-sided policy-range sensitivity.
- Xóa câu “mean ARI for clustering weights”.
- Không gọi đây là “calibration notebook”; các hằng số này chưa được calibration từ dữ liệu.

## 9. Các kiểm tra bắt buộc

Trước khi điền số:

- Baseline có đúng 40 seeds.
- Baseline mean NDCG@5 bằng `0.666889741`.
- Bundle SHA đúng `a7c7a3…f2d7e1`.
- Mỗi configuration có đúng 40 hàng.
- Không có NaN hoặc seed trùng.
- Mọi vector \(\omega\) có tổng bằng 1.
- Không có \(\mu>2\).
- Số trong LaTeX được sinh từ summary CSV, không chép thủ công.
- Thêm checksum của hai CSV sensitivity vào artifact manifest.

Tóm lại: cần chạy lại RQ2 ranking trên Candidate 4.1 với 21 cấu hình sensitivity; không cần chạy lại clustering/RQ1 và không dùng ARI cho bất kỳ hàng nào trong Table 3.

Source Candidate 4.1 đã bị xóa khỏi branch hiện tại nhưng vẫn khôi phục được từ commit trên. Notebook nên checkout đúng commit, tái sinh candidate bundle và dừng nếu SHA không khớp.

Không dùng bundle RQ1 generator 3.0.0 để điền bảng này, vì như vậy Table 3 sẽ không còn giải thích kết quả RQ2/RQ3 trong bài.

## 2. Thực nghiệm cần chạy

Nên tạo notebook riêng:

```text
RQ2_Parameter_Sensitivity_Colab.ipynb
```

hoặc bổ sung một section độc lập vào `RQ2_Priority_Robustness_Colab.ipynb`.

Thiết kế là one-at-a-time:

1. Chỉ thay đổi một tham số.
2. Giữ nguyên toàn bộ tham số khác.
3. Chạy lại ranking trên 40 test seeds.
4. Tính NDCG@5 cho từng seed.
5. Tính mean NDCG@5 của từng mức tham số.
6. Lấy min–max của các mean để điền `Metric range`.

## 3. Các mức tham số cần chạy

### Confidence heuristic

| Tham số | Các giá trị        |
| -------- | --------------------- |
| \(b_0\)  | \(-0.24,-0.20,-0.16\) |
| \(b_1\)  | \(1.12,1.40,1.68\)    |
| \(b_2\)  | \(0.72,0.90,1.08\)    |

Khi thay \(b_0,b_1,b_2\), bắt buộc tính lại toàn bộ \(Q_i\), không chỉ thay số trực tiếp trong priority score.

Điều này cũng có thể làm thay đổi near-duplicate family, vì code dùng chênh lệch confidence trong điều kiện near-duplicate. Đây là full-pipeline sensitivity hợp lệ và cần được ghi rõ.

### Priority weights

Không nên để một hàng chung \(\omega\). Tách thành:

- \(\omega_E\)
- \(\omega_F\)
- \(\omega_N\)

Với mỗi trọng số:

1. Nhân riêng thành phần đang xét với \(0.8\) hoặc \(1.2\).
2. Giữ hai thành phần còn lại ở giá trị gốc.
3. Chuẩn hóa lại cả vector để:
   \[
   \omega_E+\omega_F+\omega_N=1.
   \]

Ví dụ khi giảm \(\omega_E\):

\[
(.8\times .34,\ .33,\ .33)
\]

sau đó chuẩn hóa tổng về 1.

Nếu không chuẩn hóa, tổng trọng số thay đổi và miền bounded priority cũng thay đổi, làm sensitivity không còn chỉ phản ánh cơ cấu trọng số.

### Các hằng số còn lại

| Tham số        | Các giá trị  |
| --------------- | --------------- |
| \(\mu\)         | \(1.6,1.8,2.0\) |
| \(s\)           | \(8,10,12\)     |
| \(N_{\rm ref}\) | \(400,500,600\) |
| \(V_{\rm cap}\) | \(40,50,60\)    |

Không chạy \(\mu=2.4\). Implementation hiện quy định:

\[
1\leq\mu\leq2
\]

và sẽ từ chối 2.4. Vì baseline \(\mu=2\) nằm ngay tại trần policy, sensitivity của \(\mu\) phải là one-sided trong miền hợp lệ. Table 3 cần đổi khoảng \([1.6,2.4]\) thành \([1.6,2.0]\).

Lưu ý:

- Thay \(N_{\rm ref}\) phải đồng thời thay cap của \(N_i\) và mẫu số chuẩn hóa log.
- \(V_{\rm cap}\) nằm trong `RobustEstimatorPolicy.v_claim_cap`, không nằm trong `PriorityParams`; cần tạo estimator với policy mới thì thay đổi mới có hiệu lực.

## 4. Tổng số lần chạy

Sau khi gộp một baseline dùng chung:

- 6 cấu hình cho \(b_0,b_1,b_2\)
- 6 cấu hình cho ba thành phần \(\omega\)
- 2 cấu hình dưới baseline cho \(\mu\)
- 6 cấu hình cho \(s,N_{\rm ref},V_{\rm cap}\)
- 1 baseline

Tổng cộng:

\[
21\text{ configurations}\times40\text{ seeds}=840
\]

lượt đánh giá ranking.

## 5. Cách sửa notebook

Hàm tính ranking cần nhận cấu hình thay vì luôn dùng `DEFAULT_CONFIG`:

```python
method_scores(
    data,
    events,
    seed,
    confidence_params,
    priority_params,
    robust_policy,
)
```

Với mỗi configuration:

1. Load lại dataset/events mới.
2. Không tái sử dụng events từ configuration trước vì `compute_confidence()` thay đổi object tại chỗ.
3. Tạo oracle incident groups giống RQ2 gốc.
4. Tính lại confidence.
5. Chạy `score_clusters()` bằng revised estimator.
6. Tính relevance bằng `independent_benefit()` như notebook gốc.
7. Tính NDCG@5.
8. Ghi kết quả cùng provenance.

Pseudo-workflow:

```python
for config in sensitivity_registry:
    for seed in range(3000, 3040):
        data = load_candidate_dataset(seed)
        events = candidate_inference_events(data)

        compute_confidence(events, config.confidence_params)

        scores = revised_scores(
            data,
            events,
            priority_params=config.priority_params,
            robust_policy=config.robust_policy,
        )

        ndcg = compute_ndcg_at_5(scores, independent_benefit(data))
        save_row(config, seed, ndcg)
```

## 6. File kết quả cần xuất

### Kết quả từng seed

```text
rq2_parameter_sensitivity_test.csv
```

Nên có các cột:

```text
seed
parameter
level
b0
b1
b2
omega_e
omega_f
omega_n
mu
s
n_ref
v_cap
ndcg_at_5
spearman
top5_overlap
generator_version
candidate_bundle_sha256
source_commit
package_versions
```

### Kết quả tổng hợp

```text
rq2_parameter_sensitivity_summary.csv
```

Mỗi parameter/level nên có:

```text
parameter
tested_value
mean_ndcg_at_5
std_ndcg_at_5
median_ndcg_at_5
ci95_low
ci95_high
paired_delta_from_baseline
paired_delta_ci95_low
paired_delta_ci95_high
n_test_seeds
```

Sensitivity này là post-hoc exploratory analysis, nên không cần thêm Holm test. Không được dùng kết quả để chọn lại tham số tốt nhất.

## 7. Cách tính `Metric range`

Giả sử \(b_1\) cho kết quả:

| \(b_1\) | Mean NDCG@5 |
| ------: | ----------: |
|    1.12 |      0.6601 |
|    1.40 |      0.6669 |
|    1.68 |      0.6635 |

Khi đó:

\[
\text{Metric range}=[0.6601,0.6669].
\]

Công thức tổng quát:

\[
\left[
\min_{\ell}\overline{\operatorname{NDCG@5}}_{\ell},
\max_{\ell}\overline{\operatorname{NDCG@5}}_{\ell}
\right].
\]

Tiêu chí ổn định trong bài hiện là:

\[
\max-\min < 0.01.
\]

## 8. Table 3 cần thay đổi

Bảng hiện tại nên sửa từ 8 thành 10 hàng:

- \(b_0,b_1,b_2\)
- \(\omega_E,\omega_F,\omega_N\)
- \(\mu,s,N_{\rm ref},V_{\rm cap}\)

Đồng thời:

- `Calibrated value` → `Reference value`
- `Perturbed range` → `Tested values`
- Ghi rõ metric là mean NDCG@5 trên 40 Candidate-4.1 test seeds.
- Ghi rõ \(\omega\) được renormalize.
- Ghi rõ \(\mu\) là one-sided policy-range sensitivity.
- Xóa câu “mean ARI for clustering weights”.
- Không gọi đây là “calibration notebook”; các hằng số này chưa được calibration từ dữ liệu.

## 9. Các kiểm tra bắt buộc

Trước khi điền số:

- Baseline có đúng 40 seeds.
- Baseline mean NDCG@5 bằng `0.666889741`.
- Bundle SHA đúng `a7c7a3…f2d7e1`.
- Mỗi configuration có đúng 40 hàng.
- Không có NaN hoặc seed trùng.
- Mọi vector \(\omega\) có tổng bằng 1.
- Không có \(\mu>2\).
- Số trong LaTeX được sinh từ summary CSV, không chép thủ công.
- Thêm checksum của hai CSV sensitivity vào artifact manifest.

Tóm lại: cần chạy lại RQ2 ranking trên Candidate 4.1 với 21 cấu hình sensitivity; không cần chạy lại clustering/RQ1 và không dùng ARI cho bất kỳ hàng nào trong Table 3.
