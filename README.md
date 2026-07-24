# Phân cụm và xếp hạng sự kiện cứu hộ bão lũ bằng đồ thị trọng số

Đây là mã nguồn và tài liệu nghiên cứu cho khung **Weighted Graph-Based Event
Clustering and Priority Scoring for Flood-Rescue Coordination Using Edge AI**.
Khung giải pháp chuyển mỗi báo cáo cứu hộ thành một vector thuộc tính gọn nhẹ,
xây dựng đồ thị không gian–thời gian–ngữ cảnh, phân cụm bằng Louvain/Leiden và
xếp hạng các cụm để hỗ trợ điều phối cứu hộ.

Kho lưu trữ hiện tập trung vào **mô hình toán học, pipeline thực nghiệm, bộ dữ
liệu mô phỏng, dashboard minh họa và bài báo khoa học**. Mobile app, mô hình AI
trên thiết bị biên và backend thời gian thực chưa được triển khai trong phiên
bản này.

## Ý tưởng chính

Mỗi sự kiện cứu hộ được biểu diễn bởi:

```text
vᵢ = (Lᵢ, Tᵢ, Fᵢ, Eᵢ, Nᵢ, Vᵢ, Cᵢ)
```

Trong đó `L` là vị trí, `T` là thời gian, `F` là mức ngập, `E` là mức khẩn cấp,
`N` là số người mắc kẹt, `V` là mức dễ bị tổn thương và `C` là độ tin cậy của
báo cáo.

Pipeline gồm bốn bước:

1. Trích xuất vector thuộc tính tại thiết bị biên.
2. Tạo đồ thị trọng số với khoảng cách địa lý đóng vai trò **cổng nhân**
   (multiplicative gate), hạn chế việc ghép các điểm ở quá xa nhau.
3. Phân cụm các sự kiện thành vùng tác nghiệp bằng Louvain hoặc Leiden.
4. Tính điểm ưu tiên cấp cụm, trong đó mức dễ bị tổn thương đóng vai trò hệ số
   khuếch đại.

## Kết quả nổi bật

Các kết quả dưới đây được sinh từ bộ dữ liệu mô phỏng tất định gồm 285 sự kiện
tại Huế, Quảng Trị, Quảng Nam và Đà Nẵng (`seed=42`):

| Kết quả | Giá trị |
|---|---:|
| ARI của Louvain/Leiden | 0.892 |
| Đường kính cụm trung bình: trọng số cộng → gating | 100.07 km → 0.30 km |
| Modularity trung bình qua 10 seed | 0.8311 |
| Giảm số nạn nhân ảo nhờ confidence gate | 55% |
| Kendall's τ trung bình khi nhiễu trọng số ±0.10 | 0.9857 |
| Top-3 được giữ nguyên khi nhiễu trọng số ±0.10 | 99% |
| Kích thước gói metadata JSON | 100–111 byte |

Đây là kết quả trên **dữ liệu synthetic**, không phải bằng chứng về hiệu năng
triển khai cứu hộ thực tế. Các giới hạn và hướng kiểm chứng tiếp theo được trình
bày trong bài báo.

## Cấu trúc dự án

```text
.
├── demo/
│   ├── data/                 # Sinh và lưu bộ dữ liệu synthetic
│   ├── pipeline/             # Thuộc tính, trọng số, phân cụm, ưu tiên, metrics
│   ├── experiments/          # 10 nhóm thí nghiệm và mã sinh hình
│   ├── results/
│   │   ├── tables/           # Kết quả thô dạng JSON
│   │   └── figures/          # Biểu đồ dùng trong bài báo
│   ├── dashboard/            # Dashboard Leaflet tự chứa dữ liệu
│   └── run_all.py            # Chạy toàn bộ pipeline 13 bước
├── paper/
│   ├── main.tex              # Bài báo theo định dạng Springer LNCS
│   ├── references.bib
│   ├── figures/
│   └── main.pdf              # Bản PDF đã biên dịch
├── resource/                 # Thuyết minh và tài liệu giải thích công thức
├── loop/                     # Báo cáo review và kế hoạch xử lý theo vòng
├── archive/                  # Tài liệu phiên bản cũ, không dùng làm nguồn hiện tại
└── LaTeX2e_Proceedings_Template/
                               # Template LNCS tham khảo
```

## Cài đặt

Yêu cầu Python 3.11 trở lên. Từ thư mục gốc của dự án:

```bash
python3 -m venv demo/.venv
source demo/.venv/bin/activate
python -m pip install --upgrade pip
python -m pip install numpy networkx python-louvain scikit-learn scipy \
  matplotlib igraph leidenalg
```

`igraph` và `leidenalg` cần thiết cho các thí nghiệm sử dụng Leiden. Louvain có
thể chạy chỉ với `networkx` và `python-louvain`, nhưng `run_all.py` cần đầy đủ
các thư viện ở trên.

## Chạy thực nghiệm

Chạy toàn bộ quy trình:

```bash
cd demo
./.venv/bin/python run_all.py
```

Quy trình sẽ tạo lại dataset, chạy 10 nhóm thí nghiệm, sinh 7 hình và dựng lại
dashboard. Kết quả được ghi vào:

- `demo/results/tables/*.json`
- `demo/results/figures/*.png`
- `demo/dashboard/dashboard.html`

Có thể chạy riêng từng phần, ví dụ:

```bash
cd demo
./.venv/bin/python data/generate.py
./.venv/bin/python experiments/exp1_formula_validation.py
./.venv/bin/python experiments/exp4_baselines.py
./.venv/bin/python experiments/make_figures.py
./.venv/bin/python dashboard/build_dashboard.py
```

Mở `demo/dashboard/dashboard.html` trong trình duyệt để xem bản đồ và thứ tự ưu
tiên của các cụm. Dashboard nhúng dữ liệu trực tiếp vào HTML, nhưng cần Internet
để tải Leaflet và lớp bản đồ OpenStreetMap.

## Biên dịch bài báo

Máy cần có bộ công cụ LaTeX hỗ trợ `pdflatex` và `bibtex`:

```bash
cd paper
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Các hình trong `paper/figures/` được đồng bộ từ kết quả thực nghiệm. Khi thay
đổi công thức hoặc tham số, nên chạy lại `demo/run_all.py`, kiểm tra các file
JSON, cập nhật hình trong bài báo rồi mới biên dịch lại `paper/main.pdf`.

## Tính tái lập và phạm vi

- Dataset mặc định dùng `seed=42`, gồm 240 sự kiện lõi, 20 điểm nhiễu và 25 sự
  kiện stress-test.
- Tham số mặc định nằm tại `demo/pipeline/config.py`.
- Mỗi thí nghiệm ghi kết quả máy đọc được dưới dạng JSON.
- `archive/` chỉ dùng để lưu phiên bản cũ và không phản ánh trạng thái hiện tại.
- Kết quả chưa được xác nhận trên dữ liệu cứu hộ thực, dữ liệu mạng xã hội hoặc
  trong điều kiện vận hành ngoài hiện trường.

## Nhóm nghiên cứu

- Giảng viên hướng dẫn: TS. Nguyễn Thanh Khoa
- Chủ nhiệm: Lê Thị Ngọc Ảnh
- Thành viên: Nguyễn Thanh Trọng, Cao Tường Hưng, Nguyễn Như Quỳnh, Ngô Hưng Thịnh

Đơn vị: Trường Công nghệ Thông tin và Truyền thông, Đại học Cần Thơ.
