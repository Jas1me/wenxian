# -*- coding: utf-8 -*-
"""基于缓存的 PubMed 出版物类型，给出 pub_type 修正建议（标题优先，避免把 meta 分析降级成综述）"""
import json, re, sqlite3

CACHE = json.load(open(r"C:\Users\User\WorkBuddy\2026-10-30-16-02-06\pubtypes.json", encoding="utf-8"))
DB = r"C:\Users\User\Desktop\neurosearch\server\neurosearch.db"
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
rows = [dict(r) for r in conn.execute("SELECT id,pmid,title,pub_type FROM articles WHERE id>85 ORDER BY id")]

META = re.compile(r"meta[- ]analy", re.I)
SR = re.compile(r"systematic review|systematic literature", re.I)
CASE = re.compile(r"case (report|study|series)", re.I)


def decide(title, types, cur):
    t = [x.lower() for x in types]
    join = " ".join(t)
    if META.search(title) or "meta-analysis" in join:
        return "Meta分析"
    if SR.search(title) or "systematic review" in join:
        return "系统评价"
    if "case reports" in join or CASE.search(title):
        return "病例报告"
    if "randomized controlled trial" in join or "clinical trial" in join or "controlled clinical trial" in join:
        return "临床试验"
    if "scoping review" in join or "review" in join:
        return "综述"
    if "observational study" in join or "cohort" in join:
        return "队列研究"
    return cur


changes = []
for r in rows:
    types = CACHE.get((r["pmid"] or "").strip())
    if not types:
        continue
    new = decide(r["title"], types, r["pub_type"])
    if new != r["pub_type"]:
        changes.append({"id": r["id"], "old": r["pub_type"], "new": new,
                        "types": ",".join(types), "title": r["title"]})

print("建议调整", len(changes), "条")
for c in changes:
    print(f"  id{c['id']:<4} {c['old']} -> {c['new']:<5} | {c['title'][:72]}")

json.dump({str(c["id"]): {"pub_type": c["new"]} for c in changes},
          open(r"C:\Users\User\WorkBuddy\2026-10-30-16-02-06\pubtype_patch2.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
