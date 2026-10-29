"""Figure 3-14 — PDM tổng quan v8: tên bảng + quan hệ, không cột.

Nguồn: docs/02-data/db/evidence/pdm_v8_foreign_keys.csv, pdm_v8_columns.csv,
pdm_tools/groups.txt (lược đồ đang chạy, schema_migrations = 8).

Quy ước rút gọn (ghi trong chú giải dưới hình):
* FK tới `tenants` (40) và `users` (47) KHÔNG vẽ thành đường — mỗi bảng mang
  nhãn [T] / [U] (kèm ×n khi nhiều FK). Vẽ hết 87 đường ấy thì hình mất đọc.
* Nhiều FK giữa cùng một cặp bảng gộp thành một đường, ghi ×n.
* Nét liền = quan hệ định danh (cột FK nằm trong khoá chính của bảng con).
"""
import csv, json, sys
from collections import defaultdict
from pathlib import Path
import erd, toi_uu

REPO = Path(r"E:/CTU_ProjectOutside/VOYA-Collector/docs/02-data/db")
OUT = Path(__file__).parent / "output"

GROUPS = {
    "A": ("A · IDENTITY, ORGANIZATION AND AUTHORIZATION", "#0B4DA2", "#E7EEF9"),
    "B": ("B · AUTHENTICATION CREDENTIALS", "#7A3E9D", "#F0E8F7"),
    "C": ("C · VOCABULARY, CATALOGUE AND REGISTRY", "#0E6E7A", "#E2F1F3"),
    "D": ("D · COLLECTION AND SAMPLE REPOSITORY", "#1B6E4A", "#E4F1EA"),
    "E": ("E · LEGAL, CONSENT, AUDIT AND DATA LIFECYCLE", "#8E1F5E", "#F7E5EF"),
    "F": ("F · TRAINING (DOWNSTREAM)", "#8A4B12", "#F7EBE0"),
    "G": ("G · PLANS, SUBSCRIPTION AND QUOTA", "#7A6410", "#F5F0DC"),
    "H": ("H · PLATFORM SERVICES", "#4D4D4D", "#EFEFEF"),
}
# Khối ô (hàng0, cột0, số hàng, số cột) của mỗi nhóm trên lưới toàn hình
BLOCKS = {
    "A": (0, 0, 3, 4), "B": (0, 4, 3, 2), "G": (0, 6, 3, 2),
    "C": (3, 0, 3, 4), "D": (3, 4, 3, 2), "F": (3, 6, 3, 1),
    "E": (6, 0, 3, 4), "H": (6, 4, 3, 3),
}
CARD = {"1": "one and only one", "0..1": "zero or one", "0..N": "zero or many", "1..N": "one or many"}


def load():
    groups = {}
    for ln in (REPO / "pdm_tools/groups.txt").read_text(encoding="utf-8").splitlines():
        parts = ln.split()
        if parts and parts[0] in GROUPS:
            for t in parts[1:]:
                groups[t] = parts[0]
    pk = defaultdict(set)
    for r in csv.DictReader(open(REPO / "evidence/pdm_v8_columns.csv", encoding="utf-8")):
        if r["is_pk"] == "PK":
            pk[r["table_name"]].add(r["column_name"])
    fks = list(csv.DictReader(open(REPO / "evidence/pdm_v8_foreign_keys.csv", encoding="utf-8")))
    return groups, pk, fks


def build(grid=None):
    groups, pk, fks = load()
    assert len(groups) == 63, len(groups)
    assert len(fks) == 132, len(fks)
    d = erd.Diagram("3-14")
    tcount, ucount = defaultdict(int), defaultdict(int)
    pairs = defaultdict(list)
    for f in fks:
        c, p = f["child_table"], f["parent_table"]
        if p == "tenants" and c != "users":
            tcount[c] += 1
        elif p == "users" and c != "tenants":
            ucount[c] += 1
        else:
            pairs[(c, p)].append(f)
    for t, g in groups.items():
        tags = []
        if tcount[t]:
            tags.append("T" if tcount[t] == 1 else f"T×{tcount[t]}")
        if ucount[t]:
            tags.append("U" if ucount[t] == 1 else f"U×{ucount[t]}")
        _, col, fil = GROUPS[g]
        d.boxes[t] = erd.Box(t, [], table=True, tags=tags, color=col, fill=fil)
    for (c, p), lst in pairs.items():
        f = lst[0]
        ident = all(set(x["child_cols"].split(",")) <= pk[c] for x in lst)
        lab = f"×{len(lst)}" if len(lst) > 1 else ""
        # a = cha, b = con: ký hiệu sát cha là parent_card, sát con là child_card
        d.rels.append(erd.Rel(p, c, lab, CARD[f["parent_card"]], CARD[f["child_card"]], ident))
    for g, (lab, col, fil) in GROUPS.items():
        d.panels.append((lab, col, fil, [t for t, gg in groups.items() if gg == g]))
    if grid is None:
        grid = [[None] * 8 for _ in range(9)]
        for g, (r0, c0, nr, nc) in BLOCKS.items():
            ts = [t for t, gg in groups.items() if gg == g]
            assert len(ts) <= nr * nc, (g, len(ts))
            for i, t in enumerate(ts):
                grid[r0 + i // nc][c0 + i % nc] = t
    return d, grid, groups, tcount, ucount, pairs


def realize(d, grid):
    for _ in range(3):
        d.layout(grid, colgap=72, rowgap=64)
        d.choose_sides()
        if not d.fit_context():
            break
    d.assign_ports()
    d.straighten()
    d.route()
    d.place_labels()
    return d


def score(d):
    d.quiet = True
    geo = d.check()
    m = d.metrics()
    return m["length"] / erd.CELL + 25 * m["bends"] + 40 * m["cross"] + 400 * m["labels"] + 3000 * geo, m, geo


def main():
    d0, grid, groups, tcount, ucount, pairs = build()
    zones = {}
    for t, g in groups.items():
        r0, c0, nr, nc = BLOCKS[g]
        zones[t] = {(r, c) for r in range(r0, r0 + nr) for c in range(c0, c0 + nc)}
    edges = [(r.a, r.b) for r in d0.rels]
    best = None
    cands = [(0, grid)] + toi_uu.search(grid, edges, keep=6, zones=zones) if "--toi-uu" in sys.argv else [(0, grid)]
    for est_sc, g in cands:
        d = realize(build(g)[0], g)
        sc, m, geo = score(d)
        print(f"   ước lượng {est_sc:5.0f}  điểm {sc:7.0f}  {m}  hình học {geo}")
        if best is None or sc < best[0]:
            best = (sc, g)
    g = best[1]
    saved = OUT / "luoi_3-14.json"
    if "--toi-uu" in sys.argv:
        saved.write_text(json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")
    elif saved.exists():
        g = json.loads(saved.read_text(encoding="utf-8"))
    print("chọn lưới:")
    for row in g:
        print("    ", row)
    d = realize(build(g)[0], g)
    d.quiet = False
    n = d.check()
    nt, nu = sum(tcount.values()), sum(ucount.values())
    other = sum(len(v) for v in pairs.values())
    note = (f"Schema v8: 63 tables, 132 foreign keys. Lines show {other} foreign keys between {len(pairs)} table pairs; "
            f"×n = n foreign keys merged into one line. Solid line = identifying relationship.\n"
            f"[T] = foreign key tenant_id → tenants ({nt} in total); [U] = foreign key → users ({nu} in total); "
            f"×n on a tag = number of such keys. Group colours follow Appendix A (PDM-A … PDM-H).")
    d.render(str(OUT / "Figure_3-14_PDM_overview_v8"), note)
    print(f"Figure 3-14: {len(d.boxes)} bảng, {len(d.rels)} đường ({other} FK), [T] {nt}, [U] {nu}, "
          f"tổng {other + nt + nu} FK, {n} lỗi hình học, {d.W}x{d.H}px, {d.metrics()}")


if __name__ == "__main__":
    main()
