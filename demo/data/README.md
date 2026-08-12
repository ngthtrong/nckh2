# dataV2 — geographically anchored semi-synthetic sanity set

`dataV2` là một bộ dữ liệu bán tổng hợp được neo theo bối cảnh địa lý thật của
Copernicus EMS activation `EMSR848` (flood ở miền Trung Việt Nam). OSM,
Copernicus và WorldPop chỉ cung cấp bối cảnh/anchor tham chiếu; incident,
report, duplicate, coordinated fake campaign, nhu cầu, urgency và confidence
là dữ liệu mô phỏng có kiểm soát.

Không được gọi bundle này là real rescue-report dataset, independent real-world
validation hoặc confirmation evidence.

## Phạm vi hiện tại

- 80 run: `run_001`–`run_080`, seed 1–80.
- 1.280 latent incident (16/run).
- 26.288 report (trung bình 328,6/run).
- 17.901 genuine, 3.587 duplicate và 4.800 coordinated fake.
- Mỗi run có đúng năm tệp: `algorithm_input.json`, `observable_reports.json`,
  `ground_truth.json`, `latent_incidents.json`, `run_manifest.json`.
- `enriched_anchors.parquet` có 29.430 anchor; `V_reference` đang null toàn bộ
  và phải được xem là một quality finding, không được âm thầm bù giá trị.

## Bốn lớp dữ liệu trong một run

`algorithm_input.json` là đầu vào duy nhất được phép đưa vào inference. Nó có
`event_id`, vị trí/thời gian, `flood`, `urgency`, `n_trapped`, `vulnerability`,
`confidence`, ảnh và các trường mô tả phụ. `gt_cluster` và `is_fake` không nằm
trong bảng này.

`ground_truth.json` chỉ dùng sau inference để nối nhãn theo `event_id`, gồm
cluster, fake/duplicate class, duplicate lineage và attack campaign.

`observable_reports.json` được giữ để audit exposure của oracle fields;
`latent_incidents.json` chỉ mô tả incident mô phỏng; `run_manifest.json` giữ
seed, generator version, parameters, nguồn và các cảnh báo thiết kế.

## Nguồn tham chiếu

- [Copernicus EMS EMSR848](https://mapping.emergency.copernicus.eu/activations/EMSR848/)
- [WorldPop 2025 constrained population count](https://hub.worldpop.org/geodata/summary?id=56514)
- [Geofabrik Vietnam](https://download.geofabrik.de/asia/vietnam.html)

`vietnam-latest.osm.pbf` là URL thay đổi theo thời gian. Bundle hiện tại không
đóng kèm raw/cropped snapshot, notebook/generator gốc, per-row lineage,
checksum nguồn hoặc license record; vì vậy README chỉ mô tả ý định thiết kế,
không chứng minh provenance của từng hàng.

## Chạy benchmark một run

Entrypoint đã được cập nhật để đọc schema mới. Ví dụ:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m demo.v2.external_benchmark \
  --reports demo/dataV2/gold/run_001/algorithm_input.json \
  --truth demo/dataV2/gold/run_001/ground_truth.json \
  --selection revision/v2/results/calibration_selection.json \
  --random-state 42 \
  --output /tmp/run_001_external_sanity.json
```

Khi cần audit đủ năm tệp của run, dùng `load_external_run()` hoặc notebook
Colab; loader sẽ đọc `algorithm_input.json` cho inference, rồi kiểm tra
observable/truth/latent/manifest độc lập.

## Chạy toàn bộ 80 run

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m demo.v2.external_benchmark \
  --all-runs \
  --data-root demo/dataV2 \
  --output-dir /tmp/external_sanity_80 \
  --expected-runs 80 \
  --random-state 42 \
  --resume
```

Batch runner:

- yêu cầu chính xác `run_001`–`run_080`;
- chỉ dùng bốn configuration đã khóa trong `revision/v2/results/calibration_selection.json`;
- ghi `per_run/run_NNN.json` theo cách atomic;
- lưu lỗi và adverse result thay vì lọc bỏ;
- kiểm tra checksum, Git SHA, protocol/selection SHA và random state khi resume;
- từ chối ghi đè output có provenance khác.

## Notebook Colab

Mở [datav2_external_benchmark_colab.ipynb](../notebooks/datav2_external_benchmark_colab.ipynb)
trên Colab. Notebook yêu cầu clone một commit SHA cố định, cài
`requirements.lock` cùng `pyarrow==18.1.0`, chạy smoke test rồi mới chạy full
80 run. Notebook sinh ZIP đầy đủ gồm per-run JSON, CSV tổng hợp, CI ghép cặp,
campaign/dedup audit, hình PNG/PDF, provenance, manifest và executed notebook.

Quy trình:

1. Commit/push `dataV2`, benchmark code và notebook.
2. Ghi lại commit SHA 40 ký tự.
3. Nhập SHA vào cell cấu hình trên Colab.
4. Chạy setup, integrity gate và smoke test.
5. Chạy full batch trong artifact directory riêng; nếu runtime bị ngắt, tải lại đúng
   checkpoint directory và chạy lại với cùng output để resume. Smoke directory chưa
   có batch manifest 80-run nên không dùng nó làm output full.
6. Tải ZIP và executed notebook về máy.
7. Đưa artifact vào `demo/dataV2/results/<run-id>/` để audit; không chỉnh tay JSON/CSV.

Notebook chỉ báo cáo descriptive statistics và paired bootstrap percentile 95%
CI theo run. Không có p-value, tuning, priority/dispatch evaluation hay claim
confirmatory.

Nếu Colab báo lỗi NumPy/SciPy private symbol như
`_blas_supports_fpe`, hãy chọn **Runtime → Restart session**, checkout lại đúng
commit rồi chạy notebook từ đầu. Cell cài môi trường có compatibility shim
no-op cho symbol này và sẽ dừng rõ ràng nếu binary package vẫn không nhất quán;
không chạy tiếp từ cell import trong kernel đã lỗi.

## Các quality finding phải giữ nguyên

- `gt_cluster`/`is_fake` xuất hiện trong observable table nhưng bị loại trước inference.
- `source_id`/`source_family` và receipt time độc lập chưa có.
- Numeric suffix của `event_id` tách các generation class thành block trong 80/80 run.
- 0/902 nhãn `exact` khớp exact fingerprint v2; 2.498/2.685 nhãn `near` khớp near envelope.
- `V_reference` trong parquet null 100%.
- Không có incident-level gain, deadline, service hoặc harm độc lập; không suy ra priority/dispatch benefit.

Các finding này là kết quả cần công bố trong sanity analysis, không phải lý do để
sửa dữ liệu âm thầm.
