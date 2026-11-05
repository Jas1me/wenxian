# -*- coding: utf-8 -*-
"""把 final_add.json 的 319 篇文献追加到 seed.py 的 SEED_ARTICLES（幂等：按 PMID 查重跳过已存在）。"""
import ast, json, re, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
SEED = r"C:\Users\User\Desktop\neurosearch\server\seed.py"
DRY = "--dry" in sys.argv

add = json.load(open(os.path.join(BASE, "final_add.json"), encoding="utf-8"))
zh = json.load(open(os.path.join(BASE, "zh_all.json"), encoding="utf-8"))

KEYWORDS = {
    "AAC辅助沟通": "augmentative and alternative communication; AAC; autism spectrum disorder; communication intervention",
    "PECS图片交换沟通系统": "PECS; picture exchange communication system; autism spectrum disorder; communication",
    "ABA应用行为分析": "applied behavior analysis; ABA; early intensive behavioral intervention; autism spectrum disorder",
    "PRT关键反应训练": "pivotal response treatment; PRT; naturalistic intervention; autism spectrum disorder",
    "ESDM丹佛模式": "Early Start Denver Model; ESDM; early intervention; autism spectrum disorder",
    "JASPER": "JASPER; joint attention; symbolic play; naturalistic developmental behavioral intervention",
    "PACT学龄前孤独症沟通 trial": "PACT; parent-mediated communication therapy; social communication; autism",
    "NDBI自然发展行为干预": "naturalistic developmental behavioral intervention; NDBI; early intervention; autism spectrum disorder",
    "TEACCH结构化教学": "TEACCH; structured teaching; autism spectrum disorder; intervention",
    "言语语言治疗": "speech-language therapy; speech intervention; language development; autism spectrum disorder",
    "语言干预(泛ASD)": "language intervention; expressive language; autism spectrum disorder",
    "共同注意与游戏干预": "joint attention; play intervention; social communication; autism spectrum disorder",
    "家长介导干预": "parent-mediated intervention; parent training; autism spectrum disorder; early intervention",
    "社交技能训练": "social skills training; social communication; autism spectrum disorder",
    "视频示范与社交故事": "video modeling; social stories; behavioral intervention; autism spectrum disorder",
    "音乐治疗(沟通)": "music therapy; social communication; autism spectrum disorder",
    "同伴介导与融合": "peer-mediated intervention; inclusive education; social interaction; autism spectrum disorder",
    "技术辅助干预": "technology-assisted intervention; virtual reality; telehealth; autism spectrum disorder",
    "感觉统合与运动干预": "sensory integration; physical exercise; occupational therapy; autism spectrum disorder",
    "早期干预(泛ASD)": "early intervention; developmental outcomes; autism spectrum disorder",
}

def clean(s):
    s = s or ""
    s = s.replace("&lt;i&gt;", "").replace("&lt;/i&gt;", "")
    s = s.replace("&lt;sup&gt;", "").replace("&lt;/sup&gt;", "")
    s = s.replace("&amp;", "&")
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip()

def pystr(v):
    """生成安全的单行 Python 字符串字面量"""
    return json.dumps(str(v), ensure_ascii=False)

# 现有条目 PMID（用于查重）
src = open(SEED, encoding="utf-8").read()
tree = ast.parse(src)
existing_pmids = set()
for n in tree.body:
    if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "SEED_ARTICLES":
        for el in n.value.elts:
            for kw in el.keywords:
                if kw.arg == "pmid":
                    existing_pmids.add(str(ast.literal_eval(kw.value)))

entries = []
skipped = []
for x in add:
    pmid = str(x["pmid"])
    if pmid in existing_pmids:
        skipped.append(pmid)
        continue
    entries.append({
        "pmid": pmid,
        "title": clean(x["title"]),
        "authors": clean(x["authors"]).rstrip("."),
        "journal": clean(x["journal"]),
        "year": str(x["year"]),
        "pub_type": x["pub_type"],
        "collection": x["proposed_collection"],
        "abstract": clean(zh[pmid]),
        "keywords": KEYWORDS.get(x["treatment_type"], "autism spectrum disorder; intervention"),
        "doi": (x.get("doi") or "").strip(),
        "url": x["url"],
    })

print(f"现有 {len(existing_pmids)} 条 | 待追加 {len(entries)} 条 | 因重复跳过 {len(skipped)} 条")
if skipped:
    print("  跳过 PMID:", skipped)

# 校验字段完整性
for e in entries:
    for f in ("pmid", "title", "authors", "journal", "year", "pub_type", "collection", "abstract", "url"):
        assert e[f], f"字段为空: {e['pmid']} {f}"

def render(e):
    lines = [f"dict(pmid={pystr(e['pmid'])},"]
    order = ["title", "authors", "journal", "year", "pub_type", "collection", "abstract", "keywords", "doi", "url"]
    for f in order:
        lines.append(f"      {f}={pystr(e[f])},")
    lines[-1] = lines[-1].rstrip(",") + ")"
    return "\n".join(lines)

if DRY:
    print("--- 预览第一条 ---")
    print(render(entries[0]))
    print("--- 预览最后一条 ---")
    print(render(entries[-1]))
    sys.exit(0)

# 定位 SEED_ARTICLES 最后一个元素的结束位置，在其后插入
tree = ast.parse(src)
target = None
for n in tree.body:
    if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "SEED_ARTICLES":
        target = n
if target is None:
    sys.exit("找不到 SEED_ARTICLES")
last = target.value.elts[-1]
lines = src.splitlines(keepends=True)
ins_line = last.end_lineno  # 1-based，元素结束行；插入点在第 ins_line 行末尾
prev_tail = lines[ins_line - 1].rstrip()
joiner = "" if prev_tail.endswith(",") else ","
insert_text = joiner + ",\n".join(render(e) for e in entries) + ",\n"
new = "".join(lines[:ins_line]) + insert_text + "".join(lines[ins_line:])
ast.parse(new)  # 语法校验
open(SEED, "w", encoding="utf-8", newline="\n").write(new)
print(f"已写入 {len(entries)} 条到 seed.py")
