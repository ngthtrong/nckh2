# REVIEW 3 — CÔNG THỨC TRỌNG SỐ VÀ PHÂN CỤM LOUVAIN

**Dự án:** Hệ thống phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI  
**Mục tiêu:** Chuẩn hóa công thức trọng số cho sự kiện, xây dựng đồ thị có trọng số từ dữ liệu mô phỏng, và áp dụng Louvain để trích xuất cộng đồng.

---

## 1. Bối cảnh và giả thiết thiết kế

Dữ liệu đầu vào gồm:

- GPS của người gửi báo cáo.
- Thời điểm gửi báo cáo.
- Nhãn ảnh từ Edge AI: `none / low / medium / high`.
- Nhãn văn bản từ Edge AI: `urgent_rescue / need_supplies / safe_update / irrelevant`.
- Tên, số điện thoại, và nội dung mô tả.

Mục tiêu của tầng backend là gom nhóm các báo cáo có khả năng thuộc cùng một sự kiện cứu hộ. Vì Louvain là thuật toán tối ưu hóa modularity trên đồ thị có trọng số, cách biểu diễn phù hợp nhất là xây đồ thị với:

- **Nút**: một báo cáo cứu hộ.
- **Cạnh**: hai báo cáo đủ gần nhau về không gian, thời gian, và có độ tương đồng ngữ nghĩa/khẩn cấp đủ cao.
- **Trọng số cạnh**: mức độ “nên nằm cùng cộng đồng” của hai báo cáo.

Lý thuyết nền phù hợp gồm:

- Louvain cho phát hiện cộng đồng trên đồ thị có trọng số [1].
- ST-DBSCAN/DBSCAN cho tiêu chí gần nhau trong không gian-thời gian [2][3].
- Các bộ dữ liệu multimodal khủng hoảng như CrisisMMD và FloodNet xác nhận tính hữu ích của việc kết hợp ảnh và văn bản trong ngữ cảnh thiên tai [4][5][6].

---

## 2. Công thức trọng số đề xuất

### 2.1 Chuẩn hóa các biến đầu vào

Đặt với mỗi báo cáo $i$:

- $t_i$: thời điểm gửi.
- $(lat_i, lng_i)$: tọa độ.
- $I_i$: nhãn ảnh.
- $T_i$: nhãn văn bản.
- $u_i$: điểm khẩn cấp tổng hợp của nút.

Các biến chuẩn hóa về miền $[0,1]$:

- $r_i$: độ mới của báo cáo.
- $d^t_i$: mật độ báo cáo trong cửa sổ thời gian lân cận.
- $d^s_i$: mật độ báo cáo trong bán kính không gian lân cận.
- $v^I_i$: điểm từ nhãn ảnh.
- $v^T_i$: điểm từ nhãn văn bản.

### 2.2 Công thức điểm nút

Điểm nút được dùng để xếp mức ưu tiên, đồng thời tham gia vào trọng số cạnh:

$$
u_i = \alpha r_i + \beta d^t_i + \gamma d^s_i + \delta v^I_i + \varepsilon v^T_i
$$

với:

$$
\alpha + \beta + \gamma + \delta + \varepsilon = 1
$$

Khuyến nghị khởi tạo:

- $\alpha = 0.25$ cho độ mới.
- $\beta = 0.20$ cho mật độ theo thời gian.
- $\gamma = 0.20$ cho mật độ theo không gian.
- $\delta = 0.20$ cho nhãn ảnh.
- $\varepsilon = 0.15$ cho nhãn văn bản.

### 2.3 Giải thích từng trọng số

#### $\alpha$ — độ mới của sự kiện

Rationale: báo cáo mới hơn thường đáng chú ý hơn trong bối cảnh bão lũ vì nhu cầu cứu hộ thay đổi nhanh. Thành phần này được mô hình hóa theo hàm suy giảm theo thời gian:

$$
r_i = e^{-\Delta t_i/\tau}
$$

trong đó $\Delta t_i$ là số giờ kể từ mốc tham chiếu, và $\tau$ là hằng số suy giảm.

#### $\beta$ — mật độ báo cáo theo thời gian

Rationale: khi nhiều người cùng gửi báo cáo trong cùng cửa sổ thời gian ngắn, xác suất các báo cáo thuộc cùng một sự kiện cao hơn. Đây là tín hiệu phù hợp với hướng phát hiện cụm sự kiện theo thời gian trong ST-DBSCAN [2].

Đề xuất:

$$
d^t_i = \frac{\log(1+n^t_i)}{\log(1+n^t_{max})}
$$

với $n^t_i$ là số báo cáo trong cửa sổ $[t_i-2h, t_i+2h]$.

#### $\gamma$ — mật độ báo cáo theo không gian

Rationale: nếu nhiều báo cáo tập trung trong bán kính nhỏ, chúng có khả năng phản ánh một ổ ngập hoặc điểm cứu hộ thực tế. Tín hiệu này cũng phù hợp với logic truy vấn không gian trong PostGIS và tiền lọc bằng khoảng cách địa lý.

Đề xuất:

$$
d^s_i = \frac{\log(1+n^s_i)}{\log(1+n^s_{max})}
$$

với $n^s_i$ là số báo cáo trong bán kính 1 km quanh báo cáo $i$.

#### $\delta$ — điểm từ nhãn ảnh

Rationale: nhãn ảnh phản ánh mức độ ngập trực quan. Trong thiên tai, đặc trưng hình ảnh là tín hiệu mạnh để nhận biết nguy cơ khu vực [5][6].

Khuyến nghị ánh xạ:

| Nhãn ảnh | Điểm |
|---|---:|
| `none` | 0.00 |
| `low` | 0.33 |
| `medium` | 0.67 |
| `high` | 1.00 |

#### $\varepsilon$ — điểm từ nhãn văn bản

Rationale: văn bản là tín hiệu trực tiếp về nhu cầu cứu hộ. Các bộ dữ liệu khủng hoảng đa phương thức cho thấy văn bản khẩn cấp có giá trị dự báo cao [4][6].

Khuyến nghị ánh xạ:

| Nhãn văn bản | Điểm |
|---|---:|
| `irrelevant` | 0.00 |
| `safe_update` | 0.25 |
| `need_supplies` | 0.65 |
| `urgent_rescue` | 1.00 |

---

## 3. Công thức trọng số cạnh cho đồ thị

Để Louvain hoạt động tốt, cạnh giữa hai báo cáo $i,j$ nên phản ánh xác suất hai báo cáo thuộc cùng một cộng đồng.

### 3.1 Điều kiện tạo cạnh

Chỉ tạo cạnh nếu đồng thời thỏa:

- $d_{ij} \le 1$ km.
- $\Delta t_{ij} \le 2$ giờ.

Đây là quy tắc tiền lọc hợp lý cho bối cảnh cứu hộ, và bám với thiết kế hệ thống hiện có sử dụng vùng đệm không gian-thời gian để gom nhóm.

### 3.2 Công thức cạnh

$$
w_{ij} = \lambda_1 e^{-d_{ij}/\sigma_d} + \lambda_2 e^{-\Delta t_{ij}/\sigma_t} + \lambda_3 s_{ij}^{label} + \lambda_4 \min(u_i, u_j)
$$

với:

- $d_{ij}$: khoảng cách Haversine giữa hai báo cáo.
- $\Delta t_{ij}$: chênh lệch thời gian theo giờ.
- $s_{ij}^{label}$: độ tương đồng nhãn.
- $u_i, u_j$: điểm nút.

Khuyến nghị khởi tạo:

- $\lambda_1 = 0.35$.
- $\lambda_2 = 0.25$.
- $\lambda_3 = 0.20$.
- $\lambda_4 = 0.20$.

với:

- $\sigma_d = 1$ km.
- $\sigma_t = 2$ giờ.

### 3.3 Độ tương đồng nhãn

Khuyến nghị định nghĩa:

- 1.00 nếu cả ảnh và văn bản đều cùng mức nghiêm trọng cao.
- 0.75 nếu cùng nhóm khẩn cấp gần nhau.
- 0.40 nếu một báo cáo là `safe_update` nhưng báo cáo kia là `need_supplies` cùng vị trí.
- 0.00 nếu một báo cáo là `irrelevant`.

Mục tiêu của thành phần này là giữ các báo cáo có cùng ngữ cảnh cứu hộ vào cùng cộng đồng, ngay cả khi chênh lệch thời gian nhỏ.

---

## 4. Cách giải thích trọng số trong báo cáo khoa học

Bạn có thể diễn giải ngắn gọn như sau:

1. **Trọng số thời gian** ưu tiên báo cáo mới và chùm báo cáo gửi liên tục.
2. **Trọng số mật độ** ưu tiên nơi xuất hiện nhiều báo cáo gần nhau, giảm nhiễu đơn lẻ.
3. **Trọng số ảnh** phản ánh mức độ ngập quan sát trực tiếp từ Edge AI.
4. **Trọng số văn bản** phản ánh mức độ khẩn cấp nội dung người dùng mô tả.
5. **Trọng số cạnh** kết hợp mọi tín hiệu để Louvain tìm các cộng đồng tự nhiên của sự kiện cứu hộ.

Về mặt thực nghiệm, công thức này giúp:

- Giảm gộp nhầm giữa các tin rời rạc ở xa nhau.
- Tăng khả năng gom các báo cáo cùng sự kiện trong cùng khu vực ngập.
- Tận dụng được cả metadata nhẹ khi mạng yếu.

---

## 5. Quy tắc kết nối sự kiện trong mô phỏng

Khi sinh dữ liệu mô phỏng, nên tạo cạnh trong các trường hợp sau:

- Cùng bán kính 1 km và cùng khung thời gian 2 giờ.
- Cùng khu dân cư, cùng hướng dòng ngập, khác nhau ở người gửi nhưng cùng nhãn `high` hoặc `urgent_rescue`.
- Một báo cáo `high + urgent_rescue` nối với báo cáo `medium + need_supplies` nếu cách nhau rất gần và chênh lệch thời gian nhỏ.
- Nhiều báo cáo cùng một điểm GPS nhưng khác nhau nhẹ về thời điểm, để mô phỏng dữ liệu trùng lặp.

---

## 6. Phương pháp trích xuất cộng đồng khuyến nghị

### 6.1 Phương án chính

- **Louvain**: phù hợp nhất để tối ưu modularity trên đồ thị có trọng số, nhanh và dễ trực quan hóa [1].

### 6.2 Phương án so sánh / dự phòng

- **Leiden**: ổn định hơn Louvain, ít gặp cộng đồng rời rạc.
- **DBSCAN/HDBSCAN**: tốt cho tiền xử lý không gian-thời gian trước khi dựng đồ thị.
- **ST-DBSCAN**: phù hợp khi muốn một bước gom cụm trực tiếp theo không gian-thời gian [2].

### 6.3 Diễn giải thực nghiệm

- Dùng DBSCAN/ST-DBSCAN để lọc noise và tạo nhóm ứng viên.
- Dùng Louvain trên đồ thị ứng viên để trích xuất cộng đồng cuối cùng.
- Dùng PostGIS để hỗ trợ truy vấn không gian và sinh tập cạnh.

---

## 7. Tài liệu tham khảo

[1] Blondel, V. D., Guillaume, J.-L., Lambiotte, R., & Lefebvre, E. (2008). *Fast unfolding of communities in large networks*. Journal of Statistical Mechanics: Theory and Experiment, 2008(10), P10008.

[2] Birant, D., & Kut, A. (2007). *ST-DBSCAN: An algorithm for clustering spatial–temporal data*. Data & Knowledge Engineering, 60(1), 208–221.

[3] Ester, M., Kriegel, H.-P., Sander, J., & Xu, X. (1996). *A density-based algorithm for discovering clusters in large spatial databases with noise*. KDD.

[4] Alam, F., Ofli, F., & Imran, M. (2018). *CrisisMMD: Multimodal Twitter Datasets from Natural Disasters*. ICWSM.

[5] Rahnemoonfar, M., et al. (2021). *FloodNet: A High Resolution Aerial Imagery Dataset for Post Flood Scene Understanding*. IEEE Access.

[6] Ofli, F., Alam, F., & Imran, M. (2020). *Analysis of Social Media Data using Multimodal Deep Learning for Disaster Response*. ISCRAM.

---

## 8. Ghi chú triển khai trên máy này

Để chạy nhanh trong môi trường hiện tại, bộ script mặc định dùng SQLite local tại `review3/data/review3.sqlite`. Nếu cần môi trường chuẩn hóa theo kiến trúc hệ thống, có thể bật PostGIS bằng `review3/docker-compose.yml`.

Luồng chạy nhanh:

1. `python review3/scripts/generate_sample_gps.py`
2. `python review3/scripts/import_sample_data.py`
3. `python review3/scripts/run_louvain.py`

Luồng đầy đủ với PostGIS:

1. `docker compose -f review3/docker-compose.yml up -d`
2. Đặt `DATABASE_URL=postgresql+psycopg://review3:review3@localhost:5432/review3`
3. Chạy lại 3 script ở trên.
