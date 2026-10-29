#!/usr/bin/env python3
"""Render a portable JSON CDM/LDM/PDM with the original orthogonal ER engine."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

try:
    import erd
except ModuleNotFoundError as exc:
    if exc.name == "PIL":
        raise SystemExit("Thiếu Pillow: cài requirements.txt của skill trong một virtualenv.") from exc
    raise

CARD = {"1": "one and only one", "0..1": "zero or one",
        "0..N": "zero or many", "1..N": "one or many"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_grid(grid, names):
    require(isinstance(grid, list) and grid and all(isinstance(row, list) and row for row in grid),
            "grid phải có ít nhất một hàng, mỗi hàng có ít nhất một ô.")
    require(all(n is None or isinstance(n, str) for row in grid for n in row),
            "Ô lưới phải là tên thực thể hoặc null.")
    placed = [n for row in grid for n in row if n is not None]
    require(Counter(placed) == Counter(names),
            "grid phải chứa đúng mỗi thực thể một lần, không có tên lạ hoặc thiếu.")


def validate(spec):
    require(spec.get("layer") in ("CDM", "LDM", "PDM"), "layer phải là CDM, LDM hoặc PDM.")
    for key in ("title", "source"):
        require(isinstance(spec.get(key), str) and spec[key].strip(), f"Thiếu {key}.")
    entities = spec.get("entities")
    require(isinstance(entities, list) and entities, "entities không được trống.")
    names = []
    for entity in entities:
        name = entity.get("name")
        require(isinstance(name, str) and name.strip(), "Thiếu tên thực thể.")
        names.append(name)
        attrs = entity.get("attrs", [])
        require(isinstance(attrs, list), f"{name}: attrs phải là danh sách.")
        for attr in attrs:
            require(isinstance(attr, list) and len(attr) == 4 and type(attr[0]) is bool
                    and isinstance(attr[1], str) and isinstance(attr[2], str) and type(attr[3]) is bool,
                    f"{name}: thuộc tính phải có dạng [is_pk, name, type, nullable].")
            require(not (attr[0] and attr[3]), f"{name}.{attr[1]}: PK không được nullable.")
        for flag in ("context", "compact"):
            require(type(entity.get(flag, False)) is bool, f"{name}: {flag} phải là boolean.")
        require(not (attrs and (entity.get("context") or entity.get("compact"))),
                f"{name}: context/compact sẽ ẩn thuộc tính; hãy bỏ attrs hoặc bỏ chế độ này.")
        require(not (entity.get("context") and entity.get("compact")),
                f"{name}: chỉ chọn context hoặc compact.")
        if spec["layer"] == "CDM":
            require(not attrs, "CDM dùng khái niệm nghiệp vụ, không chứa cột/kiểu SQL.")
        tags = entity.get("tags", [])
        require(isinstance(tags, list) and all(isinstance(t, str) for t in tags),
                f"{name}: tags phải là danh sách chuỗi.")
        require(not tags or entity.get("compact"), f"{name}: tags chỉ hiển thị trên hộp compact.")
    require(len(names) == len(set(names)), "Tên thực thể bị lặp.")
    require(isinstance(spec.get("relations"), list), "relations phải là danh sách (có thể trống).")
    for rel in spec["relations"]:
        require(rel.get("a") in names and rel.get("b") in names, "Quan hệ trỏ tới thực thể không tồn tại.")
        require(rel.get("ca") in CARD and rel.get("cb") in CARD, "Cardinality phải là 1, 0..1, 0..N hoặc 1..N.")
        require(isinstance(rel.get("label", ""), str), "label phải là chuỗi.")
        if spec["layer"] != "CDM":
            require(type(rel.get("ident")) is bool, "LDM/PDM phải khai báo ident cho từng quan hệ.")
        if "sides" in rel:
            require(isinstance(rel["sides"], list) and len(rel["sides"]) == 2
                    and all(s in erd.NORMAL for s in rel["sides"]), "sides phải gồm hai cạnh L/R/T/B.")
    validate_grid(spec.get("grid"), names)
    panels = spec.get("panels", [])
    require(isinstance(panels, list), "panels phải là danh sách.")
    for panel in panels:
        require(isinstance(panel.get("names"), list) and panel["names"]
                and all(n in names for n in panel["names"]), "Panel chứa thực thể thiếu/không hợp lệ.")
        require(isinstance(panel.get("label"), str), "Panel thiếu label.")
    require(isinstance(spec.get("note", ""), str), "note phải là chuỗi.")
    for gap in ("colgap", "rowgap"):
        require(type(spec.get(gap, 96)) in (int, float) and spec.get(gap, 96) >= 64,
                f"{gap} phải >= 64 để chừa hành lang định tuyến.")


def build(spec, grid, quiet=False):
    d = erd.Diagram(spec["title"])
    d.quiet = quiet
    for entity in spec["entities"]:
        name = entity["name"]
        context = entity.get("context", False)
        compact = entity.get("compact", spec["layer"] == "CDM" and not context)
        d.boxes[name] = erd.Box(name, entity.get("attrs", []), context=context,
                                table=compact, tags=entity.get("tags", []),
                                color=entity.get("color", erd.BORDER),
                                fill=entity.get("fill", erd.HEAD_FILL))
    force = {}
    for rel in spec["relations"]:
        r = erd.Rel(rel["a"], rel["b"], rel.get("label", ""), CARD[rel["ca"]], CARD[rel["cb"]],
                    True if spec["layer"] == "CDM" else rel["ident"])
        d.rels.append(r)
        if "sides" in rel:
            force[(r.a, r.b, r.label)] = rel["sides"]
    for panel in spec.get("panels", []):
        d.panels.append((panel["label"], panel.get("color", erd.BORDER),
                         panel.get("fill", "#F2F2F2"), panel["names"]))
    # fit_context can change side choices; only route after dimensions settle.
    for _ in range(10):
        d.layout(grid, spec.get("colgap", erd.GAPX), spec.get("rowgap", erd.GAPY))
        d.choose_sides(force)
        if not d.fit_context():
            break
    else:
        raise ValueError("Cỡ hộp chưa ổn định; tăng khoảng cách hoặc chia nhỏ sơ đồ.")
    d.assign_ports()
    d.straighten()
    d.route()
    d.place_labels()
    return d


def inspect(d):
    geometry = d.check()
    boxes = list(d.boxes.values())
    geometry += sum(erd.overlap(a.rect, b.rect) for i, a in enumerate(boxes) for b in boxes[i + 1:])
    # All boxes, including an edge's own endpoints: touching the border is fine,
    # crossing the interior is not. This also catches loops routed through self.
    geometry += sum(erd.seg_hits(box.rect, p, q, shrink=1)
                    for rel in d.rels for p, q in zip(rel.path, rel.path[1:]) for box in boxes)
    metrics = d.metrics()
    return geometry, metrics


def score(d):
    geometry, m = inspect(d)
    return (m["length"] / erd.CELL + 25 * m["bends"] + 40 * m["cross"]
            + 400 * m["labels"] + 3000 * geometry + m["area"] / 3000)


def optimize(spec, grid):
    import toi_uu
    names = [e["name"] for e in spec["entities"]]
    if len(names) < 2 or not spec["relations"]:
        return grid
    # Preserve each panel's original rectangular zone; do not mix modules.
    zones = None
    if spec.get("panels"):
        pos = {n: (i, j) for i, row in enumerate(grid) for j, n in enumerate(row) if n}
        all_cells = {(i, j) for i in range(len(grid)) for j in range(max(map(len, grid)))}
        zones = {n: set(all_cells) for n in names}
        for panel in spec["panels"]:
            cells = [pos[n] for n in panel["names"]]
            zone = {(i, j) for i in range(min(c[0] for c in cells), max(c[0] for c in cells) + 1)
                    for j in range(min(c[1] for c in cells), max(c[1] for c in cells) + 1)}
            for n in names:
                zones[n] = zones[n] & zone if n in panel["names"] else zones[n] - zone
        require(all(pos[n] in zones[n] for n in names), "Panel chồng vùng; chỉnh lưới trước khi tối ưu.")
    pairs = [(r["a"], r["b"]) for r in spec["relations"]]
    candidates = [grid] + [g for _, g in toi_uu.search(grid, pairs, iters=600, seeds=2, keep=4, zones=zones)]
    best = None
    for candidate in candidates:
        try:
            d = build(spec, candidate, quiet=True)
            key = score(d)
        except (ValueError, RuntimeError):
            continue
        if best is None or key < best[0]:
            best = (key, candidate)
    require(best is not None, "Không có bố cục định tuyến được; tăng khoảng cách hoặc chia module.")
    return best[1]


def legend(spec):
    common = "1 = đúng một; 0..1 = tùy chọn một; 0..N = không hoặc nhiều; 1..N = một hoặc nhiều."
    if spec["layer"] == "CDM":
        note = "CDM: thực thể nghiệp vụ; nét liền biểu diễn quan hệ, không hàm ý khóa vật lý."
    else:
        note = ("Chìa khóa + gạch chân = PK; N = nullable. Nét liền = định danh; "
                "nét đứt = không định danh.")
    if any(e.get("context") for e in spec["entities"]):
        note += " Hộp xám nét đứt = thực thể tham chiếu từ module khác."
    return note + "\n" + common + ("\n" + spec["note"] if spec.get("note") else "")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path, help="Đặc tả JSON; xem references/input-format.md")
    parser.add_argument("--out", type=Path, required=True, help="Tiền tố đầu ra, không có phần mở rộng")
    parser.add_argument("--layout", type=Path, help="Dùng lưới JSON đã lưu thay cho grid trong model")
    parser.add_argument("--optimize", action="store_true", help="Tìm lưới mới, ghi vào <out>.layout.json")
    parser.add_argument("--font-dir", type=Path, help="Thư mục Times New Roman (4 tệp times*.ttf)")
    parser.add_argument("--check-only", action="store_true", help="Định tuyến và kiểm tra, không xuất ảnh")
    args = parser.parse_args()
    try:
        raw = args.model.read_bytes()
        spec = json.loads(raw)
        validate(spec)
        erd.configure_fonts(args.font_dir)
        grid = json.loads(args.layout.read_text(encoding="utf-8")) if args.layout else spec["grid"]
        validate_grid(grid, [e["name"] for e in spec["entities"]])
        if args.optimize:
            grid = optimize(spec, grid)
        d = build(spec, grid)
        geometry, metrics = inspect(d)
        passed = geometry == 0 and metrics["labels"] == 0
        report = {"status": "PASS" if passed else "FAIL", "layer": spec["layer"],
                  "title": spec["title"], "source": spec["source"],
                  "model_sha256": hashlib.sha256(raw).hexdigest(),
                  "entities": len(d.boxes), "relations": len(d.rels),
                  "geometry_errors": geometry, "metrics": metrics,
                  "font_family": erd.FONT_FAMILY, "font_files": erd.FONT_FILES,
                  "scope": "Geometry only; verify semantics, coverage and final document visually."}
        args.out.parent.mkdir(parents=True, exist_ok=True)
        Path(str(args.out) + ".layout.json").write_text(
            json.dumps(grid, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        Path(str(args.out) + ".check.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if not passed:
            print("Chưa xuất ảnh: sửa lỗi hình học/nhãn, tăng khoảng cách hoặc chia module.", file=sys.stderr)
            return 1
        if not args.check_only:
            d.render(str(args.out), legend(spec))
        return 0
    except (ValueError, RuntimeError, OSError, KeyError, TypeError, AttributeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
