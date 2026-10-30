# -*- coding: utf-8 -*-
"""
NeuroSearch 后端服务（零依赖，仅需 Python 3.8+）
启动:  python server/server.py
访问:  http://localhost:8000
"""
import json, os, re, sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "..", "public")
DB_PATH    = os.path.join(BASE_DIR, "neurosearch.db")
PORT       = int(os.environ.get("PORT", "8000"))

import seed
if not os.path.exists(DB_PATH):
    seed.init_db()

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def rows_to_dicts(rows):
    return [dict(r) for r in rows]

# ---------------- 查询逻辑 ----------------
def search_articles(q, pub_type, year_from, year_to, if_min, collection, page, page_size):
    where, params = [], []
    if q:
        like = f"%{q}%"
        where.append("(title LIKE ? OR authors LIKE ? OR journal LIKE ? OR keywords LIKE ? OR abstract LIKE ?)")
        params += [like] * 5
    if pub_type:
        where.append("pub_type = ?")
        params.append(pub_type)
    if year_from: where.append("year >= ?"); params.append(int(year_from))
    if year_to:   where.append("year <= ?"); params.append(int(year_to))
    if if_min:    where.append("(impact_factor >= ? OR (impact_factor IS NULL AND ? = 0))"); params += [float(if_min), float(if_min)]
    if collection: where.append("collection = ?"); params.append(collection)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    conn = db()
    total = conn.execute(f"SELECT COUNT(*) c FROM articles {where_sql}", params).fetchone()["c"]
    items = conn.execute(
        f"SELECT id,pmid,title,authors,journal,year,pub_type,abstract,keywords,doi,url,impact_factor,collection "
        f"FROM articles {where_sql} ORDER BY year DESC, id DESC LIMIT ? OFFSET ?",
        params + [page_size, (page - 1) * page_size]).fetchall()
    conn.close()
    return {"total": total, "page": page, "page_size": page_size,
            "items": rows_to_dicts(items)}

def get_stats():
    conn = db()
    total   = conn.execute("SELECT COUNT(*) c FROM articles").fetchone()["c"]
    types   = {r["pub_type"]: r["c"] for r in conn.execute(
        "SELECT pub_type, COUNT(*) c FROM articles GROUP BY pub_type")}
    years   = conn.execute("SELECT MIN(year) y1, MAX(year) y2 FROM articles").fetchone()
    sources = conn.execute("SELECT COUNT(DISTINCT journal) c FROM articles").fetchone()["c"]
    recent  = conn.execute("SELECT COUNT(*) c FROM articles WHERE year >= 2025").fetchone()["c"]
    conn.close()
    return {"total": total, "by_type": types,
            "year_min": years["y1"], "year_max": years["y2"],
            "sources": sources, "recent": recent}

def get_collections():
    conn = db()
    counts = {r["collection"]: r["c"] for r in conn.execute(
        "SELECT collection, COUNT(*) c FROM articles GROUP BY collection")}
    latest = {r["collection"]: r["y"] for r in conn.execute(
        "SELECT collection, MAX(year) y FROM articles GROUP BY collection")}
    conn.close()
    return [{"name": m["name"], "icon": m["icon"], "desc": m["desc"],
             "count": counts.get(m["name"], 0), "latest_year": latest.get(m["name"])}
            for m in seed.COLLECTION_META]

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# ---------------- HTTP 处理 ----------------
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # 静音访问日志
        pass

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _static(self, path):
        if path in ("/", ""):
            path = "/index.html"
        fp = os.path.normpath(os.path.join(PUBLIC_DIR, path.lstrip("/")))
        if not fp.startswith(os.path.abspath(PUBLIC_DIR)) or not os.path.exists(fp) or os.path.isdir(fp):
            self.send_response(404); self.end_headers(); return
        ctype = {".html": "text/html; charset=utf-8", ".js": "text/javascript",
                 ".css": "text/css", ".png": "image/png", ".svg": "image/svg+xml",
                 ".json": "application/json"}.get(os.path.splitext(fp)[1], "application/octet-stream")
        with open(fp, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        path, qs = u.path, parse_qs(u.query)
        g = lambda k, d=None: (qs.get(k, [d])[0])
        try:
            if path == "/api/stats":
                self._send(200, get_stats())
            elif path == "/api/search":
                self._send(200, search_articles(
                    g("q"), g("type"), g("year_from"), g("year_to"),
                    g("if_min"), g("collection"),
                    int(g("page", 1)), min(int(g("page_size", 10)), 50)))
            elif path == "/api/collections":
                self._send(200, get_collections())
            elif path == "/api/articles":
                conn = db()
                items = conn.execute(
                    "SELECT id,pmid,title,authors,journal,year,pub_type,collection,url FROM articles ORDER BY year DESC").fetchall()
                conn.close()
                self._send(200, rows_to_dicts(items))
            elif path.startswith("/api/articles/"):
                aid = path.rsplit("/", 1)[1]
                conn = db()
                row = conn.execute("SELECT * FROM articles WHERE id=?", (aid,)).fetchone()
                conn.close()
                self._send(200 if row else 404, dict(row) if row else {"error": "not found"})
            elif path.startswith("/api/"):
                self._send(404, {"error": "unknown endpoint"})
            else:
                self._static(path)
        except Exception as e:
            self._send(500, {"error": str(e)})

    def do_POST(self):
        u = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            payload = {}
        try:
            if u.path == "/api/subscribe":
                email = (payload.get("email") or "").strip().lower()
                if not EMAIL_RE.match(email):
                    self._send(400, {"ok": False, "msg": "邮箱格式不正确"})
                    return
                conn = db()
                try:
                    conn.execute("INSERT INTO subscriptions(email) VALUES(?)", (email,))
                    conn.commit()
                    self._send(200, {"ok": True, "msg": "订阅成功，每周更新将发送至您的邮箱"})
                except sqlite3.IntegrityError:
                    self._send(200, {"ok": True, "msg": "该邮箱已订阅"})
                finally:
                    conn.close()
            elif u.path == "/api/articles":
                a = payload
                required = ["title", "authors", "journal", "year", "pub_type"]
                if any(not a.get(k) for k in required):
                    self._send(400, {"ok": False, "msg": "缺少必填字段: " + ", ".join(required)})
                    return
                conn = db()
                cur = conn.execute(
                    """INSERT INTO articles (pmid,title,authors,journal,year,pub_type,abstract,keywords,doi,url,impact_factor,collection)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (a.get("pmid"), a["title"], a["authors"], a["journal"], int(a["year"]),
                     a["pub_type"], a.get("abstract"), a.get("keywords"), a.get("doi"),
                     a.get("url"), a.get("impact_factor"), a.get("collection") or "共病研究"))
                conn.commit()
                new_id = cur.lastrowid
                conn.close()
                self._send(201, {"ok": True, "id": new_id, "msg": "文献已入库"})
            else:
                self._send(404, {"error": "unknown endpoint"})
        except Exception as e:
            self._send(500, {"ok": False, "msg": str(e)})

    def do_DELETE(self):
        u = urlparse(self.path)
        if u.path.startswith("/api/articles/"):
            aid = u.path.rsplit("/", 1)[1]
            conn = db()
            cur = conn.execute("DELETE FROM articles WHERE id=?", (aid,))
            conn.commit()
            n = cur.rowcount
            conn.close()
            self._send(200, {"ok": n > 0, "msg": "已删除" if n else "记录不存在"})
        else:
            self._send(404, {"error": "unknown endpoint"})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

if __name__ == "__main__":
    print(f"NeuroSearch 数据库服务已启动: http://localhost:{PORT}")
    print(f"数据库文件: {DB_PATH}")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
