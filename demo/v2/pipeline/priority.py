"""Hàm ưu tiên cấp cụm P(C_k) — Mục 4.4.

P(C_k) = V_agg * ( w1*Ẽ_agg + w2*F̃_max + w3*Ñ )   [lõi rủi ro chuẩn hóa, V nhân ngoài]

Ẽ_agg  = (1/|C|) sum E_i*C_i                  [khẩn cấp TB có trọng số tin cậy]
F̃_max  = max (F_i*C_i)                         [nguyên lý bình thông nhau, gate tin cậy]
Ñ      = log(1+sum N_i*C_i) / log(1+N_max)    [dân số, gate C_i, nén log, chuẩn hóa]
V_agg  = 1 + tanh( (1/s) sum V_i )            [hệ số khuếch đại công bằng, chống bão hòa]
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .attributes import Event
from .config import PriorityParams


@dataclass
class ClusterScore:
    cluster_id: int
    size: int
    e_agg: float          # Ẽ_agg (đã chuẩn hóa/[0,1])
    f_max: float          # F̃_max
    n_total_raw: float    # sum N_i*C_i (thô, trước nén log)
    n_norm: float         # Ñ (đã nén log + chuẩn hóa)
    v_agg: float          # V_agg in (1,2)
    core: float           # lõi rủi ro = w1*Ẽ + w2*F̃ + w3*Ñ
    priority: float       # P(C_k) = V_agg * core
    center_lat: float
    center_lng: float
    member_ids: list[str]


def _cluster_members(events: list[Event], labels: list[int]) -> dict[int, list[Event]]:
    groups: dict[int, list[Event]] = {}
    for ev, lab in zip(events, labels):
        groups.setdefault(lab, []).append(ev)
    return groups


def score_clusters(
    events: list[Event],
    labels: list[int],
    params: PriorityParams,
    gate_confidence: bool = True,
    normalize_v: bool = True,
    gate_fmax: bool = True,
) -> list[ClusterScore]:
    """Tính P(C_k) cho mọi cụm.

    gate_confidence=False  -> N_total = sum N_i (không gate C_i, cho ablation)
    normalize_v=False      -> V_agg cộng vào lõi thay vì nhân (cho ablation)
    gate_fmax=False        -> F_max = max F_i (không gate C_i, cho ablation)
    """
    groups = _cluster_members(events, labels)

    # N_max để chuẩn hóa dân số: tổng dân số (đã gate) của cụm lớn nhất
    n_totals = {}
    for cid, members in groups.items():
        if gate_confidence:
            n_totals[cid] = sum(ev.n_trapped * ev.confidence for ev in members)
        else:
            n_totals[cid] = sum(ev.n_trapped for ev in members)
    n_max = max(n_totals.values()) if n_totals else 1.0
    log_nmax = math.log1p(n_max) if n_max > 0 else 1.0

    scores: list[ClusterScore] = []
    for cid, members in groups.items():
        size = len(members)
        e_agg = sum(ev.urgency * ev.confidence for ev in members) / size
        if gate_fmax:
            f_max = max(ev.flood * ev.confidence for ev in members)
        else:
            f_max = max(ev.flood for ev in members)
        n_raw = n_totals[cid]
        n_norm = (math.log1p(n_raw) / log_nmax) if log_nmax > 0 else 0.0

        v_sum = sum(ev.vulnerability for ev in members)
        v_agg = 1.0 + math.tanh(v_sum / params.v_scale)

        core = params.omega_e * e_agg + params.omega_f * f_max + params.omega_n * n_norm

        if normalize_v:
            priority = v_agg * core
        else:
            # dạng cộng ngây thơ (ablation): V góp một số hạng cộng
            priority = core + (v_agg - 1.0)

        center_lat = sum(ev.lat for ev in members) / size
        center_lng = sum(ev.lng for ev in members) / size

        scores.append(
            ClusterScore(
                cluster_id=cid,
                size=size,
                e_agg=round(e_agg, 4),
                f_max=round(f_max, 4),
                n_total_raw=round(n_raw, 2),
                n_norm=round(n_norm, 4),
                v_agg=round(v_agg, 4),
                core=round(core, 4),
                priority=round(priority, 4),
                center_lat=round(center_lat, 6),
                center_lng=round(center_lng, 6),
                member_ids=[ev.event_id for ev in members],
            )
        )

    scores.sort(key=lambda s: s.priority, reverse=True)
    return scores
