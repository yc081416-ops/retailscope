"""Build README and resume facts using the latest completed P4 test evidence."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]


def main():
    suite=ET.parse(ROOT/'reports/p4/pytest.xml').getroot().find('testsuite')
    assert all(int(suite.get(k,0))==0 for k in ('failures','errors','skipped'))
    tests=int(suite.get('tests'))
    readme=f'''# RetailScope｜电商经营分析与用户增长决策平台

基于Olist真实历史订单，以PostgreSQL数据仓库、交互式BI和可复核统计诊断，回答“卖得怎样、谁在购买、如何履约、哪些现象值得继续验证”。

个人非商业求职作品；不是企业实习经历或已上线商用系统。P0–P3已验收，P4已完成本地交付验证，等待最终验收。

## 实际成果

- 九份真实CSV共 **1,550,922行**，订单主表 **99,441行**；默认delivered有效订单 **96,478单**、唯一购买用户 **93,358人**。
- 商品成交额 **BRL 13,221,498.11**，运费与支付金额分开统计；这不是利润或财务确认收入。
- 六个页面、RFM六个非空规则分层、Cohort留存、七条代码生成的统计发现及报告下载。
- **{tests}项Pytest通过，0失败、0跳过**；含独立CSV/Pandas、统计区间、UI与启动边界检查。
- 同一Windows主机上，干净虚拟环境及新空数据库完成全流程复现、重复初始化和版本化更新。未将其宣称为全新操作系统或公网部署验收。

## 业务问题与功能

| 页面 | 解决的问题与交互 |
|---|---|
| 经营总览 | 商品金额、订单、唯一用户、客单价、月度与地区；日期/州筛选，CSV导出 |
| 用户价值分析 | RFM人数/金额贡献、频次、整体复购、Cohort与新增用户；固定P1全样本 |
| 商品与品类分析 | TOP类目、贡献与帕累托、月度结构、件数/订单；日期/州/类目筛选 |
| 履约与评价分析 | 配送分母、逾期率、评价、州表现与描述性关联 |
| 经营发现 | 完整月增长、MAD、HHI、地区/用户结构、用户整群Bootstrap区间；Markdown报告 |
| 数据质量中心 | 当前九表行数与mart异常、明确标注的历史审计快照、构建及独立复核 |

## 架构与技术栈

```mermaid
flowchart LR
    A[Olist 官方9 CSV] --> B[审计与SHA-256]
    B --> C[(PostgreSQL raw)]
    C --> D[core 类型视图]
    D --> E[mart 维表与事实]
    E --> F[SQL指标 / RFM / Cohort]
    F --> G[统计诊断 / 用户整群Bootstrap]
    F --> H[SQLAlchemy只读查询]
    G --> H
    H --> I[Streamlit / Plotly]
    I --> J[CSV / Markdown导出]
    E --> K[独立Pandas / Pytest / 浏览器验证]
```

Python 3.12、PostgreSQL 16、Pandas、SQLAlchemy/psycopg、Streamlit、Plotly、SciPy/NumPy、Pytest、Docker Compose。运行不需要付费服务。实际验证依赖锁定在[requirements-lock.txt](requirements-lock.txt)，完整架构见[ARCHITECTURE.md](docs/ARCHITECTURE.md)。

## 数据仓库与核心口径

- raw保留原始文本、缺失与重复；core进行可审查类型转换；mart订单事实一订单一行、商品事实主键为(order_id,item_id)。
- 商品、支付、评价分别预聚合后再关联，禁止多对多JOIN后汇总金额；邮编先规范为唯一粒度。
- 核心经营指标默认delivered且购买时间有效，以购买时间归月；金额NUMERIC(18,2)，独立Pandas按整数分复核。
- 用户按customer_unique_id跨单去重。无支付不删除商品金额，无商品保留订单并标记，缺配送日期不进入配送分母。
- RFM基准日2018-08-30，离散五分位同值同分；F大量为1，评分档不均衡是数据特征。
- Cohort是购买活跃留存；完整目标月区间[2016-10-01,2018-08-01)，**298个未观察单元为NULL/NA，不填0**。
- 经营诊断只用合格完整月作比较；MAD为回顾提示，HHI描述样本类目结构。配送/评价主95%区间按唯一用户整群bootstrap，差异不解释为因果。

详细见[指标口径](docs/METRICS.md)、[数据模型](docs/P1_DATA_MODEL.md)、[统计方法](docs/P3_ANALYSIS_METHODS.md)和[经营报告](docs/P3_BUSINESS_REPORT.md)。

## 实机截图

以下均来自实际运行页面，非效果图；来源Olist/Kaggle，数据衍生截图按CC BY-NC-SA 4.0注明来源。点击[经营总览全页面](docs/screenshots/01-overview-full.png)查看全部内容。

![经营总览](docs/screenshots/01-overview.png)

| RFM用户价值 | 商品与品类 |
|---|---|
| ![RFM分层](docs/screenshots/02-users.png) | ![商品分析](docs/screenshots/03-products.png) |
| 履约与评价 | 经营发现 |
| ![履约分析](docs/screenshots/04-delivery.png) | ![经营诊断](docs/screenshots/05-findings.png) |

[Cohort热力图](docs/screenshots/02-cohort.png) · [品类帕累托](docs/screenshots/03-pareto.png) · [配送评价关联](docs/screenshots/04-association.png) · [统计置信区间](docs/screenshots/05-confidence.png) · [质量中心](docs/screenshots/06-quality.png)

## Windows本地部署

前提：Windows x64、Python **3.12**、Docker Desktop及WSL 2，硬件虚拟化开启、Docker Engine正常。建议16GB内存并预留足够磁盘。系统安装按[微软WSL文档](https://learn.microsoft.com/en-us/windows/wsl/install)及[Docker官方文档](https://docs.docker.com/desktop/setup/install/windows-install/)操作；需要重启时先保存工作。

在**同一个工程根目录**打开PowerShell。首次安装需网络访问Python包与Kaggle官方下载，可能复用缓存；数据就绪后本地分析无需付费服务。

```powershell
# 首次安装：创建缺失的.venv/.env，下载及审计真实CSV，空库导入、建仓、生成诊断
powershell -NoProfile -ExecutionPolicy Bypass -File .\\start.ps1 -Action init

# 后续日常启动：等待数据库健康，再验证仓库和快照，最后启动页面
powershell -NoProfile -ExecutionPolicy Bypass -File .\\start.ps1
```

打开 **http://127.0.0.1:8501**。Python启动器不在PATH时，首装可加`-PythonExe 'C:\\实际路径\\Python312\\python.exe'`。脚本使用UTF-8 BOM兼容Windows PowerShell 5.1；不要求永久改变执行策略。

`.env.example`是模板；正常首装会自动生成随机密码，只创建缺失的.env，**不会改写已有密码**。若手动复制模板，需自行同步数据库密码与DATABASE_URL；不要把凭证发到聊天或提交Git。Docker默认只绑定127.0.0.1:5432，Streamlit只绑定127.0.0.1:8501。

```powershell
# 就绪检查（不是只检查Docker是否启动）
powershell -NoProfile -ExecutionPolicy Bypass -File .\\start.ps1 -Action check
# 停止数据库但保留数据卷；页面终端用Ctrl+C停止
powershell -NoProfile -ExecutionPolicy Bypass -File .\\start.ps1 -Action stop
# 重启数据库，检查数据和快照，再启动页面
powershell -NoProfile -ExecutionPolicy Bypass -File .\\start.ps1 -Action restart
# 仅检查/自动验收时可加-NoServe，不打开重复的页面服务
```

首装支持安全重跑：完整已有数据只验证，部分或不一致raw拒绝覆盖。Docker健康后还要通过真实SQL、独立Pandas及分析输入检查，不能将容器启动称为系统完成。

## 数据与快照更新

日常启动不会偷偷刷新数据。SQL、数据、源文件或统计代码与快照不一致时会停止并提示。确认需要更新后：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\\start.ps1 -Action refresh
```

该命令不重载raw，显式重建派生core/mart并生成新的`reports/runtime/runs/时间戳`报告；旧P0–P3文档不覆盖，页面通过active.json切换版本。源CSV更新时应保留旧库，在新空数据库验证，不自动覆盖有效原始库。不要运行`docker compose down -v`。

历史阶段脚本保留用于追溯；日常使用本节入口，不直接重跑会替换raw的旧导入命令。

## 测试与复现证据

```powershell
.\\.venv\\Scripts\\python.exe -m pytest -q -rA --junitxml=reports/p4/pytest.xml
```

最新结果 **{tests} passed，0 failed，0 skipped**。独立复核覆盖订单/金额/用户、关联膨胀、每用户RFM、每Cohort单元、Welch/Wilson与用户bootstrap、筛选/导出、只读连接、空数据及启动保护。真实浏览器检查包括六页、CSV/Markdown、故障提示与数据库恢复。

全流程复现使用`.venv-repro`及`retailscope_p4_repro`新空数据库：官方数据准备→审计→COPY导入→建仓→独立Pandas→P3→重复init→版本化refresh→完整测试→实际页面和报告下载。它复用同一主机的Docker/WSL和包/Kaggle缓存；**未声称全新OS、断网安装、公网部署或生产压测通过**。

验收：[P4报告](docs/P4_ACCEPTANCE_REPORT.md)。完整本地日志位于reports/p4，原始数据和用户级结果不进入公开仓库。

## 数据来源、许可与公开范围

数据：[Olist / Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)，数据版本2，许可[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)。这是非商业个人作品，不代表Olist/Kaggle背书；已作清洗规范、聚合与统计衍生。保留署名、许可和修改说明，数据衍生报告/截图遵守相同方式共享要求，详情见[DATA_LICENSE.md](docs/DATA_LICENSE.md)。

原始CSV、.env/密钥、虚拟环境、数据卷/备份、用户级导出和日志均被Git忽略；公开候选文件还经实际本地密码及常见密钥模式扫描。当前仅准备本地Git仓库，**没有创建远端、推送GitHub或部署公网**。原创代码许可证由作者公开前确定。

## 演示与求职材料

- [4分钟演示脚本与真实录制步骤](docs/DEMO_SCRIPT.md)：本次不虚报视频已生成。
- [简历项目经历及岗位版本](docs/RESUME_PROJECT.md)
- [25个面试问题及参考回答](docs/INTERVIEW_GUIDE.md)
- [架构图](docs/ARCHITECTURE.md)与[P0–P3历史验收文档](docs/)

## 局限与后续方向

样本是历史数据，首尾月份不完整、用户观察机会不同；缺少成本、完整退款与曝光，不能计算利润、ROI或点击转化率。统计关联和RFM规则不证明营销效果。可继续补充数据、统一回购窗口、做前瞻性对照试验及生产性能验证，但不把这些待办写成已完成成果。

目录：app六页面；src/retailscope数据与统计/BI；sql仓库及只读诊断；tests自动化；scripts阶段验收；docs说明与聚合截图；data/raw与reports为本地忽略数据。
'''
    (ROOT/'README.md').write_text(readme,encoding='utf-8')
    resume=f'''# RetailScope 简历项目经历

## 项目名称与背景

**RetailScope｜真实电商经营分析与用户增长决策平台（个人非商业项目）**

面向数据分析/商业分析实习，基于Olist公开历史样本构建从审计、入库、SQL数仓到BI、统计诊断和报告的可复核工作流。不存在企业雇佣关系或真实线上干预效果。

技术栈：Python 3.12、PostgreSQL 16、SQL、Pandas、SQLAlchemy、SciPy/NumPy、Streamlit、Plotly、Pytest、Docker Compose。

## 一页简历建议保留的3条

- 基于Olist九张真实CSV（约155万行、9.94万订单）搭建raw/core/mart分层仓库，明确订单/商品粒度，分别预聚合支付与评价，使用独立Pandas对账避免JOIN金额膨胀。
- 实现六页面交互式经营分析，覆盖9.65万有效订单、9.34万购买用户的经营指标、RFM分层、Cohort留存及筛选导出，保留未完整观察月份的NULL。
- 构建7项可追溯经营统计发现，采用完整月/MAD、HHI及用户整群Bootstrap区间；完成{tests}项自动测试与真实浏览器验收，并在干净虚拟环境/新空数据库验证全流程复现。

## 数据分析岗位版本

- 设计可审查SQL指标体系及订单事实层，商品金额与运费/支付分开计算；对96,478个有效订单的商品金额BRL 13,221,498.11及用户等结果执行独立CSV/Pandas复核。
- 基于customer_unique_id完成RFM及月度购买活跃Cohort，处理重复分位边界、跨类目订单不可加及298个不可观察留存单元。
- 对6,381笔逾期与89,443笔未逾期订单的评价作描述性比较，按用户整群bootstrap给出95%区间，并使用独立公式/数值方法复核，明确混杂与选择偏差。

## 数据运营 / 商业分析岗位版本

- 围绕经营规模、品类/地区结构、用户复购和履约体验，构建六页真实SQL看板，支持统一日期与地区/类目筛选、指标解释及CSV/Markdown导出。
- 将7项经营现象组织为“实际结果—样本与分母—来源—方法—局限—待验证建议”，避免将规则分层和相关性包装成已验证增长。
- 建立数据质量中心、版本化报告及首装/日常启动分离流程，通过{tests}项测试、浏览器交互及隔离复现提高作品可审查性和演示可靠性。

## 可量化成果与证据

| 可写事实 | 实际值 | 证据 |
|---|---:|---|
| 原始数据 | 9 CSV / 1,550,922行 | P0验收、原始审计 |
| 全状态订单 | 99,441 | P0 raw及P1订单事实 |
| 有效订单 / 唯一购买用户 | 96,478 / 93,358 | P1 kpi_overview、独立CSV对账 |
| 商品成交额（历史样本，BRL） | 13,221,498.11 | P1/P4基线对账，不代表利润 |
| 整体观察期复购率 | 3.0003% | P1 repurchase_summary |
| 确保NULL的不可观察Cohort单元 | 298 | P1/P2/P4测试与实际热力图 |
| P3核心发现 | 7 | 结构化analysis.json和经营报告 |
| 当前测试 | {tests}通过、无失败/跳过 | P4完整Pytest日志 |
| 全流程复现 | 同主机干净venv+新空数据库 | P4 reproduction证据，非全新OS |

作品可展示：[README](../README.md)、[P4验收](P4_ACCEPTANCE_REPORT.md)、[架构](ARCHITECTURE.md)、[经营报告](P3_BUSINESS_REPORT.md)、[截图](screenshots/)。

## 避免的夸大表述

- 不写“在Olist实习”“为企业搭建并上线”“服务真实运营团队”，本项目是个人作品。
- 不写收入/转化率提升、ROI或利润增长；没有这些数据和干预实验。
- 不写“配送延迟导致差评”；可写“描述性关联及用户聚类置信区间”。
- 不把9.94万全状态订单说成9.94万成交订单，也不把155万源记录说成155万订单。
- 不把复购用户金额较高或RFM标签说成召回策略有效，不将NULL留存填0。
- 不宣称已公开部署、生产并发压测或全新操作系统复现；没有未经授权的GitHub发布。
- 不写不存在的演示视频或企业推荐；录制是否完成以实际视频和回放检查为准。
'''
    (ROOT/'docs/RESUME_PROJECT.md').write_text(resume,encoding='utf-8')
    print('Wrote README.md and docs/RESUME_PROJECT.md using',tests,'actually passing tests.')


if __name__=='__main__':
    main()
