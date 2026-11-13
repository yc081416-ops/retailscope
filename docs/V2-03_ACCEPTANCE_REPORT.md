# RetailScope V2-03 经营发现与数据质量中心验收报告

日期：2026-11-13。新增两个正式独立页面，六个业务模块均实际可访问；工程与浏览器验证通过，等待用户最终验收。只到V2-03，未进入V2-04、项目二、GitHub推送或公网部署。

## 页面交付与既有功能保护

- 经营发现：从P3弹窗迁移为/findings，保留总览原“查看经营发现”和方法入口，但改为导航到正式页面。七项发现按专题筛选，展示真实结果、样本量、分母、区间、SQL标识、方法、解释边界与待验证建议，可展开完整聚合证据。
- 数据质量中心：/quality，按“来源与规模→历史缺失/重复→关联及异常→架构约束→构建与对账→后端测试历史”组织。当前SQL、P0历史、P1/P3构建、测试记录有不同来源标记与时间，不混称实时全量检测。
- 侧栏六个正式链接均可用，没有待开放标签。页面标题、面包屑、前进/后退与直接访问统一；冻结的标题29px、导航/正文14px、辅助12px及白色/紫/青色语言继续复用。
- Overview、Users、Products、Delivery四个已有页面源码，以及overview.css、index.css、analysis.css均未改写，源文件SHA-256保持一致。仅共享Shell注册新页面及迁移发现回调，不重构既有四页。
- 原Findings弹窗源文件保留，正式入口不再指向它；旧版Streamlit源码保留，原P0–P4测试仍通过。

## 经营发现：与P3逐项一致

| ID | 已验收发现 | 样本与解释来源 |
|---|---|---|
| F01 | 完整月经营趋势 | 完整月/比较月订单及金额；P3_MONTHLY |
| F02 | MAD异常月份回顾筛查 | 金额、订单各18个可用相邻月份对；P3_MONTHLY |
| F03 | 商品类目集中度、HHI | 74类、有效商品金额分母；P3_CATEGORIES |
| F04 | 地区规模与履约 | 订单客户州及独立配送/逾期分母；P3_REGIONS |
| F05 | 逾期与评价的描述性差异 | 95,824单有效比较，排除654单；P3_ASSOCIATION |
| F06 | RFM、一次购买与复购结构 | 93,358位购买用户、2,801位复购用户及原RFM结果 |
| F07 | Cohort留存与观察窗口 | 合格cohort分母、次月活跃用户及未观察单元 |

所有result/sample/statistics/method/limitations/suggestion直接读取已生成P3分析JSON；API测试逐项对账，浏览器逐条核对七项结果原文。没有新估计、重新执行Bootstrap或生成新业务结论。

固定有效购买期2016-09-15—2018-08-29。页面持续标记“P3固定全样本”，不接收其他页面日期/州/类目作为统计过滤；专题选择只控制展示。F05优先展示以突出证据，不改变原P3对象内容。

### F05重点证据

| 分组 | 实际订单 | 去重用户 | 最新评分均值 | 低评分订单 |
|---|---:|---:|---:|---:|
| 未逾期 | 89,443 | 86,662 | 4.2906 | 8,289 |
| 逾期 | 6,381 | 6,346 | 2.2718 | 3,983 |

评分均值差（逾期减未逾期）-2.0188分，用户整群percentile Bootstrap 95%区间 **[-2.0575,-1.9800]**；低评分率差区间[51.99,54.36]个百分点。重采样2,000次、种子20261113均来自原P3记录。两组用户可能交叉，不把组内去重用户直接相加作为全体唯一用户。

页面同时显示有效比较95,824单、全体有效订单96,478单和排除654单。低评分为最新评分≤2；方法、选择偏差、同用户相关与地区/类目/时间混杂边界保留。图表为真实组均值，文字与表格提供区间；不把统计关联解释为延误的因果效应或已验证运营收益。

### Markdown下载

新接口读取已生成报告原文件，先用原格式化函数核对其文字与同一P3快照配对，再返回原始字节；只做配对校验，不运行统计计算、不改写报告文件。报告缺失、不一致或路径越界则拒绝返回。

实际浏览器下载文件与本地P3报告**字节完全相同**，SHA-256：`166a8a9cda6d144aaeab4cd540e6c8a6a392537800bc99ae34f15d8563a447dc`。不是重新手写的摘要，也不是仅规范化换行后相同。

## 数据质量中心的证据分层

| 展示内容 | 实际来源 | 时间与含义 |
|---|---|---|
| 当前九表行数 | 新只读COUNT(*)查询 | 同一REPEATABLE READ事务的查询时间，不是新增订单实时流 |
| Raw/Core/Mart对象与主/外键/唯一约束 | PostgreSQL系统目录 | 当前数据库目录，不冒充逻辑键审计 |
| 当前有效订单异常 | 既有mart.quality_checks | 当前派生仓库查询，仍依赖P1构建，不证明Raw已经重新审计 |
| 缺失、重复、逻辑唯一键与源关联 | reports/raw_quality.json | P0历史CSV审计，不标为当前重审计 |
| 数据集版本和下载校验 | reports/download_manifest.json | 原记录的checked_at_utc和cache_version=2 |
| 构建与幂等、Pandas状态 | reports/p1/run.json | 原started_at，不等于页面访问时间 |
| 22项独立对账 | reports/p1/pandas_reconciliation.json | 历史对账结果；单项执行时间未独立记录 |
| P3快照与报告状态 | 已生成analysis.json、Markdown | 生成时间与文件SHA、配对检查，不对当前全库输入重做指纹或模型验证 |
| 最近可验证后端测试 | 固定白名单的完整Pytest XML | 核对逐项计数，按文件保存时间选择最近完整记录；不在页面执行测试 |

**时间缺口如实披露：**P0质量JSON没有审计执行时间字段；页面executed_at=null，明确“执行时间未记录；文件保存时间不是执行时间”。初始化清单与单项Pandas对账也不补造执行时间。文件保存时间与已记录执行时间分别展示，XML原时间不擅自补造时区。前端20项测试与生产构建日志在阶段交付中，不混入后端XML计数。

当前真实九表总计**1,550,922行**：customers99,441、geolocation1,000,163、order_items112,650、order_payments103,886、order_reviews99,224、orders99,441、products32,951、sellers3,095、category_translation71。与P0历史行数并列，特意标明“行数一致不等于内容审计”。

当前目录为Raw9、Core8、Mart29个表/视图关系对象。旧验收的27个Mart快照核对对象清单不含dim_month、eligible_orders，目录统计范围不同；并非本阶段新建了两个对象。实际未执行建表、重建或任何写数据操作。

历史地理整行重复、空评价文本、邮编覆盖缺口，以及非唯一review_id/邮编/customer_unique_id均保留并解释；没有把它们自动判为程序错误。没有逻辑唯一键的原始表相关检查显示NA，不伪装成已检查唯一且通过。实际数据库主键/外键与CSV逻辑审计键分开。

数据库查询不可用时，质量API保留历史证据，将live置为unavailable、当前计数不可用，绝不以历史计数代替当前值或补假0。页面刷新只读有限表计数、目录和本地证据；未调用完整audit、runtime readiness、仓库重建、模型或测试运行器。对应禁止调用测试已通过。

## 新增API与安全

- GET /api/evidence/findings：七项聚合证据、固定范围、来源/生成时间/SHA及报告配对状态。
- GET /api/evidence/findings/report：已验收Markdown原文件。
- GET /api/evidence/quality：当前只读SQL与安全投影后的历史证据。
- GET /api/evidence/quality/export?section=all|historical|tests：白名单聚合JSON下载，包含明确的来源与时间。

不接受任意SQL、表名或文件读取路径。报告/分析文件解析限制于项目内允许的reports/docs位置；越界/错配返回脱敏错误。P1运行清单只投影必要状态，不把数据库用户配置、连接串、source_path或用户级记录发给页面。XML只返回核对后的计数/时间/相对路径/SHA，不返回可能含堆栈的原日志。

现有/api/findings和四页接口契约保留。连接继续使用既有只读SQLAlchemy访问层；没有改P1指标、RFM/Cohort/P3模型或原始数据。

## 实际测试与浏览器验收

- 完整后端：**143 passed，0 failed，0 errors，0 skipped**，原129项继续通过，新增14项覆盖报告字节、七项结果、真实计数/约束、历史时间、错配/越界、缺失证据、脱敏和禁止自动重建。
- 完整前端：**20 passed，0 failed**，原13项继续通过，新增7项覆盖专题选择、优先展示不修改原对象、真实样本摘要、空证据与时间缺失不补造。
- TypeScript与Vite生产构建通过。新FindingsPage/Quality是独立动态代码入口；首页网络没有预取两个新页面代码块。
- 六页均通过实际导航、标题/面包屑、基线/数据加载检查；浏览器后退/前进正常。总览发现入口确实迁移到/findings，不再打开旧弹窗。
- 七项结果原文、专题过滤、证据展开、95%区间、九表、历史字段表筛选、客户表无缺失时空表提示与下载实际验证。
- 两页均在1440×1000及1280×900验证，29px标题、14px导航，0整页横向溢出，0 pageerror。必要的长表/证据内部滚动不扩展页面宽度。
- 发现空数组、两页503、质量当前DB不可用局部态及加载延迟采用浏览器拦截验证，恢复后使用真实API；未声称本阶段真实停库。质量缺失字段空结果则来自真实P0历史快照筛选。

## 真实截图

| 页面 | 1440首屏 | 1280首屏 | 1440完整页面 | 1280完整页面 |
|---|---|---|---|---|
| 经营发现 | [截图](screenshots/v2-03/findings-1440.png) | [截图](screenshots/v2-03/findings-1280.png) | [全页](screenshots/v2-03/findings-1440-full.png) | [全页](screenshots/v2-03/findings-1280-full.png) |
| 数据质量 | [截图](screenshots/v2-03/quality-1440.png) | [截图](screenshots/v2-03/quality-1280.png) | [全页](screenshots/v2-03/quality-1440-full.png) | [全页](screenshots/v2-03/quality-1280-full.png) |

另有[F05区间与样本证据](screenshots/v2-03/findings-association.png)、[历史审计与未知执行时间](screenshots/v2-03/quality-historical.png)，共10张实际页面截图。不是效果图或假数据。

## 运行方式与证据位置

实际运行：Windows11、Python3.12.10、PostgreSQL16.16、现有React/TypeScript/Vite/Tailwind/shadcn/ECharts/FastAPI技术栈；未新增依赖。使用Playwright CLI的Chrome频道（Chromium内核）检查本机生产构建预览。

生产预览：[经营发现](http://127.0.0.1:5174/findings)、[数据质量中心](http://127.0.0.1:5174/quality)。开发入口仍5173，API8000，旧版8501；没有公网部署。

```powershell
# 两个终端分别启动既有服务
powershell -NoProfile -ExecutionPolicy Bypass -File .\start-v2.ps1 -Action api
powershell -NoProfile -ExecutionPolicy Bypass -File .\start-v2.ps1 -Action web
# 构建与本机生产预览
npm --prefix frontend run build
npm --prefix frontend run preview -- --port 5174
# 自动测试
.\.venv\Scripts\python.exe -m pytest -q -rA --junitxml=reports/v2-03/pytest.xml
npm --prefix frontend test
```

| 证据 | 本地文件 |
|---|---|
| 全部后端测试 | reports/v2-03/pytest.log、pytest.xml |
| 新API测试 | reports/v2-03/api_tests.log、api_tests.xml |
| 前端测试/构建 | reports/v2-03/frontend_tests.log、build.log |
| 实际服务 | reports/v2-03/api.log、preview.log |
| 六页导航与完整交互 | reports/v2-03/browser.log；scripts/v203_browser_check.js |
| 两类实际下载 | reports/v2-03/downloaded_report.md、downloaded_quality.json |
| 数据/源码保护 | reports/v2-03/baseline.json、accepted_artifact_check.json、final_verification.json |
| 安全/清单 | reports/v2-03/public_safety.json、npm_audit.json、modified_files.json |

## 保护检查与已知限制

64个阶段前受保护源码/历史文档/冻结CSS/.env文件SHA-256未变；九表Raw与Mart内容指纹未变。另以P1已验收清单重核9个原始CSV及4个P0关键证据，共13个文件SHA一致；P3分析JSON也与P3验收时SHA一致。没有仅凭本阶段自建基线声称历史数据正确。

公开候选文件检查通过，原始CSV、.env/凭证、用户级导出、日志、node_modules/dist仍忽略；无远端、无推送、无部署，npm audit本次0已知漏洞。没有执行批量删除或覆盖既有报告。

范围限制：未验证手机、其他分辨率、Firefox/Safari、全新OS、公网身份认证/性能或生产并发。共享ECharts核心仍约534KB，构建有大包告警，未隐藏或宣称性能优化完成。历史审计缺少执行时间的问题保留为可见证据缺口，不能补造。页面文件配对/计数不是全量审计或当前输入模型重验。

六页模块交付完成，等待用户最终验收；在此停止，不进入V2-04。

## 本次文件修改清单

- `README.md`
- `api/README.md`
- `api/main.py`
- `frontend/src/App.tsx`
- `api/evidence.py`
- `frontend/src/evidence.ts`
- `frontend/src/evidence.css`
- `frontend/src/pages/FindingsPage.tsx`
- `frontend/src/pages/Quality.tsx`
- `frontend/tests/evidence.test.ts`
- `tests/test_v2_evidence.py`
- `scripts/v203_browser_check.js`
- `scripts/verify_v203.py`
- `scripts/write_v203_report.py`
- `docs/V2-03_ACCEPTANCE_REPORT.md`
- `docs/screenshots/v2-03/findings-1280-full.png`
- `docs/screenshots/v2-03/findings-1280.png`
- `docs/screenshots/v2-03/findings-1440-full.png`
- `docs/screenshots/v2-03/findings-1440.png`
- `docs/screenshots/v2-03/findings-association.png`
- `docs/screenshots/v2-03/quality-1280-full.png`
- `docs/screenshots/v2-03/quality-1280.png`
- `docs/screenshots/v2-03/quality-1440-full.png`
- `docs/screenshots/v2-03/quality-1440.png`
- `docs/screenshots/v2-03/quality-historical.png`

另有被Git忽略的reports/v2-03、output/playwright/v2-03运行材料；未删除旧版或原Findings弹窗文件。
