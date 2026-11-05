# -*- coding: utf-8 -*-
"""从 seed.py 中删除指定位置(id)的文献条目，并清理空分类。幂等：重跑无变化。
注意：seed.py 条目是 dict(pmid=..., collection=...) 调用，无 id 字段，
id = 在 SEED_ARTICLES 中的位置（1 起）。"""
import ast, sys

SEED = r"C:\Users\User\Desktop\neurosearch\server\seed.py"

# 待删除：明显不符合 27 + 边缘不符合 32
DELETE = {53,57,58,59,60,61,135,136,
          50,51,56,82,83,84,85,133,
          54,55,64,77,78,
          116,
          139,140,141,142,143,
          65,66,67,68,69,70,73,114,115,117,118,119,124,
          45,46,47,48,49,
          14,80,89,144,
          71,113,130,
          40,41,42,
          137,132,62,79}

src = open(SEED, encoding="utf-8").read()
tree = ast.parse(src)

seed_assign = meta_assign = None
for node in tree.body:
    if isinstance(node, ast.Assign):
        tid = getattr(node.targets[0], "id", "")
        if tid == "SEED_ARTICLES":
            seed_assign = node
        elif tid == "COLLECTION_META":
            meta_assign = node
assert seed_assign is not None and meta_assign is not None

ranges = []
remaining_coll = {}
n_seed = len(seed_assign.value.elts)
to_del = []
for idx, el in enumerate(seed_assign.value.elts, start=1):
    coll = None
    for kw in el.keywords:
        if kw.arg == "collection":
            coll = ast.literal_eval(kw.value)
    if idx in DELETE:
        ranges.append((el.lineno, el.end_lineno))
        to_del.append(idx)
    else:
        remaining_coll[coll] = remaining_coll.get(coll, 0) + 1

meta_removed = []
for el in meta_assign.value.elts:
    name = ast.literal_eval(el.values[0])   # {"name": "儿童早期筛查", ...}
    if name not in remaining_coll:
        ranges.append((el.lineno, el.end_lineno))
        meta_removed.append(name)

assert len(to_del) == len(DELETE), f"实际匹配 {len(to_del)} != 期望 {len(DELETE)}"
print(f"原条目 {n_seed}，待删 {len(to_del)}，剩余 {n_seed - len(to_del)}")
print("剩余分类:", remaining_coll)
print("清空并移除的分类:", meta_removed)
if "--dry" in sys.argv:
    sys.exit(0)

lines = src.splitlines(keepends=True)
for start, end in sorted(ranges, reverse=True):
    del lines[start - 1:end]
out = "".join(lines)
open(SEED, "w", encoding="utf-8", newline="").write(out)

# 校验
ns = {}
exec(compile(out, SEED, "exec"), ns)
arts = ns["SEED_ARTICLES"]
assert len(arts) == n_seed - len(DELETE), f"条目数 {len(arts)} != {n_seed - len(DELETE)}"
pmids = [a["pmid"] for a in arts if a.get("pmid")]
dup = len(pmids) - len(set(pmids))
colls = {a["collection"] for a in arts}
meta_names = [m["name"] for m in ns["COLLECTION_META"]]
print(f"写入完成：{len(arts)} 条，重复 PMID {dup} 个")
print("数据分类:", colls)
print("META 分类:", meta_names)
assert colls == set(meta_names), f"分类不一致: {colls ^ set(meta_names)}"
