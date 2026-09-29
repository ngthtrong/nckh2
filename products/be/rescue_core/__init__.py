"""Lõi thuật toán phân cụm và xếp hạng ưu tiên theo bài báo ISDS 2026 #6444.

Khung mã lấy từ demo/v2 (commit a6be3e9), đã chỉnh để khớp công thức bài báo:
- Algorithm 1 / Eq. (2)-(3): G, T, C trên toàn bộ ma trận cặp như notebook
  Benchmark_Cij (commit 6ac75c2), ngưỡng quantile, top-k hợp hai chiều, Louvain.
- Eq. (1): Q_i = sigmoid(-0.2 + 1.4*1{ảnh} + 0.9*log(1+n_corrob)), n_corrob đếm
  payload quan sát phân biệt trong 400 m / 60 phút (demo/pipeline/attributes.py).
- Mục 2.3: gom bản gần trùng bằng thành phần liên thông (demo/pipeline/priority.py).
- Eq. (4): omega=(.34,.33,.33), mu=2, s=10, N_ref=500, V_cap=50.
Server chỉ gọi các hàm này; muốn đổi công thức thì phải đối chiếu lại với bài báo.
"""

from .clustering import ClusterRunV2, GraphConfigV2, run_graph_clustering
from .contracts import ReportV2
from .priority import ClusterPriorityV2, PriorityPolicyV2, score_clusters

__all__ = [
    "ClusterPriorityV2",
    "ClusterRunV2",
    "GraphConfigV2",
    "PriorityPolicyV2",
    "ReportV2",
    "run_graph_clustering",
    "score_clusters",
]
