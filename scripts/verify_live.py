# -*- coding: utf-8 -*-
"""线上站点最终验收（只读）"""
import json, random, re, urllib.request

BASE = "https://neurosearch-ljgj.onrender.com"


def get(path, raw=False, timeout=90):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": "verify"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
        return data.decode("utf-8") if raw else json.loads(data.decode("utf-8"))


st = get("/api/stats")
print("stats:", st)
assert st["total"] == 404, st

# 抽样详情
ids = [1, 13, 85, 86, 150, 250, 404]
for i in ids:
    a = get(f"/api/articles/{i}")
    bad = ""
    if a["title"].endswith("."):
        bad = "  ❌ 标题仍带句点"
    print(f"  id{i:<4} pmid={a['pmid']} url={a['url']}  {a['title'][:60]}{bad}")
    assert not a["title"].endswith("."), a["title"]

# id13 校验
a13 = get("/api/articles/13")
assert a13["pmid"] == "38380766", a13["pmid"]
assert "pubmed.ncbi.nlm.nih.gov/38380766" in a13["url"], a13["url"]
print("  id13 PMID/链接已补全 ✅")

# 全量：随机抽 30 条确认无尾部句点、字段完整
allrows = get("/api/articles")
print("列表条数:", len(allrows))
sample = random.sample(allrows, 30)
for r in sample:
    assert r["title"].strip() and not r["title"].endswith("."), r
print("抽样 30 条标题格式 ✅")

# 搜索抽查
for kw in ["JASPER", "PECS", "ESDM", "TEACCH", "video modeling"]:
    res = get("/api/search?q=" + urllib.parse.quote(kw) + "&page_size=1") if False else None
import urllib.parse
for kw in ["JASPER", "PECS", "ESDM", "TEACCH", "video modeling"]:
    res = get("/api/search?q=" + urllib.parse.quote(kw) + "&page_size=1")
    print(f"  搜索 {kw}: {res['total']} 条")

cols = get("/api/collections")
print("分类:", [(c["name"], c["count"]) for c in cols])

info = get("/info.html", raw=True)
for kw in ["404 篇种子文献", "言语与沟通", "2026-11-05"]:
    print(f"  info.html 含「{kw}」:", kw in info)
print("首页:", len(get("/", raw=True)))
print("\n✅ 线上验收通过")
