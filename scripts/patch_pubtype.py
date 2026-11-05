# -*- coding: utf-8 -*-
"""按 PubMed 出版物类型修正 pub_type（逐条人工复核后的定稿清单）"""
import ast, json, shutil, sys, time

SEED = r"C:\Users\User\Desktop\neurosearch\server\seed.py"
DRY = "--dry" in sys.argv

# 复核依据：Europe PMC pubTypeList + 标题/中文摘要人工判断
PATCH = {
    3: "Meta分析",     # EIBI meta-analysis（原标系统评价）
    16: "Meta分析",    # 家长介导干预 meta-analysis
    55: "Meta分析",    # 早期行为干预效应 meta-analysis
    59: "Meta分析",    # AAC 影响 meta-analysis
    78: "Meta分析",    # 运动干预 meta-analysis
    88: "综述",        # Scoping Review
    95: "综述",        # Scoping Review
    106: "综述",       # Review: EIBI/发育干预效果
    146: "综述",       # PRT current perspectives
    186: "系统评价",   # Overview of Meta-Analyses（系统检索+滚雪球）
    220: "病例报告",   # Case Reports
    257: "综述",       # Scoping Review
    259: "综述",       # Review
    260: "临床试验",   # RCT（原标综述）
    273: "综述",       # 叙述性综述
    294: "综述",       # Scoping Review
    314: "综述",       # 整合综述
    336: "综述",       # 述评性综述
    338: "综述",       # Scoping Review
    395: "Meta分析",   # IPD meta-analysis
}
# 明确保留原分类的特例（PubMed 类型与内容不符，以内容为准）
KEEP = {100: "伞式综述，系统评价", 180: "PACT-G 试验报告，临床试验", 202: "单一被试实验，临床试验", 357: "单一被试实验，临床试验"}

src = open(SEED, encoding="utf-8").read()
tree = ast.parse(src)
items = [n for n in tree.body if isinstance(n, ast.Assign)
         and any(getattr(t, "id", None) == "SEED_ARTICLES" for t in n.targets)][0].value.elts

lines = src.split("\n")
starts, acc = [], 0
for ln in lines:
    starts.append(acc)
    acc += len(ln) + 1


def pos(ln, col):
    raw = lines[ln - 1].encode("utf-8")
    return starts[ln - 1] + len(raw[:col].decode("utf-8", errors="ignore"))


edits = []
for idx, el in enumerate(items, start=1):
    if idx not in PATCH:
        continue
    keys = {kw.arg: kw.value for kw in el.keywords if kw.arg} if isinstance(el, ast.Call) else {}
    node = keys.get("pub_type")
    if node is None:
        print("  !! id%d 没有 pub_type", idx)
        continue
    old = ast.get_source_segment(src, node)
    new = json.dumps(PATCH[idx], ensure_ascii=False)
    if old == new:
        continue
    edits.append((pos(node.lineno, node.col_offset), pos(node.end_lineno, node.end_col_offset), new, idx, old, PATCH[idx]))

print(f"待改 {len(edits)} 条；保留特例 {KEEP}")
for e in edits:
    print(f"  id{e[3]:<4} {e[4]} -> {e[5]}")
if DRY:
    raise SystemExit(0)

out = src
for s, e, t, *_ in sorted(edits, key=lambda x: -x[0]):
    out = out[:s] + t + out[e:]

bak = SEED + ".bak." + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(SEED, bak)
open(SEED, "w", encoding="utf-8").write(out)
tree2 = ast.parse(open(SEED, encoding="utf-8").read())
n2 = [n for n in tree2.body if isinstance(n, ast.Assign)
      and any(getattr(t, "id", None) == "SEED_ARTICLES" for t in n.targets)][0].value.elts
assert len(n2) == len(items)
print("已写入，备份", bak)
