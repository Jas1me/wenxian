# -*- coding: utf-8 -*-
"""为缺失 PMID / DOI / 链接不规范的条目做权威反查（Europe PMC + Crossref），只产出补丁，不改库"""
import difflib, json, re, sqlite3, urllib.parse, urllib.request

DB = r"C:\Users\User\Desktop\neurosearch\server\neurosearch.db"
OUT = r"C:\Users\User\WorkBuddy\2026-10-30-16-02-06\patch_missing.json"
UA = {"User-Agent": "NeuroSearch/1.0 (mailto:neurosearch@example.com)"}


def get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def norm(t):
    t = (t or "").lower()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def epmc_by_title(title):
    q = 'TITLE:"%s"' % re.sub(r'"', "", title[:220])
    url = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?query="
           + urllib.parse.quote(q) + "&format=json&pageSize=5&resultType=core")
    try:
        d = get(url)
    except Exception as e:
        print("  EPMC 失败", e)
        return None
    best = None
    for it in d.get("resultList", {}).get("result", []):
        s = difflib.SequenceMatcher(None, norm(title), norm(it.get("title"))).ratio()
        if s >= 0.90 and (best is None or s > best[0]):
            best = (s, it)
    return best


def crossref_by_title(title, year=None):
    url = ("https://api.crossref.org/works?query.bibliographic="
           + urllib.parse.quote(title[:200]) + "&rows=5&select=DOI,title,issued,container-title")
    try:
        d = get(url)
    except Exception as e:
        print("  Crossref 失败", e)
        return None
    best = None
    for it in d["message"]["items"]:
        t = (it.get("title") or [""])[0]
        s = difflib.SequenceMatcher(None, norm(title), norm(t)).ratio()
        if s >= 0.88 and (best is None or s > best[0]):
            best = (s, it)
    return best


def doi_alive(doi):
    try:
        req = urllib.request.Request("https://doi.org/api/handles/" + urllib.parse.quote(doi),
                                     headers=UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode()).get("responseCode") == 1
    except Exception:
        return False


conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
rows = [dict(r) for r in conn.execute("SELECT * FROM articles ORDER BY id")]

patch = {}
report = []

for r in rows:
    needs = []
    if not (r["pmid"] or "").strip():
        needs.append("pmid")
    if not (r["doi"] or "").strip():
        needs.append("doi")
    url = r["url"] or ""
    if url and "pubmed.ncbi.nlm.nih.gov" not in url and "doi.org" not in url:
        needs.append("url")
    if not needs or needs == ["url"] and not (r["doi"] or "").strip() and not (r["pmid"] or "").strip():
        pass
    if not needs:
        continue

    print(f"\nid{r['id']} 需补: {needs}  {r['title'][:80]}")
    upd = {}

    # 已有 PMID 但链接不规范 -> 直接用 PubMed 链接
    if "url" in needs and (r["pmid"] or "").strip():
        upd["url"] = f"https://pubmed.ncbi.nlm.nih.gov/{r['pmid'].strip()}/"

    if "pmid" in needs:
        hit = epmc_by_title(r["title"])
        if hit:
            s, it = hit
            if it.get("pmid"):
                upd["pmid"] = it["pmid"]
                upd.setdefault("url", f"https://pubmed.ncbi.nlm.nih.gov/{it['pmid']}/")
            if it.get("doi") and not (r["doi"] or "").strip():
                upd["doi"] = it["doi"].lower()
            for k, f in (("journalTitle", "journal"), ("pubYear", "year")):
                if it.get(k):
                    upd.setdefault(f, int(it[k]) if f == "year" else it[k])
            print(f"  EPMC {s:.3f} pmid={it.get('pmid')} doi={it.get('doi')}")
        else:
            print("  EPMC 未命中")

    if "doi" in needs and "doi" not in upd:
        hit = crossref_by_title(r["title"], r["year"])
        if hit:
            s, it = hit
            doi = it["DOI"].lower()
            if doi_alive(doi):
                upd["doi"] = doi
                print(f"  Crossref {s:.3f} doi={doi}")
            else:
                print(f"  Crossref 命中但 DOI 无法解析: {doi}")
        else:
            print("  Crossref 未命中")

    if "url" in needs and "url" not in upd:
        d = upd.get("doi") or (r["doi"] or "").strip()
        if d:
            upd["url"] = "https://doi.org/" + d

    if upd:
        patch[str(r["id"])] = upd
        report.append((r["id"], upd))

json.dump(patch, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"\n=== 可补全 {len(patch)} 条 -> {OUT}")
