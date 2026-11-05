# 换电脑 / 备份 / 恢复手册

> 看完这一页，你就知道哪些东西在 GitHub、哪些只在本机、换电脑怎么一步步搬过去。

## 一、先回答最关心的三个问题

**1）网站的全部内容都在 GitHub 吗？**

**代码和数据源在，运行时生成的东西不在。** 仓库里的 8 个文件就足以把整个网站原样重建：

| 文件 | 作用 |
|---|---|
| `server/seed.py` | **唯一数据源**：404 篇文献的全部字段（标题/作者/期刊/年份/类型/专题/中文摘要/关键词/DOI/链接） |
| `server/server.py` | 后端（零依赖，Python 标准库） |
| `public/index.html` | 检索页 |
| `public/info.html` | 项目信息页 |
| `DEPLOY.md` | 部署与维护手册 |
| `README.md`、`mobile_fix.py`、`.gitignore` | 说明与移动端补丁 |

**2）那本地还要不要保存？**

要，但**只需要保存 `server/seed.py` 这一个文件**就够救命（它就是全部文献数据）。
`server/neurosearch.db` 是程序根据 `seed.py` 生成的数据库，删了会自动重建，**不要拿它当备份**。

**3）换电脑怎么办？**

新电脑上装好 Python，从 GitHub 拉一份代码，运行 `python server/seed.py`，网站就回来了。完整步骤见第三节。

## 二、三处存储的分工

| 位置 | 存了什么 | 丢了会怎样 |
|---|---|---|
| **GitHub `Jas1me/wenxian`（公开）** | 源码 + 404 篇文献数据 + 维护脚本 `scripts/` + 历史报告 `docs/` | 有本机副本就能重建仓库；数据本身在 `seed.py` 里 |
| **本机 `C:\Users\User\Desktop\neurosearch`** | 工作副本、`neurosearch.db`、`seed.py.bak.*` 备份 | 可从 GitHub 完整恢复 |
| **WorkBuddy 工作区 `...\WorkBuddy\2026-10-30-16-02-06`** | 维护脚本、候选文献清单、核验报告、每日工作记忆 | 脚本与报告已同步到 GitHub 的 `scripts/` 与 `docs/`；候选文献原始 JSON（约 1.2 MB）仍只在本地 |
| **Render** | 线上运行的实例（不存数据，重启即按 `seed.py` 重建） | 重新部署即可，网址不变 |

## 三、换电脑：从零到网站跑起来（约 10 分钟）

### 最省事的方式：整包拷过去，双击启动（推荐换 Mac 用这个）

项目里所有文件都是纯文本（`.py` / `.html` / `.md`），**换设备后内容一字不变**，不存在"Windows 版文件 Mac 打不开"的问题——只有启动命令从 `python` 变成 `python3`。

1. 把 `NeuroSearch-完整备份-*.zip` 拷到新电脑桌面（AirDrop / U 盘 / 网盘都行）
2. 双击解压，得到桌面的 `neurosearch` 文件夹
3. 双击里面的 **`启动网站.command`**（Mac）/ **`启动网站.bat`**（Windows）
   - 它会自动找 Python、首次自动建库、启动服务并打开浏览器
   - Mac 第一次双击若提示"无法打开，因为来自身份不明的开发者"：右键→打开→再点"打开"；或在终端执行一次
     `xattr -dr com.apple.quarantine ~/Desktop/neurosearch` 和 `chmod +x ~/Desktop/neurosearch/启动网站.command`
4. 看到文献列表就是成功；关网站就关掉那个终端窗口

Mac 自带 Python 3（终端里 `python3 --version` 能看到版本），**一般不需要额外安装**；如果提示找不到 Python，去 https://www.python.org/downloads/macos/ 装一个即可。项目代码兼容 Python 3.8 及以上。

> 8000 端口若被占用（`Address already in use`），用 `PORT=8010 python3 server/server.py` 换端口启动。

### 或者：从 GitHub 重新拉一份（适合新电脑网络正常的情况）

#### 第 1 步：装 Python

到 https://www.python.org/downloads/ 装 3.10 以上版本（3.12/3.13 都行），安装时勾选 **Add Python to PATH**。
Mac 上安装包自带命令，装完终端里 `python3 --version` 能出版本即可。

### 第 2 步：拿到代码（两种任选）

```bash
# 方式 A：有 git
git clone https://github.com/Jas1me/wenxian.git neurosearch

# 方式 B：没 git —— 浏览器打开仓库页 → 绿色 Code 按钮 → Download ZIP → 解压并改名为 neurosearch
```

仓库地址：https://github.com/Jas1me/wenxian

### 第 3 步：重建数据库并本地跑起来

```bash
cd neurosearch
python  server/seed.py       # Windows
python3 server/seed.py       # macOS / Linux
# → 生成 server/neurosearch.db（404 条）

python  server/server.py     # Windows
python3 server/server.py     # macOS / Linux
# → 打开 http://localhost:8000
```

看到文献列表就是成功了。`seed.py` 会打印建库信息，条数应为 **404**。

### 第 4 步：部署到线上（网址永远不变）

线上服务已经在 Render 跑着，**换电脑不需要重建服务**，只要能提交代码 + 触发部署：

1. 改完 `server/seed.py` 后把文件更新到 GitHub：
   - 网页直接上传/编辑（仓库 → 文件 → 铅笔图标 → Commit），或
   - 命令行 `git add -A && git commit -m "..." && git push`（见第四节关于网络问题的说明）
2. 到 Render 控制台点 **Manual Deploy → Deploy latest commit**，约 45 秒完成
3. 打开 https://neurosearch-ljgj.onrender.com/api/stats 确认 `{"total": 404, ...}`

Render 控制台：https://dashboard.render.com/web/srv-dbi79noae00c73be5410

### 第 5 步：确认这三样东西在手（不进仓库，需自己保管）

| 凭据 | 用途 | 在哪找 |
|---|---|---|
| GitHub 细粒度令牌 | 用脚本/API 批量推文件（`scripts/push_file.py`、`git_bulk_push.py`） | GitHub → Settings → Developer settings → Personal access tokens；旧的 2027-01-28 到期，可随时新建 |
| Render API Key（`rnd_` 开头） | 用 API 触发部署 | Render → Account Settings → API Keys |
| Render 服务 ID | 部署接口的路径参数 | 当前 `srv-dbi79noae00c73be5410`（见 `DEPLOY.md` 第一节） |

> 这三样**故意不写进仓库**（仓库是公开的）。建议存到密码管理器里。

## 四、这台旧电脑上的两个已知限制

1. **git 通道经常超时**（`github.com` 直连不通，`api.github.com` 是通的）。
   所以此前一直用 GitHub Contents / Git Data API 推文件：
   ```bash
   set GITHUB_TOKEN=github_pat_xxx
   python scripts/push_file.py 本地文件 仓库内路径 "提交说明"     # 单文件
   python scripts/git_bulk_push.py "提交说明"                      # 多文件一次提交
   ```
2. **自动部署不生效**，推送后必须手动触发一次部署（控制台或 API），否则网站不变。

3. **维护脚本里的路径是写死的**（`C:\Users\User\Desktop\neurosearch`）。
   新电脑如果目录不同，打开 `scripts/*.py`，改文件顶部的 `PROJ` / `BASE` / `SEED` 常量即可，逻辑不用动。

新电脑如果是正常的网络环境，直接 `git push` 即可，不受这两条限制。

## 五、备份建议（3 分钟做完）

- **主要备份 = GitHub**：源码与 404 篇文献都在里面，已经是最好的异地备份。
- **本地兜底**：把 `server/seed.py` 复制一份到网盘/移动硬盘，改名带上日期，例如
  `seed-20261105-404篇.py`。这一个文件就是全部文献数据。
- **别备份**：`server/neurosearch.db`（会自动重建）、`seed.py.bak.*`（历史快照，占空间）、`__pycache__`。
- 想连维护脚本和历史报告一起留档：直接 `git clone` 整个仓库即可，`scripts/` 与 `docs/` 都在里面。

## 六、恢复后自检清单

- [ ] `python server/seed.py` 打印 404 条
- [ ] `http://localhost:8000/api/stats` 返回 `total: 404`、`sources: 158`
- [ ] 首页搜索 `JASPER` 有 16 条、`ESDM` 32 条
- [ ] 线上 `/api/articles/13` 的 `pmid` 为 `38380766`
- [ ] `public/info.html` 页脚显示「404 篇种子文献」「2026-11-05」

## 七、还是出问题？

- 服务状态与日志：Render 控制台 → Logs
- 回滚到上一次部署：Render 控制台 → Events → 选历史部署 → Rollback
- 代码层面的坑（批量改 `seed.py` 的字节偏移、插入逗号等）：见 `DEPLOY.md` 第五节
