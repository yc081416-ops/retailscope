# RetailScope P2 验收报告

生成时间：2026-11-13T12:30:24+08:00。**P2已实际完成并通过本地技术验收，等待用户验收。**

## 范围与环境

复用P1 PostgreSQL 16.16及现有core/mart。没有重建数据库、修改指标SQL或生成模拟业务数据。
Python 3.12.10；Streamlit 1.67.0；Plotly 6.9.0；SQLAlchemy 2.1.8；Pandas 2.3.3；Pytest 9.2.0。
浏览器通过已安装的Node.js/npx运行Playwright CLI，使用真实Chromium界面；不是仅以AppTest或HTTP健康检查替代浏览器验收。
P0/P1受保护文件哈希不变=True；raw九表指纹不变=True；P1的27个mart对象内容哈希不变=True。对比基线保存在reports/p2/baseline.json。

## 六页交付及真实浏览器验证

| 页面 | 实际图表数 | 页面异常 | 横向页面溢出 |
|---|---:|---|---|
| 经营总览 | 3 | 0 | False |
| 用户价值分析 | 5 | 0 | False |
| 商品与品类分析 | 5 | 0 | False |
| 履约与评价分析 | 4 | 0 | False |
| 经营发现 | 0 | 0 | False |
| 数据质量中心 | 0 | 0 | False |

共17张真实业务图表；经营发现展示P1已验收的8项事实并标明来源和观察期；质量中心展示数据库实时九表行数和清楚标注的历史审计快照。
主界面为浅色蓝系、统一Plotly样式；已实际检查1440×1000及1280×900桌面截图，长金额完整可见。长页使用浏览器正常滚动，截图分别保留顶部及Cohort区域。

## 默认KPI与P1逐项对账

| 指标 | 真实SQL结果/展示值 | 结果 |
|---|---|---|
| 有效订单 | 96,478 | 与P1一致 |
| 唯一购买用户 | 93,358 | 与P1一致 |
| 商品成交额 | BRL 13,221,498.11 | 精确到分一致 |
| 平均订单商品金额 | BRL 137.04 | 原始精度及展示值一致 |
| 整体复购率 | 3.0003% | 实际查询mart.repurchase_summary并对账 |
| 平均配送天数 | 12.56 | 与P1一致 |
| 逾期率 | 6.7731% | 与P1一致 |
| 订单等权评价均分 | 4.16 | 与P1一致 |

上述数值仅作验收基线，没有硬编码进正式页面；数据来自SQLAlchemy参数化SQL或P1固定视图。

## 筛选、导出和边界实测

- 总览日期/州筛选，商品及履约日期/州/类目筛选。程序测试用独立SQL对照2018-01及SP/RJ/MG、单类目和多类目组合，并验证同页金额、订单、配送及评价汇总一致。
- 浏览器实际选择SP和beleza_saude，商品金额BRL 453,916.48、4,125件、3,715个有效订单、运费BRL 56,338.90。实际下载category_ranking.csv，与同筛选SQL逐字段、逐金额对账通过。
- 浏览器使用可访问日期字段键盘编辑，选择2018-01-01至2018-01-31；点击控件外确认后页面更新。全州/全类目商品金额BRL 924,645.00、8,037件、7,069单、运费BRL 153,242.46，与SQL一致。
- 浏览器实际点击清空筛选，恢复全样本金额；AppTest另验证日期单端输入提示、2018-10-17无有效订单提示，以及页面间筛选隔离。
- RFM六个非空分层的人数、金额、占比完全复用P1；Frequency大量为1、F评分2–4空档有明确说明。用户分析无局部筛选控件，不能产生虚假联动。
- 浏览器读取实际渲染的Plotly Heatmap，确认298个不可观察单元保留NULL；AppTest检查类别轴及全部NULL数量，导出NA数量也与SQL一致。0只表示完整观察无回购。
- 配送/评价按订单粒度；类目订单筛选使用EXISTS，商品页只统计选中类目的明细。未直接连接一对多支付、评价或原始地理表；跨类目订单不能相加有醒目提示。
- 总览月度数据与P1观察范围对齐；不完整月和局部日期窗口标记橙色，不计算增长率。

## 异常处理的实际证据

单独启动8502端口的临时实例，连接本机不可用端口，真实触发数据库连接失败。浏览器显示中文提示及“重新连接”，不展示密码、连接串或异常堆栈；截图09及failure-browser.log保留证据。正式数据库与8501实例未被停止或改配置。
查询层采用PostgreSQL只读会话，连接超时5秒、SQL超时20秒；未知查询名被拒绝；绑定参数注入测试返回空结果，mart仍完整。日志仅记录查询名、行数、耗时和异常类型。

## 自动测试

实际运行结果：**64通过、0失败、0错误、0跳过**。含原P0/P1的44项及新增P2的20项。最终测试无warnings汇总。
覆盖默认所有KPI、固定RFM/Cohort、独立筛选SQL、同页图表对账、空结果、缓存筛选隔离、只读连接、查询白名单与参数绑定、CSV金额/NA、六页渲染、清空/不完整日期和中文故障提示。

## 实际执行命令与日志

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/Home.py
.\.venv\Scripts\python.exe -m pytest -q -rA --junitxml=reports/p2/pytest.xml
npx.cmd --yes --package @playwright/cli playwright-cli -s=retailscope open http://127.0.0.1:8501 --headed
npx.cmd --yes --package @playwright/cli playwright-cli -s=retailscope run-code --filename scripts/p2_browser_check.js
# 日期脚本从商品页运行，固定验证2018-01（不写内部session状态）：
npx.cmd --yes --package @playwright/cli playwright-cli -s=retailscope run-code --filename scripts/p2_date_check.js
.\.venv\Scripts\python.exe scripts/verify_p2.py
.\.venv\Scripts\python.exe scripts/write_p2_report.py
```

- reports/p2/streamlit.stdout.log、streamlit.stderr.log：实际服务运行日志。
- reports/p2/queries.log：SQL白名单查询行数/耗时/失败类型。
- reports/p2/pytest.log、pytest.xml：完整自动测试。
- reports/p2/browser.log、browser-date.log、browser-download.log：实际浏览器与下载记录。
- reports/p2/failure-browser.log、failure-server.stderr.log：独立真实故障检查。
- reports/p2/acceptance.json、baseline.json、final_verification.log：基线、验收结果和P0/P1保护检查。

## 页面截图

截图位于output/playwright，以下均为实际运行截图，不是设计稿。

- [01-overview.png](../output/playwright/01-overview.png)
- [02-cohort.png](../output/playwright/02-cohort.png)
- [02-users.png](../output/playwright/02-users.png)
- [03-products.png](../output/playwright/03-products.png)
- [04-delivery.png](../output/playwright/04-delivery.png)
- [05-findings.png](../output/playwright/05-findings.png)
- [06-quality.png](../output/playwright/06-quality.png)
- [07-filtered-products.png](../output/playwright/07-filtered-products.png)
- [08-desktop-1280.png](../output/playwright/08-desktop-1280.png)
- [09-database-unavailable.png](../output/playwright/09-database-unavailable.png)
- [10-date-filter.png](../output/playwright/10-date-filter.png)

## 修改文件清单

- app/Home.py；app/pages/overview.py、users.py、products.py、delivery.py、findings.py、quality.py。
- src/retailscope/bi/__init__.py、data.py、components.py。
- .streamlit/config.toml；.gitignore（仅增加Playwright本地缓存排除）；README.md。
- tests/test_p2.py。
- scripts/p2_browser_check.js、p2_date_check.js、verify_p2.py、write_p2_report.py。
- docs/P2_UI_SPEC.md；本报告。
- reports/p2与output/playwright为本地运行证据，不写入P0/P1报告目录，不提交原始CSV或敏感配置。

## 已知问题与范围限制

- 无阻塞验收的问题。直接进入子页面URL时，当前Streamlit版本会先尝试子路径下的health/host-config，记录404后自动回退根路径并正常加载；浏览器日志如实保留。侧栏导航及业务查询正常，没有隐藏这些请求记录。
- 缓存最多120秒；数据质量中的缺失/重复/关联细节是已验收审计快照，界面已标注；数据库九表行数与mart异常为当前查询结果。
- P1数据本身的缺失、地理重复、首尾观察不完整等限制继续保留；没有改统计模型，也没有声称因果或未来增长。
- 本次已做Windows本地桌面浏览器验收；手机适配、公开托管、并发压测属于后续交付范围，未将其声称为通过。

**P2完成后已停止开发，等待用户验收；未进入P3/P4。**
