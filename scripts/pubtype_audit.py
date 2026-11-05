# -*- coding: utf-8 -*-
"""核对新增条目的 pub_type 是否与 PubMed 出版物类型一致（只诊断，不改数据）"""
import json, re, sqlite3, time, urllib.parse, urllib.request

DB = r"C:\Users\User\Desktop\neurosearch\server\neurosearch.db"
UA = {"User-Agent": "NeuroSearch/1.0"}

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
rows = [dict(r) for r in conn.execute("SELECT id,pmid,title,pub_type FROM articles WHERE id>85 ORDER BY id")]
print("待核对", len(rows))


def fetch(pmid):
    u = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:"
         + pmid + "%20AND%20SRC:MED&format=json&resultType=core")
    req = urllib.request.Request(u, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode())
    res = d.get("resultList", {}).get("result", [])
    return res[0].get("pubTypeList", {}).get("pubType", []) if res else None


def map_type(types):
    t = [x.lower() for x in types]
    has = lambda *k: any(any(k2 in x for x in t) for k2 in k)
    if has("meta-analysis", "meta analysis"):
        return "Meta分析"
    if has("systematic review"):
        return "系统评价"
    if has("randomized controlled trial", "clinical trial", "controlled clinical trial", "clinical study"):
        return "临床试验"
    if has("case reports", "case report"):
        return "病例报告"
    if "review" in " ".join(t):
        return "综述"
    if has("observational study", "cohort"):
        return "队列研究"
    return None


cache_path = r"C:\Users\User\WorkBuddy\2026-10-30-16-02-06\pubtypes.json"
try:
    cache = json.load(open(cache_path, encoding="utf-8"))
except Exception:
    cache = {}

changed = []
unknown = []
for i, r in enumerate(rows, 1):
    pmid = (r["pmid"] or "").strip()
    if not pmid:
        continue
    if pmid in cache:
        types = cache[pmid]
    else:
        for attempt in range(3):
            try:
                types = fetch(pmid)
                break
            except Exception as e:
                types = None
                time.sleep(1.5)
        cache[pmid] = types
        if i % 50 == 0:
            json.dump(cache, open(cache_path, "w", encoding="utf-8"))
    if types is None:
        unknown.append(r["id"])
        continue
    new = map_type(types)
    if new and new != r["pub_type"]:
        changed.append((r["id"], r["pub_type"], new, ",".join(types)[:70], r["title"][:60]))

json.dump(cache, open(cache_path, "w", encoding="utf-8"))
json.dump([{"id": c[0], "old": c[1], "new": c[2], "types": c[3], "title": c[4]} for c in changed],
          open(r"C:\Users\User\WorkBuddy\2026-10-30-16-02-06\pubtype_patch.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("查询失败:", len(unknown), unknown[:10])
print("类型需调整:", len(changed))
import collections
print("调整方向:", collections.Counter(f"{o}->{n}" for _, o, n, *_ in changed))
for c in changed[:15]:
    print("  id%-4s %s -> %s | %s | %s" % c)
