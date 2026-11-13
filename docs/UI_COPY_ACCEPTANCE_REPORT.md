# RetailScope 全站UI文案精简验收报告

生成时间：2026-11-13T17:42:29+08:00。**文案与交互技术检查通过，等待视觉验收。**

## 完成内容

统一删除重复来源行、自证式导航说明、开发阶段徽标与重复页脚许可；Olist/Kaggle来源、2016–2018历史样本、CC BY-NC-SA 4.0和非商业属性集中在侧边栏，质量详情保留数据版本。保留原有六页面、配色、字体、导航、图表、筛选和导出。

总览保留四KPI、已选范围、月度切换和趋势；交易/状态区别、两类数据日期与完整月条件收进“指标说明”和“月份与解读说明”，局部筛选仍默认标明全样本趋势不联动。用户页保留全样本标识及NA/0图例，RFM基准/分位规则、同月去重与观察窗口收进说明。商品和履约优先显示结果，跨类目订单去重、有效分母、缺失、订单均分与每单最新评分区别在展开说明保留。

经营发现默认显示短标题、从真实结果提取的关键摘要、一句业务解读和“查看分析依据”。7项完整结果原文、样本量、分母、日期、SQL标识、方法、局限、建议、原聚合统计JSON均在详情保留。F05均分和低评分口径、样本表、95%区间、整群Bootstrap次数/种子及非因果解释完整保留，展开后图表正常显示。没有新统计计算。

质量中心默认展示九表规模、当前/历史对照、历史审计与分析快照状态；缺失重复、关联、架构约束、构建对账、运行检查分组折叠。UI不再展示哈希、阶段编号、测试数量；运行详情仅显示状态/时间/来源，完整历史记录和哈希仍保留在原文件与JSON导出。审计执行时间未记录仍如实显示“未记录”，文件保存时间单列。

[全站修改前后对照](UI_COPY_BEFORE_AFTER.md)覆盖47项文案及迁移。旧阶段报告/截图未覆盖，原始修改前前端源码和逐文件diff保存在本地证据目录。

## 实际运行验收

本机Windows 11、Python3.12.10、PostgreSQL16.16。实际启动并访问FastAPI 8000及生产构建预览5174，使用Chromium浏览器逐页验证1440×1000、1280×900；没有把服务启动或测试通过当作浏览器验收。页面标题仍29px，12组页面尺寸均无水平溢出/KPI截断，默认可见文本不含阶段编号、哈希或测试通过数量。

- 六页直接URL、侧边栏及浏览器前进/后退实际通过。
- 总览日期草稿+SP地区点击得到BRL250,817.27，重置恢复BRL13,221,498.11。
- 商品/履约日期2017-05-10—2017-06-20、SP、beleza_saude得到BRL15,182.76 / 135订单；真实2020空结果、重置实际通过。
- 用户全样本93,358、6层、Cohort552单元/298 NULL不变；展开指标说明验证298计数。
- 7条发现逐项展开，完整result、method、limitations、suggestion与API原值逐项一致；F05区间[-2.0575,-1.9800]不变，展开图表宽度正确；专题筛选与Markdown下载通过。
- 质量9表当前/历史对照、未知执行时间和字段筛选空态通过，JSON下载通过。
- 六页受控503、延迟加载、重试恢复实际通过；未在此轮停库，V2-04真实停库记录保留。
- 4个CSV下载（总览、Cohort、商品、履约）与新SQL API逐字段对账；Markdown与原报告字节一致；JSON规模与历史来源一致。

## 数据及测试

| 核查 | 实际结果 |
|---|---|
| 完整Pytest | **144 passed / 0 failed / 0 errors / 0 skipped**，102.21秒 |
| 完整Vitest | **23 passed** |
| TypeScript | tsc -b exit 0 |
| Vite生产构建 | 成功 |
| 受保护源码/配置 | 33项Python/SQL/API/.env哈希未变 |
| 原始数据/仓库 | Raw/Mart行数及全表内容指纹与已验收V2-04一致 |
| P0原验收文件 | 13项原CSV/审计文件SHA与P1保存值一致 |
| 核心业务接口 | 总览、用户、商品、履约、7项发现五个完整响应与修改前逐值相同 |

KPI仍为96,478有效订单、93,358购买用户、商品金额BRL13,221,498.11、平均订单商品金额BRL137.04；RFM、Cohort和P3结果未更改。后端代码/API业务逻辑、SQL、数据库和统计模型没有改动。

前端曾有4个旧标题/边界句的文本断言失败，更新为精简后的文字期望后通过，保留原统计结果、来源和局部范围检查；新增1项摘要不改变原证据的回归（含缺证据兜底）。本轮未删除原统计测试。后端144项全部真实执行通过。

## 最新实际截图

| 页面 | 1440×1000 | 1280×900 | 修改前参考 |
|---|---|---|---|
| 经营总览 | [首屏](screenshots/ui-copy/overview-1440.png) / [全页](screenshots/ui-copy/overview-1440-full.png) | [首屏](screenshots/ui-copy/overview-1280.png) / [全页](screenshots/ui-copy/overview-1280-full.png) | [修改前](screenshots/v2-04/overview-1440-full.png) |
| 用户价值 | [首屏](screenshots/ui-copy/users-1440.png) / [全页](screenshots/ui-copy/users-1440-full.png) | [首屏](screenshots/ui-copy/users-1280.png) / [全页](screenshots/ui-copy/users-1280-full.png) | [修改前](screenshots/v2-04/users-1440-full.png) |
| 商品品类 | [首屏](screenshots/ui-copy/products-1440.png) / [全页](screenshots/ui-copy/products-1440-full.png) | [首屏](screenshots/ui-copy/products-1280.png) / [全页](screenshots/ui-copy/products-1280-full.png) | [修改前](screenshots/v2-04/products-1440-full.png) |
| 履约评价 | [首屏](screenshots/ui-copy/delivery-1440.png) / [全页](screenshots/ui-copy/delivery-1440-full.png) | [首屏](screenshots/ui-copy/delivery-1280.png) / [全页](screenshots/ui-copy/delivery-1280-full.png) | [修改前](screenshots/v2-04/delivery-1440-full.png) |
| 经营发现 | [首屏](screenshots/ui-copy/findings-1440.png) / [全页](screenshots/ui-copy/findings-1440-full.png) | [首屏](screenshots/ui-copy/findings-1280.png) / [全页](screenshots/ui-copy/findings-1280-full.png) | [修改前](screenshots/v2-04/findings-1440-full.png) |
| 数据质量 | [首屏](screenshots/ui-copy/quality-1440.png) / [全页](screenshots/ui-copy/quality-1440-full.png) | [首屏](screenshots/ui-copy/quality-1280.png) / [全页](screenshots/ui-copy/quality-1280-full.png) | [修改前](screenshots/v2-04/quality-1440-full.png) |

另见[F05展开依据](screenshots/ui-copy/findings-evidence.png)。25张PNG已逐张格式/尺寸verify，可由普通查看器打开；全页图按内容高度保存，浏览器原生滚动条可能使内容宽度少15px。首屏尺寸严格为1440×1000或1280×900。

## 日志与修改文件

本地`reports/ui-copy/`：`baseline.json`、`before/`、`frontend.diff`、`pytest.log/xml`、`frontend_tests.log`、`typecheck.log`（成功无输出）/`typecheck_result.json`、`build.log`、`browser.log`、`screens.log`、`verification.json/log`及实际下载文件。浏览器脚本`scripts/ui_copy_browser.js`、最终截图脚本`scripts/ui_copy_screens.js`、独立核查`scripts/verify_ui_copy.py`可复核执行动作。

修改：`frontend/src/App.tsx`、`AnalysisUI.tsx`、`presentation.ts`、`analysis.ts`、`evidence.ts`、`evidence.css`、`overview.css`、六个`pages/*.tsx`；`frontend/tests/presentation.test.ts`仅文案断言。
新增：`frontend/src/findingCopy.ts`、`frontend/tests/findingCopy.test.ts`、`scripts/ui_copy_browser.js`、`scripts/ui_copy_screens.js`、`scripts/verify_ui_copy.py`、`scripts/write_ui_copy_report.py`，本报告与对照表、`docs/screenshots/ui-copy/`最新截图。

CSS仅为原生详情正文补充既有字号/色值和间距，并修正总览删去重复说明后“已选范围”的对齐选择器，没有更改全局字体、颜色、图表配置与页面网格。没有删除文件、引入付费服务或新业务功能，没有推送GitHub或部署公网。

## 验证范围

本轮验证当前本机Chromium两种桌面尺寸及既有数据，未重做干净系统安装、移动端或公网负载验收。详情由用户点击展开；简化了默认展示，没有删除分析依据。最终视觉判断等待用户验收，完成后停止开发。
