"""Dựng Figure 3-11/3-12/3-13 bằng erd.py. Dữ liệu: dac_ta_CDM_LDM_PDM.md (qua ve_ldm.parse)."""
import json, sys
from pathlib import Path
from ve_ldm import parse, verb
import erd

OUT = Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)
M = parse()
ALL = [r for v in M.values() for r in v["rels"]]


def build(title, entities, context, grid, keep=lambda r: True, force=None, align=None,
          colgap=erd.GAPX, rowgap=erd.GAPY):
    d = erd.Diagram(title)
    for n, attrs in entities.items():
        d.boxes[n] = erd.Box(n, attrs)
    for n in context:
        d.boxes[n] = erd.Box(n, [], context=True)
    present = set(d.boxes)
    seen = set()
    for r in ALL:
        if r["e1"] not in present or r["e2"] not in present:
            continue
        if r["e1"] in context and r["e2"] in context:
            continue
        if not keep(r):
            continue
        k = (r["e1"], r["e2"], r["name"])
        if k in seen:
            continue
        seen.add(k)
        a, b, ca, cb = r["e1"], r["e2"], r["c1"], r["c2"]
        if not r["name"].startswith(a.split()[0]) and r["name"].startswith(b.split()[0]):
            a, b, ca, cb = b, a, cb, ca
        d.rels.append(erd.Rel(a, b, verb(r["name"]), ca, cb, r["ident"]))
    placed = {n for row in grid for n in row if n}
    missing = present - placed
    assert not missing, f"chưa đặt vào lưới: {missing}"
    for _ in range(3):
        d.layout(grid, colgap, rowgap, align)
        d.choose_sides(force)
        if not d.fit_context():
            break
    d.assign_ports()
    d.straighten()
    d.route()
    d.place_labels()
    return d


def fig_3_11():
    e = M["LDM-1"]["entities"]
    grid = [
        [None, "Project Allocation", "Tenant Invitation", "Role"],
        ["Workspace", "Tenant", "User", "Role Assignment"],
        ["Project", "Membership", "API Key", "Permission"],
    ]
    return dict(title="3-11", entities=e, context=[], grid=grid)


AUX = {"Dialect Merge", "Dialect Template", "Recognition Profile Template",
       "Template Version", "Signer Merge"}
# Đặc tả cho phép lược nhóm "User tạo/duyệt …" (dấu vết thao tác), miễn ghi chú.
# Giữ các quan hệ mang nghĩa vận hành: operates, opens, uploads, records, corresponds to.
OMIT_VERBS = {"creates", "approves", "reviews", "updates"}


def fig_3_12():
    e = {k: v for k, v in {**M["LDM-2"]["entities"], **M["LDM-3"]["entities"]}.items() if k not in AUX}
    grid = [
        ["Vocabulary Group", "Recognition Profile", "Region", "Registry Version"],
        ["Sign Language", "Sign Class", "Tenant", "Dialect"],
        ["Raw Upload", "Sample", "Capture Session", "Collection Session"],
        ["User", "Signer", "Signer Consent", None],
    ]
    keep = lambda r: not (r["e1"] == "User" and verb(r["name"]) in OMIT_VERBS)
    return dict(title="3-12", entities=e, context=["Tenant", "User", "Signer Consent"], grid=grid, keep=keep)


def fig_3_13():
    e = M["LDM-4"]["entities"]
    grid = [
        ["Legal Document", "Legal Document Version", "User Consent", None],
        ["Legal Document Draft", "User", "Signer Consent", "Signer"],
        ["Audit Entry", "Tenant", "Personal Export", "Tenant Export"],
        ["Legal Document Event", "SOT Writer Key", "Tenant Purge", None],
    ]
    return dict(title="3-13", entities=e, context=["Signer", "Tenant", "User"], grid=grid)


LEGEND = ("Underlined attribute with key icon = primary key; N = optional (nullable). "
          "Solid line = identifying relationship; dashed line = non-identifying relationship.")
FIGS = {"3-11": (fig_3_11, "Figure_3-11_LDM_module_1", LEGEND),
        "3-12": (fig_3_12, "Figure_3-12_LDM_module_2",
                 LEGEND + "\nGrey dashed boxes are reference entities: Tenant and User (Figure 3-11), "
                          "Signer Consent (Figure 3-13)."),
        "3-13": (fig_3_13, "Figure_3-13_LDM_module_3",
                 LEGEND + "\nGrey dashed boxes are reference entities: Tenant and User (Figure 3-11), "
                          "Signer (Figure 3-12).")}

def score(d):
    d.quiet = True
    geo = d.check()
    m = d.metrics()
    return (m["length"] / erd.CELL + 25 * m["bends"] + 40 * m["cross"] + 400 * m["labels"]
            + 3000 * geo + m["area"] / 3000), m, geo


def best_layout(spec, tries=8):
    import toi_uu
    d0 = build(**spec)
    pairs = [(r.a, r.b) for r in d0.rels]
    # thực thể không có quan hệ nào: gom thành một hàng riêng ở cuối hình
    linked = {n for pr in pairs for n in pr}
    lone = [n for row in spec["grid"] for n in row if n and n not in linked]
    core = [[n if n not in lone else None for n in row] for row in spec["grid"]]
    core = [row for row in core if any(row)]
    tail = [lone + [None] * (len(core[0]) - len(lone))] if lone else []
    cands = [(0, spec["grid"])] + [(sc, g + tail) for sc, g in toi_uu.search(core, pairs, keep=tries)]
    results = []
    for est_sc, g in cands:
        try:
            d = build(**{**spec, "grid": g})
        except RuntimeError as ex:
            continue
        sc, m, geo = score(d)
        results.append((sc, g, m, geo))
        print(f"   ước lượng {est_sc:5.0f}  điểm {sc:7.0f}  {m}  hình học {geo}")
    results.sort(key=lambda x: x[0])
    return results[0]


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    want = args or list(FIGS)
    for k in want:
        fn, stem, note = FIGS[k]
        spec = fn()
        saved = OUT / f"luoi_{k}.json"
        if "--toi-uu" in sys.argv:
            sc, g, m, geo = best_layout(spec)
            print(f"Figure {k}: chọn lưới (điểm {sc:.0f}):")
            for row in g:
                print("     ", row)
            spec["grid"] = g
            saved.write_text(json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")
        elif saved.exists():   # lưới đã chọn ở lượt tối ưu trước: dựng lại y hệt
            spec["grid"] = json.loads(saved.read_text(encoding="utf-8"))
        d = build(**spec)
        n = d.check()
        d.render(str(OUT / stem), note)
        print(f"Figure {k}: {len(d.boxes)} hộp, {len(d.rels)} quan hệ, {n} lỗi hình học, "
              f"{d.W}x{d.H}px, {d.metrics()}")
