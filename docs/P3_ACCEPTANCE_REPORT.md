# RetailScope P2.1 + P3 验收报告

验收时间：2026-11-13T12:55:49.130610+08:00。**P2.1界面修复及P3统计诊断已实际完成，等待用户验收；未进入P4。**

## 环境与保护检查

Windows 11 / Python 3.12.10 / PostgreSQL 16.16；SciPy 1.18.1、Pandas 2.3.3、Streamlit 1.67.0、Plotly 6.9.0、SQLAlchemy 2.1.8。SciPy已实际安装并加入pyproject依赖。
95个既有SQL、文档、测试及验收证据文件SHA-256不变；raw九表指纹不变=True，P1全部27个mart对象的行数与内容SHA-256不变=True。
P0/P1原始数据、指标定义、建模SQL和验收报告均未修改。P2的已验收报告与证据保留，新证据单独写入reports/p3和output/playwright/p3。P3只读现有仓库。

## P2.1 修复结果

浏览器实测金额轴范围[0, 1106297.2144000002]，订单轴范围[0, 8163.680000000001]；两轴都从0开始，订单标签用整数格式。
保留原双轴业务图及SQL数据，调整坐标字体、辅助文字对比度、筛选/KPI间距；清空筛选与控件同排，中文占位提示“请选择（留空为全部）”。没有修改筛选边界、颜色风格或指标。
优化后的总览截图：output/playwright/p3/00-p21-overview.png；最终总览：01-overview.png，1280桌面：10-desktop-1280.png。

## 真实统计范围与结果

固定有效购买范围：2016-09-15至2018-08-29；完整目标月[2016-10-01, 2018-08-01)。
核心基线：96,478有效订单、93,358唯一购买用户、商品金额BRL 13,221,498.11；所有P1指标均经测试逐字段对账。

### F01 完整月商品金额与订单变化

2018-07 商品金额 BRL 867,953.46，环比 +1.39%；有效订单 6,159 单，环比 +0.98%。
来源：P3_MONTHLY；完整方法、样本、分母、范围、解释边界及待验证建议见业务报告对应条目。

### F02 稳健异常月份回顾筛查

金额/订单对数环比筛查共标记 1 个月：2017-02。
来源：P3_MONTHLY；完整方法、样本、分母、范围、解释边界及待验证建议见业务报告对应条目。

### F03 商品类目贡献集中度

TOP5 类目贡献 39.83%，TOP10 贡献 62.43%；HHI=0.0489（万分制 489.48）；18 个类目覆盖80%商品金额。
来源：P3_CATEGORIES；完整方法、样本、分母、范围、解释边界及待验证建议见业务报告对应条目。

### F04 地区规模与履约的联合观察

SP 有效订单 40,501 单，商品金额 BRL 5,067,633.16；平均配送 8.76 天，逾期率 4.49%。3 个州少于100单，已标注小样本。
来源：P3_REGIONS；完整方法、样本、分母、范围、解释边界及待验证建议见业务报告对应条目。

### F05 逾期与评价存在描述性差异

逾期 6,381 单均分 2.2718，未逾期 89,443 单均分 4.2906；差值（逾期−未逾期）-2.0188 分，用户聚类95%区间 [-2.0575, -1.9800]。低评分率分别 62.42% 与 9.27%，差值95%区间 [51.99, 54.36] 个百分点。
来源：P3_ASSOCIATION；完整方法、样本、分母、范围、解释边界及待验证建议见业务报告对应条目。

### F06 一次购买用户占多数，复购结构需结合窗口解读

一次购买用户 90,557 人，占 96.9997%；复购用户 2,801 人，累计商品金额 BRL 728,408.75，占全部用户金额 5.51%。
来源：P3_RFM_USERS；完整方法、样本、分母、范围、解释边界及待验证建议见业务报告对应条目。

### F07 留存分析必须保留不可观察月份

20 个非左截断cohort具备完整次月观察，其M1回购活跃人数 390 / 首购用户 81,264，加权留存为 0.4799%；298 个cohort/月龄单元不可观察，仍为NULL。
来源：P3_COHORT；完整方法、样本、分母、范围、解释边界及待验证建议见业务报告对应条目。

## 配送与评价的区间及使用条件

| 分组 | 实际订单n | 用户数 | 订单评价均分 | 低评分人数 | 低评分比例 |
|---|---:|---:|---:|---:|---:|
| 未逾期 | 89443 | 86662 | 4.290589 | 8289 | 9.2674% |
| 逾期 | 6381 | 6346 | 2.271823 | 3983 | 62.4197% |

有效对照订单95,824单，排除654单；其中无有效逾期判断8、缺评价646、缺唯一用户0。逐项缺失可重叠，排除总数以并集为准。
检查结果：{"one_order_one_row": true, "score_within_1_5": true, "both_groups_at_least_30": true, "largest_user_cluster": 15, "users_in_both_groups": 261}。最大用户聚类15单，同用户跨两组的关系由用户整群抽样保留。
主区间：92,747个唯一用户聚类、2000次bootstrap、种子20261113；均分差-2.018767，95%区间[-2.057502, -1.980023]；低评分比例差95%区间[51.9890, 54.3643]个百分点。
工作独立近似对照：Welch均分差95%区间[-2.058048220059342, -1.9794849128509513]；Newcombe比例差95%区间[0.5194155324660802, 0.543477946673163]（比例0–1尺度）。
直接SciPy订单数组核对Welch摘要公式；二项score数值反演核对Wilson，包括零/全成功边界；独立展开重采样用户的全部订单核对聚类bootstrap。相同输入和固定种子重复计算得到相同主区间。
不依赖p值作商业判断；这些是条件于历史样本的观察性关联。用户内相关得到处理，但用户间/商户/线路/时间相关、混杂与评价缺失仍可能影响解释。

## 页面、导出与视觉验收

| 页面 | 实际图表数 | 页面异常 | 横向页面溢出 |
|---|---:|---:|---|
| 经营总览 | 3 | 0 | False |
| 用户价值分析 | 5 | 0 | False |
| 商品与品类分析 | 5 | 0 | False |
| 履约与评价分析 | 4 | 0 | False |
| 经营发现 | 3 | 0 | False |
| 数据质量中心 | 0 | 0 | False |

“经营发现”现含7条代码生成的P3核心发现、完整月趋势、集中度/地区表、配送/评价区间和用户结构明细；原P1八项事实在下方保留。每条P3发现均带SQL来源、范围、样本与分母、方法、局限和待验证建议。
实际浏览器下载文件RetailScope_P3_BUSINESS_REPORT.md与docs/P3_BUSINESS_REPORT.md及同一结构化结果生成的Markdown逐字一致=True。
所有六页均在真实Chromium中打开并截图；还检查了诊断展开、统计明细、报告下载、双轴零起点、中文筛选占位及1280/1440桌面。截图是实际页面，不是设计稿。

## 自动测试与执行证据

**78通过，0失败，0错误，0跳过，无最终warnings汇总。** 其中原P0/P1/P2的64项全部继续通过，P3新增14项。
覆盖基线、SQL样本量、精确金额/增长分母、集中度、独立CI、相同种子重现、小样本/缺失/空结果、MAD=0、不完整月份、Cohort分母、报告生成一致性与UI零起点/下载。

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe scripts/run_p3.py
.\.venv\Scripts\python.exe -m pytest -q -rA --junitxml=reports/p3/pytest.xml
.\.venv\Scripts\python.exe -m streamlit run app/Home.py
npx.cmd --yes --package @playwright/cli playwright-cli -s=p3 open http://127.0.0.1:8501 --headed
npx.cmd --yes --package @playwright/cli playwright-cli -s=p3 run-code --filename scripts/p3_browser_check.js
.\.venv\Scripts\python.exe scripts/verify_p3.py
.\.venv\Scripts\python.exe scripts/write_p3_report.py
```

- reports/p3/analysis.json：结构化结果、配置、SQL与输入SHA-256、所有发现及统计量。
- reports/p3/sql_results/*.csv、monthly_diagnostics.csv：真实SQL输入与月度计算结果。
- reports/p3/analysis_run_final.log、pytest.log、pytest.xml：实际计算与测试日志。
- reports/p3/p21_browser.log、browser.log、streamlit.log：P2.1和P3真实页面证据及服务日志。
- reports/p3/baseline.json、verification.json、verification.log：旧成果保护、重复区间、浏览器导出对账。
- docs/P3_ANALYSIS_METHODS.md：方法、条件、阈值、独立验证与文献来源。
- docs/P3_BUSINESS_REPORT.md：可导出的完整经营分析报告。

## 六页截图与补充截图

- [output\playwright\p3\00-p21-overview.png](../output\playwright\p3\00-p21-overview.png)
- [output\playwright\p3\01-overview.png](../output\playwright\p3\01-overview.png)
- [output\playwright\p3\02-users.png](../output\playwright\p3\02-users.png)
- [output\playwright\p3\03-products.png](../output\playwright\p3\03-products.png)
- [output\playwright\p3\04-delivery.png](../output\playwright\p3\04-delivery.png)
- [output\playwright\p3\05-findings.png](../output\playwright\p3\05-findings.png)
- [output\playwright\p3\06-quality.png](../output\playwright\p3\06-quality.png)
- [output\playwright\p3\07-association-finding.png](../output\playwright\p3\07-association-finding.png)
- [output\playwright\p3\08-statistical-details.png](../output\playwright\p3\08-statistical-details.png)
- [output\playwright\p3\09-trend-diagnostics.png](../output\playwright\p3\09-trend-diagnostics.png)
- [output\playwright\p3\10-desktop-1280.png](../output\playwright\p3\10-desktop-1280.png)

## 修改文件清单

- P2.1：app/Home.py、app/pages/overview.py、src/retailscope/bi/components.py。
- P3界面：app/pages/findings.py、src/retailscope/bi/diagnostic_page.py。
- 计算：src/retailscope/diagnostics.py；sql/p3/context.sql、kpis.sql、monthly.sql、categories.sql、regions.sql、association_orders.sql、rfm_users.sql、cohort.sql。
- 执行与验收：scripts/run_p3.py、p3_browser_check.js、verify_p3.py、write_p3_report.py；tests/test_p3.py。
- 依赖/文档：pyproject.toml、README.md、docs/P3_ACCEPTANCE_REPORT.md、P3_ANALYSIS_METHODS.md、P3_BUSINESS_REPORT.md。
- 原P0/P1数据/统计SQL/报告、既有P2报告与旧测试文件均未修改；没有执行文件批量删除或公开提交原始CSV与凭证。

## 已知限制与后续边界

无未解决的运行阻塞。早期样本覆盖稀疏、首尾月份不完整；完整日历月不等于有完整市场覆盖。MAD仅历史回顾提示，阈值有方法选择空间；没有季节控制或未来预测。
置信区间依赖抽样/独立聚类近似，不修复选择偏差或混杂；评价为有序量，分差不等同于效用差。RFM组与复购组金额差异部分来自定义及观察机会不同，建议需要未来试验验证。
统计结果为离线生成的固定快照。若以后重建仓库，应重新运行P3计算和测试，再刷新页面；本轮没有修改P1口径。P4部署、最终打包和求职材料均未开发。

**完成P3后已停止开发，等待用户验收。**
