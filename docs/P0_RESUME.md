# P0 复跑说明

当前工程、真实 CSV、虚拟环境、源数据哈希和执行日志均已保存在原目录；不需要再次下载数据或重新创建工程。

已安装 Python 3.12.10、WSL 3.0.5 和 Docker Desktop。用户重启后，待重启状态已清除，Docker Engine 正常；PostgreSQL 16.16 已启动，真实导入与两次对账通过，Pytest 18 通过、无失败或跳过。P0 已停止开发，等待验收。最终证据见 `docs/P0_ACCEPTANCE_REPORT.md`。

需要复跑 P0 时，打开 Docker Desktop，等待引擎启动，在工程根目录 PowerShell 执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_p0.ps1
```

该命令复核现有 CSV、检查 Docker、生成本地随机密码 `.env`（仅缺失时生成，不打印），启动 Compose PostgreSQL 16、初始化 raw、实际导入两次并核对九表行数和内容指纹、对比 CSV/SQL 关联检查，最后运行 Pytest 并更新报告。它会替换本项目九张 raw 表的数据，保留源文件；不会清空 Docker 卷或操作其他工程。

若仍失败，保留报错并继续排查，不能把报告状态改为通过。不要把 `.env`、Kaggle 凭证或数据库密码发到聊天。

官方安装依据：[微软 WSL 文档](https://learn.microsoft.com/en-us/windows/wsl/install)、[Docker Windows 安装文档](https://docs.docker.com/desktop/setup/install/windows-install/)。
