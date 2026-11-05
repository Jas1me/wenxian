# -*- coding: utf-8 -*-
"""对本地 404 篇库做完整字段体检（不改数据）"""
import re, sqlite3, json, collections, sys

DB = r"C:\Users\User\Desktop\neurosearch\server\neurosearch.db"
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
rows = [dict(r) for r in conn.execute("SELECT * FROM articles ORDER BY id")]
print("总数:", len(rows))

CJK = re.compile(r"[\u4e00-\u9fff]")
issues = collections.defaultdict(list)

for r in rows:
    for f in ("pmid", "title", "authors", "journal", "year", "pub_type", "abstract", "keywords", "doi", "url", "collection"):
        v = r.get(f)
        if v is None or (isinstance(v, str) and not v.strip()):
            issues["空字段:" + f].append(r["id"])
    ab = r.get("abstract") or ""
    if ab and not CJK.search(ab):
        issues["摘要无中文"].append(r["id"])
    if len(ab) < 60:
        issues["摘要过短"].append((r["id"], len(ab)))
    kw = r.get("keywords") or ""
    if kw and not CJK.search(kw):
        issues["关键词无中文"].append(r["id"])
    doi = r.get("doi") or ""
    if doi and not doi.startswith("10."):
        issues["DOI格式异常"].append((r["id"], doi))
    url = r.get("url") or ""
    if url and "pubmed.ncbi.nlm.nih.gov" not in url and "doi.org" not in url:
        issues["链接非常规"].append((r["id"], url))
    y = r.get("year")
    if not isinstance(y, int) or not (1900 <= y <= 2027):
        issues["年份异常"].append((r["id"], y))
    t = r.get("title") or ""
    if t != t.strip() or t.endswith("."):
        issues["标题尾部标点/空白"].append(r["id"])
    au = r.get("authors") or ""
    if "(" in au or "indexed journal" in au.lower() or "et al" in au.lower():
        issues["作者占位符"].append((r["id"], au[:60]))

# 重复
for f in ("pmid", "doi"):
    c = collections.Counter((r.get(f) or "").strip().lower() for r in rows if r.get(f))
    for k, n in c.items():
        if n > 1:
            issues[f + "重复"].append((k, n, [r["id"] for r in rows if (r.get(f) or "").lower() == k]))
c = collections.Counter((r["title"] or "").strip().lower() for r in rows)
for k, n in c.items():
    if n > 1:
        issues["标题重复"].append((k[:70], n))

# 分类统计
print("分类:", collections.Counter(r["collection"] for r in rows))
print("类型:", collections.Counter(r["pub_type"] for r in rows))
print("无 DOI:", sum(1 for r in rows if not (r.get("doi") or "").strip()))
print()
if not issues:
    print("✅ 无任何字段问题")
for k, v in issues.items():
    print(f"[{k}] {len(v)} 条 -> {v[:12]}")
