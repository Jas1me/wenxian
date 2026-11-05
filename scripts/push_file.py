# -*- coding: utf-8 -*-
"""用 GitHub Contents API 创建或更新单个文件（令牌从环境变量 GITHUB_TOKEN 读）"""
import base64, json, os, sys, urllib.request

OWNER, REPO, BRANCH = "Jas1me", "wenxian", "main"
TOKEN = os.environ.get("GITHUB_TOKEN")
if not TOKEN:
    sys.exit("缺少环境变量 GITHUB_TOKEN")

local_path, repo_path = sys.argv[1], sys.argv[2]
msg = sys.argv[3] if len(sys.argv) > 3 else "Update " + repo_path

API = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{repo_path}"


def req(url, method="GET", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Authorization", "Bearer " + TOKEN)
    r.add_header("Accept", "application/vnd.github+json")
    r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


with open(local_path, "rb") as f:
    content = base64.b64encode(f.read()).decode()

code, meta = req(API + "?ref=" + BRANCH)
sha = meta.get("sha") if code == 200 else None
body = {"message": msg, "content": content, "branch": BRANCH}
if sha:
    body["sha"] = sha

code, out = req(API, "PUT", body)
if code in (200, 201):
    print(f"OK  {'更新' if sha else '新建'} {repo_path}  -> {out.get('content', {}).get('html_url')}")
else:
    print("失败 HTTP", code, json.dumps(out, ensure_ascii=False)[:400])
