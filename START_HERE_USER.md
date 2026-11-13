> 历史阶段说明：本文保留最初的数据接入任务。当前 React + FastAPI 系统的安装与启动，请以 [README](README.md) 为准。

# RetailScope｜用户唯一启动指南（2026-11-13 修订）

## 我需要做的事（最简 3 步）

1. 将本压缩包解压到自己的电脑，例如 `D:\Projects\RetailScope`；用 VS Code 或 Codex 打开**解压后的 RetailScope 文件夹**，不要只打开单独的 .py 文件或 ZIP。此前若已经有同名项目，请先备份，避免覆盖你的更改。
2. 将 `prompts/START_P0.md` **整篇复制到 Codex**；告诉它“根据指令直接在当前工程内执行”。
3. Codex 若需要 Docker Desktop、Python 3.12 或 Kaggle 认证时，再按其明确提示操作；不要把账号密码/API key 发到聊天或上传 GitHub。完成后把它生成的 P0 验收报告和实际命令输出发给 ChatGPT 验收。

## 硬性要求

- 当前只做项目一 RetailScope，不做项目二；本轮只做 P0，不做 UI、RFM 或业务诊断。
- **Olist 九份 CSV 优先交由 Codex 自动下载**：Kaggle 数据集 `olistbr/brazilian-ecommerce`；采用 kagglehub；保持真实原始文件，不能生成模拟订单代替。
- 若 Kaggle 下载因网络或认证被阻断，可尝试正规官方下载方式；仍失败，报告原因让用户处理，禁止跳过真实数据入库并宣称成功。
- Python 3.12、PostgreSQL 16（Docker Compose）、真实 CSV 审计、原始数据入库、数据库行数对账、重跑幂等、Pytest 测试、质量报告都是 P0 验收项。
- 对已有源码先检查、再修复；不重建或删除用户已有项目内容；绝不提交原始 CSV、`.env`、凭证。

## 后续全程路线

P0 数据下载+数据检查+入库 → P1 SQL/指标与统计分析 → P2 六页面经营看板 → P3 业务诊断报告 → P4 测试/演示/简历素材。

每一阶段 Codex 先出实际运行证据，ChatGPT 验收后再进入下一阶段。
