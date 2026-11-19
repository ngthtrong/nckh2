# Khảo sát dữ liệu từ bài báo cho RQ1–RQ3

Ngày chốt khảo sát: **29/10/2026**. Phạm vi: dữ liệu quốc tế, ưu tiên lũ lụt và yêu cầu cứu hộ; giữ nguyên ba RQ trong [bài báo hiện tại](../../paper/main.tex). Đây là khảo sát có ghi vết và kiểm tra khả dụng, chưa phải kết quả chạy lại RQ hoặc một systematic review toàn diện.

**Cập nhật sau tìm kiếm mở rộng:** xem [báo cáo so sánh đợt 2](round2/README.md) trước khi chọn dữ liệu. **Chưa chốt IDRISI-D cho RQ1**: KeralaRescue sát yêu cầu cứu hộ hơn nhưng chưa lấy được snapshot lịch sử; Ushahidi Haiti có bản xuất tải được để cân nhắc pilot ngoài miền. **TREC-IS vẫn là ứng viên ưu tiên cho bằng chứng bổ trợ RQ2 về ưu tiên thông tin**. Chưa có nguồn đã kiểm tra nào thay trực tiếp toàn bộ RQ1/RQ2; RQ3 vẫn cần tách rõ mô phỏng trên đầu vào thực. Các thống kê và ma trận bên dưới là hồ sơ của đợt đầu, được giữ để truy vết.

**Tiếp tục với bản bài báo KeralaRescue gốc:** đã xác minh [PDF người dùng tải](paper/1-s2.0-S2212420922001273-main.pdf) và chuẩn bị [hồ sơ tiếp cận dữ liệu/pilot Kerala](kerala-rescue/README.md), gồm thư xin dữ liệu chưa gửi, ánh xạ trường và protocol riêng. PDF không nhúng dữ liệu; Slack chưa truy cập được, tên miền KeralaRescue hiện trả trang bán tên miền. Chưa nhận tệp yêu cầu cứu hộ hoặc tạo kết quả RQ mới.

## 1. Đã thực hiện

- Thực hiện **40 truy vấn** theo bốn hướng của kế hoạch và mở rộng theo tài liệu tham chiếu; sàng lọc **34 công trình**. Có **13 công trình được đọc có mục tiêu ở các phần dữ liệu/phương pháp/đánh giá hoặc khả dụng dữ liệu**; mức đọc của từng bài được ghi riêng.
- Tải và kiểm tra **6 nguồn dữ liệu**, thêm IDRISI-D ngoài nhóm đầu mối ban đầu vì có văn bản, thời gian và thông tin địa lý cùng hàng.
- Sinh **600 dòng kiểm tra sự hiện diện của trường**, 100 dòng mỗi nguồn, cùng thống kê trên toàn bộ tệp hoặc tập con đã tải. Đây là kiểm tra cấu trúc tự động, **không phải 600 nhãn được xác nhận thủ công**, cũng không phải 600 mẫu độc lập.
- Lưu URL, phản hồi HTTP, phạm vi tải và SHA-256; với DisasterLocDesc chỉ đọc một thành viên ZIP bằng HTTP range và kiểm tra CRC, không tải toàn bộ archive.
- Soạn yêu cầu dữ liệu theo RQ, quy trình gán nhãn pilot và protocol đánh giá tiếp theo. Chưa tạo nhãn của người gán hoặc số đo hiệu quả thuật toán mới.

Hồ sơ chi tiết: [bảng bài báo](papers.csv), [ghi chú đọc sâu](paper-notes.md), [nhật ký tìm kiếm](search-log.md), [bảng ứng viên dữ liệu](datasets.csv), [kết quả kiểm tra](audit/profiles.json).

Các vấn đề được phân mức và gắn hướng xử lý trong [quality-findings.csv](audit/quality-findings.csv).

## 2. Kết quả kiểm tra tệp thật

Các số dưới đây được tính bằng [script kiểm tra](scripts/audit_sources.py), trên đúng các tệp có mã băm trong [sổ nguồn](audit/sources.json). Chúng không mặc định bằng quy mô công bố trong bài báo.

| ID | Nguồn/phần đã kiểm tra | Quan sát trên tệp | Giới hạn quyết định |
|---|---|---|---|
| D01 | HumAID, event-wise set1 | 43.409 hàng, 13 sự kiện; không lặp ID; 6 hàng dư do trùng nguyên văn không rỗng | Chỉ có `tweet_id`, `tweet_text`, `class_label`; nhãn chủ đề không phải gold sự cố hay ưu tiên. Con số khác tên liên kết “47K” chưa được giải thích. |
| D02 | TREC-IS, bundle training 2018–2020B | 97.577 hàng thuộc 71 sự kiện; 21.118 hàng thiếu văn bản; sau nhóm theo sự kiện/ID có 53.938 nhóm có văn bản | Các hàng lặp trong artifact không được xem là bản sao tin nhắn tự nhiên. Có `postPriority`; thiếu vị trí và thời gian có cấu trúc. |
| D03 | CrisisFACTS 2022, `allFacts` | 1.778 fact tham chiếu thuộc 8 thiên tai | Đây là fact để đánh giá tóm tắt; chưa tải luồng báo cáo gốc, không có gold sự cố cứu hộ nhỏ lẻ. |
| D04 | DisasterLocDesc v2, Batch1–St Louis | 200 hàng; 185 hàng có footprint; 9 hàng mang chủ đề “Requests or urgent needs” | Không có full tweet; footprint có thể là vùng/địa danh nền. Không suy kết quả này cho toàn bộ 7.149 tweet của bộ công bố. |
| D05 | England flooding/water rescue, workbook công khai | 266.767 hàng sau mở rộng hàng lặp của ODS; 13 trường dữ liệu | Chỉ có vùng LSOA và năm tài chính; thiếu tọa độ chính xác, thời điểm điều phối, nội dung báo cáo và ID sự cố. |
| D06 | IDRISI-D, English Harvey train | 360 hàng có văn bản, `created_at` và ít nhất một tọa độ địa danh OSM; 495 location mention | 447/495 mention thuộc City/town, State hoặc Country. Tọa độ tâm địa danh không phải vị trí cần cứu hộ chính xác. |

Nguồn tài liệu: [HumAID](https://crisisnlp.qcri.org/humaid_dataset), [TREC-IS](https://www.dcs.gla.ac.uk/~richardm/TREC_IS/2020/data.html), [CrisisFACTS](https://crisisfacts.github.io/), [DisasterLocDesc](https://doi.org/10.6084/m9.figshare.31044040.v2), [hướng dẫn England](https://www.gov.uk/government/statistics/fire-statistics-incident-level-datasets/flooding-and-water-rescue-incidents-dataset-guidance), [IDRISI-D](https://github.com/rsuwaileh/IDRISI/tree/main/LMD).

### Những phát hiện cần giữ nguyên khi thiết kế thí nghiệm

1. **IDRISI-D và HumAID có quan hệ nguồn:** 358/360 ID của phần IDRISI-D đã kiểm tra xuất hiện trong HumAID set1. Không dùng hai tên corpus làm hai tập xác nhận độc lập. Không thấy ID chung giữa hai phần HumAID/TREC đã tải; điều đó chưa chứng minh mọi phiên bản của chúng độc lập.
2. **TREC cần chuẩn hóa đơn vị:** có 72.983 cặp sự kiện/ID, trong đó 20.966 nhóm lặp. Không thấy xung đột nhãn ưu tiên trong các nhóm lặp đã kiểm tra. Chỉ giữ một bản ghi chuẩn cho mỗi cặp sau đối chiếu văn bản/nhãn; giữ nested judgments làm provenance, không nhân cỡ mẫu.
3. **Hai bất nhất metadata chưa được nguồn giải thích:** HumAID set1 có ít hàng hơn tên liên kết tải; workbook England ghi datacut `12-May-26` trong khi trang hướng dẫn ghi `1 May 2026`. Chọn snapshot bằng checksum, ghi cả hai mô tả; không tự sửa một phía.
4. **Điều khoản theo từng bản phát hành:** `Licensing.txt` trong HumAID yêu cầu dùng cho nghiên cứu humanitarian computing, giữ kín nội dung, và xóa theo yêu cầu/khi hoàn tất nghiên cứu. Không áp nhãn CC lấy từ một mirror cho bundle này. Figshare DisasterLocDesc và kho IDRISI-D ghi CC BY 4.0; giấy phép bài báo, mã và dữ liệu phải phân biệt.

## 3. Khuyến nghị cho từng RQ

| RQ | Nguồn ưu tiên | Nguồn dự phòng/bổ trợ | Phần có thể đánh giá và điều kiện |
|---|---|---|---|
| **RQ1** | D06 IDRISI-D làm nguồn khởi đầu cho pilot gán nhãn sự cố | D04 DisasterLocDesc; các bộ Harvey chuyên yêu cầu cứu hộ khi lấy được dữ liệu gốc | Cần xác minh vị trí thực sự chỉ nơi cần cứu, đủ độ phân giải; bổ sung gold cùng/khác sự cố độc lập. Hiện chưa có benchmark trực tiếp đã sẵn sàng. |
| **RQ2** | D02 TREC-IS cho nhãn mức cần chú ý của thông tin | D01 HumAID để tìm tin nhu cầu; dữ liệu Harvey có nhãn ưu tiên nếu tiếp cận được | Nhãn TREC là ở mức tin nhắn, chưa phải mức cụm hoặc lợi ích cứu hộ. Chỉ chạy score gốc trên tập đủ đầu vào và nhãn cùng đơn vị; nếu không, giữ ở phân tích bổ trợ. |
| **RQ3** | Báo cáo thực đủ điều kiện từ pilot RQ1, kết hợp mô hình điều phối khóa trước | D05 để khảo sát phân bố nguồn lực/kết quả theo nhóm; bài tình huống Shenzhen cho giả định mô hình | Tách nguồn nhu cầu thực khỏi đội cứu hộ, deadline, thời gian phục vụ và harm còn mô phỏng. Chưa có dữ liệu đủ để kết luận lợi ích cứu hộ thực. |

**Thứ tự thực hiện tiếp theo:** kiểm tra pilot địa điểm và sự cố của D06 → khóa rubric/nhãn → xác định phần RQ1/RQ2 đủ điều kiện → thiết kế RQ3 trên cùng tập đủ điều kiện. Nếu bước vị trí hoặc gold incident thất bại, ghi nhận thất bại và chuyển nguồn; không thay địa chỉ thiếu bằng tâm thành phố hoặc nhãn do thuật toán sinh.

Nguồn ưu tiên ở đây là **ưu tiên khảo sát/pilot**, không phải tuyên bố đã vượt các cổng khoa học. [Yêu cầu dữ liệu](rq-requirements.md) và [protocol](evaluation-protocol.md) quy định các cổng đó.

## 4. Những nguồn phù hợp về chủ đề nhưng chưa sẵn sàng

- Nhóm bài Harvey có yêu cầu cứu hộ thực đáng truy nguyên. Tuy nhiên, bài của Feng và cộng sự chưa cung cấp một tệp từng yêu cầu tải được trong các tài liệu đã xem. Wang và cộng sự ghi mục khả dụng dữ liệu là “Not applicable”. [Feng 2022](https://doi.org/10.32866/001c.37903), [Wang 2022](https://jshang2.github.io/pubs/rescue.pdf).
- **VictimFinder** và bài **Khallouli 2025** ghi dữ liệu cung cấp theo yêu cầu. Chưa gửi yêu cầu hoặc nhận dữ liệu; mã công khai không chứng minh quyền truy cập dữ liệu. [VictimFinder](https://par.nsf.gov/servlets/purl/10338275), [Khallouli 2025](https://link.springer.com/article/10.1007/s13278-025-01462-7).
- Bài **112 calls 2026** xác nhận dữ liệu cuộc gọi không công khai. Đây là bằng chứng về loại dữ liệu cần tìm, chưa phải lựa chọn chạy được. [Bài gốc](https://nhess.copernicus.org/articles/26/3943/2026/nhess-26-3943-2026.html).
- **PetaBencana** có schema phù hợp báo cáo ngập, nhưng tài liệu archive có yêu cầu API key khác với bảng endpoint cũ. Phản hồi thực tế của lần kiểm tra lưu ở [access receipt](audit/petabencana-access.json); chưa có mẫu báo cáo archive được xác minh. [Tài liệu archive](https://docs.petabencana.id/authenticated-api/laporan-urun-saya-arsip).
- Lần gọi archive PetaBencana không có khóa trả **HTTP 403**; không dùng dữ liệu ví dụ trong tài liệu API làm bản ghi quan sát thực.
- **FloodNet/RescueNet** được loại khỏi vai trò benchmark trực tiếp RQ1–RQ3: chúng phục vụ ảnh UAV và thiệt hại, thiếu chuỗi báo cáo/nhãn đúng bài toán. [FloodNet](https://arxiv.org/abs/2012.02951), [RescueNet](https://doi.org/10.1038/s41597-023-02799-4).

## 5. Tái lập và trạng thái hoàn thành

Yêu cầu: Python 3.10+; `requests` chỉ cần khi tải. Dữ liệu thô mặc định ở `/tmp/nckh2-dataset-search-20261029`, nằm ngoài repo. Hồ sơ theo dõi chỉ chứa thống kê, cấu trúc, liên kết và provenance.

```bash
# Tính lại từ cache đã tải; đối chiếu checksum trước khi đọc.
python3 docs/dataset-search/scripts/audit_sources.py

# Tải đúng snapshot rồi tính lại; từ chối nếu nguồn đổi byte/checksum.
python3 docs/dataset-search/scripts/audit_sources.py --download \
  --cache-dir /tmp/nckh2-dataset-search-20261029

# Kiểm tra tính nhất quán của hồ sơ, không cần mạng/dữ liệu thô.
python3 docs/dataset-search/scripts/validate_dossier.py
```

[Mẫu hiện diện trường](audit/sample-presence.csv) không chứa văn bản, số điện thoại hoặc địa chỉ của người cần cứu. Cột `location=True` chỉ nói có cấu trúc địa lý trong tệp; ý nghĩa và độ chính xác phải đọc cùng profile nguồn. Mẫu England là 100 hàng đầu; các nguồn khác lấy 100 vị trí cách đều trong thứ tự tệp. Không dùng các mẫu này để ước lượng tính đại diện hay cỡ mẫu suy luận.

[Biên bản kiểm tra](audit/validation.json) ghi kết quả tái lập profile/mẫu, kiểm tra từ chối checksum sai, tải lại HTTP range và kiểm tra tính nhất quán của hồ sơ.

Giai đoạn khảo sát/kiểm tra khả dụng đã có đầu ra và khuyến nghị cho cả ba RQ. **Gán nhãn bởi hai người, kiểm chứng ngữ nghĩa từng địa điểm, chạy thuật toán và đánh giá thực nghiệm mới là phần chưa thực hiện.** Hướng dẫn và biểu mẫu cho các bước này ở [annotation-guide.md](annotation-guide.md); nhãn hiện để trống.
