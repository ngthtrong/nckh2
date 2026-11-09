# Prompt Phase 02 — Hồ sơ dữ liệu, LR, tối ưu hóa và scope phép đo

Bạn làm việc tại `/home/ngthtrong/nckh2` cho đề tài **Xây dựng hệ thống phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI (THS2026-68)**. Chỉ thực hiện phase này; ưu tiên tái phân tích artifact, không huấn luyện.

## A. Bối cảnh nghiên cứu

Hội đồng hỏi dữ liệu/nhãn/split/đặc điểm ảnh (C1/C2), LR và căn cứ ưu tiên (C3/C7), giải thích PTQ/QAT/pruning (B2) và phân biệt PC/mobile (C6). Đã có artifact đủ cho phần lớn giải trình; tài liệu `docs/nghiem-thu/doi_chieu_thuyet_minh.md` và CLAUDE.md có snapshot cũ. **A3 ảnh cá nhân được người dùng thêm sau**, không tìm/chèn/hỏi ảnh, không chặn phase.

## B. Nguồn, trạng thái và phụ thuộc

Đọc report README/RULES, `docs/revision-plan/{00-repository-audit.md,02-experiment-gap-analysis.md,04-phase-roadmap.md}`, request/amendment/snapshot và `outputs/phase-01/{scope-register.md,dataflow.md,handoff.md}`. Các output01 là dự kiến: thiếu thì xác minh lại tối thiểu DOCX và E_i code, ghi prerequisite gap trước khi sửa đoạn phụ thuộc; tiếp tục metadata độc lập.

Nguồn ảnh: `products/fe/model/training_img.ipynb`, `products/fe/model/Edge Ai/split_train_val_test_mobilenetv3_large.csv`, dataset và folder seed1024; LR: `products/fe/model/urgency_ei/{data,model,sources,audits,scripts}`. Compression: `products/fe/reports/seed1024/{pth_onnx_pte,fp32_ptq_qat,prunning_st}/`, config `report/config/benchmark-sources.json`. Mobile raw: `products/fe/reports/seed{159,1024}/mobile/`; metadata audit đã có trong snapshot.

Snapshot đã kiểm1.702 ảnh, split1.189/257/256, không MD5/group vượt tập; format JPEG1.521/PNG24/WEBP152/AVIF5. Model FP32/PTQ/QAT Accuracy75,78/66,80/46,48%, byte16,04/4,51/4,57MiB; QAT median CPU53,11ms. Phone32 JSON là classifyImage, CPU là predict; không so speedup chéo scope. Kiểm lại sources/hashes trước dùng.

## C. Mục tiêu

Tạo data card/source map/method description tái lập được. Giữ uncertainty về nguồn ảnh/license/IAA, split của lần train và lựa chọn model dựa trên test. Không tạo provenance chưa có.

## D. Tác vụ

1. **P02.01:** hash/status đầu vào; thống kê clean/split theo class, width/height/ratio/bytes quantiles, magic format/mode theo split. Dùng `evidence/audit-snapshot.json` nếu hash còn khớp hoặc đọc header bằng Pillow sẵn có. Tạo `outputs/phase-02/{data-card.md,image-profile.csv}`; cập nhật data.tex/image-design/setup tương ứng. Ghi URL/license từng ảnh, annotator/IAA và source/event independence là unknown khi không có bản ghi; không suy từ filename.
2. **P02.02:** đọc CSV 32 profiles, model JSON và source mapping; kiểm OR baseline/threshold/coefficient, count-equivalence và sanity audit có thất bại. Đọc nguồn WHO/PDF chính thức khi giải thích dấu hiệu; ghi từng mapping/adaptation/unclear và tách khỏi dispatch weights. Tra cứu quy định/hướng dẫn nghiệp vụ Việt Nam từ nguồn chính thức nếu liên quan; ghi điều khoản, phạm vi và chỗ chưa có căn cứ, không ép trọng số dispatch vào một quy định. Tạo `lr-audit.csv`, `criterion-source-map.csv`; cập nhật phương pháp LR mà không gọi nhãn synthetic là clinical gold. P01 đã sửa E_i runtime: giữ đúng luồng, không sửa code.
3. **P02.03:** tính lại confusion/Accuracy/macro-F1/high recall/lỗi nặng từ `all_predictions.csv`, đối chiếu summary/model/config/split hash; lập byte/latency trade-off và error taxonomy FP32/PTQ/QAT/pruning. Cùng seed/runtime/scope mới so sánh được; giữ seed42 lịch sử riêng; PTH checkpoint chứa metadata/optimizer không được coi byte pruning là mức nén cấu trúc tương đương mặc định. Tạo `compression-audit.csv`, `error-taxonomy.md`. Không chạy quantize/QAT entrypoint hoặc sửa kết quả xấu.
4. **P02.04:** tạo `measurement-scopes.csv` cho CPU predict, phone classifyImage, server clustering, proxy transmission, Android manual UI. Đối chiếu 32raw JSON với summary, ghi E2E narrative/raw vắng. README phone nhắc nhiều CSV hiện không tồn tại: chỉ tái xuất từ raw vào output riêng khi cần. Chuẩn bị preflight model/export/package availability cho P04/P05; không gọi 8.192 prediction là8.192 ảnh độc lập.
5. **P02.05:** đưa bảng từ raw qua script/generator phù hợp, không sửa generated tay; cập nhật LaTeX phạm vi data/LR/optimization, không sửa RQ inference. Chạy metric/hash/coverage checks; nếu report đổi thì content build/check và PDF/log phần đổi. Tạo `handoff.md` kèm script/command/env/source hash, gap còn lại.

## E. Nguyên tắc và rủi ro

Không train, tune test, chọn model mới sau xem test hoặc thay seed/split để tăng số. Giữ toàn bộ artifact cũ, source data và working-tree edits. Nguyên nhân QAT là giả thuyết nếu chưa cô lập; giảm byte, giảm params và tăng tốc là ba kết quả riêng. Không “khắc phục” source/hash mismatch bằng sửa manifest; công bố sai lệch và dừng phần phụ thuộc. Không commit/push/gửi bên ngoài.

## F. Deliverables

`docs/revision-plan/outputs/phase-02/{data-card.md,image-profile.csv,lr-audit.csv,criterion-source-map.csv,compression-audit.csv,error-taxonomy.md,measurement-scopes.csv,handoff.md}`, script thống kê nếu cần; data/method/setup/report optimization sources và generated outputs qua exporter khi hợp lệ.

## G. Acceptance criteria và chuyển phase

Raw→bảng tính lại khớp; class-order và ordinal mapping đúng; n/split/version/timing scope rõ; unknown không bị điền giả; không clinical/NLP/fusion claim. Model selection trên test và seed1024 split provenance chưa đủ được giữ hạn chế. Handoff đủ cho P03 và preflight P04/P05; phần thiếu thiết bị không chặn phase02.

## H. Final report

Báo việc hoàn thành, file sửa/tạo, kiểm chạy thực tế/exit/giới hạn, nhận xét xử lý, gap/unknown, quyết định khoa học/kỹ thuật và đầu vào bàn giao. Tách thống kê metadata mới khỏi thí nghiệm inference chưa chạy.
