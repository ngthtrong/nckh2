"""Sinh Figure 3-11, 3-12, 3-13 (LDM) từ dac_ta_CDM_LDM_PDM.md bằng Graphviz.

Mọi thực thể, thuộc tính, quan hệ đều đọc từ đặc tả; không có dòng nào gõ tay.
Ký pháp: chìa khoá = PK, `N` = cho phép NULL, nét liền = định danh,
nét đứt = không định danh, chân chim theo cột "Đầu E1"/"Đầu E2".
"""
import re, subprocess, sys, html
from pathlib import Path

HERE = Path(__file__).parent
SPEC = HERE.parent / "dac_ta_CDM_LDM_PDM.md"
OUT = HERE / "output"
DOT = r"E:/CTU IN SCHOOL/4.Year_4.Semester25-26/Semester 1/KiemChungMoHinh/Code/Graphviz-14.0.0-win64/bin/dot.exe"
FONT = "Times New Roman,"

ARROW = {  # ký hiệu vẽ sát hộp
    "one and only one": "teetee",
    "zero or one": "teeodot",
    "zero or many": "crowodot",
    "one or many": "crowtee",
}


def parse():
    lines = SPEC.read_text(encoding="utf-8").splitlines()
    mods, cur, ent = {}, None, None
    for ln in lines:
        m = re.match(r"^### (LDM-\d) (.+)$", ln)
        if m:
            cur = m.group(1)
            mods[cur] = {"title": m.group(2), "entities": {}, "rels": []}
            ent = None
            continue
        if ln.startswith("## 5."):
            break
        if cur is None:
            continue
        m = re.match(r"^\*\*(.+)\*\*$", ln)
        if m:
            ent = m.group(1)
            mods[cur]["entities"][ent] = []
            continue
        # bỏ ghi chú của người soạn kiểu "*(khoá thay thế: …)*" — không lên hình
        ln = re.sub(r"\s+\*\(.*\)\*$", "", ln)
        m = re.match(r"^- (🔑 )?(.+?) : (.+?)( `N`)?$", ln)
        if m and ent:
            mods[cur]["entities"][ent].append(
                (bool(m.group(1)), m.group(2), m.group(3), bool(m.group(4))))
            continue
        if ln.startswith("| ") and not ln.startswith("| E1") and "---" not in ln:
            # bỏ ký hiệu "( || )", "( o| )" trước khi tách cột, vì chúng chứa "|"
            c = [x.strip() for x in re.sub(r"\s*\([^()]*\)", "", ln).strip("|").split("|")]
            if len(c) == 6:
                ent = None
                card = lambda s: s
                mods[cur]["rels"].append({
                    "e1": c[0].rstrip("*"), "e2": c[1].rstrip("*"), "name": c[2],
                    "c1": card(c[3]), "c2": card(c[4]), "ident": c[5] == "liền"})
    return mods


def verb(name):
    """'User creates API Key' -> 'creates'; 'Signer is subject of Signer Consent' -> 'is subject of'."""
    w = name.split()
    i = 0
    while i < len(w) and w[i][:1].isupper():
        i += 1
    j = i
    while j < len(w) and not w[j][:1].isupper():
        j += 1
    return " ".join(w[i:j]) or name


def node_id(e):
    return re.sub(r"\W", "_", e)


def entity_label(name, attrs):
    rows = [f'<TR><TD BGCOLOR="#DCE6F2" ALIGN="CENTER" COLSPAN="3"><B>{html.escape(name)}</B></TD></TR>']
    for pk, a, t, n in attrs:
        key = "&#x1F511;" if pk else ""
        a_txt = f"<U>{html.escape(a)}</U>" if pk else html.escape(a)
        rows.append(
            f'<TR><TD ALIGN="LEFT" WIDTH="14">{key}</TD>'
            f'<TD ALIGN="LEFT">{a_txt}</TD>'
            f'<TD ALIGN="LEFT"><FONT COLOR="#444444">{html.escape(t)}{" &#160;N" if n else ""}</FONT></TD></TR>')
    return ('<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#1F3864">'
            + "".join(rows) + "</TABLE>>")


def context_label(name):
    return f'<<TABLE BORDER="0" CELLPADDING="5"><TR><TD><I>{html.escape(name)}</I></TD></TR></TABLE>>'


def figure(fname, entities, rels, context, drop_rels=lambda r: False, rankdir="LR", extra=""):
    present = set(entities) | set(context)
    used = []
    for r in rels:
        if r["e1"] in present and r["e2"] in present and not drop_rels(r):
            if r["e1"] in context and r["e2"] in context:
                continue
            used.append(r)
    # mỗi quan hệ chỉ vẽ một lần
    seen, uniq = set(), []
    for r in used:
        k = (r["e1"], r["e2"], r["name"])
        if k not in seen:
            seen.add(k)
            # Tên quan hệ bắt đầu bằng E2 ("Tenant Invitation intends Role" đặt dưới
            # E1 = Role): đảo cả hai đầu để động từ đọc đúng chiều mũi tên.
            # Lực lượng đi theo hộp nên đảo cùng, nghĩa không đổi.
            if not r["name"].startswith(r["e1"].split()[0]) and r["name"].startswith(r["e2"].split()[0]):
                r = {**r, "e1": r["e2"], "e2": r["e1"], "c1": r["c2"], "c2": r["c1"]}
            uniq.append(r)
    out = [f'digraph G {{ graph [rankdir={rankdir}, bgcolor="white", pad="0.2", nodesep="0.55", ranksep="0.75", '
           f'splines=ortho, forcelabels=true, fontname="{FONT}"]; '
           f'node [shape=plain, fontname="{FONT}", fontsize=12]; '
           f'edge [fontname="{FONT}", fontsize=10, color="#333333", arrowsize=0.9, dir=both, penwidth=1.0];']
    for e, attrs in entities.items():
        out.append(f'{node_id(e)} [label={entity_label(e, attrs)}];')
    for e in context:
        out.append(f'{node_id(e)} [shape=box, style="dashed,rounded", color="#7F7F7F", fontcolor="#404040", '
                   f'label={context_label(e)}];')
    for r in uniq:
        style = "solid" if r["ident"] else "dashed"
        out.append(f'{node_id(r["e1"])} -> {node_id(r["e2"])} [arrowtail={ARROW[r["c1"]]}, '
                   f'arrowhead={ARROW[r["c2"]]}, style={style}, xlabel=" {html.escape(verb(r["name"]))} "];')
    out.append(extra)
    out.append("}")
    dot = OUT / f"{fname}.dot"
    dot.write_text("\n".join(out), encoding="utf-8")
    for fmt, extra_args in (("svg", []), ("png", ["-Gdpi=200"])):
        subprocess.run([DOT, f"-T{fmt}", *extra_args, str(dot), "-o", str(OUT / f"{fname}.{fmt}")], check=True)
    return uniq


def main():
    OUT.mkdir(exist_ok=True)
    m = parse()
    for k, v in m.items():
        print(k, v["title"], len(v["entities"]), "thực thể", len(v["rels"]), "quan hệ")

    all_rels = [r for v in m.values() for r in v["rels"]]
    report = []

    # 3-11: 11 thực thể LDM-1, chỉ quan hệ nội bộ
    e1 = m["LDM-1"]["entities"]
    r = figure("Figure_3-11_LDM_module_1", e1, all_rels, [])
    report.append(("3-11", len(e1), 0, r))

    # 3-12: LDM-2 + LDM-3, bỏ 5 thực thể phụ; ngữ cảnh Tenant, User, Signer Consent
    drop = {"Dialect Merge", "Dialect Template", "Recognition Profile Template",
            "Template Version", "Signer Merge"}
    if "--giu-17" in sys.argv:
        drop = set()
    e2 = {k: v for k, v in {**m["LDM-2"]["entities"], **m["LDM-3"]["entities"]}.items() if k not in drop}
    r = figure("Figure_3-12_LDM_module_2", e2, all_rels, ["Tenant", "User", "Signer Consent"])
    report.append(("3-12", len(e2), 3, r))

    # 3-13: LDM-4; ngữ cảnh Signer, Tenant, User
    e3 = m["LDM-4"]["entities"]
    r = figure("Figure_3-13_LDM_module_3", e3, all_rels, ["Signer", "Tenant", "User"])
    report.append(("3-13", len(e3), 3, r))

    for fig, ne, nc, rels in report:
        print(f"Figure {fig}: {ne} thực thể chính, {nc} hộp ngữ cảnh, {len(rels)} quan hệ")
        for x in rels:
            print(f"   {x['e1']} -> {x['e2']}: {x['name']} [{x['c1']} / {x['c2']}]{' định danh' if x['ident'] else ''}")


if __name__ == "__main__":
    main()
