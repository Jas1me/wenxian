# T³ — 孤独症医学文献检索系统（真实数据库版）

孤独症谱系障碍 **干预与康复** 文献库，覆盖 ABA/EIBI、ESDM、NDBI、JASPER、PACT、PRT、TEACCH、AAC、言语治疗、
家长介导干预、视频示范、音乐与数字疗法等方向。

- 线上：https://neurosearch-ljgj.onrender.com
- 数据量：**404 篇** PubMed 真实文献 / 158 个期刊 / 1985–2026
- 四个专题：干预与康复、言语与沟通、新兴技术干预、共病研究

```
neurosearch/
├── server/
│   ├── server.py        # 后端 API（Python 标准库，零依赖）
│   ├── seed.py          # ★ 唯一数据源：404 篇文献的全部字段
│   └── neurosearch.db   # SQLite（首次启动自动生成，不入库）
├── public/
│   ├── index.html       # 检索页
│   └── info.html        # 项目信息页（实时统计 + 运维入口）
├── scripts/             # 维护脚本（体检/补全/批量改 seed/检索候选/线上验收）
├── docs/                # 历次核验与修正报告
├── DEPLOY.md            # 部署与维护手册
├── RESTORE.md           # 换电脑 / 备份 / 数据恢复
├── 启动网站.command       # macOS 双击启动
├── 启动网站.bat           # Windows 双击启动
└── README.md
```

## 快速启动

要求：Python 3.8+（无需第三方库）

**最省事**：双击 `启动网站.command`（macOS）/ `启动网站.bat`（Windows）——自动找 Python、首次自动建库、起服务并打开浏览器。

命令行方式：

```bash
cd neurosearch
python  server/seed.py      # Windows  → 生成数据库（404 条）
python3 server/seed.py      # macOS
python  server/server.py    # Windows
python3 server/server.py    # macOS → 打开 http://localhost:8000
```

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

- 全部为 PubMed 真实文献，逐条含 PMID / DOI / 原文链接与中文摘要
- 标题不带句末英文句点；链接规则：有 PMID 用 PubMed，无 PMID 有 DOI 用 doi.org
- `pub_type` 已与 PubMed 出版物类型逐条比对校正
- 5 篇 1987–1994 年老文献本身无 DOI、10 篇期刊不被 PubMed 收录（无 PMID），均属正常
- 重置数据库：`python server/seed.py`（会清空订阅记录）

## 部署与迁移

- 部署、新增文献、常见故障：见 `DEPLOY.md`
- 换电脑、备份策略、恢复后自检：见 `RESTORE.md`

> 注意：推送代码后 Render **不会**自动部署（webhook 未生效），需手动触发一次，约 45 秒。
