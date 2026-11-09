# Taxonomy lỗi và đánh đổi — prediction hiện có

Class-index [low,medium,high,non_flood] khác ordinal [non_flood=0,low=1,medium=2,high=3]. Lỗi nặng là khoảng ordinal≥2; không gọi mỗi lỗi high→medium là lỗi nặng. error-counts.csv giữ mọi ô off-diagonal với hướng over/under.

| Bundle/model | Accuracy | macro-F1 | recall high | lỗi nặng | CPU predict median ms |
|---|---:|---:|---:|---:|---:|
| pth_onnx_pte/pth | 0.757812 | 0.742649 | 0.740741 | 3 | 50.9270 |
| pth_onnx_pte/onnx | 0.757812 | 0.742649 | 0.740741 | 3 | 19.0789 |
| pth_onnx_pte/pte | 0.757812 | 0.742649 | 0.740741 | 3 | 34.3868 |
| fp32_ptq_qat/onnx_fp32 | 0.757812 | 0.742649 | 0.740741 | 3 | 14.8116 |
| fp32_ptq_qat/ptq_int8 | 0.667969 | 0.643617 | 0.648148 | 17 | 13.9674 |
| fp32_ptq_qat/qat_int8 | 0.464844 | 0.429079 | 0.740741 | 45 | 53.1143 |
| prunning_st/baseline_pth | 0.757812 | 0.742649 | 0.740741 | 3 | 37.9173 |
| prunning_st/structured_pth | 0.800781 | 0.782610 | 0.851852 | 4 | 24.1793 |
| prunning_st/baseline_onnx | 0.757812 | 0.742649 | 0.740741 | 3 | 10.2830 |
| prunning_st/structured_onnx | 0.800781 | 0.782610 | 0.851852 | 4 | 17.0155 |
| prunning_st/baseline_pte | 0.757812 | 0.742649 | 0.740741 | 3 | 30.2785 |
| prunning_st/structured_pte | 0.800781 | 0.782610 | 0.851852 | 4 | 59.1985 |

QAT high recall ngang FP32 nhưng macro-F1 giảm và45 lỗi nặng; không dùng một metric để gọi QAT đạt. Recall medium7/60=11,67%; chưa cô lập nguyên nhân (calibration/observer/backend/training là giả thuyết, không causal diagnosis). PTQ có17 lỗi nặng.

Pruning params4.207.156→4.145.694 giảm1,46%; PTH bytes còn chịu optimizer/metadata. ONNX/PTE size giảm khoảng1,46%; trong bundle pruning CPU median ONNX/PTE tăng dù PTH giảm. Không suy speedup CPU→phone hoặc giữa các bundle khác timing/session. Checkpoint fine-tuning và pruning là can thiệp kết hợp, chưa cô lập pruning-only.

12 cấu hình trong ba bundle khớp confusion/Accuracy/F1/critical/median summary từ prediction, ID/nhãn test khớp, có exact local artifact cùng hash (compression-audit.csv). Không chạy model/nén mới.
