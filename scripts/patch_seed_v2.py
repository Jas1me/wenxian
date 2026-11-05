# -*- coding: utf-8 -*-
"""对 seed.py 做三项规范化（AST 精确编辑）：
1) 去掉标题尾部多余的英文句点（316 条，新入库批次带入）
2) 有 DOI 但链接指向出版社页面的，统一改为 doi.org 直链
3) id13（Child Care Health Dev, TEACCH 单案例 Meta 分析）补 PMID 38380766，链接改 PubMed
用法: python patch_seed_v2.py --dry | (无参数)写入
"""
import ast, json, os, shutil, sqlite3, sys, time

BASE = os.path.dirname(os.path.abspath(__file__))
SEED = r"C:\Users\User\Desktop\neurosearch\server\seed.py"
DB = r"C:\Users\User\Desktop\neurosearch\server\neurosearch.db"
DRY = "--dry" in sys.argv

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
db_rows = {r["id"]: dict(r) for r in conn.execute("SELECT * FROM articles")}

src = open(SEED, encoding="utf-8").read()
tree = ast.parse(src)


def load_articles(t):
    for node in t.body:
        if isinstance(node, ast.Assign) and any(getattr(x, "id", None) == "SEED_ARTICLES" for x in node.targets):
            return node.value.elts
    raise SystemExit("找不到 SEED_ARTICLES")


items = load_articles(tree)
print("seed.py 条目数:", len(items))

lines = src.split("\n")
offsets = []
_acc = 0
for _ln in lines:
    offsets.append(_acc)
    _acc += len(_ln) + 1


def pos(ln, col):
    """ast 的 col_offset 是 UTF-8 字节偏移，需换算成字符偏移（含中文/† 等非 ASCII 时必需）"""
    line = lines[ln - 1]
    raw = line.encode("utf-8")
    char_col = len(raw[:col].decode("utf-8", errors="ignore"))
    return offsets[ln - 1] + char_col


edits = []   # (start, end, text, id, field, old, new)
inserts = []  # (offset, text, id)

# 经 Europe PMC 按 DOI 精确反查确认的补全（DOI 一致才算命中）
PMID_FILL = {13: "38380766"}   # 10.1111/cch.13234

for idx, el in enumerate(items, start=1):
    keys = {}
    if isinstance(el, ast.Dict):
        for k, v in zip(el.keys, el.values):
            if isinstance(k, ast.Constant):
                keys[k.value] = v
    elif isinstance(el, ast.Call):
        for kw in el.keywords:
            if kw.arg:
                keys[kw.arg] = kw.value
    else:
        continue

    row = db_rows.get(idx, {})

    # 1) 标题尾部句点
    t = keys.get("title")
    if isinstance(t, ast.Constant) and isinstance(t.value, str) and t.value.rstrip().endswith("."):
        new = t.value.rstrip()[:-1].rstrip()
        edits.append((pos(t.lineno, t.col_offset), pos(t.end_lineno, t.end_col_offset),
                      json.dumps(new, ensure_ascii=False), idx, "title", t.value[-30:], new[-30:]))

    # 2) 链接规范化：有 DOI 但 url 不是 doi.org / pubmed
    u = keys.get("url")
    doi = (row.get("doi") or "").strip()
    pmid = (row.get("pmid") or "").strip()
    if isinstance(u, ast.Constant) and isinstance(u.value, str) and doi:
        url = u.value
        if "doi.org" not in url and "pubmed.ncbi.nlm.nih.gov" not in url:
            if idx in PMID_FILL:
                new = f"https://pubmed.ncbi.nlm.nih.gov/{PMID_FILL[idx]}/"
            else:
                new = f"https://doi.org/{doi}"
            edits.append((pos(u.lineno, u.col_offset), pos(u.end_lineno, u.end_col_offset),
                          json.dumps(new), idx, "url", url, new))

    # 3) 缺失 PMID 的补全（None/空串 -> 实值；字段不存在则插入）
    if idx in PMID_FILL:
        pnode = keys.get("pmid")
        if pnode is None:
            if isinstance(el, ast.Call):
                at = pos(el.lineno, el.col_offset) + len("dict(")
                inserts.append((at, f'pmid="{PMID_FILL[idx]}", ', idx))
        else:
            old = ast.get_source_segment(src, pnode)
            if old in ("None", "''", '""'):
                edits.append((pos(pnode.lineno, pnode.col_offset), pos(pnode.end_lineno, pnode.end_col_offset),
                              f'"{PMID_FILL[idx]}"', idx, "pmid", old, PMID_FILL[idx]))

print(f"标题去句点 {sum(1 for e in edits if e[4]=='title')} 条 | 链接规范化 {sum(1 for e in edits if e[4].startswith('url'))} 条 | 补 pmid {len(inserts)} 条")
for e in edits:
    if e[4] != "title":
        print(f"  id{e[3]} {e[4]}: {e[5]} -> {e[6]}")

if DRY:
    print("[dry-run] 未写入")
    raise SystemExit(0)

out = src
for s, e, text, *_ in sorted(edits, key=lambda x: -x[0]):
    out = out[:s] + text + out[e:]
for at, text, _ in sorted(inserts, key=lambda x: -x[0]):
    out = out[:at] + text + out[at:]

bak = SEED + ".bak." + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(SEED, bak)
open(SEED, "w", encoding="utf-8").write(out)

# 回读校验
tree2 = ast.parse(open(SEED, encoding="utf-8").read())
items2 = load_articles(tree2)
assert len(items2) == len(items), "条数变化！"
print("已写入，备份:", bak)
