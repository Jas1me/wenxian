# -*- coding: utf-8 -*-
"""按治疗方法分类，在 Europe PMC(PubMed镜像) 做标题级全面检索，
收集网站所需字段并与现有85篇去重。输出 candidates.json"""
import json, urllib.request, urllib.parse, time, re, runpy, sys

OUT = r"C:\Users\User\WorkBuddy\2026-10-30-16-02-06\candidates.json"
UA = {"User-Agent": "Mozilla/5.0 NeuroSearch/1.0"}

# ---------- 现有库（85篇）去重基准 ----------
ns = runpy.run_path(r"C:\Users\User\Desktop\neurosearch\server\seed.py")
existing = ns["SEED_ARTICLES"]
exist_pmids = {str(a["pmid"]) for a in existing if a.get("pmid")}
exist_dois = {(a.get("doi") or "").lower() for a in existing if a.get("doi")}
exist_titles = {re.sub(r"[^a-z0-9]+", "", (a["title"] or "").lower()) for a in existing}
print(f"现有库 {len(existing)} 篇（PMID {len(exist_pmids)}，DOI {len(exist_dois)}）")

# ---------- 检索式：按治疗方法，标题级 ----------
QUERIES = [
 ("AAC辅助沟通", 'TITLE:(autism* AND (augmentative OR "alternative communication"))'),
 ("PECS图片交换系统", 'TITLE:PECS'),
 ("ABA应用行为分析", 'TITLE:(autism* AND ("applied behavior*" OR ABA OR "early intensive behavioral" OR "early intensive behavioural" OR "discrete trial"))'),
 ("PRT关键反应训练", 'TITLE:(autism* AND ("pivotal response" OR PRT))'),
 ("ESDM丹佛模式", 'TITLE:("early start denver" OR (ESDM AND autism*))'),
 ("JASPER", "TITLE:JASPER"),
 ("PACT学龄前孤独症沟通 trial", 'TITLE:("preschool autism communication trial" OR (PACT AND autism* AND communication))'),
 ("NDBI自然发展行为干预", 'TITLE:((autism* OR "spectrum disorder") AND ("naturalistic developmental behavioral" OR NDBI OR "enhanced milieu" OR "reciprocal imitation" OR "project impact"))'),
 ("TEACCH结构化教学", "TITLE:TEACCH"),
 ("言语语言治疗", 'TITLE:(autism* AND (speech OR "language intervention*" OR "language therapy" OR "language outcomes" OR "language acquisition" OR phonolog* OR "spoken language"))'),
 ("共同注意与游戏干预", 'TITLE:((autism* OR "spectrum disorder") AND ("joint attention" OR "symbolic play" OR "pretend play"))'),
 ("家长介导干预", 'TITLE:((autism* OR "spectrum disorder") AND ("parent-mediated" OR "parent-implemented" OR "parent training" OR "caregiver-mediated" OR "mother-implemented"))'),
 ("社交技能训练", 'TITLE:(autism* AND "social skills")'),
 ("视频示范与社交故事", 'TITLE:(autism* AND ((video AND (modeling OR modelling OR "self-model")) OR "social stories" OR "social story"))'),
 ("音乐治疗(沟通)", 'TITLE:(autism* AND music)'),
 ("同伴介导与融合", 'TITLE:(autism* AND ("peer-mediated" OR "peer-mediated" OR "peer training" OR "peer play" OR inclusive))'),
 ("技术辅助干预", 'TITLE:((autism* OR "spectrum disorder") AND (telehealth OR telepractice OR "virtual reality" OR "social robot*" OR "digital intervention*" OR wearable OR tablet))'),
 ("感觉统合与运动干预", 'TITLE:(autism* AND (sensory OR "occupational therapy" OR "physical exercise" OR "physical activity" OR "motor skill*"))'),
 ("语言干预(泛ASD)", 'TITLE:("spectrum disorder" AND (intervention OR training) AND (language OR communication OR speech))'),
 ("早期干预(泛ASD)", 'TITLE:((autism* OR "spectrum disorder") AND "early intervention")'),
]

BLACK = re.compile(r"prevalence|vaccine|vaccination|exome|genome|genetic|transcriptom|gene expression|biomarker|camouflag|pathway|mice|murine|rat model|neural mechanism|gut microbiota|fecal|pharmacokinetic|dietary intake|physical activity level|activity level|barrier|perspective of|knowledge and attitude|willingness|stigma|service use|access to|waitlist|psychometric|\bblock\b|nerve block|anesthe|analges|ultrasound.guided|mutant|transcriptional|cofactor|proteomic|correction:|erratum|bibliometric|critical analysis|editorial|commentar|saliva|hair|biomarker|polymorph", re.I)
# 必须是干预/治疗/训练性质的研究
INTERV = re.compile(r"intervention|treatment|therap|training|trial|teach|program|effective|efficacy|effect of|effects of|improv|increas|reduc|enhanc|promot|skill|randomi[sz]ed|pilot|case report|case study|single.case|meta.analysis|review", re.I)
ADULT = re.compile(r"\badults?\b|young adults|geriatric|older adults", re.I)
AUTISM_OK = re.compile(r"autis|ASD|spectrum disorder|PECS|JASPER|ESDM|PACT", re.I)

def epmc(query, size=30):
    q = query + " AND SRC:MED"
    u = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?query="
         + urllib.parse.quote(q) + f"&format=json&pageSize={size}&resultType=core")
    for k in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40) as r:
                return json.load(r)
        except Exception as e:
            err = f"{type(e).__name__}"
            time.sleep(2)
    print("  !! 检索失败:", err, query[:50])
    return {"hitCount": 0, "resultList": {"result": []}}

def pub_type(t):
    tl = t.lower()
    if "meta-analysis" in tl or "meta analysis" in tl: return "Meta分析"
    if "systematic review" in tl or "scoping review" in tl or "umbrella" in tl: return "系统评价"
    if tl.startswith("review") or "a review" in tl or "evidence" in tl: return "综述"
    if "case report" in tl or "case study" in tl: return "病例报告"
    if re.search(r"randomi[sz]ed|randomised|\bRCT\b|controlled trial|clinical trial|pilot|crossover|cross-over", tl): return "临床试验"
    return "临床试验"

def trim_authors(s):
    parts = [x.strip() for x in (s or "").split(",") if x.strip()]
    return ", ".join(parts[:6]) + (", et al." if len(parts) > 6 else "")

def norm_title(t):
    return re.sub(r"[^a-z0-9]+", "", (t or "").lower())

results = []
seen_key = set()
stats = []
for cat, q in QUERIES:
    d = epmc(q)
    n_hit = d.get("hitCount", 0)
    kept = 0
    for x in d.get("resultList", {}).get("result", []):
        title = re.sub(r"\s+", " ", x.get("title", "")).strip()
        pmid = x.get("pmid") or ""
        doi = (x.get("doi") or "").lower().replace("http://dx.doi.org/", "")
        key_n = norm_title(title)
        k = pmid or key_n
        if k in seen_key: continue
        # 纳入：标题含孤独症/干预体系名；摘要兜底
        if not AUTISM_OK.search(title) and "autis" not in (x.get("abstractText") or "")[:400].lower(): continue
        # 排除：机制/流行病学/疫苗/动物等
        if BLACK.search(title): continue
        # 必须是干预/治疗性质
        if not INTERV.search(title): continue
        # 去重：与现有85篇
        if pmid and pmid in exist_pmids: continue
        if doi and doi in exist_dois: continue
        if key_n in exist_titles: continue
        seen_key.add(k)
        abst = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", x.get("abstractText") or "")).strip()
        year = int(x["pubYear"]) if x.get("pubYear", "").isdigit() else None
        results.append({
            "treatment_type": cat,
            "proposed_collection": "言语与沟通" if cat in ("AAC辅助沟通","PECS图片交换系统","言语语言治疗") else
                                   ("新兴技术干预" if cat == "技术辅助干预" else "干预与康复"),
            "pmid": pmid, "title": title,
            "authors": trim_authors(x.get("authorString", "")),
            "journal": (x.get("journalInfo", {}).get("journal", {}) or {}).get("title", ""),
            "year": year, "pub_type": pub_type(title),
            "doi": doi,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else (f"https://doi.org/{doi}" if doi else ""),
            "abstract_en": abst[:1500],
            "age_flag": "成人/老年" if ADULT.search(title) else ("含青少年" if re.search(r"adolescent|teenager", title, re.I) else "儿童/未限定"),
            "cited": x.get("citedByCount", 0),
        })
        kept += 1
    stats.append((cat, n_hit, kept))
    print(f"{cat:<24} 命中{n_hit:>5} 纳入{kept:>3}")
    time.sleep(0.4)

json.dump(results, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\n共纳入 {len(results)} 篇候选 -> {OUT}")
import collections
print(collections.Counter(r["proposed_collection"] for r in results))
print(collections.Counter(r["age_flag"] for r in results))
print("无PMID:", sum(1 for r in results if not r["pmid"]), "无DOI:", sum(1 for r in results if not r["doi"]))
