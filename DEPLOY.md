# NeuroSearch 部署与维护手册

> 这份文件跟着项目走，换电脑、换会话都能照着做，不依赖任何人的记忆。

## 一、当前部署状态

| 项目 | 值 |
|---|---|
| 公开访问地址 | https://neurosearch-ljgj.onrender.com |
| Render 服务 ID | `srv-dbi79noae00c73be5410` |
| Render 控制台 | https://dashboard.render.com/web/srv-dbi79noae00c73be5410 |
| 源码仓库 | https://github.com/Jas1me/wenxian （当前为**公开**） |
| 运行环境 | Python 3 · 新加坡节点 · 免费档 · main 分支 |
| 构建命令 | `echo done` |
| 启动命令 | `python server/server.py` |
| 自动部署 | 已开启，但**实测不生效**（见第三节），需手动或 API 触发 |
| 部署耗时 | 约 40 秒 |

线上数据：144 篇文献 / 71 个期刊 / 覆盖 1985–2026 年。

## 二、日常更新：不要删文件，改完提交就行

**核心原则：改文件 → 提交到 GitHub → 触发一次重新部署，网址永远不变。**
不需要删除任何东西，也不需要重新创建服务。

### 方式 A：在 GitHub 网页上直接改（最简单）

1. 打开 https://github.com/Jas1me/wenxian
2. 点进要改的文件 → 右上角铅笔图标 Edit
3. 改完拉到页面底部 → Commit changes
4. 按第三节的方式触发一次部署（约 40 秒），刷新网站就能看到

### 方式 B：改完让 WorkBuddy 帮你部署

把改好的文件（或"我改完了"）告诉 WorkBuddy，它会用 Render API 直接触发部署，
约 40 秒完成。这是最省事的方式。

### 方式 C：本地改完提交

本地目录：`C:\Users\User\Desktop\neurosearch`

```bash
cd C:/Users/User/Desktop/neurosearch
git add -A
git commit -m "说明改了什么"
git push origin main
```

> 已知问题：这台机器到 `github.com` 的 git 通道会超时（`api.github.com` 是通的）。
> 如果 `git push` 卡住，改用 SSH 通道 `ssh.github.com:443`，或让 WorkBuddy
> 用 GitHub Contents API 代传（脚本见工作区 `upload_github.py`）。

### 方式 D：拿到一份整体重写的新文件（不在原文件上改）

经常遇到的情况：不是在原文件里改几行，而是拿到一份**全新写好**的 `seed.py`。

**处理方式：直接覆盖同名文件，不用先删旧的。**
Windows 复制粘贴时选"替换目标中的文件"即可。

| 文件 | 必须放在这个位置，文件名不能改 |
|---|---|
| 文献数据 | `C:\Users\User\Desktop\neurosearch\server\seed.py` |
| 后端 | `C:\Users\User\Desktop\neurosearch\server\server.py` |
| 前端 | `C:\Users\User\Desktop\neurosearch\public\index.html` |

**为什么文件名不能改**：`server.py` 第 16 行写死了 `import seed`，
第 12 行硬编码了 `../public`。文件改名或挪位置，启动就会
`ModuleNotFoundError`，部署直接失败。

新文件放在别的地方（桌面、下载目录）也完全没关系——把路径告诉 WorkBuddy，
它会帮你复制覆盖、校验、推送、部署，一步到位。

**新的 `seed.py` 必须包含这三个东西**，否则后端起不来：

| 必须存在 | 作用 | 当前所在行 |
|---|---|---|
| `SEED_ARTICLES` | 文献列表 | 第 39 行 |
| `COLLECTION_META` | 六个专题的定义 | 第 1028 行 |
| `init_db(force=False)` | 建库函数 | 第 1043 行 |

覆盖后想本地预览，注意顺序（第一条不能省）：

```bash
python server/seed.py      # 强制重建数据库，新文献才会出现
python server/server.py    # 打开 http://localhost:8000
```

## 三、⚠️ 自动部署实测不生效，改完代码要手动触发

**2026-10-30 实测**：往 main 分支推送新提交后，Render **没有**自动重新部署
（仓库已到 `1cd661ca`，服务仍停在旧提交 `271a15de`）。
原因：Render 这次是通过 OAuth 连接的 GitHub，没有安装 webhook，
所以收不到 push 事件。`autoDeployTrigger` 显示 `commit` 但实际不触发。

触发部署有三种方式，选一个即可：

| 方式 | 怎么做 | 适合 |
|---|---|---|
| 让 WorkBuddy 触发 | 说一声"部署一下"，它调 API 完成 | 日常最省事 |
| 控制台手动 | Render 控制台 → 右上角 **Manual Deploy** → **Deploy latest commit** | 不想找我时 |
| 配 Deploy Hook（一劳永逸） | 见下方步骤 | 想彻底自动化 |

**配置 Deploy Hook（配一次，以后推送即自动部署）：**

1. Render 控制台 → 服务 → **Settings** → 找到 **Deploy Hook** → 复制那个 URL
   （形如 `https://api.render.com/deploy/srv-xxx?key=yyy`）
2. GitHub 仓库 → **Settings** → **Webhooks** → **Add webhook**
3. Payload URL 粘贴刚复制的地址；Content type 选 `application/json`
4. 触发事件选 **Just the push event** → **Add webhook**

配好后，以后每次推送代码都会自动触发部署，不用再管。

> 补充：GitHub 那边的 webhook 需要仓库管理员权限才能添加。
> 当前的细粒度令牌只有 Contents 和 Metadata 权限，加不了，
> 所以这一步要在网页上手动做。

## 四、新增文献：必须改 seed.py

**关键机制**：数据库文件 `server/neurosearch.db` 不在版本控制里，
每次部署都是全新实例，`server.py` 启动时会检查——数据库不存在就调用
`seed.init_db()` 从 `seed.py` 重新生成。

所以：

- ✅ **正确做法**：在 `server/seed.py` 的 `SEED_ARTICLES` 列表里加一条
  （第 39 行开始，格式照抄现有的 `dict(...)`），提交后重新部署，新文献就会出现。
- ❌ **会丢失的做法**：通过网页表单或 `POST /api/articles` 接口添加的文献。
  免费档磁盘是临时的，服务一重启就重置，这些记录会消失。

新增一条的模板：

```python
dict(pmid=None,
     title="文献标题（英文原文）",
     authors="Smith J, et al",
     journal="期刊名",
     year=2025,
     pub_type="临床试验",          # 或从：队列研究/系统评价/综述/Meta分析/病例报告/基础研究
     collection="干预与康复",      # 或从：儿童早期筛查/基因检测与诊断/言语与沟通/新兴技术干预/共病研究
     abstract="中文摘要……",
     keywords="关键词; 关键词",
     doi="10.xxxx/xxxx",
     url="https://pubmed.ncbi.nlm.nih.gov/……"),
```

## 五、链接有效期

**网址没有 90 天限制，也不会过期**——只要服务在，链接就一直在。

真正有 90 天期限的是 **GitHub 个人访问令牌**（2027-01-28 到期）。它只影响
"用 API 代你传文件"这个能力，已上线的服务不受任何影响。到期后重新生成一个
给我即可。Render 的 API Key 不会自动过期。

## 六、免费档的三个特性（不是故障）

1. **冷启动**：15 分钟无人访问会休眠，下次打开要等 30–50 秒，之后恢复速度。
   想去掉就升级到 $7/月的 Starter 档。
2. **数据不持久**：服务重启后 SQLite 重置。种子文献会自动重建，
   但通过订阅框提交的邮箱会丢失。需要长期保存的话要另存到外部服务。
3. **仓库必须公开**：Render 用的是 OAuth 连接，读不了私有仓库。
   如果改成私有，以后推送代码就不会再自动部署了（已运行的服务照常）。

## 七、出问题怎么查

- 服务状态、实时日志：Render 控制台 → 左侧 **Logs**
- 手动重新部署：控制台右上角 **Manual Deploy** → **Deploy latest commit**
- 想回滚：控制台 **Events** 里找到历史部署点 → Rollback
