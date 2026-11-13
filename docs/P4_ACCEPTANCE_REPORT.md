# P4 最终交付验收报告

验收日期：2026-11-13。结论：具备本地简历展示与面试演示条件，等待用户最终验收。未创建远端仓库、未推送GitHub、未部署公网；本次到P4停止。

## 真实验证范围与环境

- Windows-11-10.0.26200-SP0；Python 3.12.10；PostgreSQL 16.16（Docker Alpine）。Docker Engine 29.9.3、Compose 5.7.0。
- Pandas 2.3.3、SQLAlchemy 2.1.8、Streamlit 1.67.0、Plotly 6.9.0、SciPy 1.18.1、Pytest 9.2.0；锁定依赖见requirements-lock.txt。
- 单一工程D:/Projects/RetailScope；主库retailscope、复现库retailscope_p4_repro。数据库仅绑定本地；.env密码未修改。
- 审阅README、全部既有阶段验收、METRICS、数据模型、质量报告及P3方法/业务报告；保留历史成果。

## 数据完整性与指标

初始基线与最终数据库指纹一致：九张raw的行数和包含NULL/重复重数的内容指纹均未变化；mart各对象的行数/内容指纹一致。30个受保护历史文档/SQL/.env文件SHA-256未变化。新增运行流程对有效已有数据只检查，部分/不一致raw拒绝覆盖。

| 表 | 实际行数 |
|---|---:|
| raw.customers | 99,441 |
| raw.geolocation | 1,000,163 |
| raw.order_items | 112,650 |
| raw.order_payments | 103,886 |
| raw.order_reviews | 99,224 |
| raw.orders | 99,441 |
| raw.products | 32,951 |
| raw.sellers | 3,095 |
| raw.category_translation | 71 |
| 合计 | 1,550,922 |

全样本SQL及独立Pandas对账仍通过：有效订单96,478；唯一购买用户93,358；商品成交额BRL 13,221,498.11；平均订单商品金额BRL 137.04；复购率3.0003%；平均配送12.56天；逾期率6.7731%；评价均值4.16。统计口径、仓库SQL、原始CSV未更改；商品金额不是财务收入或利润。

## 功能与真实浏览器验收

| 页面/功能 | 实际结果 |
|---|---|
| 经营总览 | 4项KPI符合基线，3张真实图；完整页面截图高1838px |
| 用户价值 | 5张图，RFM固定全样本；Cohort热图保留298个未观察NULL |
| 商品品类 | 5张图，排行/帕累托/件数与去重订单单位正确 |
| 履约评价 | 4张图，12.56天/6.7731%/4.16；关联说明保留解释边界 |
| 经营发现 | 3张图和7项代码生成发现，实际展开用户聚类Bootstrap 95%区间 |
| 数据质量 | 9表/1,550,922行；历史审计快照与数据库实时行数分别标识 |
| 筛选与清空 | 真实浏览器选择SP+beleza_saude：BRL 453,916.48、4,125件、3,715单；清空恢复全样本 |
| CSV导出 | 当前筛选category_ranking.csv实际下载，全部列与参数化SQL逐项对账一致 |
| 报告下载 | 主环境与复现环境Markdown均实际下载，文本与各自代码生成报告一致（规范化换行） |
| 故障与恢复 | 实际停止数据库，刷新后显示“数据暂时无法读取”及重新连接；重启后恢复KPI，无Streamlit异常堆栈 |
| 浏览器布局 | 6页无异常组件、无整页横向溢出；长明细表允许内部滚动 |

日期范围/空结果/组合过滤/SQL一致性由原P2 AppTest和查询测试继续覆盖；P4浏览器重点新增地区+类目、清空、报告、故障恢复验证。不是仅凭HTTP健康或Docker启动判定页面通过。

P4只做小修：提高辅助文字对比度，将订单级“低评分人数”改为“低评分订单数（单）”，区分订单与去重用户，比例差区间标“百分点”。历史P3验收报告原标签作为历史记录未覆盖，该标签应按订单单位理解；生成器已纠正。七项统计数值均未修改。

## 一次全流程复现与安全重复运行

真实新建.venv-repro并安装锁定依赖，在同一PostgreSQL服务的新空数据库中执行：官方kagglehub数据准备/九CSV校验→数据质量→raw COPY导入→core/mart构建→独立CSV/Pandas对账→P3统计与报告→重复init→显式版本化refresh→再次就绪检查→完整测试→Streamlit 8503及浏览器/下载。

每一步退出码0；初次导入1,550,922行；重复init跳过已有数据；refresh只重建派生仓库并产生新时间戳报告，不重载raw、不覆盖已验收报告。两次统计计算所有科学结果与原P3严格相等（仅generated_at不同），包括七项发现、重采样区间、输入与SQL哈希。主库指纹未变。

**实际范围限制：**同一Windows主机、同一Docker PostgreSQL服务的新空数据库；复用官方Kagglehub缓存和pip缓存，未声称新OS或清空网络缓存验证。 也未验证全新Docker卷下的首次系统安装；PowerShell入口实际执行了主环境check、stop、restart -NoServe，首装数据流水线通过同一个runtime的隔离入口执行。未声称整台陌生电脑或所有网络/认证条件均已实测。官方缓存复用不能说成清空缓存后重新联网下载。

### 推荐启动方式

```powershell
# 首次安装：创建缺失环境/随机.env，已有有效数据只验证
powershell -NoProfile -ExecutionPolicy Bypass -File .\start.ps1 -Action init
# 后续启动；完成真实SQL/快照检查后启动Streamlit
powershell -NoProfile -ExecutionPolicy Bypass -File .\start.ps1 -Action start
# 停止/重启保留卷
powershell -NoProfile -ExecutionPolicy Bypass -File .\start.ps1 -Action stop
powershell -NoProfile -ExecutionPolicy Bypass -File .\start.ps1 -Action restart
```

访问http://127.0.0.1:8501。安装/系统要求、Python定位、更新快照流程见README。`check`检查真实数据和结果，不以容器启动代替系统可用。源数据变化时拒绝覆盖，需在新库验证；SQL/统计输入过期时提示显式refresh。旧报告保留，active.json使页面读取新快照。没有永久修改执行策略。

## 自动化测试与统计复核

- 主环境：**86 passed，0 failed，0 errors，0 skipped**；独立虚拟环境+新数据库：**86 passed，0 failed，0 errors，0 skipped**。
- P0/P1/P2/P3断言继续通过；新增8个P4测试，覆盖不覆盖文件/凭证、安全初始化、过期与不完整仓库、报告路径、统计单位及PowerShell 5.1解析。
- 原P3测试仅将证据定位改为可读当前版本化快照，统计断言保持；新增报告路径参数保持原默认行为。
- 订单金额避免支付/评价多对多膨胀、地理邮编去重、RFM/Cohort、缺失/空结果、完整月份、独立置信区间及Markdown结果一致性均通过。
- 复核示例：逾期6,381单与未逾期89,443单；评价均分2.2718与4.2906；差值（逾期减未逾期）-2.0188，用户整群Bootstrap 95%区间[-2.0575,-1.9800]。未将观察关联解释为因果或营销收益。

## 实际运行证据（本地，Git忽略）

| 内容 | 路径 |
|---|---|
| 最新完整测试 | reports/p4/pytest.log、pytest.xml |
| 干净Python+新库最终测试 | reports/p4/repro/pytest_final.log、pytest_final.xml |
| 首装/重复/更新流程 | reports/p4/repro/reproduction.json、reports/p4/reproduction.log及各步骤日志 |
| 六页/筛选/导出浏览器 | reports/p4/browser.log、filtered-category.csv、downloaded_report.md |
| 隔离服务浏览器 | reports/p4/repro/browser.log、downloaded_report.md |
| 启动/故障/恢复 | reports/p4/startup_check.log、stop.log、restart.log、failure_browser.log、recovery_browser.log、db_unavailable.png、db_recovered.png |
| 最终只读对账 | reports/p4/final_verification.json、final_verification.log |
| 安全与修改清单 | reports/p4/public_safety.json、modified_files.json |
| 新版本报告和清单 | reports/runtime/manifest.json；reports/p4/repro/runs/时间戳 |

测试日志和运行结果不默认公开；若需要公开证据，只分享已脱敏的聚合验收材料。

## 截图与求职素材

- 六页：01-overview.png、02-users.png、03-products.png、04-delivery.png、05-findings.png、06-quality.png。
- 专项：01-overview-full.png、02-cohort.png、03-pareto.png、04-association.png、05-confidence.png及05-confidence-card.png；均位于docs/screenshots，来自实际运行页面。
- 架构Mermaid：docs/ARCHITECTURE.md；简历3条核心描述及两种岗位版本：docs/RESUME_PROJECT.md；25个面试问答：docs/INTERVIEW_GUIDE.md；4分钟演示和录制步骤：docs/DEMO_SCRIPT.md。
- **没有生成演示视频**，不把截图称为录屏；已提供可执行的Windows录制和回放步骤。

## 公开仓库安全与许可

实际Git候选文件扫描通过：真实本地密码/连接串与常见密钥模式未命中；.env、九CSV、用户级CSV/Parquet/Excel、虚拟环境、数据卷/备份及运行日志均被忽略。Git索引为空、远端数0、未执行发布。扫描不是对所有秘密类型的数学保证，公开前仍应人工复查。

Olist/Kaggle来源和CC BY-NC-SA 4.0署名、非商业、相同方式共享说明已加入README与docs/DATA_LICENSE.md。仅分享必要聚合截图和报告；不再分发原始数据。原创代码许可证由作者公开前确定，当前没有替作者授权发布。

## 未验证范围、已知问题与交付判断

1. 未执行新操作系统/无缓存网络下载、公网部署、生产并发压力与安全渗透测试；没有声称已通过。
2. 历史数据首尾月份和用户观察机会不一致；未观察Cohort保留NULL，RFM/Cohort全样本不随局部过滤联动。统计分析不能证明因果或运营改善。
3. 全量哈希/独立对账使启动检查需要等待，适合本地单用户演示；未承诺生产启动延迟。
4. 本地保留独立复现数据库、虚拟环境及被忽略证据，未执行批量删除，也未破坏其他项目。
5. CLI统计证据读取有Streamlit“无runtime，使用内存缓存”提示，不影响退出码、SQL和测试；浏览器没有异常组件。
6. 没有录屏文件；没有公开仓库/网站；源码许可证仍需作者在公开前选择。

在上述明确范围内，数据可靠性、六页交互、七项统计发现、测试、可复现工作流和求职展示材料已实际验证，具备简历展示和本地面试演示条件。最终批准由用户验收，本次不继续开发其他项目。

## 本次修改/新增文件清单

- `README.md`
- `.gitignore`
- `pyproject.toml`
- `app/Home.py`
- `src/retailscope/diagnostics.py`
- `src/retailscope/bi/components.py`
- `src/retailscope/bi/diagnostic_page.py`
- `scripts/write_p3_report.py`
- `tests/test_p3.py`
- `start.ps1`
- `requirements-lock.txt`
- `src/retailscope/runtime.py`
- `tests/test_p4.py`
- `scripts/audit_public.py`
- `scripts/reproduce_p4.py`
- `scripts/serve_repro.py`
- `scripts/test_repro_p4.py`
- `scripts/p4_browser_check.js`
- `scripts/p4_failure_check.js`
- `scripts/p4_recovery_check.js`
- `scripts/verify_p4_final.py`
- `scripts/write_career_materials.py`
- `scripts/write_p4_report.py`
- `docs/ARCHITECTURE.md`
- `docs/DATA_LICENSE.md`
- `docs/DEMO_SCRIPT.md`
- `docs/RESUME_PROJECT.md`
- `docs/INTERVIEW_GUIDE.md`
- `docs/P4_ACCEPTANCE_REPORT.md`
- `docs/screenshots/01-overview-full.png`
- `docs/screenshots/01-overview.png`
- `docs/screenshots/02-cohort.png`
- `docs/screenshots/02-users.png`
- `docs/screenshots/03-pareto.png`
- `docs/screenshots/03-products.png`
- `docs/screenshots/04-association.png`
- `docs/screenshots/04-delivery.png`
- `docs/screenshots/05-confidence-card.png`
- `docs/screenshots/05-confidence.png`
- `docs/screenshots/05-findings.png`
- `docs/screenshots/06-quality.png`

另新增本地忽略的reports/p4、reports/runtime证据；创建本地.git（main、无远端/提交）。.env.example和docker-compose.yml复用已有有效配置，未改密码、未删除原始数据或历史报告。完整结构化清单见reports/p4/modified_files.json。
