# 发给 Codex：第一阶段（P0）—— 环境初始化 + 数据接入 + 质量基线

你是资深数据分析工程师和 Python 开发工程师。请在当前**单一项目根目录**开发 RetailScope。先阅读 `docs/PRD.md`、`docs/METRICS.md`、`docs/ACCEPTANCE.md`，它们是唯一的产品与指标口径基准。

**本阶段只完成 P0，不得抢先开发花哨页面或自动生成未经验证的经营洞察。**

按下面顺序真实执行：
1. 检查当前仓库和开发环境（OS、Python、Docker、可用磁盘、已有文件），不要覆盖用户代码；汇报检测结果。
2. 建立 `README.md`、`.gitignore`、`.env.example`、`requirements.txt`、`docker-compose.yml`、`app/`、`src/`、`sql/`、`tests/`、`data/raw/` 目录。
3. PostgreSQL 16 Docker Compose 服务，健康检查，环境变量，不要把真实密码提交 Git。
4. 实现 `python -m src.etl.run --source data/raw`：检测 9 个 CSV，打印缺失文件；读取 CSV 时尽可能按块处理，保留原数据；建 raw schema + 合理的数据类型转换/质量检查；给出实际导入行数与字段概况。
5. 首次质量基线报告：每表行数、关键字段缺失/重复、无效日期/金额、订单-客户关联率；保留真实结果到 `docs/quality_report.md`。
6. Pytest 基础测试：缺少文件时明确报错、CSV 标头检查、行数与唯一键检查、数据库连通性（缺数据库时清晰标记而非静默通过）。
7. README 提供 Windows PowerShell 的完整运行指令，并给出 Docker 未安装时的具体报错与处理提示。

**硬约束：**
- 数据只来自 https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce，许可 CC BY-NC-SA 4.0。若文件不在 `data/raw/`，请完成不依赖数据的框架和测试，并明确列出需要用户下载的文件，严禁伪造数据或声称已经成功入库。
- 不要在没有亲自运行命令的情况下声称测试通过；不能跑的测试必须写清原因。
- 只允许在本仓库内修改代码。不能引用本机其他项目目录或泄露绝对路径与密钥。
- 首次交付后必须暂停进入下一阶段，等待验收。

**最后按此结构汇报：** 修改文件清单｜实际执行的命令及输出摘要｜实际 CSV 检测结果｜数据库是否启动｜pytest 结果｜阻塞事项｜P0 验收逐项状态。
