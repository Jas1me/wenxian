# T³ — 孤独症医学文献检索系统（真实数据库版）

覆盖 ABA/EIBI、ESDM、PACT、AAC、言语治疗、家长干预、RDI、DSP、PRT、TEACCH、数字疗法与音乐干预等方向的完整全栈应用：

```
neurosearch/
├── server/
│   ├── server.py        # 后端 API 服务（Python 标准库，零依赖）
│   ├── seed.py          # 数据库初始化 + 真实 PubMed 种子文献（22篇）
│   └── neurosearch.db   # SQLite 数据库（首次启动自动生成）
├── public/
│   └── index.html       # 前端页面（从 API 读取真实数据）
└── README.md
```

## 快速启动

要求：Python 3.8+（无需安装任何第三方库）

```bash
cd neurosearch
python server/server.py
```

打开 http://localhost:8000

## API 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/stats | 文献统计（总数、按类型、年份范围、期刊数） |
| GET | /api/search?q=&type=&year_from=&if_min=&collection=&page= | 分页检索 |
| GET | /api/collections | 专题合集及文献计数 |
| GET | /api/articles | 全部文献列表 |
| GET | /api/articles/{id} | 单篇详情 |
| POST | /api/articles | 新增文献（JSON body） |
| DELETE | /api/articles/{id} | 删除文献 |
| POST | /api/subscribe | 邮箱订阅（校验格式、防重复） |

## 数据说明

- 种子数据为 **PubMed/PMC 真实文献**（2020–2026，含 PMID/DOI/原文链接）
- 影响因子字段暂为空（NULL），前端显示不受影响；补录后筛选自动生效
- 重置数据库：`python server/seed.py`（会清空订阅记录）
- 用 DB Browser for SQLite 或 `sqlite3 neurosearch.db` 可直接查看/编辑数据

## 部署

任意支持 Python 的虚拟主机/VPS 均可运行；`public/` 为纯静态文件，
也可将前端部署到静态托管、后端部署到云函数，跨域已放开（CORS: *）。
