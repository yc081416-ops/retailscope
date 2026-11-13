# RetailScope GitHub 发布准备清单

> 先前准备快照：本文中的 430 个文件及“许可证待决定”记录保留当时状态。作者随后已选择 MIT 并确认版权署名；最新文件分类、许可范围和检查结果见 [最终发布报告](GITHUB_FINAL_RELEASE_REPORT.md)。

检查日期：2026-11-13。当前仅完成本地发布准备，尚未公开发布。

## 仓库状态

- 工程：`D:\Projects\RetailScope`；当前分支 `main`。
- 正常提交 0、已跟踪文件 0、暂存文件 0、远端 0；项目文件仍是候选文件。
- 存在 3 个 `refs/codex/` 工具快照引用，不能将“没有正常提交”当作没有历史对象。
- 实际检查 574 个对象：485 个 blob、89 个 tree；包含 97 个不可达对象，reflog 记录为 0。`git fsck` 成功。
- 本轮未执行暂存、提交、远端设置、推送、公开建仓或部署，也没有删除或移动旧文件。

推荐仓库名：**retailscope**，备选 `retailscope-analytics`。名称可用性由作者创建时确认。

## 公开内容与展示

[逐文件公开候选清单](GITHUB_PUBLIC_FILES.md) 覆盖实际 `git ls-files --cached --others --exclude-standard` 的 430 个文件；它是审阅清单，不代表已经提交。

保留 React 前端、FastAPI、Python 分析与旧版 Streamlit 源码、SQL、测试、锁文件、Docker Compose、启动脚本、配置模板和项目文档。历史验收报告及截图保留原位置，避免破坏引用。当前精选展示位于 `docs/screenshots/showcase/`：六页实拍及 RFM、Cohort、统计置信区间，共 9 张 PNG。

[README](../README.md) 已以新版工作台为主，首屏包含名称、用途、技术栈、真实规模与经营总览；正文包含六模块、Raw/Core/Mart、分析方法、实际截图、Windows 初始化与日常启动、测试和数据许可。历史启动说明新增了当前入口提示。

## 公开安全检查

- 除检查忽略规则外，读取所有实际候选文件内容、全部 485 个 Git blob（含二进制、工具快照、不可达对象）及树路径。
- 对照本机真实密码与连接地址进行匹配，并检查常见令牌、私钥、带凭证 PostgreSQL URL、源数据和环境文件路径；结果未发现实际秘密或禁止公开的数据文件。
- 9 处连接 URI 属于 `.env.example` 占位符或自动化测试夹具（含历史对象），已明确分类，并非实际凭证。
- `.env`、原始 CSV、用户级导出、数据库备份、虚拟环境、node_modules、构建产物、日志和浏览器本地状态不在公开候选中；10 项实际 `git check-ignore` 检查通过。`.gitignore` 已复核，本轮未改动。
- 此检查覆盖已知真实凭证、常见凭证模式和上述数据路径，不构成对任意未知秘密的绝对保证。后续新增文件、许可证或提交前应再次审阅。

本地详细证据（已被忽略，不随仓库公开）：`reports/github-release/public_safety.json`、`public_files.json`（逐文件大小与 SHA256）、`public_safety.log`。

## 运行与测试结果

环境：Windows 11、Python 3.12.10、Node.js 24.15.0、npm 11.12.1、Docker Engine 29.9.3、Compose 5.7、PostgreSQL 16.16。

| 检查 | 本轮实际结果 | 本地日志 |
|---|---|---|
| 完整 Pytest | 144 通过，0 失败/错误/跳过，99.13 秒 | `reports/github-release/pytest.log`、`pytest.xml` |
| 完整 Vitest | 28 通过，7 个测试文件，1.32 秒 | `reports/github-release/frontend_tests.log` |
| TypeScript | 退出码 0 | `reports/github-release/typecheck_result.json` |
| Vite 生产构建 | 成功；无大于 500KB 的块警告 | `reports/github-release/build.log` |
| 日常数据库与快照启动 | `start.ps1 -Action start -NoServe` 成功；9 张 raw 表、7 项发现就绪 | `reports/github-release/start_check.log` |
| API 与前端检查 | `start-v2.ps1 -Action check` 成功，实际 SQL 96,478 单 | `reports/github-release/v2_check.log` |
| 生产预览浏览器 | 6 个直接 URL 真实加载，采集 9 张截图并查看图片 | `reports/github-release/showcase.log` |
| 数据与源码保护 | 92 个受保护文件、5 组 API 结果、Raw/Mart 指纹、13 项原始成果及既有统计结果全部一致 | `reports/github-release/verification.json` |

README 与本检查单的 25 个本地链接已验证，9 张新截图的 PNG 格式与尺寸检查通过；六页缩略总览及 RFM、Cohort、置信区间图片已实际查看。两个 PowerShell 启动脚本语法解析均为 0 错误，记录于 `reports/github-release/powershell_parse.json`。

本轮浏览器验证范围为六页面直接访问、数据加载与展示截图，不冒充重新执行整套筛选/导出/错误状态验收。完整交互记录仍保留于历史 UI 验收材料。

本轮复用已初始化的本机环境，实际执行日常启动、真实查询、测试与构建。首次 `init` / `install` 命令及文件路径已审查；未重新执行干净 Windows、全新数据库或无缓存网络安装，亦未用 `npm ci` 清除现有依赖。跨机器首次安装仍需作者按 README 实机确认。没有重建数据库或覆盖既有分析成果。

## 许可证待作者决定

- 数据来源：Olist / Kaggle，数据版本 2，CC BY-NC-SA 4.0；署名与衍生材料说明见 [数据许可](DATA_LICENSE.md)。
- 原创代码许可证尚未指定，未擅自创建 `LICENSE` 或选用 MIT 等许可。公开可见不等于授权他人任意再使用代码，正式发布前请作者决定是否及如何授权。
- 原始数据通过官方下载脚本准备，不随 GitHub 分发。公开范围为源码、聚合分析材料与不含用户级记录的截图。

## 作者手动发布步骤（尚未执行）

1. 确认原创代码许可，按决定补充相应文件，并复核 README 中的许可说明。
2. 审阅公开清单，在项目根目录执行 `.\.venv\Scripts\python.exe scripts/audit_github_release.py` 重新检查；查看暂存前后文件，确认没有本地数据与凭证。
3. 作者在 GitHub 创建空仓库，选择名称与可见性；不要自动添加另一份 README 或许可证。
4. 作者确认发布后，可手动执行以下命令。远端地址替换为自己的账户；提交前如发现异常，先停止处理。

```powershell
git status --short
git add .
git diff --cached --name-only
git diff --cached --check
git commit -m "Publish RetailScope analytics portfolio"
git remote add origin https://github.com/YOUR_USERNAME/retailscope.git
git push -u origin main
```

只推送 `main`；不要使用 `--mirror`、`--all`，不要上传 `.git` 目录或打包整个本地工程。完成后检查 GitHub README、图片和下载文件，再补充 About 中的项目描述与主题标签。以上发布操作全部留待作者执行。

## 本轮修改范围

- 更新：`README.md`、`START_HERE_USER.md`（仅入口说明）。
- 新增：本检查单、公开候选文件清单。
- 新增：`scripts/audit_github_release.py`、`scripts/verify_github_release.py`、`scripts/github_showcase.js`、`scripts/write_release_readme.py`，均用于本轮审查或展示准备。
- 新增：`docs/screenshots/showcase/` 下 9 张实际 PNG；本轮本地日志及结构化验证文件置于忽略的 `reports/github-release/`。
- 未修改：业务源码、SQL、API 指标、原始数据、RFM/Cohort/P3 模型、测试、依赖锁文件、密码、启动脚本及已验收报告。

准备完成后停止开发。发布仍待原创代码许可决定及作者明确授权。
