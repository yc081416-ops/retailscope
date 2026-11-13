# 直接发送给 Codex｜RetailScope 项目一 P0 统一指令（2026-11-13）

你现在担任 RetailScope 电商经营分析与用户增长决策平台的主开发工程师。我使用 Windows，本地工程已经解压并作为当前工作区打开。此项目用于应统研二求职，必须真实、可复现、可展示。**只做项目一，当前只做 P0**，不能自行开发后续功能。

## 首先阅读

`README.md`、`START_HERE_USER.md`、`docs/PRD.md`、`docs/METRICS.md`、`docs/ACCEPTANCE.md`、`docs/ROADMAP.md`、`sql/00_raw.sql` 以及 `src/retailscope/` 下的全部代码。当前工程已经有初始代码，先修复，不要重新创建另一个项目。

## 本轮必须实际执行的任务

1. 检查操作系统、Python 3.12、Docker Desktop / Docker Compose、当前工程目录与依赖安装条件；必要时安装项目 Python 依赖。无法自动安装的系统软件，清楚告诉我怎么操作，等环境就绪继续。
2. **你负责自动下载真实 Olist 数据**：优先 `kagglehub.dataset_download("olistbr/brazilian-ecommerce")`；必要时安装 kagglehub；实现可重复运行的下载脚本。将数据集完整的 9 个 CSV 放到项目 `data/raw/`，数据已齐全就跳过下载，不要每次重复拉取。不可使用随机/合成/示例订单冒充真实 Olist 数据。自动下载失败时先检查网络、包依赖、缓存路径和认证错误；若需要本人登录 Kaggle，只提出最小操作要求，不要索要明文密码或令牌。不得绕过登录、声称下载成功或擅自更换数据源。
3. 基于源码中的 `contracts.py` 检查 9 个 CSV 的文件名、表头、真实记录数、字段类型和关键字段缺失；输出质量检查 JSON/Markdown。
4. 使用已有 Docker Compose 启动 PostgreSQL 16，初始化 raw 层九张表（保留原始字段，不随意修订数据）。数据库如连接失败，检查端口、容器、凭证与日志，修复配置但不能泄露秘密。
5. 把 9 张真实 CSV 导入数据库；严格核对每表 CSV 行数与数据库行数；重复运行相同导入命令，确认行数不增加；必要时修复数据导入逻辑。
6. 运行 `python -m pytest -q`；测试失败先修复再报告，不要以“理论上能运行”替代实际运行。请检查 Olist 的特殊点：`customer_unique_id` 才是跨订单用户，reviews.review_id 可能重复，geolocation_zip_prefix 非唯一，订单商品/支付需要组合键，原始列名 `lenght` 是数据集错拼且应保留。
7. 生成 `docs/P0_ACCEPTANCE_REPORT.md`，必须包含：环境版本、实际执行命令、9 个文件及表的行数对账、数据质量统计、Docker/数据库状态、幂等验证、测试通过/失败数、改动文件清单、风险/未完成事项。不得把网上示例数字作为实际执行结果。

## 限制与交付

- 保持单一工程根目录，禁止自行引入 React、AI 模型、复杂微服务。
- 本轮不要制作页面、经营看板、RFM、同期群或项目二。
- 不要把 `data/raw/*.csv`、`.env`、密码、API Key 上传 GitHub；保留原始数据许可声明。
- **P0 完成即停止**，等待验收通过再开始 P1。
- 若卡在网络、Kaggle 授权或本机 Docker，请明确报告已完成部分和下一步用户只需要做的一件事，不要把阶段当作通过。
