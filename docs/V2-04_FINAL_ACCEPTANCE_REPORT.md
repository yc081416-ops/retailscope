# RetailScope V2-04 最终验收报告

生成：2026-11-13T17:12:47+08:00。**本阶段技术验收通过，等待用户最终验收；已停止业务开发。**

## 交付结论与范围

六个React页面真实可访问，默认KPI、RFM/Cohort和7项P3发现与已验收结果一致。完成两种桌面尺寸的真实浏览器交互、真实停库/恢复、下载对账和旧版Streamlit检查。项目具备本地简历展示、面试演示和整理为公开GitHub候选工程的条件；本次未推送、未创建远端、未部署公网。没有开发项目二或新增业务模块/统计模型。

本阶段仅修复F05展示术语，精简停用入口与未用注册，进行低风险图表分包和测试快照路径修正，更新展示材料。未重新设计颜色/字体/布局；三个冻结CSS哈希保持一致。

## 实际环境与启动

Windows 11（10.0.26200），Python 3.12.10，PostgreSQL 16.16（Docker），Node 24.15.0 / npm 11.12.1。当前锁定依赖：React 19.3.1、Vite 8.3.8、TypeScript 7.0.2、ECharts 6.1.0、Vitest 5.1、FastAPI 0.162.5。

在工程根目录执行（初次安装流程见主README，本阶段未重新入库）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start.ps1 -Action start -NoServe
# 独立终端
powershell -NoProfile -ExecutionPolicy Bypass -File .\start-v2.ps1 -Action api
# 构建后另开终端
npm --prefix frontend run build
npm --prefix frontend run preview -- --port 5174
```

演示地址 http://127.0.0.1:5174，API http://127.0.0.1:8000，旧版 http://127.0.0.1:8501。本阶段真实浏览器检查使用生产构建的Vite preview及Chromium引擎，API/预览仅监听本机；preview用于本地演示，未声称生产托管。原.env密码未改动。

## 数据及统计基线保护

| 核查 | 实际结果 |
|---|---:|
| 九张Raw总记录 | 1,550,922 |
| 全状态订单 | 99,441 |
| 有效delivered订单 | 96,478 |
| 唯一购买用户 | 93,358 |
| 商品成交额（不含运费） | BRL 13,221,498.11 |
| 平均订单商品金额（展示） | BRL 137.04 |
| 复购用户/复购率 | 2,801 / 3.0003% |
| 平均配送天数/逾期率 | 12.56 / 6.7731% |
| 订单等权评价均分（展示） | 4.16 |
| RFM层数/人数 | 6 / 93,358 |
| Cohort单元/未观察NULL | 552 / 298 |

原始CSV和P0关键审计文件13项重新与P1保存的原验收SHA核对一致；Raw/Mart全表行数及内容指纹与阶段开始一致。43项统计源码、SQL、原验收报告、指标文档、密码配置和冻结CSS哈希未变。P3分析JSON与原验收SHA一致，7项发现逐项匹配；完整Pytest同时复核独立Pandas对账、RFM、Cohort及统计区间。未重建Raw/Core/Mart、未运行新统计方法。

完整原始表数：customers 99,441；geolocation 1,000,163；order_items 112,650；order_payments 103,886；order_reviews 99,224；orders 99,441；products 32,951；sellers 3,095；category_translation 71。当前SQL与P0审计分别标明来源。

## F05术语纠正与数值不变

V2-03发现页表头曾将均分误标为“最新评分均值”。现在为“订单评价均分（订单等权）”，解释为**先在订单内平均，再对订单等权**；不是把每单最新评分拿来平均。低评分比例仍使用每单latest_review_score≤2，统计方法和数值未变。

| 分组 | 有效评价订单 | 订单等权均分 | 最新评分≤2订单 | 低评分率 |
|---|---:|---:|---:|---:|
| 未逾期 | 89,443 | 4.2905891648 | 8,289 | 9.2674% |
| 逾期 | 6,381 | 2.2718225983 | 3,983 | 62.4197% |

比较95,824单，相对96,478有效订单排除654单（缺失日期/评分等分组条件按原P3保留）。均分差“逾期−未逾期”=-2.0187665664；唯一用户整群Bootstrap 2000次、种子20261113，95%区间[-2.0575024182,-1.9800231077]。低评分率差的95%区间为[51.9890,54.3643]个百分点。是历史统计关联，不能解释为因果效应。

新增独立真实SQL回归证明均分等于AVG(review_mean)，并与AVG(latest_review_score)区分（未逾期后者4.2903860559、逾期2.2704905187），同时复核低评分分子/分母。已检查新版发现、履约页、图表Tooltip及求职文案；保留历史验收报告原文以供追溯。

## 真实浏览器与视觉验收

1440×1000和1280×900各逐页检查六页面。商品月度/件数订单图例原先漏注册，现已恢复并实际点击验证。所有页面标题29px，未出现页面横向溢出或KPI截断；图表SVG均有真实数据：总览2、用户4、商品4、履约4、发现1；质量页以证据表格为主。实际悬停五个含图表页面，读取真实Tooltip文本，并保存局部截图。保持现有紫色/青色、文字层级、导航与组件间距，未发现需要大规模视觉修改的问题。

| 验收动作 | 本次结果/范围 |
|---|---|
| 六页直达URL、导航、前进/后退 | 全部实际通过，不依赖首页跳转 |
| 日期/州/类目及应用 | 商品、履约使用2017-05-10—06-20 / SP / beleza_saude；商品金额15,182.76、142明细、跨类目去重135订单；履约范围135订单 |
| 草稿与地区点击 | 总览保留待应用日期并使用该日期点击SP，金额250,817.27；重置回到全样本 |
| 空数据与重置 | 总览/商品/履约使用2020年真实SQL空结果；没有模拟业务数据 |
| RFM/Cohort | 全样本标签明确，6层/93,358用户；298个NA不补0，NULL与真实0有视觉区分 |
| 经营发现 | 7条result与P3逐项相同；专题筛选、展开证据、F05样本/均分/CI均实际检查 |
| 数据质量 | 9表当前SQL、P0历史审计、构建及测试来源区分；展开目录/约束；P0审计时间缺失保持未知 |
| CSV | 总览月度、Cohort、商品类目、履约两组共4个浏览器下载与新API查询逐单元对账；包含实际scope |
| Markdown | 实际下载与已生成P3报告逐字节一致，不重新生成结论 |
| JSON | 质量导出9表合计1,550,922，与P0缺失/重复审计及144项测试记录一致 |
| 加载/错误 | 六页拦截503、延迟响应验证加载和恢复，错误时不保留旧KPI；这是受控网络状态测试 |
| 真实DB异常 | 实际stop容器→首页HTTP503/中文重连/隐藏旧KPI；质量历史保留、当前不可用不伪造0；compose up --wait后重试恢复基线 |
| 旧版Streamlit | 真实浏览器3个Plotly图，4个KPI与基线相符、0异常；原六页AppTest在完整测试内通过 |

浏览器日志：`reports/v2-04/browser.log`、`tooltips.log`、`legend.log`、`extra_interactions.log`、`db_failure.log`、`db_recovery.log`、`legacy_browser.log`；运行脚本在`scripts/v204_*.js`。实际DB停止/恢复日志为`db_stop.log`、`db_restart.log`。浏览器断言是运行结果，不把启动服务当作页面通过。

## 最终截图

| 页面 | 1440×1000首屏 / 全页 | 1280×900首屏 / 全页 |
|---|---|---|
| 经营总览 | [overview-1440.png](screenshots/v2-04/overview-1440.png) / [全页](screenshots/v2-04/overview-1440-full.png) | [overview-1280.png](screenshots/v2-04/overview-1280.png) / [全页](screenshots/v2-04/overview-1280-full.png) |
| 用户价值 | [users-1440.png](screenshots/v2-04/users-1440.png) / [全页](screenshots/v2-04/users-1440-full.png) | [users-1280.png](screenshots/v2-04/users-1280.png) / [全页](screenshots/v2-04/users-1280-full.png) |
| 商品品类 | [products-1440.png](screenshots/v2-04/products-1440.png) / [全页](screenshots/v2-04/products-1440-full.png) | [products-1280.png](screenshots/v2-04/products-1280.png) / [全页](screenshots/v2-04/products-1280-full.png) |
| 履约评价 | [delivery-1440.png](screenshots/v2-04/delivery-1440.png) / [全页](screenshots/v2-04/delivery-1440-full.png) | [delivery-1280.png](screenshots/v2-04/delivery-1280.png) / [全页](screenshots/v2-04/delivery-1280-full.png) |
| 经营发现 | [findings-1440.png](screenshots/v2-04/findings-1440.png) / [全页](screenshots/v2-04/findings-1440-full.png) | [findings-1280.png](screenshots/v2-04/findings-1280.png) / [全页](screenshots/v2-04/findings-1280-full.png) |
| 数据质量 | [quality-1440.png](screenshots/v2-04/quality-1440.png) / [全页](screenshots/v2-04/quality-1440-full.png) | [quality-1280.png](screenshots/v2-04/quality-1280.png) / [全页](screenshots/v2-04/quality-1280-full.png) |

另有[RFM/Cohort热力图](screenshots/v2-04/users-cohort.png)与[F05样本/置信区间](screenshots/v2-04/findings-association.png)。共26张最终PNG，Pillow逐张verify通过，可由普通图片查看器打开；全页截图按浏览器可滚动内容高度保存，原生滚动条可能使全页内容宽度比viewport少15px，首屏尺寸严格为1440×1000或1280×900。完整像素尺寸见本地`final_verification.json`。悬停、停库等调试截图另放`output/playwright/v2-04`，不当成正式展示图。

## 性能与工程取舍

原来已使用ECharts core按需注册，本阶段仅去掉没有调用的MarkPoint注册，补齐原本漏注册的LegendComponent以恢复配置的图例与点击切换，并用独立zrender chunk分离渲染器，保持6页动态导入。最大JS chunk由533,691字节降至363,472字节，渲染器独立约182KB；全部JS总量由911,700变为923,732字节。构建未提高告警阈值，当前无500KB大包告警。首页网络资源不提前加载其他5页模块，全部图表/Tooltip实际回归。

这是包结构优化，不声称LCP、网络加载时间或并发性能提升。配置依据[Vite构建说明](https://vite.dev/guide/build)及[Rolldown codeSplitting](https://rolldown.rs/reference/OutputOptions.codeSplitting)，不引入无必要依赖或手工重写图表。前后体积含gzip在`performance_before.json`/`performance_after.json`。

删除已不再引用的旧发现弹窗入口`frontend/src/Findings.tsx`（先备份至`reports/v2-04/before/Findings.tsx`），移除总览无用图标import；单独删除根目录0字节临时文件`({engine`。没有批量删除，未删除Streamlit/历史报告。保留未影响使用的兼容样式，不为消除少量冗余冒险重构。

测试fixture沿用应用active.json选择活动P3快照，约束路径在reports内；不通过改统计期望值掩盖数据差异。质量页新增读取本阶段真实pytest XML，未更改业务SQL/API统计逻辑。

## 自动测试及日志

| 实际执行 | 结果 | 本地日志 |
|---|---|---|
| 完整Pytest（含P0–P4及V2） | **144 passed / 0 failed / 0 errors / 0 skipped**，94.89秒 | `reports/v2-04/pytest.log`、`pytest.xml` |
| Vitest | **22 passed** | `frontend_tests.log` |
| TypeScript tsc -b | exit 0 | `typecheck.log`（成功无输出）、`typecheck_result.json` |
| Vite生产构建 | 成功，无大包告警 | `build.log` |
| npm audit | 0已报告漏洞 | `npm_audit.json` |
| 最终只读综合核查 | passed=true | `final_verification.log/json` |

此前V2-03的143项后端/20项前端均保留；本阶段新增1项真实SQL术语/分母回归、1项活动快照路径边界测试和1项真实ECharts图例注册/切换回归。测试日志仍含先前正常历史阶段记录，最终数量以本阶段XML为准。TypeScript曾使用错误npm exec命令仅显示帮助；已改为明确项目路径的tsc -b并真实通过，没有将该无效调用计为通过。

## 求职材料与文件清单

- [README](../README.md)：React/FastAPI为主、架构、规模/许可、六页截图、首装/日常/停止/更新、测试与限制。
- [简历](RESUME_PROJECT.md)：一页三条、分析/运营/商业分析版本及可量化证据。
- [面试问答](INTERVIEW_GUIDE.md)：34问，覆盖SQL/仓库/清洗/RFM/Cohort/Bootstrap/因果/Python/可视化/React/API/工程边界。
- [演示脚本](DEMO_SCRIPT.md)：约4分钟，含录制步骤与故障预案；未交付或声称已生成视频。
- [架构](ARCHITECTURE.md)：新增新版架构，旧版结构作为历史保留。
- [完整公开候选工程清单](V2_FINAL_FILE_MANIFEST.md)：列出实际Git候选文件；本地结构化SHA清单`reports/v2-04/final_project_manifest.json`。

本阶段修改：README、上述4份作品文档；`frontend/src/Chart.tsx`、`frontend/src/pages/Overview.tsx`（仅未用import）、`frontend/src/pages/FindingsPage.tsx`、`frontend/vite.config.ts`、`api/evidence.py`；`tests/test_p4.py`、`tests/test_v2_api.py`、`frontend/tests/presentation.test.ts`、`frontend/tests/evidence.test.ts`。

新增：`tests/test_v2_final.py`、`frontend/tests/p3Evidence.ts`、`frontend/tests/fixturePaths.test.ts`、`frontend/tests/chartRegistration.test.ts`，`scripts/v204_browser_check.js`、`v204_tooltips.js`、`v204_legend_check.js`、`v204_extra_interactions.js`、`v204_db_failure.js`、`v204_db_recovery.js`、`verify_v204.py`、`write_v204_materials.py`、`write_v204_report.py`，本报告/工程清单及26张最终截图。删除两项为上节明确路径文件。运行证据、备份、导出均在被忽略的reports/output目录，不作为公开数据包。

## 公开安全与未验证范围

实际Git候选扫描通过，.env/密码与连接串、原CSV、用户级临时导出、备份/卷、虚拟环境、node_modules/dist及日志未进入候选；无staged文件、无远端、无推送/部署。扫描包括本机真实秘密匹配和常见密钥模式，但不是所有秘密类型的数学保证。最终候选清单/许可证仍由作者公开前审阅；Olist/Kaggle版本2及CC BY-NC-SA 4.0署名、非商业、相同方式共享见README/DATA_LICENSE，原创代码许可由作者确定。

本阶段在**现有同一Windows主机**回归V2，不声称另一台干净电脑首装。P4已验收的同主机新venv/新空库全流水线复现保留，未在此阶段重复导入或重建；不覆盖原数据/报告。未验证公网鉴权、多用户负载、生产部署、所有浏览器/移动端或全新系统安装，没有实际企业使用/增长收益，未制作视频。历史观察窗口、缺失、混杂和低复购结构等统计限制继续保留。

数据库已恢复，API/新版预览及旧版可本地演示。**等待最终验收，未进入后续开发。**
