"""Bộ dựng sơ đồ ER ký pháp chân chim: bố cục lưới tay, định tuyến vuông góc A*.

Nguyên tắc:
* Đường nối chỉ đi ngang/dọc; không được đi xuyên hộp, không chạy chồng lên
  đường khác (phạt rất nặng), hạn chế bẻ góc.
* Cổng nối trên mỗi cạnh hộp được rải đều và sắp theo vị trí đầu bên kia để
  đỡ cắt nhau.
* Nhãn quan hệ đặt trên đoạn dài nhất còn chỗ trống; kiểm va chạm với hộp,
  nhãn khác và đường khác.
Một hình học dùng chung cho hai đầu ra: SVG (vector, chèn luận văn) và PNG.
"""
from __future__ import annotations
import heapq, html, math
from dataclasses import dataclass, field
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = "C:/Windows/Fonts/"
FS = 12          # cỡ chữ thuộc tính
FS_H = 12.5      # cỡ chữ tiêu đề hộp
FS_L = 10.5      # cỡ chữ nhãn quan hệ
ROW = 17
HEAD = 22
PADX = 7
CELL = 8         # bước lưới định tuyến
STUB = 3         # số ô đoạn thẳng bắt buộc ở mỗi đầu (chỗ vẽ ký hiệu lực lượng)
GAPX = 120
GAPY = 96
FS_T = 11.5      # tên bảng ở hình tổng quan
FS_TAG = 9

_fonts = {}


def font(size, bold=False, italic=False):
    name = "times" + ("bd" if bold else "") + ("i" if italic else "") + ".ttf"
    if bold and italic:
        name = "timesbi.ttf"
    k = (name, size)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(FONT_DIR + name, size=int(round(size * 4)))  # đo ở x4
    return _fonts[k]


def tw(text, size, bold=False, italic=False):
    return font(size, bold, italic).getlength(text) / 4


def snap(v):
    return int(round(v / CELL)) * CELL


@dataclass
class Box:
    name: str
    attrs: list            # (is_pk, name, type, nullable)
    context: bool = False
    x: float = 0
    y: float = 0
    w: float = 0
    h: float = 0
    minw: float = 0        # hộp ngữ cảnh giãn theo số cổng (xem Diagram.fit_context)
    minh: float = 0
    table: bool = False    # hộp PDM tổng quan: tên bảng + nhãn [T]/[U]
    tags: list = field(default_factory=list)
    color: str = "#1F3864"
    fill: str = "#DCE6F2"

    def measure(self):
        if self.table:
            tagw = sum(tw(t, FS_TAG) + 9 for t in self.tags) + (6 if self.tags else 0)
            self.w = max(snap(tw(self.name, FS_T, bold=True) + 2 * PADX + tagw + CELL / 2), self.minw)
            self.h = max(snap(26), self.minh)
            return
        if self.context:
            self.w = max(snap(tw(self.name, FS_H, italic=True) + 2 * PADX + 16), self.minw)
            self.h = max(snap(HEAD + 10), self.minh)
            return
        c1 = max([tw(a[1], FS, underline_bold(a)) for a in self.attrs] + [0])
        c2 = max([tw(a[2] + ("  N" if a[3] else ""), FS) for a in self.attrs] + [0])
        self.col1 = 18
        self.col2 = self.col1 + c1 + 14
        w = self.col2 + c2 + PADX
        w = max(w, tw(self.name, FS_H, bold=True) + 2 * PADX)
        self.w = snap(w + CELL / 2) if snap(w) < w else snap(w)
        self.h = snap(HEAD + ROW * len(self.attrs) + 6 + CELL / 2)

    @property
    def rect(self):
        return (self.x, self.y, self.x + self.w, self.y + self.h)


def underline_bold(a):
    return False


@dataclass
class Rel:
    a: str
    b: str
    label: str
    ca: str               # ký hiệu sát hộp a
    cb: str               # ký hiệu sát hộp b
    ident: bool
    sa: str = ""          # cạnh của a: L R T B
    sb: str = ""
    pa: tuple = ()
    pb: tuple = ()
    path: list = field(default_factory=list)
    lab: tuple = ()       # (x, y, w, h) hộp nhãn


NORMAL = {"L": (-1, 0), "R": (1, 0), "T": (0, -1), "B": (0, 1)}


class Diagram:
    def __init__(self, title=""):
        self.boxes: dict[str, Box] = {}
        self.rels: list[Rel] = []
        self.title = title
        self.panels = []   # (nhãn, màu viền, màu nền, [tên hộp]) — nền nhóm, KHÔNG phải vật cản

    # ------------------------------------------------------------ bố cục
    def layout(self, grid, colgap=GAPX, rowgap=GAPY, align=None):
        """grid: danh sách hàng, mỗi hàng là danh sách tên (None = ô trống)."""
        for b in self.boxes.values():
            b.measure()
        ncol = max(len(r) for r in grid)
        colw = [0] * ncol
        rowh = [0] * len(grid)
        for i, r in enumerate(grid):
            for j, n in enumerate(r):
                if n:
                    colw[j] = max(colw[j], self.boxes[n].w)
                    rowh[i] = max(rowh[i], self.boxes[n].h)
        xs, x = [], CELL * 6
        for w in colw:
            xs.append(x)
            x += w + colgap
        ys, y = [], CELL * 6
        for h in rowh:
            ys.append(y)
            y += h + rowgap
        for i, r in enumerate(grid):
            for j, n in enumerate(r):
                if n:
                    b = self.boxes[n]
                    va = (align or {}).get(n, "c")
                    b.x = snap(xs[j] + (colw[j] - b.w) / 2)
                    if va == "t":
                        b.y = snap(ys[i])
                    elif va == "b":
                        b.y = snap(ys[i] + rowh[i] - b.h)
                    else:
                        b.y = snap(ys[i] + (rowh[i] - b.h) / 2)
        self.W = snap(x - colgap + CELL * 6)
        self.H = snap(y - rowgap + CELL * 6)

    # ------------------------------------------------------------ chọn cạnh
    def choose_sides(self, force=None):
        force = force or {}
        for r in self.rels:
            k = (r.a, r.b, r.label)
            if k in force:
                r.sa, r.sb = force[k]
                continue
            A, B = self.boxes[r.a], self.boxes[r.b]
            if r.a == r.b:          # vòng tự quan hệ: phải -> dưới (phía trên hay sát viền nhóm)
                r.sa, r.sb = "R", "B"
                continue
            ax0, ay0, ax1, ay1 = A.rect
            bx0, by0, bx1, by1 = B.rect
            ox = min(ax1, bx1) - max(ax0, bx0)    # chồng theo x
            oy = min(ay1, by1) - max(ay0, by0)    # chồng theo y
            if oy > 2 * CELL:                      # cùng hàng → nối ngang
                r.sa, r.sb = ("R", "L") if ax0 < bx0 else ("L", "R")
            elif ox > 2 * CELL:                    # cùng cột → nối dọc
                r.sa, r.sb = ("B", "T") if ay0 < by0 else ("T", "B")
            else:                                  # chéo → chữ L, ưu tiên ra ngang
                r.sa = "R" if ax0 < bx0 else "L"
                r.sb = "T" if ay0 < by0 else "B"

    def fit_context(self):
        """Hộp ngữ cảnh chỉ có tên nên rất nhỏ; nhiều đường đổ vào thì ký hiệu chân
        chim đè nhau. Giãn cạnh theo số cổng: mỗi cổng 3 ô lưới. Trả về True nếu
        có hộp đổi cỡ (khi đó phải dựng lại bố cục)."""
        changed = False
        for b in self.boxes.values():
            if not (b.context or b.table):
                continue
            n = {s: 0 for s in "LRTB"}
            for r in self.rels:
                if r.a == b.name:
                    n[r.sa] += 1
                if r.b == b.name:
                    n[r.sb] += 1
            mh = snap((max(n["L"], n["R"]) + 1) * 3 * CELL)
            mw = snap((max(n["T"], n["B"]) + 1) * 3 * CELL)
            if mh > b.minh or mw > b.minw:
                b.minh, b.minw = max(b.minh, mh), max(b.minw, mw)
                changed = True
        return changed

    # ------------------------------------------------------------ rải cổng
    def assign_ports(self):
        """Đặt cổng theo vị trí MONG MUỐN rồi dãn cách tối thiểu.

        * Hai hộp đối diện (R↔L hoặc B↔T) có khoảng chồng: cả hai đầu nhắm cùng
          một toạ độ giữa khoảng chồng → đường thẳng, không bẻ.
        * Hai hộp chéo (đường chữ L): mỗi đầu nhắm phía gần hộp kia nhất →
          một lần bẻ.
        Sau đó trên mỗi cạnh, xếp theo toạ độ mong muốn và dãn cách >= GAP.
        """
        GAP = 3 * CELL
        want = {}
        for i, r in enumerate(self.rels):
            A, B = self.boxes[r.a], self.boxes[r.b]
            if r.a == r.b:
                want[(i, "a")] = A.y + A.h - CELL * 2
                want[(i, "b")] = A.x + A.w - CELL * 2
                continue
            for which, me, other, side in (("a", A, B, r.sa), ("b", B, A, r.sb)):
                if side in "LR":
                    hm = 0 if (me.context or me.table) else HEAD
                    ho = 0 if (other.context or other.table) else HEAD
                    lo = max(me.y + hm, other.y + ho) + (CELL if hm == 0 else 0)
                    hi = min(me.y + me.h, other.y + other.h) - CELL
                    if (r.sa in "LR") == (r.sb in "LR") and hi > lo:
                        want[(i, which)] = (lo + hi) / 2
                    else:   # chữ L: đầu ngang nhắm sát phía hộp kia
                        want[(i, which)] = me.y + me.h - CELL * 2 if other.y > me.y else me.y + HEAD + CELL
                else:
                    lo, hi = max(me.x, other.x) + CELL, min(me.x + me.w, other.x + other.w) - CELL
                    if (r.sa in "TB") == (r.sb in "TB") and hi > lo:
                        want[(i, which)] = (lo + hi) / 2
                    else:   # đầu dọc nhắm thẳng tới tâm-x của hộp kia nếu được
                        cx = other.x + other.w / 2
                        want[(i, which)] = min(max(cx, me.x + CELL * 2), me.x + me.w - CELL * 2)
        ends = {}
        for i, r in enumerate(self.rels):
            ends.setdefault((r.a, r.sa), []).append((i, "a"))
            ends.setdefault((r.b, r.sb), []).append((i, "b"))
        for (bn, side), lst in ends.items():
            B = self.boxes[bn]
            if side in "LR":
                lo, hi = B.y + (HEAD if not (B.context or B.table) else CELL), B.y + B.h - CELL
            else:
                lo, hi = B.x + CELL * 2, B.x + B.w - CELL * 2
            lst.sort(key=lambda k: want[k])
            pos = [min(max(snap(want[k]), snap(lo)), snap(hi)) for k in lst]
            for j in range(1, len(pos)):                     # dãn xuôi
                pos[j] = max(pos[j], pos[j - 1] + GAP)
            if pos and pos[-1] > hi:                          # tràn thì đẩy ngược
                pos[-1] = snap(hi) if snap(hi) <= hi else snap(hi) - CELL
                for j in range(len(pos) - 2, -1, -1):
                    pos[j] = min(pos[j], pos[j + 1] - GAP)
            if pos and pos[0] < lo:                           # vẫn không đủ chỗ: rải đều
                n = len(pos)
                pos = [snap(lo + (hi - lo) * (j + 1) / (n + 1)) for j in range(n)]
            for k, v in zip(lst, pos):
                i, which = k
                r = self.rels[i]
                if side == "L":
                    pt = (B.x, v)
                elif side == "R":
                    pt = (B.x + B.w, v)
                elif side == "T":
                    pt = (v, B.y)
                else:
                    pt = (v, B.y + B.h)
                if which == "a":
                    r.pa = pt
                else:
                    r.pb = pt

    def straighten(self):
        """Hai đầu đối diện lệch nhau vài ô sinh khúc gãy chữ Z. Dời một đầu về
        cùng toạ độ với đầu kia nếu vẫn nằm trong cạnh và cách các cổng khác ≥ GAP."""
        GAP = 3 * CELL
        for _ in range(3):
            moved = False
            for r in self.rels:
                if r.a == r.b:
                    continue
                horiz = r.sa in "LR" and r.sb in "LR"
                vert = r.sa in "TB" and r.sb in "TB"
                if not (horiz or vert):
                    continue
                k = 1 if horiz else 0
                if r.pa[k] == r.pb[k]:
                    continue
                for which in ("b", "a"):
                    bn, side = (r.b, r.sb) if which == "b" else (r.a, r.sa)
                    tgt = r.pa[k] if which == "b" else r.pb[k]
                    B = self.boxes[bn]
                    lo, hi = ((B.y + (HEAD if not (B.context or B.table) else CELL), B.y + B.h - CELL) if horiz
                              else (B.x + CELL * 2, B.x + B.w - CELL * 2))
                    if not lo <= tgt <= hi:
                        continue
                    others = [(o.pa if o.a == bn and o.sa == side else o.pb)[k]
                              for o in self.rels if o is not r and
                              ((o.a == bn and o.sa == side) or (o.b == bn and o.sb == side))]
                    if all(abs(tgt - v) >= GAP for v in others):
                        if which == "b":
                            r.pb = (r.pb[0], tgt) if horiz else (tgt, r.pb[1])
                        else:
                            r.pa = (r.pa[0], tgt) if horiz else (tgt, r.pa[1])
                        moved = True
                        break
            if not moved:
                break

    # ------------------------------------------------------------ định tuyến
    def route(self, order=None):
        W, H = self.W // CELL + 1, self.H // CELL + 1
        blocked = [[False] * H for _ in range(W)]
        for b in self.boxes.values():
            x0, y0, x1, y1 = b.rect
            for gx in range(int(x0 // CELL) - 1, int(x1 // CELL) + 2):
                for gy in range(int(y0 // CELL) - 1, int(y1 // CELL) + 2):
                    if 0 <= gx < W and 0 <= gy < H:
                        blocked[gx][gy] = True
        used_h = {}   # (gx,gy) -> số đường đi ngang qua
        used_v = {}
        # Viền nền nhóm: coi như một đường đã có — được CẮT ngang, không được chạy
        # DỌC theo (trông như đường nối biến mất vào viền). Tên nhóm là vật cản.
        for lab, col, fil, (x0, y0, x1, y1) in self.panel_rects():
            gx0, gy0, gx1, gy1 = round(x0 / CELL), round(y0 / CELL), round(x1 / CELL), round(y1 / CELL)
            for gx in range(gx0, gx1 + 1):
                used_h[(gx, gy0)] = 1; used_h[(gx, gy1)] = 1
            for gy in range(gy0, gy1 + 1):
                used_v[(gx0, gy)] = 1; used_v[(gx1, gy)] = 1
            lw = tw(lab, 10.5, bold=True) + 12
            for gx in range(gx0, gx0 + int(lw // CELL) + 2):
                for gy in range(gy0, gy0 + 3):
                    if 0 <= gx < W and 0 <= gy < H:
                        blocked[gx][gy] = True
        # Đoạn ra cổng (STUB ô) và một ô đệm hai bên là của RIÊNG đường đó: đường
        # khác chạy qua đây sẽ trông như nối vào hộp sai.
        reserved = {}
        for i, r in enumerate(self.rels):
            for p, side in ((r.pa, r.sa), (r.pb, r.sb)):
                nx, ny = NORMAL[side]
                for k in range(0, STUB + 1):
                    for lat in (-1, 0, 1):
                        cx = p[0] // CELL + nx * k + (lat if nx == 0 else 0)
                        cy = p[1] // CELL + ny * k + (lat if ny == 0 else 0)
                        if lat == 0 or k < STUB:
                            reserved.setdefault((cx, cy), set()).add(i)
        idx = {id(r): i for i, r in enumerate(self.rels)}
        rels = order or sorted(self.rels, key=lambda r: abs(r.pa[0] - r.pb[0]) + abs(r.pa[1] - r.pb[1]))
        for r in rels:
            me = idx[id(r)]
            blk = lambda x, y: blocked[x][y] or bool(reserved.get((x, y), set()) - {me})
            na, nb = NORMAL[r.sa], NORMAL[r.sb]
            s = (r.pa[0] // CELL + na[0] * STUB, r.pa[1] // CELL + na[1] * STUB)
            g = (r.pb[0] // CELL + nb[0] * STUB, r.pb[1] // CELL + nb[1] * STUB)
            path = self._astar(s, na, g, (-nb[0], -nb[1]), blk, used_h, used_v, W, H)
            pts = [(r.pa[0] // CELL, r.pa[1] // CELL)] + path + [(r.pb[0] // CELL, r.pb[1] // CELL)]
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                if y0 == y1:
                    for x in range(min(x0, x1), max(x0, x1) + 1):
                        used_h[(x, y0)] = used_h.get((x, y0), 0) + 1
                else:
                    for y in range(min(y0, y1), max(y0, y1) + 1):
                        used_v[(x0, y)] = used_v.get((x0, y), 0) + 1
            r.path = simplify([(x * CELL, y * CELL) for x, y in pts])

    def _astar(self, s, d0, g, dg, blocked, used_h, used_v, W, H):
        DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        BEND, PAR, NEAR, CROSS = 30, 600, 14, 12

        def free(x, y):
            return 0 <= x < W and 0 <= y < H and (not blocked(x, y) or (x, y) in (s, g))

        def h(x, y):
            return abs(x - g[0]) + abs(y - g[1])

        start = (s[0], s[1], d0)
        dist = {start: 0}
        prev = {}
        pq = [(h(*s), 0, start)]
        while pq:
            f, c, st = heapq.heappop(pq)
            if c > dist.get(st, 1e18):
                continue
            x, y, d = st
            if (x, y) == g:
                extra = 0 if d == dg else BEND
                if d != dg and (x, y, dg) not in dist:
                    pass
                end = st
                break
            for nd in DIRS:
                if nd == (-d[0], -d[1]):
                    continue
                nx, ny = x + nd[0], y + nd[1]
                if not free(nx, ny):
                    continue
                cost = 1
                if nd != d:
                    cost += BEND
                horiz = nd[1] == 0
                same = used_h if horiz else used_v
                other_ = used_v if horiz else used_h
                if (nx, ny) in same:
                    cost += PAR
                if (nx, ny) in other_:
                    cost += CROSS
                # giữ khoảng cách với đường song song
                for off in (1, -1):
                    q = (nx, ny + off) if horiz else (nx + off, ny)
                    if q in same:
                        cost += NEAR
                if (nx, ny) == g and nd != dg:
                    cost += BEND * 3
                ns = (nx, ny, nd)
                nc = c + cost
                if nc < dist.get(ns, 1e18):
                    dist[ns] = nc
                    prev[ns] = st
                    heapq.heappush(pq, (nc + h(nx, ny), nc, ns))
        else:
            raise RuntimeError(f"không định tuyến được {s}->{g}")
        out = []
        st = end
        while st in prev:
            out.append((st[0], st[1]))
            st = prev[st]
        out.append((st[0], st[1]))
        return out[::-1]

    # ------------------------------------------------------------ nhãn
    def place_labels(self):
        placed = []
        obstacles = [b.rect for b in self.boxes.values()]
        # vùng vẽ ký hiệu lực lượng ở mỗi đầu đường cũng là vật cản của nhãn
        for r in self.rels:
            for (x, y), side in ((r.pa, r.sa), (r.pb, r.sb)):
                nx, ny = NORMAL[side]
                ex, ey = x + nx * (STUB * CELL), y + ny * (STUB * CELL)
                obstacles.append((min(x, ex) - 8, min(y, ey) - 8, max(x, ex) + 8, max(y, ey) + 8))
        self.label_bad = 0
        segs = []
        for r in self.rels:
            for p, q in zip(r.path, r.path[1:]):
                segs.append((r, p, q))
        for r in sorted(self.rels, key=lambda r: -len(r.label)):
            if not r.label:
                r.lab = ()
                continue
            lw, lh = tw(r.label, FS_L) + 4, FS_L + 3
            best, bestscore = None, 1e18
            cand_segs = sorted(zip(r.path, r.path[1:]),
                               key=lambda pq: -(abs(pq[0][0] - pq[1][0]) + abs(pq[0][1] - pq[1][1])))
            for p, q in cand_segs:
                L = abs(p[0] - q[0]) + abs(p[1] - q[1])
                horiz = p[1] == q[1]
                for t in sorted({0.5} | {k * CELL / max(L, 1) for k in range(1, int(L // CELL))}, key=lambda v: abs(v - 0.5)):
                    mx, my = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
                    if horiz:
                        cands = [(mx - lw / 2, my - lh - 2), (mx - lw / 2, my + 2)]
                    else:
                        cands = [(mx + 3, my - lh / 2), (mx - lw - 3, my - lh / 2)]
                    for (lx, ly) in cands:
                        rect = (lx, ly, lx + lw, ly + lh)
                        sc = 0
                        if lx < 4 or ly < 4 or lx + lw > self.W - 4 or ly + lh > self.H - 4:
                            sc += 1000
                        if horiz and L < lw + 2 * STUB * CELL:
                            sc += 30
                        for o in obstacles + placed:
                            if overlap(rect, o):
                                sc += 1000
                        for (rr, a, b) in segs:
                            if rr is r and not seg_hits(rect, a, b, shrink=0):
                                continue
                            if seg_hits(rect, a, b):
                                sc += 300 if rr is not r else 1000
                        sc += abs(t - 0.5) * 6 + (0 if horiz else 5)
                        if sc < bestscore:
                            best, bestscore = rect, sc
            r.lab = best
            placed.append(best)
            self.label_bad += bestscore >= 300
            if bestscore >= 300 and not getattr(self, "quiet", False):
                print(f"  ! nhãn '{r.label}' ({r.a}->{r.b}) còn va chạm, điểm {bestscore}")

    def panel_rects(self, mx=24, mtop=24):
        out = []
        for lab, col, fil, names in self.panels:
            bs = [self.boxes[n] for n in names]
            x0 = min(b.x for b in bs) - mx
            y0 = min(b.y for b in bs) - mtop
            x1 = max(b.x + b.w for b in bs) + mx
            y1 = max(b.y + b.h for b in bs) + 14
            out.append((lab, col, fil, (x0, y0, x1, y1)))
        return out

    # ------------------------------------------------------------ kiểm tra
    def metrics(self):
        bends = sum(len(r.path) - 2 for r in self.rels)
        length = sum(abs(p[0] - q[0]) + abs(p[1] - q[1]) for r in self.rels for p, q in zip(r.path, r.path[1:]))
        segs = [(r, p, q) for r in self.rels for p, q in zip(r.path, r.path[1:])]
        cross = 0
        for i, (r1, p1, q1) in enumerate(segs):
            for r2, p2, q2 in segs[i + 1:]:
                if r1 is r2:
                    continue
                h1, h2 = p1[1] == q1[1], p2[1] == q2[1]
                if h1 == h2:
                    continue
                hs, vs = ((p1, q1), (p2, q2)) if h1 else ((p2, q2), (p1, q1))
                y = hs[0][1]; x = vs[0][0]
                if min(hs[0][0], hs[1][0]) < x < max(hs[0][0], hs[1][0]) and min(vs[0][1], vs[1][1]) < y < max(vs[0][1], vs[1][1]):
                    cross += 1
        return {"bends": bends, "length": length, "cross": cross, "labels": getattr(self, "label_bad", 0),
                "area": self.W * self.H}

    def check(self):
        bad = 0
        segs = [(r, p, q) for r in self.rels for p, q in zip(r.path, r.path[1:])]
        for i, (r1, p1, q1) in enumerate(segs):
            for r2, p2, q2 in segs[i + 1:]:
                if r1 is r2:
                    continue
                if collinear_overlap(p1, q1, p2, q2):
                    bad += 1
                    if not getattr(self, "quiet", False): print(f"  ! đường chồng: {r1.a}->{r1.b} '{r1.label}' và {r2.a}->{r2.b} '{r2.label}'")
        for r in self.rels:
            for p, q in zip(r.path, r.path[1:]):
                if p[0] != q[0] and p[1] != q[1]:
                    bad += 1
                    print("  ! đoạn xiên", r.a, r.b)
        return bad

    # ------------------------------------------------------------ xuất
    def render(self, stem, note=""):
        if note:
            self.H += 18 * (note.count("\n") + 1) + 12
        self._svg(stem + ".svg", note)
        self._png(stem + ".png", note)

    def _svg(self, path, note):
        o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.W}" height="{self.H}" '
             f'viewBox="0 0 {self.W} {self.H}" font-family="Times New Roman, Times, serif">',
             f'<rect width="{self.W}" height="{self.H}" fill="white"/>']
        for lab, col, fil, rect in self.panel_rects():
            x0, y0, x1, y1 = rect
            o.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="6" fill="{fil}" stroke="{col}" stroke-width="1"/>')
            o.append(f'<text x="{x0 + 8}" y="{y0 + 14}" font-size="10.5" font-weight="bold" fill="{col}">{html.escape(lab)}</text>')
        # Cầu vượt: đoạn ngang có viền trắng vẽ SAU đoạn dọc, nên tại giao điểm
        # đoạn dọc bị ngắt — chỗ cắt nhau không bị đọc nhầm thành chỗ nối.
        for horiz_pass in (False, True):
            for r in self.rels:
                dash = "" if r.ident else ' stroke-dasharray="6 4"'
                for p, q in zip(r.path, r.path[1:]):
                    if (p[1] == q[1]) != horiz_pass:
                        continue
                    if horiz_pass:
                        o.append(f'<line x1="{p[0]}" y1="{p[1]}" x2="{q[0]}" y2="{q[1]}" stroke="white" stroke-width="5"/>')
                    o.append(f'<line x1="{p[0]}" y1="{p[1]}" x2="{q[0]}" y2="{q[1]}" stroke="#333" stroke-width="1"{dash}/>')
        for r in self.rels:
            for (x, y), side, kind in ((r.pa, r.sa, r.ca), (r.pb, r.sb, r.cb)):
                for prim in symbol(x, y, side, kind):
                    if prim[0] == "line":
                        _, x0, y0, x1, y1 = prim
                        o.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}" stroke="#222" stroke-width="1.1"/>')
                    else:
                        _, cx, cy, rad = prim
                        o.append(f'<circle cx="{cx}" cy="{cy}" r="{rad}" fill="white" stroke="#222" stroke-width="1.1"/>')
        for b in self.boxes.values():
            o += svg_box(b)
        for r in self.rels:
            if not r.lab:
                continue
            x0, y0, x1, y1 = r.lab
            o.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" fill="white" opacity="0.92"/>')
            o.append(f'<text x="{(x0 + x1) / 2:.1f}" y="{y1 - 3:.1f}" font-size="{FS_L}" text-anchor="middle" '
                     f'fill="#222">{html.escape(r.label)}</text>')
        if note:
            lines = note.split("\n")
            for i, ln in enumerate(lines):
                yy = self.H - 12 - 18 * (len(lines) - 1 - i)
                o.append(f'<text x="{CELL * 6}" y="{yy}" font-size="11" font-style="italic" fill="#333">{html.escape(ln)}</text>')
        o.append("</svg>")
        open(path, "w", encoding="utf-8").write("\n".join(o))

    def _png(self, path, note, S=3):
        im = Image.new("RGB", (int(self.W * S), int(self.H * S)), "white")
        dr = ImageDraw.Draw(im)
        fpan = ImageFont.truetype(FONT_DIR + "timesbd.ttf", int(10.5 * S))
        for lab, col, fil, rect in self.panel_rects():
            x0, y0, x1, y1 = rect
            dr.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=6 * S, fill=fil, outline=col, width=S)
            dr.text(((x0 + 8) * S, (y0 + 14) * S), lab, font=fpan, fill=col, anchor="ls")
        for horiz_pass in (False, True):
            for r in self.rels:
                for p, q in zip(r.path, r.path[1:]):
                    if (p[1] == q[1]) != horiz_pass:
                        continue
                    if horiz_pass:
                        dr.line([(p[0] * S, p[1] * S), (q[0] * S, q[1] * S)], fill="white", width=5 * S)
                    line(dr, p, q, S, dashed=not r.ident)
        for r in self.rels:
            for (x, y), side, kind in ((r.pa, r.sa, r.ca), (r.pb, r.sb, r.cb)):
                for prim in symbol(x, y, side, kind):
                    if prim[0] == "line":
                        _, x0, y0, x1, y1 = prim
                        dr.line([(x0 * S, y0 * S), (x1 * S, y1 * S)], fill="#222222", width=max(1, int(1.1 * S)))
                    else:
                        _, cx, cy, rad = prim
                        dr.ellipse([(cx - rad) * S, (cy - rad) * S, (cx + rad) * S, (cy + rad) * S],
                                   fill="white", outline="#222222", width=max(1, int(1.1 * S)))
        for b in self.boxes.values():
            png_box(dr, b, S)
        for r in self.rels:
            if not r.lab:
                continue
            x0, y0, x1, y1 = r.lab
            dr.rectangle([x0 * S, y0 * S, x1 * S, y1 * S], fill="white")
            f = ImageFont.truetype(FONT_DIR + "times.ttf", int(FS_L * S))
            dr.text(((x0 + x1) / 2 * S, (y1 - 3) * S), r.label, font=f, fill="#222222", anchor="ms")
        if note:
            f = ImageFont.truetype(FONT_DIR + "timesi.ttf", int(11 * S))
            lines = note.split("\n")
            for i, ln in enumerate(lines):
                yy = self.H - 12 - 18 * (len(lines) - 1 - i)
                dr.text((CELL * 6 * S, yy * S), ln, font=f, fill="#333333", anchor="ls")
        im.save(path, dpi=(300, 300))


# ------------------------------------------------------------------ hình học
def simplify(pts):
    out = [pts[0]]
    for p in pts[1:]:
        if p == out[-1]:
            continue
        if len(out) >= 2 and (out[-2][0] == out[-1][0] == p[0] or out[-2][1] == out[-1][1] == p[1]):
            out[-1] = p
        else:
            out.append(p)
    return out


def overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def seg_hits(rect, p, q, shrink=1):
    x0, y0, x1, y1 = rect
    x0 += shrink; y0 += shrink; x1 -= shrink; y1 -= shrink
    if p[1] == q[1]:
        lo, hi = sorted((p[0], q[0]))
        return y0 <= p[1] <= y1 and lo <= x1 and hi >= x0
    lo, hi = sorted((p[1], q[1]))
    return x0 <= p[0] <= x1 and lo <= y1 and hi >= y0


def collinear_overlap(p1, q1, p2, q2):
    if p1[1] == q1[1] == p2[1] == q2[1]:
        a0, a1 = sorted((p1[0], q1[0])); b0, b1 = sorted((p2[0], q2[0]))
        return min(a1, b1) - max(a0, b0) > 0
    if p1[0] == q1[0] == p2[0] == q2[0]:
        a0, a1 = sorted((p1[1], q1[1])); b0, b1 = sorted((p2[1], q2[1]))
        return min(a1, b1) - max(a0, b0) > 0
    return False


def symbol(x, y, side, kind):
    """Ký hiệu lực lượng tại cổng (x,y) trên cạnh `side`, vẽ ra phía ngoài hộp."""
    nx, ny = NORMAL[side]
    tx, ty = -ny, nx
    P = lambda d, t=0: (x + nx * d + tx * t, y + ny * d + ty * t)
    out = []

    def bar(d):
        a, b = P(d, -6), P(d, 6)
        out.append(("line", *a, *b))

    def circ(d):
        c = P(d)
        out.append(("circ", *c, 4))

    def crow():
        a = P(12)
        for t in (-7, 0, 7):
            b = P(0, t)
            out.append(("line", *a, *b))

    if kind == "one and only one":
        bar(7); bar(12)
    elif kind == "zero or one":
        bar(7); circ(16)
    elif kind == "zero or many":
        crow(); circ(16)
    elif kind == "one or many":
        crow(); bar(16)
    return out


def line(dr, p, q, S, dashed):
    (x0, y0), (x1, y1) = p, q
    L = math.hypot(x1 - x0, y1 - y0)
    if not dashed:
        dr.line([(x0 * S, y0 * S), (x1 * S, y1 * S)], fill="#333333", width=S)
        return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    t = 0
    while t < L:
        e = min(t + 6, L)
        dr.line([((x0 + ux * t) * S, (y0 + uy * t) * S), ((x0 + ux * e) * S, (y0 + uy * e) * S)],
                fill="#333333", width=S)
        t += 10


def key_icon(x, y):
    """Chìa khoá nhỏ: vòng tròn + thân + răng, gốc trái-giữa tại (x,y)."""
    return [("circ", x + 3.5, y, 3), ("line", x + 6.5, y, x + 13, y),
            ("line", x + 11, y, x + 11, y + 3), ("line", x + 13, y, x + 13, y + 3)]


HEAD_FILL = "#DCE6F2"
BORDER = "#1F3864"


def svg_box(b):
    x, y, w, h = b.x, b.y, b.w, b.h
    if b.table:
        o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="white" stroke="{b.color}" stroke-width="1.2"/>',
             f'<text x="{x + PADX}" y="{y + h / 2 + 4}" font-size="{FS_T}" font-weight="bold" fill="#111">{html.escape(b.name)}</text>']
        tx = x + w - PADX
        for t in reversed(b.tags):
            tw_ = tw(t, FS_TAG) + 6
            tx -= tw_
            o.append(f'<rect x="{tx:.1f}" y="{y + h / 2 - 7}" width="{tw_:.1f}" height="14" rx="3" fill="{b.fill}" stroke="{b.color}" stroke-width="0.8"/>')
            o.append(f'<text x="{tx + tw_ / 2:.1f}" y="{y + h / 2 + 3.2}" font-size="{FS_TAG}" text-anchor="middle" fill="{b.color}">{html.escape(t)}</text>')
            tx -= 3
        return o
    if b.context:
        return [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="#F2F2F2" stroke="#7F7F7F" stroke-dasharray="5 3"/>',
                f'<text x="{x + w / 2}" y="{y + h / 2 + 4.5}" font-size="{FS_H}" font-style="italic" text-anchor="middle" fill="#404040">{html.escape(b.name)}</text>']
    o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="white" stroke="{BORDER}" stroke-width="1.2"/>',
         f'<rect x="{x}" y="{y}" width="{w}" height="{HEAD}" fill="{HEAD_FILL}" stroke="{BORDER}" stroke-width="1.2"/>',
         f'<text x="{x + w / 2}" y="{y + HEAD / 2 + 4.5}" font-size="{FS_H}" font-weight="bold" text-anchor="middle">{html.escape(b.name)}</text>']
    for i, (pk, an, at, nn) in enumerate(b.attrs):
        ty = y + HEAD + 4 + ROW * i + ROW / 2 + 4
        if pk:
            for prim in key_icon(x + 3, ty - 4):
                if prim[0] == "circ":
                    o.append(f'<circle cx="{prim[1]}" cy="{prim[2]}" r="{prim[3]}" fill="none" stroke="#9C6500" stroke-width="1.2"/>')
                else:
                    o.append(f'<line x1="{prim[1]}" y1="{prim[2]}" x2="{prim[3]}" y2="{prim[4]}" stroke="#9C6500" stroke-width="1.2"/>')
        deco = ' text-decoration="underline"' if pk else ""
        o.append(f'<text x="{x + b.col1}" y="{ty}" font-size="{FS}"{deco}>{html.escape(an)}</text>')
        o.append(f'<text x="{x + b.col2}" y="{ty}" font-size="{FS}" fill="#444">{html.escape(at)}'
                 + (' <tspan fill="#9C0006">N</tspan>' if nn else "") + "</text>")
    return o


def png_box(dr, b, S):
    x, y, w, h = b.x * S, b.y * S, b.w * S, b.h * S
    if b.table:
        dr.rectangle([x, y, x + w, y + h], fill="white", outline=b.color, width=int(1.2 * S))
        fb = ImageFont.truetype(FONT_DIR + "timesbd.ttf", int(FS_T * S))
        dr.text((x + PADX * S, y + h / 2), b.name, font=fb, fill="#111111", anchor="lm")
        ft = ImageFont.truetype(FONT_DIR + "times.ttf", int(FS_TAG * S))
        tx = b.x + b.w - PADX
        for t in reversed(b.tags):
            tw_ = tw(t, FS_TAG) + 6
            tx -= tw_
            dr.rounded_rectangle([tx * S, (b.y + b.h / 2 - 7) * S, (tx + tw_) * S, (b.y + b.h / 2 + 7) * S],
                                 radius=3 * S, fill=b.fill, outline=b.color, width=max(1, int(0.8 * S)))
            dr.text(((tx + tw_ / 2) * S, (b.y + b.h / 2) * S), t, font=ft, fill=b.color, anchor="mm")
            tx -= 3
        return
    if b.context:
        dash_rect(dr, x, y, w, h, S)
        f = ImageFont.truetype(FONT_DIR + "timesi.ttf", int(FS_H * S))
        dr.text((x + w / 2, y + h / 2), b.name, font=f, fill="#404040", anchor="mm")
        return
    dr.rectangle([x, y, x + w, y + h], fill="white", outline=BORDER, width=int(1.2 * S))
    dr.rectangle([x, y, x + w, y + HEAD * S], fill=HEAD_FILL, outline=BORDER, width=int(1.2 * S))
    fb = ImageFont.truetype(FONT_DIR + "timesbd.ttf", int(FS_H * S))
    dr.text((x + w / 2, y + HEAD * S / 2), b.name, font=fb, fill="black", anchor="mm")
    f = ImageFont.truetype(FONT_DIR + "times.ttf", int(FS * S))
    for i, (pk, an, at, nn) in enumerate(b.attrs):
        ty = b.y + HEAD + 4 + ROW * i + ROW / 2 + 4
        if pk:
            for prim in key_icon(b.x + 3, ty - 4):
                if prim[0] == "circ":
                    _, cx, cy, r = prim
                    dr.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], outline="#9C6500", width=int(1.2 * S))
                else:
                    dr.line([(prim[1] * S, prim[2] * S), (prim[3] * S, prim[4] * S)], fill="#9C6500", width=int(1.2 * S))
        dr.text(((b.x + b.col1) * S, ty * S), an, font=f, fill="black", anchor="ls")
        if pk:
            L = f.getlength(an)
            dr.line([((b.x + b.col1) * S, (ty + 1.5) * S), ((b.x + b.col1) * S + L, (ty + 1.5) * S)], fill="black", width=S)
        dr.text(((b.x + b.col2) * S, ty * S), at, font=f, fill="#444444", anchor="ls")
        if nn:
            L = f.getlength(at + " ")
            dr.text(((b.x + b.col2) * S + L, ty * S), "N", font=f, fill="#9C0006", anchor="ls")


def dash_rect(dr, x, y, w, h, S):
    dr.rectangle([x, y, x + w, y + h], fill="#F2F2F2")
    for p, q in (((x, y), (x + w, y)), ((x + w, y), (x + w, y + h)), ((x + w, y + h), (x, y + h)), ((x, y + h), (x, y))):
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
        t = 0
        while t < L:
            e = min(t + 5 * S, L)
            dr.line([(p[0] + ux * t, p[1] + uy * t), (p[0] + ux * e, p[1] + uy * e)], fill="#7F7F7F", width=S)
            t += 8 * S
