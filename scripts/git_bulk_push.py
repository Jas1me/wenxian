# -*- coding: utf-8 -*-
"""用 GitHub Git Data API 一次性提交多个文件（单条 commit，避免十几次零碎提交）

用法: python git_bulk_push.py 提交说明
      文件清单改下面的 FILES
"""
import base64, json, os, sys, urllib.request, urllib.error

OWNER, REPO, BRANCH = "Jas1me", "wenxian", "main"
TOKEN = os.environ.get("GITHUB_TOKEN")
if not TOKEN:
    sys.exit("缺少环境变量 GITHUB_TOKEN")
API = f"https://api.github.com/repos/{OWNER}/{REPO}"

BASE = os.path.dirname(os.path.abspath(__file__))
PROJ = r"C:\Users\User\Desktop\neurosearch"

# (本地路径, 仓库内路径)
FILES = [
    (os.path.join(PROJ, "RESTORE.md"), "RESTORE.md"),
    (os.path.join(PROJ, "public", "info.html"), "public/info.html"),
    (os.path.join(PROJ, ".gitignore"), ".gitignore"),
    (os.path.join(BASE, "audit_final.py"), "scripts/audit_final.py"),
    (os.path.join(BASE, "resolve_missing.py"), "scripts/resolve_missing.py"),
    (os.path.join(BASE, "patch_seed_v2.py"), "scripts/patch_seed_v2.py"),
    (os.path.join(BASE, "pubtype_audit.py"), "scripts/pubtype_audit.py"),
    (os.path.join(BASE, "pubtype_plan.py"), "scripts/pubtype_plan.py"),
    (os.path.join(BASE, "patch_pubtype.py"), "scripts/patch_pubtype.py"),
    (os.path.join(BASE, "append_articles.py"), "scripts/append_articles.py"),
    (os.path.join(BASE, "remove_articles.py"), "scripts/remove_articles.py"),
    (os.path.join(BASE, "search_lit.py"), "scripts/search_lit.py"),
    (os.path.join(BASE, "verify_live.py"), "scripts/verify_live.py"),
    (os.path.join(BASE, "push_file.py"), "scripts/push_file.py"),
    (os.path.join(BASE, "git_bulk_push.py"), "scripts/git_bulk_push.py"),
    (os.path.join(BASE, "文献库核验报告.html"), "docs/文献库核验报告.html"),
    (os.path.join(BASE, "文献库修正报告.html"), "docs/文献库修正报告.html"),
    (os.path.join(BASE, "治疗方法候选文献清单.html"), "docs/治疗方法候选文献清单.html"),
    (os.path.join(BASE, "2026-11-05-规范化版", "变更记录.md"), "docs/变更记录-2026-11-05.md"),
]


def req(path, method="GET", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    r = urllib.request.Request(API + path, data=data, method=method)
    r.add_header("Authorization", "Bearer " + TOKEN)
    r.add_header("Accept", "application/vnd.github+json")
    r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


msg = sys.argv[1] if len(sys.argv) > 1 else "Update project files"

code, ref = req(f"/git/ref/heads/{BRANCH}")
if code != 200:
    sys.exit(f"取 ref 失败 {code} {ref}")
head = ref["object"]["sha"]
code, commit = req(f"/git/commits/{head}")
base_tree = commit["tree"]["sha"]
print("当前 HEAD", head[:7], "tree", base_tree[:7])

entries = []
for local, repo_path in FILES:
    if not os.path.exists(local):
        print("跳过（不存在）", local)
        continue
    content = base64.b64encode(open(local, "rb").read()).decode()
    code, blob = req("/git/blobs", "POST", {"content": content, "encoding": "base64"})
    if code not in (200, 201):
        sys.exit(f"blob 失败 {repo_path} {code} {blob}")
    entries.append({"path": repo_path, "mode": "100644", "type": "blob", "sha": blob["sha"]})
    print(f"  + {repo_path:<42} {os.path.getsize(local):>7} B")

code, tree = req("/git/trees", "POST", {"base_tree": base_tree, "tree": entries})
if code not in (200, 201):
    sys.exit(f"tree 失败 {code} {tree}")

code, newc = req("/git/commits", "POST", {"message": msg, "tree": tree["sha"], "parents": [head]})
if code not in (200, 201):
    sys.exit(f"commit 失败 {code} {newc}")

code, out = req(f"/git/refs/heads/{BRANCH}", "PATCH", {"sha": newc["sha"]})
if code != 200:
    sys.exit(f"更新 ref 失败 {code} {out}")
print(f"OK 单条提交 {newc['sha'][:7]}，{len(entries)} 个文件 -> https://github.com/{OWNER}/{REPO}")
