# GitHub 正式发布前最终报告

检查日期：2026-11-13。工程根目录：`D:\Projects\RetailScope`。本阶段仅配置许可、整理文档与发布清单、执行本地验证；没有开发业务功能或授权公开发布。

## 1. MIT 配置与版权署名

根目录 [LICENSE](../LICENSE) 已加入标准 MIT 英文完整正文。年份 2026，版权行为 **`Copyright (c) 2026 [yan]`**，严格采用作者本次明确提供的格式，方括号是作者指定文本，不再是待确认占位符。没有使用 Git 配置姓名，也没有添加其他个人信息。

[README](../README.md) 与 [数据许可](DATA_LICENSE.md) 一致说明：MIT 仅适用于作者拥有权利的原创代码，不覆盖第三方库、引用组件、Olist 数据或受其他许可约束的内容。根目录 LICENSE 不代表整个仓库中的每项内容都采用 MIT。

条款来源：[OSI 标准 MIT](https://opensource.org/license/mit)。本轮未修改许可条款，只填写作者指定的年份与版权行。

## 2. 数据与第三方许可

- Olist / Kaggle 数据版本 2、九份 CSV；继续保留来源署名、修改说明、CC BY-NC-SA 4.0 的非商业与相同方式共享要求。数据不随仓库分发。
- 数据报告、聚合结果和截图仍按 [DATA_LICENSE.md](DATA_LICENSE.md) 处理；混合代码、文字和图表的具体可分离部分及衍生范围列为待审查项，没有笼统授予 MIT。
- [第三方许可清单](THIRD_PARTY_LICENSES.md) 记录两份 Python 锁文件去重后的 **60 个依赖**，以及前端锁文件中的 **207 个运行、开发、传递与平台可选包**。后者全部有声明许可，包含 MIT、Apache-2.0、MPL-2.0、ISC、BSD、0BSD、BlueOak 等。
- 已查看 Python 分发元数据和许可文件记录、前端锁定声明及主要库许可，搜索源码的版权与引用标记；为使用 shadcn/ui 模式的组件集中保留其上游完整 MIT 声明。没有将这些组件或 Lucide/Feather 图标的版权归给作者。
- Psycopg 为 LGPL-3.0-only，certifi 为 MPL-2.0；NumPy/SciPy 二进制分发含额外声明。源码仓库不打包这些依赖二进制、node_modules、镜像或构建产物，未来分发安装包时必须另行核对随附条款。
- Streamlit 已安装元数据声明 Apache-2.0，但其本机元数据清单未列许可文件；第三方清单给出上游许可入口。锁文件声明与元数据核查不等于完成所有内嵌第三方代码的法律审计。

尚需作者复核：混合衍生材料的具体适用范围，以及历史模板/未标记引用片段的完整来源链。当前未发现必须删除的具体侵权片段；也不据此保证全部无标记代码的原创性。数据许可要求以 [CC 官方条款](https://creativecommons.org/licenses/by-nc-sa/4.0/) 为准。

## 3. 最终拟公开文件

共 **435 个**，逐文件列表见 [公开清单](GITHUB_PUBLIC_FILES.md)：

| 类别 | 数量 | 处理方式 |
|---|---:|---|
| A 必须公开 | 145 | 源码、SQL、测试、启动配置、依赖锁文件、README、许可及发布索引 |
| B 重点展示 | 17 | 六页最新版与 RFM/Cohort/置信区间共 9 张截图、架构/指标/分析与求职材料 |
| C 历史资料 | 273 | 阶段验收、旧图、过程说明和历史验证/生成脚本，集中索引并保留原路径 |

采用逻辑归档，不移动或删除已有历史文件；这样保留测试与报告引用链。README 只精选最新版展示，不堆砌历史资料。历史生成脚本不是当前运行入口，不应拿来覆盖现在的 README/许可配置。

未发现大于 5 MiB 的候选文件。源数据、用户级导出、数据库卷/备份、虚拟环境、依赖目录、构建产物、缓存和日志均不在清单中。`.gitignore` 复核通过，本阶段无须修改。

## 4. Git 状态、引用与历史安全

- 当前分支名 `main`，但 `refs/heads/main` 尚未形成提交；正常提交 0、已跟踪 0、暂存 0、远端 0。
- 因尚无 main 提交，拟发布 main 的现有可达历史对象数为 **0**。没有把这一点当作整个本地对象库为空。
- 存在 **3 个 `refs/codex/`** 工具快照引用。本轮最终检查本地全部 **592 个对象：498 个 blob、94 个 tree**，包含 **104 个不可达对象**；reflog 为 0，`git fsck --full --no-reflogs --unreachable` 成功。数量较先前准备快照增加，工具在会话间更新了本地快照；本阶段没有主动重写这些引用。
- 未修改或删除工具引用、对象、历史，未执行 `git commit`、`git push`、`git remote add` 或建仓。将来只推送作者审核后的 main，不能使用 `--all`、`--mirror`、force push，也不能上传 `.git` 目录。

## 5. 敏感内容检查

读取全部 435 个实际候选文件字节（包括 PNG 等二进制）及所有 498 个 Git blob，并检查树路径。扫描对照本机已知真实凭证与常见密钥、私钥、带凭证 PostgreSQL URI 模式，同时审查候选文件与数据/环境路径。

未发现真实本机凭证匹配、未解释的秘密模式或应排除的数据/环境文件。9 处 URI 为 `.env.example` 或测试夹具占位示例（含历史对象），已分类；没有在报告中输出任何实际凭证值。10 项 `git check-ignore` 检查通过，但结论同时依据实际文件、内容与对象检查，而非仅依据忽略规则。

新增 LICENSE、README、许可清单和整理后的文件索引已纳入扫描。自动扫描仅覆盖已知凭证与所列模式，不是绝对安全保证；本轮未遇到无法解释的潜在敏感命中。发布前如新增文件或产生提交，应重新扫描提交后的 main 可达对象。

## 6. README 整理

顺序已调整为名称与用途、真实经营总览截图、技术栈与成果、六模块、架构、分析方法、安装运行、测试、数据与代码许可。保留真实业务口径和观察性分析局限，没有虚构生产使用或增长效果。

克隆示例使用明确占位地址 `https://github.com/YOUR_USERNAME/retailscope.git` 与相对目录 `cd retailscope`；仓库尚未创建，没有编造实际地址。所有本地链接及九张精选 PNG 可解析，Markdown 表格、代码围栏及 Mermaid 源码已检查；未将此描述为已在 GitHub 在线渲染验收。

先前发布检查单保留原快照，并新增指向本报告的说明，避免其“许可待决定”和 430 个文件的旧记录被误认为当前状态。

## 7. 实际执行与回归结果

环境仍为本机 Windows 11、Python 3.12.10、Node.js 24.15.0 / npm 11.12.1、PostgreSQL 16.16。

| 检查 | 本轮结果 | 本地证据（不公开提交） |
|---|---|---|
| 完整 Pytest | **144 通过，0 失败/错误/跳过，98.52 秒** | `reports/github-final/pytest.log`、`pytest.xml` |
| 完整 Vitest | **28 通过，7 个文件，1.28 秒** | `reports/github-final/frontend_tests.log` |
| TypeScript | 退出码 0 | `reports/github-final/typecheck_result.json` |
| Vite 生产构建 | 成功，723 ms | `reports/github-final/build.log` |
| 正常启动 | `start.ps1 -Action start -NoServe` 成功；9 张表及 7 项发现就绪 | `reports/github-final/start_check.log` |
| API/前端就绪 | `start-v2.ps1 -Action check` 成功，96,478 单 | `reports/github-final/v2_check.log` |
| 真实浏览器 | 六个直接 URL 全部 HTTP 200、数据加载成功；总览 BRL 13,221,498.11 | `reports/github-final/browser.log` 与六页 PNG |
| 不变性对账 | 92 个受保护文件、5 组 API 响应、Raw/Mart 指纹、13 项原始成果和既有诊断结果一致 | `reports/github-final/verification.json` |
| 公开安全 | 候选文件、所有 Git blob 与路径检查通过 | `reports/github-final/public_safety.json`、`public_files.json` |
| 发布预演 | `git add --dry-run -- .` 列出 435 个文件，暂存区前后均为空 | `reports/github-final/git_add_dry_run.txt`、`preparation.json` |

本轮未更改 UI、SQL、API 指标、统计模型、原始数据、依赖版本或启动业务逻辑。RFM、Cohort 与七项诊断由既有完整测试和快照/真实查询继续核对。

本轮复用已有本机环境，未在全新 Windows、全新数据库或无缓存下载环境执行首次安装。浏览器范围是六页直接访问与真实加载，不冒充重新完成整套筛选、导出、空状态及错误交互验收；之前的交互证据仍保留。

## 8. 本地预演问题与待确认项

1. 版权署名已由作者明确确认并填写，已无姓名占位阻塞。
2. 技术预演未发现功能回归、失效 README 本地引用、异常大文件或敏感命中。实际暂存区没有改变；没有生成提交。
3. 混合衍生材料许可边界、历史未标记片段来源链仍需作者审查；将来分发构建包/镜像时需另做依赖随附声明检查。不能将本次元数据核查等同于无条件法律许可保证。
4. 首次跨机器安装未重验，正式演示前建议作者在另一台符合要求的电脑按 README 运行。
5. 公开仓库地址与最终名称（推荐 `retailscope`）待作者创建时确认；本阶段没有创建或探测账户身份。

结论：**已满足当前本地技术发布预演条件，无已确认技术阻塞；保留上述许可审查项，尚未取得公开发布授权。** 作者完成内容审查并明确批准后，才能进入实际提交与发布。

## 9. 作者批准后的完整发布步骤（未执行）

1. 审阅本报告与文件清单，确认混合数据材料和第三方来源处理可接受；如需调整公开范围，先更新引用并重新验证。
2. 复跑安全检查并审阅输出：

```powershell
.\.venv\Scripts\python.exe scripts/audit_github_release.py
git status --short
git remote -v
git for-each-ref --format="%(refname)"
```

3. 作者在 GitHub 创建空仓库，推荐名 `retailscope`。按批准选择可见性，不让 GitHub 自动生成另一份 README 或许可证。
4. 作者在本地暂存并逐项审阅（确认无秘密与用户级数据）：

```powershell
git add --dry-run -- .
git add .
git diff --cached --name-only
git diff --cached --stat
git diff --cached --check
```

5. 内容审核通过且作者明确批准提交后，再执行：

```powershell
git commit -m "Publish RetailScope analytics portfolio"
.\.venv\Scripts\python.exe scripts/audit_github_release.py
git rev-list --objects main
git remote add origin https://github.com/YOUR_USERNAME/retailscope.git
git push -u origin main
```

提交后安全扫描会覆盖新增提交可达的 blob；若出现任何不明命中，停止设置远端与推送。替换远端 URL 前应核对作者实际账户和新建仓库；不要将示例 URL 原样执行。只推送 `main`，不推工具引用，不强推。README 克隆占位地址可在确定真实仓库 URL 后由作者更新并再审核。

6. 在 GitHub 实际检查 LICENSE、README、六模块截图、Mermaid、数据署名和文件列表，确认没有原始 CSV、凭证、用户级记录或 `.git` 目录。设置简洁 About 与项目主题，不必部署公网。

## 10. 本阶段文件修改范围

- 新增：根目录 `LICENSE`；`docs/THIRD_PARTY_LICENSES.md`；本报告。
- 更新：`README.md`、`docs/DATA_LICENSE.md`、`docs/GITHUB_PUBLIC_FILES.md`；先前 `docs/GITHUB_RELEASE_CHECKLIST.md` 仅加最新状态入口。
- 新增发布检查脚本：`scripts/prepare_final_release.py`、`scripts/github_final_pages.js`；更新 `scripts/verify_github_release.py` 以读取本轮测试/浏览器证据并核对许可及新链接。
- 本地忽略证据：`reports/github-final/`。没有删除文件、移动目录、重写历史或修改任何业务源码。最终逐文件字节与摘要以同目录 `public_files.json` 为准。
