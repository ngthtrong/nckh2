# Changed report excerpts — partial scope, TeX source retained

\section{Đối chiếu nghiên cứu liên quan và khoảng trống}\label{sec:related-work}
\subsection{Nghiên cứu trong nước: quan trắc ngập và thông tin cứu hộ}
Các công trình trong nước giúp xác định rõ sự khác nhau giữa quan sát vùng ngập, ước lượng độ sâu và xử lý yêu cầu cứu hộ. Doan và Le-Thi nghiên cứu phát hiện ngập từ cặp ảnh SAR ở hai thời điểm, dùng kiến trúc Siamese và Swin-Transformer để biểu diễn thay đổi \citep{doan2025sar}. Đầu ra là vùng thay đổi trên ảnh vệ tinh. Cách tiếp cận này cung cấp thông tin không gian ở diện rộng, nhưng không trực tiếp cho biết một hộ dân đang cần được tiếp cận hay một bản tin là bản sao.

Ngô Thanh Vũ và cộng sự sử dụng ảnh biển báo giao thông, YOLOv11 và quan hệ hình học với chiều cao tham chiếu để quan trắc độ sâu ngập đô thị \citep{ngo2025urban}. Công trình cho thấy vai trò của vật chuẩn khi chuyển ảnh thành đại lượng vật lý. Đối với ảnh người dân gửi, một vật chuẩn có kích thước biết trước không luôn xuất hiện. Vì vậy, bốn lớp của đề tài là nhãn thị giác tương đối; báo cáo không đổi các lớp \texttt{low/medium/high} thành một giá trị độ sâu theo centimet.

Hai hướng trên có thể bổ sung bối cảnh cho hệ thống nếu sau này có nguồn dữ liệu và phép ghép không gian phù hợp. Tuy nhiên, trong repo hiện tại, chúng là tài liệu tổng quan, chưa phải dịch vụ được tích hợp hoặc dữ liệu huấn luyện của mô hình. Khoảng trống mà đề tài khảo sát nằm ở liên kết báo cáo, xử lý gửi lại khi mạng gián đoạn và kiểm tra hệ quả của thứ tự ưu tiên sau khi thông tin được tiếp nhận.

\subsection{Ảnh mặt đất và mô hình gọn cho tình huống khẩn cấp}
Lee và Joo giới thiệu AlleyFloodNet cho phát hiện có/không ngập từ ảnh mặt đất ở các khu vực đô thị dễ tổn thương, như hẻm và nhà bán hầm~\citep{lee2025alleyfloodnet}. Công trình nhấn mạnh ảnh ở góc nhìn gần và nhiều điều kiện ánh sáng. Đây là đối chiếu sát nguồn ảnh người dân, nhưng nhiệm vụ nhị phân khác phân loại bốn mức ngập của đề tài; không đối sánh trực tiếp Accuracy giữa hai bộ dữ liệu.

Kyrkou và Theocharides đề xuất EmergencyNet cho phân loại cảnh khẩn cấp từ ảnh UAV, dùng kết hợp đặc trưng tích chập giãn nở để giảm chi phí tính toán~\citep{kyrkou2020emergencynet}. Công trình cung cấp đối chiếu về mô hình gọn tại biên. Tuy nhiên, ảnh trên không khác ảnh điện thoại, và kết hợp đặc trưng trong mạng ảnh khác fusion ảnh--văn bản của báo cáo. Tốc độ của công trình không được dùng thay phép đo trên thiết bị của đề tài.

\subsection{So sánh theo đầu vào, đầu ra và điều kiện áp dụng}
Bảng~\ref{tab:related-work} so sánh các hướng ở mức bài toán, tránh đặt Accuracy phân loại cạnh F1 phân vùng như thể chúng đo cùng một nhiệm vụ. Các công trình được lựa chọn để giải thích từng thành phần của hệ thống; bảng không phải tổng quan hệ thống với tiêu chí tìm kiếm bao phủ toàn bộ ngành.
\begin{longtable}{P{.23\textwidth}P{.31\textwidth}P{.35\textwidth}}
\caption{Nghiên cứu liên quan và quan hệ với đề tài}\label{tab:related-work}\\
\toprule Công trình/hướng & Đầu vào và đầu ra & Quan hệ, điều kiện và giới hạn \\\midrule\endfirsthead
\toprule Công trình/hướng & Đầu vào và đầu ra & Quan hệ, điều kiện và giới hạn \\\midrule\endhead
Doan và Le-Thi~\citep{doan2025sar} & Cặp ảnh SAR; phát hiện thay đổi vùng ngập & Bối cảnh viễn thám; khác ảnh mặt đất và liên kết yêu cầu cứu hộ \\
Ngô Thanh Vũ và cộng sự~\citep{ngo2025urban} & Ảnh biển báo; ước lượng độ sâu nhờ tham chiếu hình học & Cần vật chuẩn và thông số; khác phân loại mức ngập tương đối \\
CrisisMMD \citep{alam2018crisismmd} & Bài đăng ảnh--văn bản thiên tai; nhãn phục vụ phân tích nhân đạo & Đã dùng nhãn informative trong pilot riêng ở Mục~\ref{sec:multimodal-pilot}; không phải nhãn mức ngập hoặc khẩn cấp cứu hộ tiếng Việt \\
FloodNet \citep{rahnemoonfar2021floodnet} & Ảnh UAV hậu thiên tai; hiểu cảnh và nhãn theo pixel & Góc nhìn trên không khác ảnh người dân; không suy ra parity dữ liệu \\
AlleyFloodNet \citep{lee2025alleyfloodnet} & Ảnh mặt đất; phân loại có/không ngập & Gần bối cảnh ảnh người dân, khác nhãn bốn mức; không phải dữ liệu huấn luyện của đề tài \\
EmergencyNet \citep{kyrkou2020emergencynet} & Ảnh UAV; phân loại cảnh khẩn cấp bằng CNN gọn & Tham chiếu thiết kế tại biên, khác góc nhìn và khác fusion ảnh--văn bản \\
MobileNetV3 \citep{howard2019mobilenetv3} & Ảnh; đặc trưng và phân loại với thiết kế cho thiết bị di động & Kiến trúc backbone của đề tài; vẫn cần tinh chỉnh và đo từng runtime \\
Louvain/Leiden \citep{blondel2008louvain,traag2019leiden} & Đồ thị có trọng số; cộng đồng nút & Không tự xác minh sự kiện thật; kết quả phụ thuộc cách dựng cạnh \\
Bundle Protocol v7 \citep{rfc9171} & Bundle trong mạng gián đoạn; lưu và chuyển tiếp qua các nút & Chuẩn tham chiếu DTN; outbox HTTP hiện tại chưa triển khai BPv7 \\
Đề tài hiện tại & Báo cáo ảnh/mô tả/vị trí; cụm và danh sách hỗ trợ điều phối & Nguyên mẫu và thực nghiệm tổng hợp; còn cần dữ liệu/kiểm chứng vận hành \\
\bottomrule
\end{longtable}

Điểm đóng góp của đề tài nằm ở tích hợp suy luận ảnh, lưu và gửi lại báo cáo, bản đồ cùng lõi liên kết sự kiện và ưu tiên trong một nguyên mẫu. Khác các công trình tập trung nhận diện ảnh, báo cáo kiểm tra cả multiplicity và hệ quả của thứ tự điều phối bằng đối chứng đơn giản. Kết quả hiện có chưa xác lập ưu thế thuật toán hoặc lợi ích nghiệp vụ tổng quát; đóng góp tích hợp và câu hỏi thực nghiệm cần được đánh giá riêng.


\section{Phạm vi của phương pháp}\label{sec:02-scope}
RQ1--RQ3 đánh giá hành vi trên dữ liệu bán tổng hợp hoặc tổng hợp, chưa đo hiệu quả cứu hộ thực địa. Bộ ảnh gồm ảnh nhóm tự chụp và ảnh nhóm thu thập từ web theo xác nhận bổ sung ngày 10/11/2026; hiện chưa có ánh xạ đầy đủ nguồn/sự kiện theo từng ID hoặc chỉ số đồng thuận nhãn. Các hằng số của $Q_i$ và điểm ưu tiên vẫn là heuristic cần xác nhận nghiệp vụ. Các giới hạn chung được tập hợp tại Mục~\ref{sec:04-evaluation-limitations}.

Logistic Regression năm cờ trong bản mã được đối chiếu học nhãn OR tự sinh, không phải mô hình xử lý văn bản tự do hoặc xác suất nguy kịch đã hiệu chuẩn. Hai pilot riêng đã học classifier văn bản, ảnh và fusion cho informative tiếng Anh hoặc request trên bản dịch/nhãn AI. DistilBERT frozen và fine-tuning được đánh giá riêng; xác suất request không được đồng nhất với khẩn cấp hoặc ưu tiên điều phối.

\subsection{Tình trạng tích hợp di động}\label{sec:mobile-integration-status}
\MobileIntegrationVI{} Việc cập nhật mobile thuộc nhóm phát triển riêng; báo cáo ghi nhận thông tin này theo xác nhận của nhóm, phân biệt thông tin triển khai với kết quả đo offline. Bộ APK, phiên bản mô hình, hợp đồng đầu vào/đầu ra và log của bản mobile đó chưa nằm trong hồ sơ được đối chiếu tại đây. Vì vậy các metric pilot ở Mục~\ref{sec:vi-silver-pilot} và Mục~\ref{sec:multimodal-pilot} được giữ là kết quả offline, không gán thành chất lượng của bản APK.

Ablation ảnh/văn bản/cả hai đã thực hiện trong từng pilot với target và ID test chung. Nhãn silver xuất phát từ câu nguồn, không phải gold do người độc lập xem cả ảnh và văn bản. Xác nhận trên corpus tiếng Việt gốc, nhãn span, mức khẩn cấp và các tình huống thiếu/mâu thuẫn nguồn vẫn cần bằng chứng riêng. Tình trạng thực hiện từng nội dung được đối chiếu tại Mục~\ref{sec:proposal-comparison}.


\subsection{Khắc phục phần mềm và kiểm hồi quy mới}\label{sec:software-revision-checks}
Đợt hiệu chỉnh ngày 10/11/2026 bổ sung bằng chứng từ bản mã đang đối chiếu, tách với hai lượt Android lịch sử. Sáu kiểm thử tái hiện lỗi khi gửi SOS/báo cáo hoặc đồng bộ hoàn tất sau khi controller đã đóng, thao tác gọi vào controller đã đóng và probe mạng phát sinh lỗi. Trước sửa cả sáu không đạt; sau sửa đều đạt. Controller không còn thông báo giao diện sau dispose hoặc khởi tạo lần gửi mới khi đã đóng; lỗi probe đi theo đường fallback, giữ bản ghi và trạng thái SMS chưa xác nhận.

\begin{table}[htbp]\centering\small
\caption{Bằng chứng phần mềm của đợt khắc phục mới}\label{tab:software-revision-checks}
\begin{tabular}{P{.28\textwidth}P{.25\textwidth}P{.36\textwidth}}\toprule
Phạm vi & Kết quả & Điều kiện \\\midrule
Hồi quy lỗi gửi/đồng bộ & \SoftwareTargetedPass{} đạt sau sửa & Chờ phản hồi, đóng controller, lỗi probe; không giả lập kết quả SMS đã giao \\
Flutter toàn bộ unit/widget & \SoftwareFlutterPass{} đạt, \SoftwareFlutterSkipped{} bỏ qua & Kiểm outbox, giữ phiên, tài khoản, trạng thái và các chức năng app \\
Backend API và đồ thị & \SoftwareBackendPass{} đạt & Có \SoftwareGraphTests{} phép kiểm bản sao, nội dung khác và hàng xem xét \\
App Linux--backend thật & \SoftwareLinuxPass{} kịch bản đạt & Mất mạng/phục hồi; gửi ảnh, nhận trạng thái và chặn sửa chéo; DB tạm riêng \\
\bottomrule\end{tabular}
\end{table}

Backend đã khử bản sao trước quantile/top-$k$ theo khóa exact gồm các trường mô hình, mô tả, liên hệ và định danh ảnh. Không thêm ngưỡng gần trùng; nội dung khác được giữ riêng dù scalar giống nhau. Nút canonical có khóa ổn định, còn đầu ra giữ mọi ID báo cáo gốc và ánh xạ bản sao. Kiểm nhân bản 2/5 lần trên fixture giữ số cặp, cạnh, ngưỡng, phân hoạch và điểm ưu tiên; các ca thiếu vị trí vẫn vào hàng xem xét. Đây là hồi quy của adapter triển khai, không phải lần đánh giá lại RQ1--RQ3.

Phép tích hợp mới chạy app Linux và backend HTTP loopback với SQLite/uploads tạm, không chạm dữ liệu vận hành. Nó kiểm được đường outbox--máy chủ, chưa phải phép thử Android qua mạng di động hoặc SMS thật. Không có thiết bị Android kết nối trong đợt này. Bằng chứng mới không được gán ngược thành raw của Case 8 lịch sử hoặc kết luận hai sự cố có cùng nguyên nhân.


\addchap{KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN}\label{chap:conclusion}
\addsec{Kết luận}
Đề tài xây dựng nguyên mẫu gồm ứng dụng Flutter có suy luận ảnh tại biên, backend FastAPI và Web GIS. Baseline MobileNetV3-Large đạt Accuracy \NewImageAccuracy\%, macro-F1 \NewImageMacroFOne\% trên \ImageTest{} ảnh; benchmark điện thoại giữ 32 cấu hình trên bốn máy. McNemar chưa xác lập cải thiện của pruning lịch sử. Thử thêm 5/10/20\% chọn mức 5\% bằng validation nhưng macro-F1 test còn \LocalPrunedFOne\%; model nguyên mẫu được giữ riêng.

Hai pilot ngoại tuyến đã đánh giá văn bản và fusion trên nhãn informative hoặc bản dịch tiếng Việt/nhãn AI. Fusion silver đạt macro-F1 \VISilverFusionFOne\%, recall request \VISilverFusionRecall\%; T2 CUDA đạt trung bình \VISilverFineFOne\%, recall \VISilverFineRecall\%. CI chưa xác lập ưu thế fusion. \MobileIntegrationVI{} Tình trạng bàn giao APK và giới hạn sử dụng các metric được trình bày tại Mục~\ref{sec:mobile-integration-status}.

RQ1 chưa xác lập Product hơn Additive độc lập (ARI 0,9072 so với 0,9191; Holm $p=0{,}2560$). RQ2 hỗ trợ bất biến bản sao exact khi grouping cố định, chưa xác lập alignment tốt hơn chung; ba raw $p$ Spearman và năm Holm vẫn chưa khớp replay. RQ3 revised kém nearest-first về harm và trễ hạn mô phỏng. Những kết quả âm này giới hạn việc suy từ điểm số thuật toán sang lợi ích điều phối thực tế.

Đợt hiệu chỉnh đã sửa đường xử lý khi thao tác gửi/đồng bộ hoàn tất sau khi controller đóng và khi probe mạng lỗi; kiểm hồi quy cùng tích hợp Linux--backend được ghi ở Mục~\ref{sec:software-revision-checks}. Backend cũng khử bản sao exact trước quantile/top-$k$, giữ ánh xạ về mọi báo cáo gốc. Đây là bằng chứng phần mềm mới, không thay kết quả RQ lịch sử hoặc kiểm thử Android qua mạng viễn thông.

Đóng góp chính là nguyên mẫu tích hợp tiếp nhận--lưu--gửi lại--hiển thị thông tin, cùng thiết kế và thực nghiệm có đối chứng cho phân cụm và ưu tiên. Đề tài cung cấp nền tảng nghiên cứu/đào tạo về Edge AI và hệ thống thông tin cứu hộ; hiệu quả cứu hộ thực địa chưa được đo.

\addsec{Hạn chế và kiến nghị}
Bộ ảnh có cả ảnh nhóm tự chụp và ảnh thu thập web, nhưng hồ sơ nguồn theo từng ID, độ đồng thuận nhãn và tính độc lập sự kiện chưa đầy đủ. Hai pilot văn bản dùng nguồn ngoại ngữ hoặc bản dịch/nhãn AI; corpus tiếng Việt gốc và gold độc lập vẫn cần xác nhận. Mô tả và số liệu kiểm thử Android lịch sử chưa có đủ raw để kiểm lại; Linux và kiểm thử tự động không thay thế bằng chứng SMS, camera hoặc mạng di động thật. Các giới hạn được tập hợp tại Mục~\ref{sec:04-evaluation-limitations}.

Nên tiếp tục sử dụng nguyên mẫu trong nghiên cứu và đào tạo. Mọi quyết định nghiệp vụ cần người xác minh, kiểm soát quyền truy cập và bảo vệ thông tin liên hệ, vị trí, người yếu thế. Chẩn đoán thêm PTQ/QAT và đo lặp hiệu năng, pin/RAM nằm ngoài phạm vi đợt hiệu chỉnh này.

\addsec{Hướng nghiên cứu tiếp theo}
\begin{itemize}
\item Xác nhận NLP/fusion trên tin tiếng Việt gốc, gold độc lập và test sự kiện mới; trích xuất thông tin cần nhãn span và đánh giá riêng;
\item Nghiên cứu lịch điều phối xét chi phí di chuyển, năng lực đội và thời hạn, so với nearest-first và chính sách hiện có; đây là hướng phát triển, không được thực thi trong đợt này;
\item Nghiên cứu định vị GPS, Wi-Fi, mạng di động và mốc địa chỉ có nguồn, thời điểm, độ bất định; khi mâu thuẫn cần người xác minh, không tạo tọa độ giả;
\item Nghiên cứu tiếp nhận âm thanh qua ASR tiếng Việt và trích xuất thông tin, đánh giá riêng tiếng địa phương, nhiễu mưa/gió, lỗi chép và độ trễ;
\item Nghiên cứu mất kết nối hoàn toàn: lưu cục bộ chưa đồng nghĩa giao tới trung tâm; SMS cần sóng/gateway, DTN cần relay và đường ra; báo hộ hoặc đội tại chỗ cần xác minh và phản hồi;
\item Xây dựng phương án thí điểm với đơn vị cứu hộ, mạng viễn thông/SMS thật và quy trình bảo vệ dữ liệu. Đây chỉ là kiến nghị hướng phát triển; báo cáo không ghi nhận đã tổ chức thí điểm.
\end{itemize}
