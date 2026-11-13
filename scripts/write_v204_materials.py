"""Render portfolio documents from executed test counts and accepted real-data evidence."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from retailscope.bi.components import evidence_path

ROOT=Path(__file__).resolve().parents[1]


def main():
    suite=ET.parse(ROOT/'reports/v2-04/pytest.xml').getroot().find('testsuite')
    assert all(int(suite.get(key,0))==0 for key in ('failures','errors','skipped'))
    tests=int(suite.get('tests'))
    front=(ROOT/'reports/v2-04/frontend_tests.log').read_text(encoding='utf-8-sig')
    assert '22 passed' in front
    baseline=json.loads((ROOT/'reports/v2-04/baseline.json').read_text(encoding='utf-8'))
    total=sum(row['rows'] for row in baseline['raw'].values())
    p3=json.loads(evidence_path('reports/p3/analysis.json').read_text(encoding='utf-8'))
    kpi=json.loads((ROOT/'reports/p1/kpi_overview.json').read_text(encoding='utf-8'))[0]
    groups=p3['association']['groups']
    readme=f'''# RetailScope｜电商经营分析与用户增长决策平台

以真实Olist历史订单为基础，贯通数据质量、PostgreSQL分层仓库、可复核统计推断与React经营分析工作台的个人非商业作品。

**用途**：面向数据分析/商业分析实习，回答“经营规模如何变化、谁在购买、哪些品类重要、配送和评价如何关联”，让图表、分母与SQL证据可以现场复核。不是企业实习经历，不声称实际商业上线或带来收入增长。

![React经营总览实拍](docs/screenshots/v2-04/overview-1440.png)

## 实际规模与成果

| 项目 | 真实结果 |
|---|---:|
| 原始数据 | 9个CSV / {total:,}行 |
| 全状态订单 | {baseline['raw']['orders']['rows']:,}单 |
| 有效delivered订单 | {kpi['orders']:,}单 |
| 唯一购买用户 | {kpi['users']:,}人 |
| 商品成交额 | BRL {float(kpi['merchandise']):,.2f} |
| 商品明细（有效订单） | 110,197行 |
| 用户分层/留存 | RFM六层 / Cohort保留298个未观察NULL |
| 统计发现 | 7项P3已验证发现 |
| 最终自动测试 | {tests}项Pytest + 22项Vitest通过 |

测试/浏览器/原始数据保护证据见[最终验收报告](docs/V2-04_FINAL_ACCEPTANCE_REPORT.md)。数字来自实际SQL与已验收结果，页面没有硬编码这些验收基线。

## 六个新版分析页面

| 页面 | 分析流程 | 范围 |
|---|---|---|
| 经营总览 `/` | KPI→月度经营→订单状态→地区贡献 | 日期/客户州，完整月视图与局部窗口明确区分 |
| 用户价值 `/users` | RFM→购买频次→Cohort→观测新增用户 | 固定P1全样本，不作虚假局部联动 |
| 商品品类 `/products` | 贡献排行→帕累托→月度结构→件数/订单覆盖 | 日期/州/类目，订单总数跨所选商品重新去重 |
| 履约评价 `/delivery` | 有效分母→配送/评分分布→地区→逾期关联 | 日期/州/类目，类目表示订单包含该类目 |
| 经营发现 `/findings` | 结论→证据→方法→解释边界→待验证建议 | 固定P3全样本，专题筛选及Markdown原文件下载 |
| 数据质量 `/quality` | 当前计数→历史审计→关联/约束→构建/对账→测试日志 | 当前SQL、历史文件与测试记录分开展示 |

CSV、Markdown、JSON下载都经过实际浏览器验收；没有空页面、模拟订单或虚假的AI诊断。原版Streamlit六页保留为旧版，不与新版身份/导航混淆。

## 技术架构

```mermaid
flowchart LR
  A[Olist / Kaggle 九CSV] --> B[结构与质量审计]
  B --> C[(PostgreSQL16 Raw)]
  C --> D[Core 类型视图]
  D --> E[Mart 维表/订单事实/商品事实]
  E --> F[SQL指标 / RFM / Cohort]
  E --> G[P3 完整月/MAD/HHI/整群Bootstrap]
  F --> H[FastAPI + SQLAlchemy 只读参数化访问]
  G --> H
  H --> I[React + TypeScript + Vite]
  I --> J[Tailwind + shadcn/ui + ECharts 六页]
  J --> K[CSV / Markdown / JSON]
  E --> L[Streamlit + Plotly 旧版]
  A --> M[独立CSV/Pandas对账]
  M --> N[Pytest / Vitest / 真实浏览器 / 哈希保护]
```

技术栈：Python3.12、PostgreSQL16、SQLAlchemy、Pandas、SciPy/NumPy、FastAPI、React/TypeScript/Vite、Tailwind CSS/shadcn/ui、Apache ECharts、Pytest、Vitest、Docker Compose。均为本地方案，无必须付费服务。

API为只读连接、参数绑定、有限连接池与超时；React页面级懒加载。ECharts按需注册，独立拆分zrender：最终最大单包约364KB，渲染器约182KB；构建没有提高阈值来隐藏告警。这是分包体积事实，不等同首屏提速或生产压测通过。

## 数据仓库与指标口径

raw保留源文本与重复；core规范类型/时间；mart明确用户、商品、商户维度与订单/商品行粒度。支付、评价、商品金额先各自按订单聚合再连接，防止一对多相乘。地理信息先规范为唯一邮编汇总，不直接连接重复地理明细。

- 核心交易使用delivered且购买时间有效的订单，日期主要为order_purchase_timestamp，含首尾日。
- 商品金额SUM(price)不含运费；运费和支付金额单列，均不等于利润或财务确认收入。
- 用户按customer_unique_id跨订单去重。类目内订单可能交叉，不能把类目订单数相加作为总量。
- 平均配送与逾期各使用有效日期分母，评价缺失与无效日期保留并说明，不默默补0。
- F05评分均值是review_mean的订单等权平均；**低评分比例才使用每单最新评分≤2**。已修复曾将均分误标为最新评分均值的展示文案，数值与模型未变。

完整定义：[METRICS](docs/METRICS.md) · [P1数据模型](docs/P1_DATA_MODEL.md) · [V2接口与筛选](docs/V2-02_API_AND_SCOPE.md)。当前目录的Mart29个关系对象与27个验收快照对象清单范围不同，后者不含dim_month和eligible_orders。

## RFM、Cohort与统计推断

RFM基准日2018-08-30，以有效订单计算Recency/Frequency/Monetary，沿用P1五分位/同值同分与六类分组。Frequency大量为1造成评分档缺失是样本特征，不是程序错误或营销效果。

Cohort为观测首次有效购买月份，同用户同月去重；只在完整目标月计算回购活跃留存，未观察为NULL，已观察无活跃才为0。观察机会不同、首尾不完整及首cohort左截断均披露。

P3仅使用完整月份做可比趋势；MAD用于稳健回顾筛查，HHI描述样本品类集中度，地区/用户结构均为描述性统计。F05按唯一用户整群Bootstrap 2,000次、固定种子给出95%区间，保留同用户多单与跨组关系。评分差（逾期减未逾期）约-2.0188分，95%区间[-2.0575,-1.9800]；这**不是配送延误的因果效应**。

方法与限制：[P3统计方法](docs/P3_ANALYSIS_METHODS.md)。经营发现下载始终返回与已验证快照配对的报告原字节，不在页面运行新模型。

## 真实界面截图

所有截图来自实际生产构建的本地浏览器，PNG可直接用普通图片查看器打开。

| 页面 | 1440×1000首屏 | 1440px完整页面 | 1280×900 |
|---|---|---|---|
| 总览 | [截图](docs/screenshots/v2-04/overview-1440.png) | [全页](docs/screenshots/v2-04/overview-1440-full.png) | [截图](docs/screenshots/v2-04/overview-1280.png) |
| 用户 | [截图](docs/screenshots/v2-04/users-1440.png) | [全页](docs/screenshots/v2-04/users-1440-full.png) | [截图](docs/screenshots/v2-04/users-1280.png) |
| 商品 | [截图](docs/screenshots/v2-04/products-1440.png) | [全页](docs/screenshots/v2-04/products-1440-full.png) | [截图](docs/screenshots/v2-04/products-1280.png) |
| 履约 | [截图](docs/screenshots/v2-04/delivery-1440.png) | [全页](docs/screenshots/v2-04/delivery-1440-full.png) | [截图](docs/screenshots/v2-04/delivery-1280.png) |
| 发现 | [截图](docs/screenshots/v2-04/findings-1440.png) | [全页](docs/screenshots/v2-04/findings-1440-full.png) | [截图](docs/screenshots/v2-04/findings-1280.png) |
| 质量 | [截图](docs/screenshots/v2-04/quality-1440.png) | [全页](docs/screenshots/v2-04/quality-1440-full.png) | [截图](docs/screenshots/v2-04/quality-1280.png) |

专项：[Cohort](docs/screenshots/v2-04/users-cohort.png) · [F05证据](docs/screenshots/v2-04/findings-association.png)。

## Windows本地运行

已验证环境为Windows11、Python3.12.10、Node24.15.0/npm11.12.1、PostgreSQL16.16。先安装Python3.12、Node和采用WSL2后端的Docker Desktop，打开Docker并等待引擎就绪。本项目不自动改无关系统配置。

首次进入已有工程根目录：

```powershell
# 创建缺失的.venv/.env，官方数据下载与校验、入库、建仓、P3结果准备
powershell -NoProfile -ExecutionPolicy Bypass -File .\\start.ps1 -Action init
# 安装V2锁定依赖；需要可用的Node/npm
powershell -NoProfile -ExecutionPolicy Bypass -File .\\start-v2.ps1 -Action install
# 终端一：API
powershell -NoProfile -ExecutionPolicy Bypass -File .\\start-v2.ps1 -Action api
# 终端二：React开发服务
powershell -NoProfile -ExecutionPolicy Bypass -File .\\start-v2.ps1 -Action web
```

打开http://127.0.0.1:5173；API文档http://127.0.0.1:8000/docs。初始化只创建缺失.env并生成随机密码，**不改已有密码**；部分/不一致数据会停止，不隐式覆盖Raw或已验收报告。Python不在启动器中时，init可加`-PythonExe 'C:\\实际路径\\Python312\\python.exe'`。

后续启动先执行`start.ps1 -Action start -NoServe`启动数据库并做真实数据/快照检查，再启动API和web；初次下载若官方要求认证，按错误提示在本机认证，不把密钥发到仓库或聊天中。

面试前建议使用实际构建产物，另开终端：

```powershell
npm --prefix frontend run build
npm --prefix frontend run preview -- --port 5174
```

访问http://127.0.0.1:5174，支持直接打开六个URL。开发/预览/API均仅绑定127.0.0.1。原Streamlit可单独运行`.\\.venv\\Scripts\\python.exe -m streamlit run app/Home.py`，端口8501。

停止页面/API在各终端按Ctrl+C；停止数据库用`start.ps1 -Action stop`，保留卷。重启检查可用`start.ps1 -Action restart -NoServe`。不要执行`docker compose down -v`丢弃数据卷。

派生SQL或分析输入变化会提示更新；确认来源后显式运行`start.ps1 -Action refresh`生成新时间戳快照，再刷新页面。它不重载Raw、不覆盖历史报告；原始CSV变化应在新库验证。应用与测试读取相同活动P3快照路径，不伪造历史验收文件。

## 测试与可复现范围

```powershell
.\\.venv\\Scripts\\python.exe -m pytest -q -rA --junitxml=reports/v2-04/pytest.xml
npm --prefix frontend test
.\\frontend\\node_modules\\.bin\\tsc.cmd -b frontend/tsconfig.json
npm --prefix frontend run build
```

本阶段{tests}项Pytest、22项Vitest通过；类型检查、构建和六页真实浏览器验收通过。SQL/Pandas独立对账、JOIN防膨胀、RFM/Cohort、区间、过滤与导出、历史/当前来源和源码/数据哈希保护均有本地证据。

P4曾在**同一主机**新虚拟环境和新空库跑完整数据流水线，复用pip/Kaggle缓存；本阶段对当前V2六页执行最终回归。没有声称全新OS、清空缓存后的网络安装、生产并发、公网认证或部署通过。历史运行日志在reports中本地保留而不公开；新安装生成自己的本地证据，不能把旧验收文档当作自己的新运行结果。

## 数据来源、许可与公开边界

来源：[Olist / Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)，验收数据版本2，许可[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)。这是个人非商业衍生分析，保留署名、许可和修改说明；数据衍生聚合报告/截图遵守相同方式共享要求，不表示Olist/Kaggle背书。[许可说明](docs/DATA_LICENSE.md)。原创代码许可证由作者发布前确定，不自动把数据许可解释为全部代码授权。

.env、密码/密钥、原始CSV、用户级导出、数据库卷/备份、虚拟环境、node_modules、dist和不必要日志都被忽略。已扫描实际Git候选文件与本地秘密，当前仅本地仓库，未创建远端、推送或公开部署。公开前由作者审阅候选清单和许可证，不打包原始数据或私人配置。

## 求职材料与局限

- [简历项目经历](docs/RESUME_PROJECT.md)：三条一页版、数据分析及运营/商业分析版本。
- [面试问答](docs/INTERVIEW_GUIDE.md)：SQL、统计、React/API与工程取舍。
- [4分钟演示脚本](docs/DEMO_SCRIPT.md)：真实筛选、RFM/Cohort、区间和质量来源。
- [最终验收](docs/V2-04_FINAL_ACCEPTANCE_REPORT.md) · [完整公开候选工程清单](docs/V2_FINAL_FILE_MANIFEST.md)。

历史样本缺少成本、完整退款、曝光与实验分配，不能计算净利润、ROI或转化率改善；样本变化不是未来预测，RFM标签不是召回效果。P0原质量JSON没有审计执行时间，界面如实保留未知，不用文件保存时间冒充。未交付视频文件，提供可执行录制步骤；无虚构企业经历、用户部署数量或增长收益。
'''
    (ROOT/'README.md').write_text(readme,encoding='utf-8')
    resume=f'''# RetailScope｜简历项目经历

## 项目名称、背景与技术栈

**RetailScope 电商经营分析与用户增长决策平台｜个人非商业项目**。基于Olist公开历史订单，构建从审计、分层SQL仓库到React分析工作台与可复核统计报告的完整作品；不是企业实习或商业上线经历。

技术：Python3.12、PostgreSQL16、SQLAlchemy、Pandas、SciPy/NumPy、FastAPI、React/TypeScript/Vite、Tailwind CSS/shadcn/ui、ECharts、Pytest/Vitest、Docker Compose；Streamlit/Plotly保留为旧版。

## 一页简历的三条核心描述

- 基于Olist九张真实CSV（{total:,}行、99,441笔全状态订单）搭建Raw/Core/Mart分层仓库，按订单预聚合商品、支付和评价，使用独立CSV/Pandas对账，防止多表JOIN金额膨胀。
- 开发React + FastAPI六页经营分析工作台，通过只读参数化SQL覆盖96,478笔有效订单、93,358位购买用户，支持统一范围筛选、RFM分层、Cohort与CSV/Markdown/JSON导出，保留298个未观察留存NULL。
- 复核7项经营统计发现，采用完整月/MAD、HHI及唯一用户整群Bootstrap 95%区间；完成{tests}项后端、22项前端测试和两种桌面尺寸的真实浏览器验收，形成可追溯报告与本地演示流程。

## 数据分析岗位版本

- 设计明确粒度与分母的SQL经营指标，商品金额与运费/支付分开；对BRL13,221,498.11商品金额、有效订单/唯一用户等结果进行独立CSV/Pandas与数据库交叉核对。
- 使用customer_unique_id构建RFM与月度回购活跃Cohort，处理重复分位边界、不等观察窗口及未观察NULL，避免将规则标签解释为实验效果。
- 对逾期6,381单与未逾期89,443单的**订单等权评价均分**作描述性比较，采用按用户整群重采样给出95%区间；最新评分≤2仅用于低评分比例，不混淆统计单位或推断因果。

## 数据运营 / 商业分析岗位版本

- 围绕经营规模、品类/地区贡献、用户复购与履约体验组织六页分析流程，支持真实筛选与导出，而非静态截图展示。
- 将7项已验证发现关联至SQL、样本量、观察区间、方法与待验证建议，区分描述性差异、数据缺失和业务效果，提出需后续对照验证的方向。
- 建立质量证据中心，区分当前SQL计数、历史审计、构建状态与测试记录，支持现场追溯而不夸大数据新鲜度。

## 可量化且有证据的成果

| 事实 | 证据 |
|---|---|
| 九表{total:,}行、全状态订单99,441 | 最终保护快照、质量中心实际SQL |
| 有效订单96,478、用户93,358、商品金额BRL13,221,498.11 | P1 SQL与独立Pandas对账、默认API |
| 复购用户2,801，复购率3.0003%；Cohort未观察NULL298个 | 原RFM/Cohort与新版接口逐项对账 |
| F05均值差-2.0188、95%区间[-2.0575,-1.9800] | 原P3结果、独立公式/重采样测试 |
| 六页、两种桌面尺寸，CSV/MD/JSON真实下载 | V2-04浏览器日志与最终PNG |
| {tests}后端+22前端测试通过 | reports/v2-04日志/XML |

## 面试叙述边界

不写企业雇佣关系、服务用户数、营收/转化提升、生产上线或云端部署。155万是多表总记录，不是订单数；99,441是全状态订单，不是全部成交。商品金额不是财务收入或利润。复购用户金额更高、RFM标签或配送评分差异均不是干预收益。分包优化只报告包体与验证结果，不捏造首屏提速指标。

历史P4同机新环境/空库复现与本阶段V2回归分别说明；没有全新操作系统验证。数据来源Olist/Kaggle版本2，非商业衍生分析遵守CC BY-NC-SA 4.0。当前等待最终验收，未公开发布。
'''
    (ROOT/'docs/RESUME_PROJECT.md').write_text(resume,encoding='utf-8')
    # Preserve the substantial existing Q&A, correct obsolete runtime descriptions and add V2 specifics.
    path=ROOT/'docs/INTERVIEW_GUIDE.md';guide=path.read_text(encoding='utf-8')
    guide=guide.replace('测试数量看最新P4报告。',f'当前V2后端{tests}项、前端22项通过，完整证据看V2-04最终验收报告。')
    guide=guide.replace('前端21项','前端22项').replace('约346KB','约364KB')
    old='缓存键包含不可变筛选对象，TTL120秒，页面指标和图表共享同一范围。RFM/Cohort则明确固定P1全样本，不作虚假联动。侧栏能清缓存；仓库更新后要刷新分析快照，不能把历史审计快照称为实时审计。'
    new='React把draft与applied范围分开，KPI/图表/导出共享已应用范围；AbortController取消旧请求，避免过期响应覆盖新筛选。地区/品类点击应用当前草稿，不覆盖未应用日期。API同一只读事务读取相关结果。旧版Streamlit才使用TTL120秒缓存和清缓存按钮。RFM/Cohort明确固定全样本，历史质量快照也不冒充当前审计。'
    guide=guide.replace(old,new)
    if '## 26. 新版React与FastAPI如何分工？' not in guide:
        guide+='''
## 26. 新版React与FastAPI如何分工？

React/TypeScript组织六个懒加载页面、草稿筛选与ECharts；FastAPI只读适配既有SQL/统计文件，SQLAlchemy绑定参数并限制连接/查询超时。金额以Decimal字符串传输，浏览器只在展示和绘图时转数值，不在页面重新开发分析模型。

## 27. F05为什么不能叫“最新评分均值”？

原P3对review_mean做订单等权平均：先每订单内平均多条评价，再对订单平均。latest_review_score只用于每单最新评分≤2的低评分比例。真实数据中未逾期两种均值约4.290589与4.290386，不能偷换。V2-04修复展示术语，并以独立SQL回归固定该区别，数值/模型未变。

## 28. 如何展示95%区间而不夸大结论？

交代样本95,824单、两组订单数、缺失排除、差值方向、重采样单位与次数，再展示按唯一用户整群的区间。它量化给定观察样本下的不确定性，不能消除混杂、选择偏差或证明配送延迟的因果效应。最新评分低评区间与订单均分区间是两种统计量。

## 29. 为什么API采用REPEATABLE READ和只读事务？

KPI、趋势、排行等查询在同一事务读取一致快照，减少查询之间范围不一致；default_transaction_read_only和白名单SQL防止页面写数据，参数绑定避免注入。它不等于已采用生产最小权限角色、身份鉴权或做过渗透测试。

## 30. ECharts大包如何处理，是否证明页面更快？

原本已按需导入图形；最终去掉未用MarkPoint注册，将独立zrender渲染器分包，保持页面懒加载。最大包约534KB变为约364KB核心与182KB渲染器，并真实回归全部图表。告警消失不等于总传输量减半，更不能捏造LCP或首屏提升。

## 31. 如何防止质量中心把历史结果说成当前检测？

对当前COUNT/目录使用数据库事务时间；P0/P1/P3/测试文件分别显示来源、执行时间（若记录）、保存时间和SHA。P0没有执行时间字段就保留未知。DB不可用时当前值不补0，历史记录仍展示；加载页面不重建、不全量审计、不运行测试。

## 32. 下载报告如何保证真实一致？

Markdown先检查已生成文件与同一P3快照的文字配对，再返回原字节；浏览器下载后与本地文件做字节/SHA核对。CSV携带已应用scope，JSON携带各证据来源与时间。不让用户输入文件路径，也不导出用户级敏感记录。

## 33. 为什么测试也要读取活动快照？

首装或显式refresh会产生新版本目录和active.json。测试若固定读旧reports/p3文件，会与正在运行的应用比较错对象。新版测试沿用应用的活动快照约定，并保留原统计断言；不能以改期望值掩盖真实数据差异。

## 34. 这个项目能直接称为生产系统吗？

不能。它完成了本地数据与统计验证、六页交互、依赖与启动流程、真实截图/报告及安全候选检查，但没有公网鉴权、生产并发或企业使用证据。求职时展示技术能力和可复核过程，不编造用户数量或经营改善。
'''
    path.write_text(guide,encoding='utf-8')
    demo=f'''# RetailScope V2｜4分钟面试演示脚本

## 录制与现场演示前

1. 提前打开Docker Desktop，执行`start.ps1 -Action start -NoServe`完成数据库与快照检查，等待结束，不把检查等待时间录入讲解。
2. API终端运行`start-v2.ps1 -Action api`；先`npm --prefix frontend run build`，另一个终端`npm --prefix frontend run preview -- --port 5174`。
3. 打开http://127.0.0.1:5174，设置1440×1000或1280×900。六页预检、清空筛选，准备下载目录。关闭个人通知，不展示.env或凭证。
4. 本文件是可执行脚本，不是已录制视频；本次没有虚报MP4。Windows截图工具录制或Win+G先试录10秒，检查声音/画面；正式录制后回放全片，检查无凭证/隐私后再分享。

## 0:00–0:30｜问题与真实数据

“这是我的个人非商业项目RetailScope，用Olist公开历史样本回答经营规模、用户回购、品类结构和履约体验问题。九CSV约155万行，其中99,441笔全状态订单；有效订单96,478。图表背后有SQL、样本量和质量证据。”

画面：新版总览，商品金额BRL13,221,498.11、用户93,358。说明商品金额不含运费，不等于收入/利润，也不是实时新增订单流。

## 0:30–1:05｜分层SQL与统一筛选

“Raw保留原值，Core规范类型，Mart把订单/商品粒度分清，支付、评价先预聚合，避免JOIN把金额相乘。FastAPI只读参数化查询，React组织交互。”

在总览输入2017-05-10—2017-06-20但先不按应用，点击SP州排行：“地区点击会应用当前草稿日期，不覆盖日期。KPI与图表共享相同范围。”重置恢复全样本。

## 1:05–1:50｜用户价值与留存

进入用户价值页：“RFM按customer_unique_id，基准2018-08-30。大量Frequency=1导致某些评分档为空，这是真实特征。全样本复购率约3.0003%，不能说召回策略有效。”

滚到Cohort：“这是月度回购活跃留存，不是连续订阅；同用户同月去重。298个未观察单元保留NULL，不填0；用户观察机会不一致。此页固定P1全样本，不跟其他页局部筛选假联动。”

## 1:50–2:30｜品类与履约流程

商品页展示TOP10、帕累托和件数/订单：“跨类目订单不能直接相加，顶部订单在选中商品行范围重新去重。”可选择SP、beleza_saude展示真实组合结果，点击CSV导出。

履约页看12.56天、6.7731%、4.16及分母：“订单均分先订单内平均、再等权；评分分布/低评比例使用最新评分，不能混淆。日期缺失不进入对应配送分母。”

## 2:30–3:20｜七项发现与统计推断

进入独立经营发现页，选择“履约体验”。“P3固定全样本，逾期6,381单、未逾期89,443单，订单均分差-2.0188，按用户整群Bootstrap 95%区间[-2.0575,-1.9800]。同用户多单保留在一个重采样簇内；区间不能消除混杂或证明因果。”

展开聚合证据、显示SQL标识和待验证建议，点击Markdown下载：“下载的是与P3结果配对的原文件，实际做过字节一致性验证，不是现场生成新结论。”

## 3:20–4:00｜数据可信与工程边界

进入数据质量中心：“上方九表COUNT是当前数据库；缺失/重复是历史P0快照。P0没有记录审计时间，就明确未知，不能拿文件时间冒充。构建、对账与测试日志也分别标来源。页面不自动重建或运行耗时审计。”

“最终{tests}项后端、22项前端测试通过；六页在两种桌面尺寸真实验收，CSV/MD/JSON下载均对账。它是可复核的个人作品，不是企业上线或已证明增长的系统。”

## 现场故障预案

API不可用先看中文重连提示，不展示过期KPI；检查两个终端与Docker后恢复。不现场删除数据卷或重建Raw；数据库停止/恢复已实际验收，可用最终报告说明。若网络下载受限，演示现有合法本地样本并说明来源，绝不用模拟数据填充。可提前准备最终PNG作为备用说明，但不称其为交互或录屏。
'''
    (ROOT/'docs/DEMO_SCRIPT.md').write_text(demo,encoding='utf-8')
    arch=ROOT/'docs/ARCHITECTURE.md';old=arch.read_text(encoding='utf-8')
    if '## V2正式工作台架构' not in old:
        intro='''
## V2正式工作台架构

主产品为React/TypeScript + FastAPI六页，旧版Streamlit单独保留。SQL与统计模型仍复用P1/P3，API只读；Markdown原字节下载、JSON质量证据及CSV都区分来源/范围。页面级懒加载与zrender独立分包在生产构建真实验证。

```mermaid
flowchart LR
  O[Olist CSV / 审计] --> R[(Raw)] --> C[Core类型视图] --> M[Mart维表/事实/分析视图]
  M --> Q[只读SQL / RFM / Cohort]
  M --> S[P3预计算统计]
  Q --> A[FastAPI / SQLAlchemy]
  S --> A
  A --> F[React / TypeScript / ECharts 六页]
  A --> E[CSV / Markdown / JSON]
  M --> L[Streamlit旧版]
```

下方P4原架构说明作为旧版与数据流水线历史保留；当前启动与最终证据以主README/V2-04报告为准。

'''
        first,rest=old.split('\n',1);arch.write_text(first+'\n'+intro+rest,encoding='utf-8')
    print(f'Updated React-first README, resume, 34-question interview guide, demo and architecture using {tests} passing backend tests.')


if __name__=='__main__':main()
