"""Tham số mặc định cho pipeline v2.

Mọi hằng số ánh xạ trực tiếp tới ký hiệu trong Mục 4 của PaperV2.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class WeightParams:
    """Tham số hàm trọng số cạnh w_ij (Mục 4.2)."""

    sigma_geo_m: float = 700.0      # sigma_geo: bán kính đặc trưng (mét) ~ tầm ca nô
    tau_temp_min: float = 45.0      # tau_temp: hằng số thời gian (phút)
    tau_f: float = 0.25             # tau_F: độ nhạy chênh lệch mức ngập
    tau_e: float = 0.35             # tau_E: độ nhạy chênh lệch mức khẩn cấp
    beta: float = 0.5               # beta: trọng số thời gian
    gamma: float = 0.5              # gamma: trọng số ngữ cảnh
    edge_threshold: float = 0.05    # theta: ngưỡng epsilon để làm thưa đồ thị
    knn: int = 12                   # k: số láng giềng giữ lại (0 = tắt k-NN)
    # alpha: trọng số địa lý CHỈ dùng cho dạng cộng (baseline ablation).
    # Đặt = beta = gamma để baseline không bị hạ trọng số địa lý một cách bất
    # công; mọi so sánh cộng-vs-nhân đều phải công bố giá trị alpha đã dùng.
    alpha: float = 0.5


@dataclass(frozen=True)
class ConfidenceParams:
    """Tham số heuristic độ tin cậy C_i (Mục 4.1)."""

    b0: float = -0.2                # bias
    b1: float = 1.4                 # trọng số cho cờ 'có ảnh'
    b2: float = 0.9                 # trọng số cho log(1 + số báo cáo củng cố)
    corrob_radius_m: float = 400.0  # bán kính coi là 'lân cận' khi đếm củng cố
    corrob_window_min: float = 60.0 # cửa sổ thời gian coi là 'cùng diễn biến'


@dataclass(frozen=True)
class PriorityParams:
    """Tham số hàm ưu tiên P(C_k) (Mục 4.4)."""

    omega_e: float = 0.34           # omega_1: trọng số khẩn cấp
    omega_f: float = 0.33           # omega_2: trọng số ngập tối đa
    omega_n: float = 0.33           # omega_3: trọng số quy mô dân số
    v_scale: float = 10.0           # s: hệ số chống bão hòa tanh
    # mu: trần khuếch đại tổn thương, V_agg = 1 + (mu-1)*tanh(sum V_i / s).
    # mu = 1 tắt khuếch đại (chỉ còn lõi rủi ro), mu = 2 là mặc định chính sách.
    # Đây là núm ĐẠO ĐỨC do ban chỉ huy đặt: nó chặn mức mà tổn thương được phép
    # đảo thứ tự danh sách ưu tiên. Mọi kết quả báo cáo dùng mu = 2.
    v_cap_mu: float = 2.0
    # n_ref: mốc chuẩn hoá dân số N_max trong Ñ = log(1+sum N_i C_i)/log(1+N_max).
    # MẶC ĐỊNH LÀ TĨNH (500 người, cỡ dân số một khu tác chiến): với mốc động
    # (N_max = cụm lớn nhất của lần chạy hiện tại), P KHÔNG so sánh được xuyên
    # thời gian — một cụm tụt hạng chỉ vì nơi khác vừa xuất hiện cụm lớn hơn, dù
    # tình hình của nó không đổi. Với hệ điều phối trực tuyến đó là lỗi thiết kế.
    # Mọi số báo cáo trong bài dùng mốc TĨNH này; mức bất ổn của mốc động được
    # định lượng riêng trong Thí nghiệm 5 (n_ref động vs tĩnh).
    n_ref: float = 500.0


@dataclass(frozen=True)
class ClusterParams:
    """Tham số phân cụm (Mục 4.3)."""

    resolution: float = 1.0         # lambda: tham số độ phân giải
    random_state: int = 42


@dataclass(frozen=True)
class PipelineConfig:
    weight: WeightParams = field(default_factory=WeightParams)
    confidence: ConfidenceParams = field(default_factory=ConfidenceParams)
    priority: PriorityParams = field(default_factory=PriorityParams)
    cluster: ClusterParams = field(default_factory=ClusterParams)


DEFAULT_CONFIG = PipelineConfig()
