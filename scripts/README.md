# 脚本使用说明

## 安装、运行与数据复现

日常操作从根目录 [README](../README.md) 的 `start.ps1`、`start-v2.ps1` 开始。数据流水线与模型源码位于 `src/retailscope/`、`sql/`，以下脚本继续保留：

| 脚本 | 用途 |
|---|---|
| `build_warehouse.py` | 构建派生数据仓库 |
| `run_p3.py` | 读取仓库，生成统计诊断与报告 |
| `run_p0.ps1`、`run_p1.py` | 早期数据接入与分阶段复现；运行前先准备相应数据与历史基线 |
| `reproduce_p4.py`、`serve_repro.py`、`test_repro_p4.py` | 本机隔离数据库与服务的复现检查 |
| `audit_github_release.py` | 检查实际 Git 候选文件、Git 对象和忽略规则 |

`run_p1.py` 会读取 `docs/P0_ACCEPTANCE_REPORT.md` 与 `docs/quality_report.md` 核对原始阶段的文件摘要，因此这两个基线文档仍随源码保留。当前首装与日常运行不需要执行历史阶段脚本。

## 历史生成与验证工具

`write_*`、`verify_v*`、`verify_ui_*`、各阶段浏览器检查脚本及发布预演脚本记录过去的开发流程。它们可能读取本地 `reports/`、阶段报告和旧截图，也可能重新生成这些材料；不是克隆后的安装、启动或自动化测试入口。

这些历史档案保留在作者本机并由 `.gitignore` 排除。需要重跑某一次历史验证时，必须准备该次对应的本地证据与截图；缺少档案不代表已通过该次验证。不要运行历史文档生成器覆盖当前 README 或许可文件。

常规回归使用根 README 中的 Pytest、Vitest、TypeScript 与 Vite 命令，数据准备按正常初始化流程完成。
