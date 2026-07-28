Hãy đóng vai trưởng nhóm nghiên cứu và kỹ sư phụ trách tái lập thực nghiệm. Dựa trên báo cáo phản biện tại:

- `phan-bien.md`

hãy lập một kế hoạch chỉnh sửa toàn diện cho bài báo và mã nguồn của dự án:

“A Product-Kernel Weighted Graph for Flood-Rescue Event Clustering and Cluster-Level Priority Scoring”.

Mục tiêu là xử lý có hệ thống toàn bộ Major Concerns, Minor Concerns và các hạng mục P0/P1/P2 trong báo cáo phản biện, đưa bài từ mức “Reject and Resubmit” đến trạng thái có thể gửi phản biện lại.

Đây chỉ là bước lập kế hoạch. Chưa sửa mã nguồn, chưa chạy lại toàn bộ thí nghiệm và chưa chỉnh `paper/main.tex`.

## 1. Nguồn cần kiểm tra

Trước khi lập kế hoạch, hãy đọc và đối chiếu:

- `phan-bien.md`: nguồn yêu cầu chính.
- `paper/main.tex`: bản thảo hiện hành.
- `demo/data/`: dữ liệu và generator.
- `demo/pipeline/`: phương pháp hiện hành.
- `demo/experiments/`: thiết kế thực nghiệm.
- `demo/results/tables/*.json`: nguồn sự thật định lượng hiện tại.
- `demo/run_all.py`: quy trình thực thi.
- `README.md` và `demo/README.md`: tài liệu tái lập.
- `loop/loop17/traceability.md`: truy vết số liệu hiện tại.
- Các `resolution_plan.md` và `execution_report.md` gần nhất để tránh lặp lại công việc đã hoàn thành.

Không mặc định mọi đề xuất trong báo cáo phản biện đều chính xác. Với từng nhận xét, hãy kiểm tra lại mã, bài báo và JSON rồi phân loại:

- Chấp nhận: phản biện đúng và cần sửa.
- Chấp nhận một phần: vấn đề đúng nhưng cách sửa cần điều chỉnh.
- Bác bỏ có bằng chứng: phản biện không còn đúng với trạng thái hiện tại.
- Bị chặn: cần dữ liệu, quyết định nghiệp vụ hoặc đầu vào bên ngoài mà dự án chưa có.

Không dùng `archive/` hoặc tài liệu cũ làm nguồn sự thật.

## 2. Các vấn đề bắt buộc phải bao phủ

Kế hoạch phải ánh xạ đầy đủ ít nhất tám Major Concerns:

- MC1: phạm vi của bổ đề, cận cạnh/cận cụm và phát biểu về additive.
- MC2: hiệu chỉnh product–additive công bằng, out-of-sample và matched-density.
- MC3: tính nội sinh của dữ liệu synthetic và external validity.
- MC4: confidence-bypass, double-counting dân số/vulnerability và duplicate reports.
- MC5: construct validity và trade-off của dispatch simulation.
- MC6: baseline và factorial ablation chưa đủ mạnh.
- MC7: fragmentation, split/merge, noise burden và operator workload.
- MC8: dependency pinning, README, environment, provenance và clean-room reproducibility.

Đồng thời phải xử lý các Minor Concerns có liên quan, nhưng không để chúng làm chậm đường găng của các lỗi khoa học P0.

## 3. Thiết kế các workstream chạy song song

Hãy tổ chức kế hoạch thành các workstream độc lập tối đa có thể. Ít nhất xem xét các nhánh sau:

- WS-A — Toán học và phạm vi tuyên bố:
  sửa bổ đề, miền ngưỡng, additive bound, hop-diameter và thuật ngữ “kernel”.
- WS-B — Protocol hiệu chỉnh và so sánh công bằng:
  train/calibration/test split hoặc nested cross-seed calibration, matched retained-edge fraction, matched degree và ngân sách tuning thống nhất.
- WS-C — Priority semantics và dispatch:
  confidence gating, unique population, duplicate reports, adversarial inputs, outcome độc lập và Pareto trade-off.
- WS-D — Dữ liệu và external validity:
  đánh giá lại generator, benchmark ngoài mô hình và phương án real-data sanity check.
- WS-E — Baseline, ablation và error metrics:
  ST-DBSCAN, spatially constrained/multiple-kernel baseline, factorial ablation, split/merge/noise/operator-burden metrics.
- WS-F — Tái lập và artifact:
  dependency lock, môi trường chạy, README, hardware provenance, checksum, clean-room command và hướng dẫn XeLaTeX.
- WS-G — Tích hợp kết quả và viết lại bài:
  chỉ bắt đầu sau khi các kết quả upstream đã ổn định; cập nhật `paper/main.tex`, hình, bảng, traceability và response-to-reviewer.

Nếu một workstream không thể thực sự chạy độc lập, hãy chỉ rõ file hoặc quyết định chung khiến nó phụ thuộc nhánh khác.

## 4. Yêu cầu tránh xung đột khi chạy song song

Với mỗi workstream, phải xác định:

- Phạm vi file được phép chỉnh sửa.
- File dùng chung nhưng chưa được chỉnh cho đến giai đoạn tích hợp.
- Đầu vào cần nhận từ workstream khác.
- Artifact đầu ra.
- Điểm đồng bộ hoặc integration gate.
- Rủi ro sửa đè hoặc làm thay đổi số liệu của nhánh khác.

Ưu tiên nguyên tắc:

- Không sửa `paper/main.tex` trước khi dataset, công thức và kết quả thực nghiệm liên quan đã ổn định.
- Không dùng cùng một test seed để lựa chọn tham số và báo cáo kết quả cuối.
- Không chỉnh tay JSON kết quả.
- Mọi JSON, bảng và hình phải được sinh từ mã.
- Nếu thay đổi generator hoặc priority formula, phải xác định rõ toàn bộ thí nghiệm downstream cần chạy lại.
- Mọi con số cuối cùng trong bài phải truy được về JSON hoặc hằng số trong mã.
- Giữ nguyên các thay đổi hiện có của người dùng và không thực hiện thao tác Git phá huỷ.

## 5. Cấu trúc chi tiết của từng nhiệm vụ

Mỗi nhiệm vụ phải có một mã ổn định, ví dụ `A1`, `B3`, `C2`, và bao gồm:

- Vấn đề phản biện được xử lý.
- Mục tiêu khoa học.
- Bằng chứng hiện tại trong repo.
- Thay đổi dự kiến.
- File hoặc module liên quan.
- Đầu vào.
- Artifact đầu ra.
- Phụ thuộc.
- Có thể chạy song song với nhiệm vụ nào.
- Lệnh hoặc phép kiểm dự kiến.
- Tiêu chí nghiệm thu định lượng.
- Điều kiện thất bại hoặc rollback về mặt khoa học.
- Rủi ro và biện pháp giảm thiểu.
- Mức ưu tiên: P0, P1 hoặc P2.
- Khối lượng tương đối: S, M, L hoặc XL.

Tiêu chí nghiệm thu không được viết chung chung như “kết quả tốt” hoặc “bài được cải thiện”. Phải dùng điều kiện kiểm chứng được, chẳng hạn:

- Proof, code và miền ngưỡng sử dụng cùng bất đẳng thức.
- Không còn threshold ngoài miền định lý trong violation count.
- Tuning không truy cập test seed.
- Mỗi phương pháp có cùng ngân sách tuning.
- Báo cáo effect size, CI và paired test trên test seeds.
- Priority không thể tăng không giới hạn từ một báo cáo confidence thấp.
- Duplicate reports không làm dân số tăng tuyến tính không kiểm soát.
- Split/merge/noise metrics bao phủ cả các điểm `gt=-1`.
- Một môi trường sạch tái tạo được JSON, hình và PDF trong dung sai định trước.

## 6. Phân biệt phạm vi khả thi

Hãy chia giải pháp thành hai mức:

### Mức tối thiểu khả thi để tái nộp

Các thay đổi có thể hoàn thành chỉ với dữ liệu và tài nguyên hiện có. Nếu không có dữ liệu thật, phải hạ đúng phạm vi tuyên bố xuống một nghiên cứu phương pháp/synthetic proof-of-concept.

### Mức đầy đủ để tăng khả năng chấp nhận

Bao gồm real-data sanity check, annotation incident-level, expert validation cho priority score và các baseline bên ngoài mạnh hơn.

Đối với dữ liệu thật hoặc xác nhận chuyên gia, phải ghi rõ:

- Đầu vào nào cần tác giả cung cấp.
- Điều gì không thể tự suy đoán.
- Workstream nào vẫn có thể tiếp tục trong lúc chờ.
- Phương án fallback nếu đầu vào không có trước thời điểm tái nộp.

Không được giả định rằng dự án đã có dữ liệu cứu hộ thật hoặc quyền truy cập dữ liệu nhạy cảm.

## 7. Phân tích phụ thuộc và đường găng

Tạo một dependency graph dạng văn bản hoặc Mermaid thể hiện:

- Nhiệm vụ nào bắt đầu ngay và chạy song song.
- Nhiệm vụ nào thay đổi nguồn sự thật của downstream.
- Các integration gate.
- Đường găng đến bản PDF cuối.
- Những nhiệm vụ có thể trì hoãn mà không ảnh hưởng tính đúng đắn khoa học.

Ví dụ logic tổng quát cần được kiểm tra lại theo repo:

```text
Audit và quyết định phạm vi
 ├── WS-A: toán học
 ├── WS-B: protocol calibration
 ├── WS-C: priority semantics
 ├── WS-D: dữ liệu/external validity
 └── WS-F: môi trường tái lập

WS-C + WS-D → sinh dữ liệu mới
Sinh dữ liệu ổn định → WS-B + WS-E chạy thực nghiệm
WS-A + WS-B + WS-C + WS-D + WS-E → khóa kết quả
Khóa kết quả + WS-F → WS-G viết lại bài và xác minh cuối
Không sao chép sơ đồ này một cách máy móc; phải điều chỉnh theo phụ thuộc thực tế của mã nguồn.
```


8. Kế hoạch chạy lại và quản lý artifacts
   Phải chỉ rõ:
   Những thay đổi nào bắt buộc tái sinh dataset.json.
   Những thí nghiệm nào phải chạy lại sau mỗi loại thay đổi.
   Các JSON, hình và bảng bị ảnh hưởng.
   Quy tắc đặt tên cho thí nghiệm mới.
   Cách tránh ghi đè kết quả cũ trước khi kết quả mới được xác minh.
   Cách tạo manifest gồm tham số, seed, commit, môi trường, hardware và checksum.
   Cách kiểm tra số liệu trong bài với source-of-truth sau khi tích hợp.
9. Đầu ra bắt buộc
   Viết kế hoạch bằng tiếng Việt theo cấu trúc:
   Kết luận điều hành.
   Kiểm chứng và phân loại từng MC1–MC8.
   Các quyết định khoa học cần chốt trước khi sửa.
   Kiến trúc workstream song song.
   Dependency graph và đường găng.
   Kế hoạch chi tiết theo từng nhiệm vụ.
   Ma trận file ownership và chống xung đột.
   Ma trận phản biện → nhiệm vụ → artifact → tiêu chí nghiệm thu.
   Kế hoạch thực nghiệm và quản lý seed/tuning/test.
   Kế hoạch tái lập và clean-room validation.
   Kế hoạch tích hợp, viết lại bài và response-to-reviewer.
   Rủi ro, blocker và đầu vào cần tác giả cung cấp.
   Checklist nghiệm thu cuối.
   Thứ tự thực thi đề xuất.
   Cuối kế hoạch, cung cấp một bảng tổng hợp có dạng:
   Task	Priority	Workstream	Dependencies	Parallel group	Files	Output	Acceptance test	Effort

Sau đó đưa ra ba danh sách:
“Có thể bắt đầu ngay và chạy song song”.
“Phải chờ integration gate”.
“Bị chặn bởi đầu vào bên ngoài”.
10. Nguyên tắc ra quyết định
Ưu tiên sửa tính đúng đắn khoa học trước khi tối ưu số liệu hoặc trình bày.
Không thiết kế lại benchmark chỉ để phương pháp đề xuất thắng.
Một kết quả tie hoặc bất lợi sau calibration vẫn là kết quả hợp lệ; khi đó phải hạ tuyên bố thay vì tiếp tục tuning trên test.
Không biến kế hoạch thành danh sách mong muốn thiếu tiêu chí nghiệm thu.
Không đưa ra ước lượng thời gian theo ngày nếu chưa biết nguồn lực; dùng effort S/M/L/XL.
Không bắt đầu thực thi. Chỉ lập kế hoạch đủ chi tiết để một hoặc nhiều người/agent có thể triển khai độc lập mà không phải tự suy đoán các quyết định quan trọng.
Điểm quan trọng của prompt này là buộc kế hoạch tách riêng các nhánh có thể song song, nhưng vẫn khóa `paper/main.tex` và kết quả cuối cho đến khi dữ liệu, công thức cùng protocol thực nghiệm đã ổn định. Điều đó giúp tránh tình trạng vừa sửa bài vừa làm thay đổi toàn bộ số liệu phía dưới.
