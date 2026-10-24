# Tư liệu kỹ thuật tách khỏi phụ lục bản nộp

Bản lưu nguồn trước khi rút gọn phụ lục A và B ngày 24/10/2026. Không được ghép vào báo cáo. Các câu lệnh, đường dẫn và mã băm trong bản lưu phải được đối chiếu lại trước khi sử dụng; mã băm cấu hình cũ không được xem là giá trị hiện hành.

## appendices/reproducibility.tex

```tex
\chapter{Tái lập thực nghiệm}\label{chap:reproducibility}
\section{Nguồn và phiên bản}
Các bảng kết quả được tổng hợp từ dữ liệu thực nghiệm đã lưu; commit đầu vào được ghi bằng SHA đầy đủ trong tệp provenance sinh tự động. Commit này mô tả nguồn trước chỉnh sửa nội dung báo cáo, không bao gồm các chỉnh sửa chưa commit. Script xuất bảng ghi SHA-256 từng JSON/CSV trực tiếp được dùng, cho phép kiểm tra bảng có còn khớp nguồn khi artifact thay đổi.

Hai snapshot lịch sử của mã nguồn phục vụ tái lập độc lập các bước sinh dữ liệu và đánh giá phân cụm:
\begin{itemize}
\item Snapshot sinh dữ liệu và kiểm thử đối chứng: commit \texttt{a6be3e9};
\item Snapshot thực nghiệm thuật toán phân cụm RQ1: commit \texttt{6ac75c2}.
\end{itemize}
Mã nguồn của hệ thống và các tập dữ liệu thực nghiệm được lưu trữ theo quy chuẩn tái lập khoa học \citep{nguyen2026floodartifact}, cho phép kiểm chứng độc lập mọi kết quả công bố trong báo cáo.

\section{Sinh lại bảng và kiểm tra ảnh}
Từ thư mục gốc repo, chạy:
\begin{verbatim}
python3 report/scripts/export_results.py
make -C report content
make -C report deliverables
make -C report check
\end{verbatim}
Script chỉ dùng Python chuẩn, đọc artifact đã lưu, đối chiếu config/split, kiểm tra từng ảnh theo MD5 và kiểm tra nhóm không vượt split. Sau đó sinh bảng TeX, macro dùng chung và provenance. Nó không huấn luyện, không thay đổi JSON/CSV nghiên cứu và không chạy benchmark thiết bị. Để tái lập chỉ số từ đầu, phải dùng công cụ runtime tương ứng.

Tệp split có SHA-256:
\begin{quote}\small\path{f7b52cd25411d4d1df2f7f80745a2cf430819773854345798cf7e093e3bcba45}\end{quote}
Tệp config có SHA-256:
\begin{quote}\small\path{a509ab6e22f47b2e53f2300275bb850017c50713453d5a86299d6b7594a7359e}\end{quote}
Ảnh test phải lấy theo cột \texttt{relative\_path}, không chia lại dataset và không thay thế bằng toàn bộ thư mục ảnh. Đường dẫn tuyệt đối Windows trong metadata là đường môi trường của lần chạy gốc; cần ánh xạ sang đường tương đối khi dùng máy khác.

\section{Tái lập các phép so sánh ảnh}
Các công cụ trong thư mục \texttt{tools/} có CLI cho so sánh FP32, PTQ/QAT và pruning. Cần xem \texttt{--help} của đúng script trước khi chạy để chọn output riêng và tránh ghi đè artifact đang dẫn trong báo cáo. Thí dụ kiểm tra parity nhỏ từ thư mục tools:
\begin{verbatim}
python3 compare_models.py --help
python3 compare_models.py --limit 3 --skip-pte --no-plots
\end{verbatim}
Lệnh smoke không thay kết quả full test. Với full test, cần checkpoint, config, split và manifest khớp hash, dependency đúng runtime và quyền truy cập đủ ảnh. Khi PTE không có runtime, trạng thái phải ghi rõ chưa thử thay vì tạo dự đoán thay thế từ ONNX.

Phiên đo cần ghi phần cứng, provider, số luồng, warmup, batch và ranh giới timing. Các phiên summary CPU tính predict; benchmark điện thoại tại Mục~\ref{sec:phone-benchmark-results} tính classifyImage rộng hơn. Cần giữ output trong một thư mục riêng khi đo lại để có thể so sánh mà không mất bản cũ. Bộ benchmark bốn điện thoại đã có metadata thiết bị và hash model; các phiên tiếp theo vẫn cần bổ sung hash APK/commit, log tải và nhiệt độ để xác nhận build và độ ổn định hiệu năng.

\section{Sinh hình và kiểm tra benchmark ứng dụng}
Chín hình định lượng và ví dụ ảnh được sinh từ artifact bằng matplotlib. PDF được dùng trong LaTeX; PNG đi cùng để xem nhanh. Script giữ mã chọn ảnh minh họa xác định, hash các nguồn trực tiếp, hash đầu ra và các số tổng hợp trong tệp provenance hình sinh tự động. Các sơ đồ kiến trúc/nghiệp vụ được viết bằng TikZ trong nguồn chương; sơ đồ khái niệm có ghi rõ không phải kết quả thực nghiệm.
\begin{verbatim}
python3 -m venv report/build/visual-env
report/build/visual-env/bin/python -m pip install \
  -r report/scripts/requirements-figures.txt
make -C report figures
\end{verbatim}
Các file hình đã có trong repo nên build nội dung thường không cần cài matplotlib. Khi nguồn thực nghiệm đổi, cần xuất lại bảng và hình để giữ đồng bộ. Bộ kiểm tra report đối chiếu hash hình/nguồn và sẽ báo nếu hình đã lỗi thời.

\subsection{Nguồn benchmark nhận diện trên điện thoại}\label{sec:phone-benchmark-evidence}
Bộ benchmark hiện tại được đo trên bốn mẫu điện thoại: realme 15, Redmi Note 11, Redmi Note 13 và Samsung S10e. Mỗi máy được đánh giá với MobileNetV3-Large seed 159 và seed 1024, hai biến thể baseline/cắt tỉa và hai runtime ONNX/ExecuTorch, tổng cộng 32 cấu hình. Mỗi cấu hình thực hiện năm lượt warmup rồi xử lý 256 ảnh test. Phương án triển khai được lựa chọn là seed 1024 cắt tỉa chạy ExecuTorch/PTE; các cấu hình còn lại cung cấp đối chứng về chất lượng và độ trễ.

Kết quả từng phiên ghi thông tin thiết bị, model, nhãn dự đoán, confidence và thời gian xử lý từng ảnh. Các bảng được đối chiếu với dự đoán gốc, ma trận nhầm lẫn và hash model; Accuracy, macro-F1, sai lệch mức ngập và mean/P50/P95 được tổng hợp theo từng cấu hình. Thời gian bao gồm giải mã, tiền xử lý và suy luận tại điện thoại, không gồm truyền bài lên backend. Kết quả chính ở Mục~\ref{sec:phone-benchmark-results}; bảng chi tiết ở Mục~\ref{sec:phone-full-results}. Việc tổng hợp báo cáo sử dụng các phiên đã đo, không chạy suy luận lại.

\section{Tái lập RQ1 và stress}
Đánh giá phân cụm RQ1 cần đúng snapshot \texttt{6ac75c2} và notebook tương ứng. Bộ dữ liệu giữ split run 1--20/21--40/41--80. Cấu hình chọn có trong tệp cấu hình đã lưu kèm kết quả. Stress dùng các cấu hình này không tuning lại.

Nguồn stress chính gồm protocol, manifest, selected configs, checkpoint từng run/điều kiện, aggregate, duplicate mapping và runtime log. Notebook đã chạy được lưu kèm kết quả stress. Một lần chạy mới cần giữ seed, snapshot notebook, checksum dữ liệu và cấu hình; resume chỉ từ checkpoint có provenance khớp.

Có 1.400 fit ở full batch. Smoke một run không chứng minh full batch hoàn thành. Nếu chạy lại, giữ kết quả trong thư mục riêng và so sánh với nguồn chính; không gộp với \texttt{rq1\_results\_v2} hoặc chọn bản có kết quả tốt hơn.

\section{Tái lập và kiểm chứng kết quả RQ2/RQ3}
Nguồn RQ2 chứa summary, alignment, robustness, paired comparisons và sensitivity. Nguồn RQ3 chứa bảng theo điều kiện, bảng theo seed, destination assignments, partition losses và provenance tái phân tích. Bản theo seed là nguồn suy luận chính cho RQ3.

Script kiểm tra artifact và số liệu manuscript đã được lưu kèm theo môi trường khóa phiên bản. Cần môi trường biệt lập có đúng phiên bản được pin trước khi dùng script; không xem việc thiếu dependency là bằng chứng artifact sai. Bản báo cáo này xuất từ artifact đã lưu, không tuyên bố đã chạy lại bộ verifier trong môi trường khác.

Để tái lập suy luận RQ3 từ bảng đã lưu, script tái tính tầng seed lấy trung bình điều kiện theo seed, bootstrap 5.000 và Holm cho 14 endpoint trong mỗi block so sánh. Nguồn provenance ghi hash vào/ra và runtime. Giữ nguyên hướng metric khi diễn giải hiệu ghép cặp.

\section{Chạy demo và kiểm thử phần mềm}
Từ gốc repo, có thể build web và chạy Compose theo hướng dẫn hiện tại:
\begin{verbatim}
products/scripts/demo/build_web.sh
FE_BUILD_TARGET=prebuilt docker compose up -d --build
\end{verbatim}
Thao tác này tạo môi trường demo và có thể nạp dữ liệu bán tổng hợp nếu volume trống. Không dùng dữ liệu nạp này như yêu cầu cứu hộ thực. Đối với test backend cục bộ, đặt database/uploads ở vùng tạm trước import \texttt{main}, vì khởi tạo module có thể tạo/migrate database.

Kiểm thử backend và Flutter được hướng dẫn trong tài liệu sản phẩm. Kiểm thử luồng xử lý và giao diện được thực hiện trên điện thoại Android thật, kết hợp coordinator, backend và dashboard. Điện thoại cần truy cập được máy chủ và có bộ dữ liệu/model đúng phiên; các bài thử được phân biệt bằng tên lượt và ID. Thử SMS cần cấu hình số tiếp nhận của phiên kiểm tra.

\section{Phạm vi kiểm chứng}
Quá trình biên soạn không thực hiện lại huấn luyện MobileNet, suy luận ảnh, notebook Colab hoặc kiểm thử E2E trên Docker và Android; các kết quả được tổng hợp từ những phiên thực nghiệm đã lưu. Kết quả test lịch sử được dẫn rõ ngày và nguồn. Kiểm tra mới chỉ xác nhận tính nhất quán dữ liệu đầu vào bảng và khả năng biên dịch báo cáo. Phân biệt này giúp người đọc biết phần nào là kết quả nghiên cứu đã lưu và phần nào là kiểm tra biên soạn.

\section{Hồ sơ kiểm thử ứng dụng di động ngày 24/10/2026}
Nguồn chính là hai bộ JSON/CSV và \texttt{manifest.json} dưới \RepoPath{products/fe/experiment_mobile/results/SM-G970U/}, cùng tiền tố \RepoPath{2026-10-24_10-28-41-463525_mobile_run_001}; bộ run\_002 có thêm hậu tố \texttt{\_run\_002}. Chọn theo \texttt{goldRun}/\texttt{seedRun} trong manifest, không suy từ riêng tên thư mục. JSON giữ trạng thái hiện tại, lịch sử lần thử và quan sát backend; \texttt{loi\_thu\_cong.csv} giữ lỗi được người chạy ghi nhận. Bản trích nguồn và hash dùng cho các bảng nằm tại \RepoPath{report/generated/mobile-system/source-audit.json}. Các lượt ngày 23/10 được giữ làm lịch sử, không cộng thành lần lặp độc lập của hai lượt chính.

```

## appendices/supplementary-results.tex

```tex
\chapter{Kết quả và tư liệu bổ sung}\label{chap:supplementary}
\section{Danh mục dữ liệu và kết quả thực nghiệm}
Bảng~\ref{tab:source-register} tóm tắt các nhóm dữ liệu và phạm vi đánh giá. Quy trình tái lập được trình bày ở Phụ lục~\ref{chap:reproducibility}; kết quả chi tiết trên điện thoại ở Mục~\ref{sec:phone-full-results}.

\begin{longtable}{P{.22\textwidth}P{.39\textwidth}P{.28\textwidth}}
\caption{Các nhóm dữ liệu và phạm vi đánh giá}\label{tab:source-register}\\
\toprule Nhóm & Dữ liệu và mô hình & Phạm vi \\\midrule\endfirsthead
\toprule Nhóm & Dữ liệu và mô hình & Phạm vi \\\midrule\endhead
Phân loại ảnh & \ImageTotal{} ảnh, chia cố định thành tập huấn luyện, xác thực và kiểm thử & \ImageTest{} ảnh kiểm thử, bốn lớp \\
Chuyển đổi và tối ưu mô hình & MobileNetV3-Large seed 1024; FP32, PTQ, QAT và cắt tỉa & Cùng tập kiểm thử; so sánh trong từng phiên đo CPU \\
Nhận diện trên điện thoại & Hai seed 159/1024, mô hình gốc và cắt tỉa, ONNX/PTE & 32 cấu hình trên bốn máy; 256 ảnh mỗi cấu hình \\
Đánh giá khẩn cấp & Logistic Regression từ các dấu hiệu có cấu trúc & 32 trạng thái tổng hợp \\
Phân cụm RQ1 & Generator 3.0; đối chứng và thử nghiệm với nhiễu, bản sao & 40 lần chạy kiểm thử; 1.400 lượt phân cụm trong thử nghiệm nhiễu \\
Xếp hạng RQ2 & Candidate 4.1; chất lượng và độ ổn định điểm ưu tiên & 40 seed kiểm thử \\
Điều phối RQ3 & Candidate 4.1; ba điều kiện nguồn lực & So sánh theo 40 seed, lấy trung bình điều kiện trong mỗi seed \\
\bottomrule
\end{longtable}

\section{Sổ đối chiếu nguồn số liệu}
\begin{longtable}{P{.24\textwidth}P{.42\textwidth}P{.23\textwidth}}
\caption{Nguồn được dùng và phạm vi}\label{tab:source-provenance-register}\\
\toprule Nội dung & Nguồn trong repo & Phạm vi \\\midrule\endfirsthead
\toprule Nội dung & Nguồn trong repo & Phạm vi \\\midrule\endhead
Nhóm, mã đề tài & Hồ sơ đề tài đã lưu & Nguồn ưu tiên thông tin nhóm \\
Mục tiêu, tiến độ, sản phẩm & Thuyết minh NCKH (bản Markdown) & Văn bản trong repo, chưa thay bản ký \\
Số lượng/chia ảnh & Split CSV trong thư mục mô hình biên & Snapshot 1.702 ảnh \\
Metric/runtime FP32 & \RuntimeBenchmarkSource{} & 256 ảnh test, CPU \\
Benchmark bốn điện thoại & CSV tổng hợp và JSON nguồn của seed 159/1024 & 32 cấu hình; số liệu đầy đủ ở Mục~\ref{sec:phone-full-results} \\
Nén/cắt tỉa & \QuantizationBenchmarkSource{}; \PruningBenchmarkSource{} & Cùng test; khác phiên timing \\
LR khẩn cấp & Gói mô hình khẩn cấp có cấu trúc & SOURCE FINAL v5, tổng hợp \\
RQ1 đối chứng cơ sở & Thư mục kết quả đối chứng cơ sở & Generator 3.0, 40 test run \\
RQ1 stress & Thư mục kết quả stress & Nguồn chính, 1.400 fit \\
RQ2/RQ3 & Thư mục kết quả RQ2 và RQ3 & Candidate 4.1, 40 seed \\
Hợp đồng/DB & Tài liệu hợp đồng kết nối và cơ sở dữ liệu & Đối chiếu cùng mã hiện tại \\
Test lịch sử & Tài liệu đối chiếu nghiệm thu & Ngày 27/09/2026 \\
\bottomrule
\end{longtable}

Các bộ dữ liệu phân cụm, xếp hạng và điều phối là dữ liệu tổng hợp hoặc bán tổng hợp. Kết quả trên các bộ dữ liệu này được phân tích riêng với kết quả nhận diện ảnh và kiểm thử phần mềm.

\input{appendices/phone-benchmarks}

```

## appendices/phone-benchmarks.tex

```tex
\section{Kết quả đầy đủ của benchmark nhận diện trên điện thoại}\label{sec:phone-full-results}
Phần này công bố đủ 32 cấu hình của bộ benchmark có provenance, làm căn cứ cho ba bảng tóm tắt và kết luận tại Mục~\ref{sec:phone-benchmark-results}. Không loại cấu hình kém thuận lợi. Mỗi cấu hình dùng cùng 256 ảnh test, gồm 86 non\_flood, 56 low, 60 medium và 54 high; mỗi ảnh có một dự đoán trong từng phiên. Các phiên dùng lại ảnh nên không làm tăng số ảnh độc lập lên 8.192.

Mã cấu hình có dạng \texttt{seed-biến thể-máy-runtime}. B là baseline, P là cắt tỉa; RM15 là realme 15, RN11 là Redmi Note 11, RN13 là Redmi Note 13 và S10e là Samsung S10e. O là ONNX, T là ExecuTorch/PTE. Ví dụ, \texttt{1024-P-RN13-T} là seed 1024 cắt tỉa chạy PTE trên Redmi Note 13. Thông tin thiết bị, dataset và phạm vi đo được mô tả ở Mục~\ref{sec:phone-benchmark-setup}.

\subsection{Chất lượng phân loại theo cấu hình}
Accuracy (Acc.) là tỷ lệ dự đoán đúng; P/R/F1 macro là trung bình có trọng số bằng nhau của chỉ số tương ứng ở bốn lớp. Macro-Recall cũng chính là balanced accuracy trong bài toán này. Các giá trị phần trăm được làm tròn hai chữ số; CSV giữ độ chính xác cao hơn.
\input{generated/tables/phone-full-quality}

\subsection{Sai lệch thứ bậc và lỗi nặng}
Đặt $s(\mathrm{non\_flood})=0$, $s(\mathrm{low})=1$, $s(\mathrm{medium})=2$, $s(\mathrm{high})=3$. Với $e_i=s(\hat y_i)-s(y_i)$ và $n=256$, hai chỉ số bổ sung được tính như sau:
\[
\operatorname{MAE}=\frac{1}{n}\sum_{i=1}^{n}|e_i|,
\qquad
\operatorname{RMSE}=\sqrt{\frac{1}{n}\sum_{i=1}^{n}e_i^2}.
\]
Lỗi nặng là số ảnh có $|e_i|\geq2$. Khoảng cách giữa các mức được quy ước bằng một, không phải độ sâu ngập hay chi phí cứu hộ. MAE/RMSE chưa có trong JSON gốc; chúng được tính lại từ dự đoán, không chạy suy luận mới và không sửa dữ liệu nguồn.
\input{generated/tables/phone-full-ordinal}

\subsection{Thời gian xử lý theo cấu hình}
Mean là trung bình thời gian từng ảnh; P50/P95 dùng nearest-rank sau khi loại năm lượt warmup khỏi latency. Đơn vị là ms; phạm vi là giải mã, tiền xử lý và suy luận trong \texttt{classifyImage}. Bảng giữ thời gian riêng từng máy, không dùng thời gian tổng hợp thay cho kết quả từng thiết bị.
\input{generated/tables/phone-full-latency}

\subsection{Precision, Recall và F1 theo từng lớp}
Bảng gồm 128 hàng, tương ứng 32 cấu hình nhân bốn lớp. Cột số ảnh là số mẫu thật của lớp trong test; không phải số ảnh model dự đoán vào lớp đó. F1 được tính riêng từ Precision/Recall từng lớp, sau đó mới lấy trung bình để có macro-F1. Việc hai runtime có cùng nhãn top-1 làm các chỉ số này bằng nhau trong từng cặp máy/model, nhưng không chứng minh vector xác suất của hai runtime giống tuyệt đối.
\input{generated/tables/phone-full-classes}

\subsection{Truy vết nguồn và cách tổng hợp}
CSV tổng hợp được lưu ở \RepoPath{report/generated/phone-benchmarks/summary.csv}; các file \path{predictions.csv}, \path{class_metrics.csv} và \path{coverage.csv} nằm trong thư mục con \path{evaluate_model_phone}. Bốn CSV từng điện thoại nằm trong \path{evaluate_phone}; các bảng so sánh model và runtime ở \path{evaluate_baseline_pruning} và \path{evaluate_onnx_pte}. Mỗi dòng summary giữ nguồn JSON, hash nguồn, hash model/split, run ID và timestamp UTC để đối chiếu. Dự đoán từng ảnh và ma trận nhầm lẫn gốc vẫn được giữ trong CSV/JSON, không in hàng nghìn dòng vào báo cáo.

Bảy bảng được sinh bởi \RepoPath{report/scripts/build_phone_report_tables.py}; công cụ đối chiếu 32 JSON với hash nguồn, dự đoán, chỉ số, thời gian và support từng lớp trước khi xuất bảng. Bảng tóm tắt bốn phương án ở Chương~4 lấy trung bình chỉ số của tám phiên máy--runtime; số lỗi nặng cũng lấy trung bình nên có thể không nguyên. Các bảng trong phụ lục này giữ chỉ số riêng của từng phiên; không thay thế bằng một ma trận gộp các ảnh được dùng lại.

```

