"""Tìm cách xếp lưới tốt cho một hình: lọc nhanh bằng ước lượng, chấm thật bằng định tuyến.

Ước lượng (rẻ): khoảng cách lưới giữa hai đầu quan hệ, phạt chéo (cần bẻ góc),
đường thẳng đi xuyên ô có hộp, và số giao cắt của các đoạn nối tâm ô.
Điểm thật (đắt): sau khi định tuyến — độ dài, số lần bẻ, số giao cắt, nhãn va
chạm, lỗi hình học, diện tích.
"""
import itertools, random


def est(pos, rels, occupied):
    cost = 0
    segs = []
    for a, b in rels:
        if a == b:
            continue
        (r1, c1), (r2, c2) = pos[a], pos[b]
        d = abs(r1 - r2) + abs(c1 - c2)
        cost += (d - 1) * 12 + (6 if r1 != r2 and c1 != c2 else 0)
        if r1 == r2:
            for c in range(min(c1, c2) + 1, max(c1, c2)):
                if (r1, c) in occupied:
                    cost += 18
        if c1 == c2:
            for r in range(min(r1, r2) + 1, max(r1, r2)):
                if (r, c1) in occupied:
                    cost += 18
        segs.append(((c1, r1), (c2, r2)))
    for (p1, q1), (p2, q2) in itertools.combinations(segs, 2):
        if len({p1, q1, p2, q2}) < 4:
            continue
        if _inter(p1, q1, p2, q2):
            cost += 5
    return cost


def _inter(p1, p2, p3, p4):
    def o(a, b, c):
        v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        return (v > 0) - (v < 0)
    return o(p1, p2, p3) * o(p1, p2, p4) < 0 and o(p3, p4, p1) * o(p3, p4, p2) < 0


def search(grid, rels, iters=6000, seeds=6, keep=8, fixed=(), zones=None):
    """zones: tên -> tập ô được phép (giữ mỗi nhóm trong khối của nó)."""
    R, C = len(grid), max(len(r) for r in grid)
    cells = [(r, c) for r in range(R) for c in range(C)]
    names = [n for row in grid for n in row if n]
    pool = {}
    for seed in range(seeds):
        rnd = random.Random(seed)
        pos = {}
        for r, row in enumerate(grid):
            for c, n in enumerate(row):
                if n:
                    pos[n] = (r, c)
        if seed and zones:
            byz = {}
            for n in names:
                byz.setdefault(frozenset(zones[n]), []).append(n)
            for z, ns in byz.items():
                cl = sorted(z)
                rnd.shuffle(cl)
                for n, c in zip(ns, cl):
                    pos[n] = c
        elif seed:
            free_names = [n for n in names if n not in fixed]
            free_cells = [cl for cl in cells if cl not in {pos[f] for f in fixed}]
            rnd.shuffle(free_cells)
            for n, cl in zip(free_names, free_cells):
                pos[n] = cl
        occ = set(pos.values())
        cur = est(pos, rels, occ)
        T = 30.0
        for it in range(iters):
            n = rnd.choice([x for x in names if x not in fixed])
            cl = rnd.choice(sorted(zones[n]) if zones else cells)
            other = next((m for m, p in pos.items() if p == cl), None)
            if other in fixed or other == n:
                continue
            old = pos[n]
            pos[n] = cl
            if other:
                pos[other] = old
            occ = set(pos.values())
            new = est(pos, rels, occ)
            if new <= cur or rnd.random() < pow(2.718, (cur - new) / T):
                cur = new
                key = tuple(sorted(pos.items()))
                pool[key] = cur
            else:
                pos[n] = old
                if other:
                    pos[other] = cl
            T = max(0.5, T * 0.999)
    best = sorted(pool.items(), key=lambda kv: kv[1])
    out, seen = [], set()
    for key, sc in best:
        g = [[None] * C for _ in range(R)]
        for n, (r, c) in key:
            g[r][c] = n
        if not zones:   # bỏ hàng/cột trống (giữ nguyên khi có khối nhóm)
            g = [row for row in g if any(row)]
            cols = [j for j in range(C) if any(row[j] for row in g)]
            g = [[row[j] for j in cols] for row in g]
        sig = str(g)
        if sig in seen:
            continue
        seen.add(sig)
        out.append((sc, g))
        if len(out) >= keep:
            break
    return out
