"""Emit the visual-refinement acceptance report after executed checks reconcile."""
from datetime import datetime
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/v2-01-1'


def main():
    result=json.loads((OUT/'final_verification.json').read_text(encoding='utf-8'))
    assert result['passed']
    modified=['frontend/src/App.tsx','frontend/src/main.tsx','frontend/src/Chart.tsx',
        'frontend/src/charts.ts','frontend/package.json','frontend/package-lock.json']
    added=['frontend/src/overview.css','frontend/src/presentation.ts','frontend/tests/presentation.test.ts',
        'scripts/v211_browser_check.js','scripts/verify_v211.py','scripts/write_v211_report.py',
        'docs/V2-01-1_DESIGN_CHANGES.md','docs/V2-01-1_ACCEPTANCE_REPORT.md',
        *sorted('docs/screenshots/v2-01-1/'+name for name in result['screenshots'])]
    changes={'modified':modified,'added':added,
        'local_ignored':['reports/v2-01-1/','output/playwright/v2-01-1/'],
        'unchanged':'API、SQL、src统计代码、原始数据、mart、.env、P0–P4和V2-01历史文档及截图；旧workbench.css保留但不再导入'}
    (OUT/'modified_files.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
    files='\n'.join('- `'+p+'`' for p in modified+added)
    report=f'''# RetailScope V2-01.1 经营总览精修验收报告

日期：{datetime.now():%Y-%m-%d}。已完成本阶段视觉、信息架构及必要交互，工程验证通过，等待用户视觉验收；不将技术验证等同于用户最终认可。仅经营总览，没有进入V2-02、推送GitHub或公网部署。

## 设计修改

详细前后对照：[V2-01-1_DESIGN_CHANGES.md](V2-01-1_DESIGN_CHANGES.md)。

- 标题29px，正文/主导航14px，辅助12px，重要说明13px；KPI数字30px，1280宽27px；BRL前缀统一14px，四列基线对齐，金额小数精度保持。
- 白色背景、低饱和紫与青色保留。普通次文字提高对比度；浏览器读取正文次文字#565D69，对白底约6.63:1，超过4.5:1。未声称完成覆盖每个交互状态的正式WCAG认证。
- 移除虚拟RS头像、R工作区装饰、Logo版本号和正式侧栏旧版入口。保留六模块导航结构，总览与P3已验收发现可用，另四模块显式disabled/待开放，没有假业务链接。原版启动入口仍在开发说明中。
- “SQL实时查询”改为“历史数据·按需查询”。来源行分别展示全状态数据期2016-09-04—2018-10-17与delivered有效购买期2016-09-15—2018-08-29；当前已应用日期/客户州另列，不将历史样本称为实时订单流。
- 日期与地区、应用/重置/导出操作统一字号与控件高度；保留更改待应用、已应用和导出范围提示。去除重复的KPI区日期说明，减少垂直冗余。
- 月度金额柱与订单折线维持上下独立零起点坐标；12px轴/图例、清楚的Tooltip及不完整月标识。订单坐标单位由ECharts自身放置，避免固定位置文字与刻度重叠。
- 地区州名称可点击立即执行真实筛选，保留当前已应用日期并同步控件；状态/地区模块分别注明全状态与有效订单口径。

## 月份切换及趋势解读的边界

默认“全部月份”，24个月全部保留，未丢弃早期月份；“完整月份”仅按既有SQL is_complete标记展示22个月。局部日期下同样采用该标记，不额外判断完整性。切换只改变图表视图，KPI和CSV仍使用当前已应用筛选；界面显示“仅切换图表，不改变KPI或导出范围”。

趋势解读读取既有/api/findings的P3 F01结果，逐字对账已验收快照，**没有新增API、SQL或分析算法**。全样本时标“P3固定全样本解读”；局部日期或地区时醒目显示“当前为局部筛选……不代表当前日期或地区的趋势”，并保留发现自身的观察期与P3_MONTHLY标识。没有用固定全样本环比伪装成局部筛选结论。

固定解读的真实结果为：2018-07商品金额BRL867,953.46，环比+1.39%；有效订单6,159单，环比+0.98%。来源仍为P3已验证完整月方法，而不是本阶段重新计算。此解释不随完整月/全部月查看切换，也不是未来预测。

## 真实运行环境与启动

Windows11；Python3.12.10；PostgreSQL16.16；React19.3.1、TypeScript7.0.2、Vite8.3.8、Tailwind4.3.5、ECharts6.1.0；FastAPI0.162.5。新增Vitest5.1.0仅用于前端开发测试，锁定于package-lock.json。

本阶段实际重新启动后端与Vite，执行start-v2.ps1 -Action check取得真实订单96,478。API、数据库和原始.env保持原配置。

```powershell
# 既有数据环境就绪后，分别在两个终端运行
powershell -NoProfile -ExecutionPolicy Bypass -File .\\start-v2.ps1 -Action api
powershell -NoProfile -ExecutionPolicy Bypass -File .\\start-v2.ps1 -Action web
# 校验SQL与前端连接
powershell -NoProfile -ExecutionPolicy Bypass -File .\\start-v2.ps1 -Action check
```

页面http://127.0.0.1:5173；API文档http://127.0.0.1:8000/docs；旧版http://127.0.0.1:8501。完整开发环境安装仍见[api/README.md](../api/README.md)。本阶段修改了前端开发依赖，已有环境运行npm --prefix frontend ci即可按锁文件同步。

复查中Vite终端进程曾结束，导致一次CSV请求连接重置；已通过普通前台npm run dev重新启动，再完整执行浏览器流程成功。最终日志vite_retry.log、browser.log为恢复后的结果，没有将中途失败记录宣称为通过。

## KPI、数据与原有成果保护

| 指标 | 浏览器/既有SQL默认结果 |
|---|---:|
| 商品成交额 | BRL13,221,498.11 |
| 有效订单 | 96,478单 |
| 唯一购买用户 | 93,358人 |
| 平均订单商品金额 | BRL137.04（原始精度由API保留） |

数据口径仍为delivered有效订单、customer_unique_id跨订单去重、商品金额不含运费且不代表财务收入/利润。前端展示函数不改变传入数据；月份筛选没有修改SQL响应对象。

阶段前后raw与mart内容指纹一致；{result['protected_files_unchanged']}个受保护API/SQL/src统计源码/既有文档/.env文件SHA-256未变，原有RFM、Cohort及P3模型没有改动。旧workbench.css与V2-01截图/报告保留；阶段开始前端源码另存于本地reports/v2-01-1/before。

## Chrome（Chromium内核）实际验证

Playwright CLI实际使用Chrome频道、独立内存浏览器配置及可见窗口，属于Chromium内核验证；频道证据在reports/v2-01-1/browser_sessions.log。未将其描述为Firefox/Safari或单独安装的开源Chromium发行版。

| 检查 | 结果 |
|---|---|
| 1440×1000、1280×900 | 标题29、正文/导航14、重要说明13、来源辅助12、图表轴12px；无整页横向溢出、KPI/标签截断 |
| 首屏 | 核心指标及主要趋势可见；次级分析/趋势解释通过正常纵向滚动查看 |
| 月份切换 | 全部24/完整22；KPI不变，返回全部恢复早期数据 |
| Tooltip | 实际悬停，显示真实BRL金额、订单数与完整/不完整观察月 |
| 地区排行点击 | 点击SP后实际SQL有效订单40,501单，地区下拉同步SP |
| 日期+地区组合 | 2017-05-10—2017-06-20、SP：商品金额BRL250,817.27、1,900单、1,863人、平均BRL132.01 |
| 待应用 | 草稿调整后保留当前结果并显示“更改待应用”；应用后图表/KPI共用范围 |
| 局部解读 | 始终显示固定全样本标签和局部范围限制，数值与P3 F01完全相同 |
| 导出 | 真实下载filtered-monthly.csv，数据列和范围列逐项对账现有API/SQL一致 |
| 空结果/无完整月 | 0金额、0单、0人、均值“—”；完整月视图显示无可展示月份说明 |
| 重置 | 恢复4项全样本基线 |
| 加载状态 | 实际延迟请求时显示加载，未填入假数值 |
| 错误状态 | 浏览器拦截503后显示中文重连、隐藏旧KPI；移除拦截后真实请求恢复 |
| 经营发现入口 | 七项既有发现可打开、Esc关闭，无新诊断页面 |
| JavaScript | 完整交互0 pageerror；预期503在控制台的网络错误不算JS异常 |
| 原版Streamlit | 实际浏览器重新打开，4项基线、3张Plotly图、0异常组件 |

错误状态验证范围明确：本阶段用浏览器传输层拦截503验证呈现，不称为本阶段真实停库。API的真实停库/恢复证据仍保留在V2-01历史报告，API业务逻辑未修改。

## 实际截图

![1440px首屏](screenshots/v2-01-1/overview-1440.png)

- [1280px首屏](screenshots/v2-01-1/overview-1280.png)
- [1440px全页面](screenshots/v2-01-1/overview-1440-full.png)
- [1280px全页面](screenshots/v2-01-1/overview-1280-full.png)
- [真实悬停提示](screenshots/v2-01-1/trend-tooltip.png)
- [局部筛选结果与解释边界](screenshots/v2-01-1/filtered-overview.png)

共6张公开聚合截图，均由真实运行页面生成。加载/空/错误等本地检查截图在output/playwright/v2-01-1；未用效果图或模拟业务数据替代结果。

## 自动测试与构建

- 后端完整Pytest：**103 passed，0 failed，0 errors，0 skipped**，原有103项全部通过，无旧断言修改。
- 新增前端Vitest：**8 passed，0 failed**。覆盖完整/全部月选择、空视图、原数组不变、真实P3原文与SQL来源、日期/州局部边界、缺失快照、零起点和精确Tooltip格式。
- npm run build：TypeScript检查与Vite生产构建通过。仍有约853KB（gzip约283KB）的JS单包告警，未隐藏或声称已完成生产包体优化。
- npm audit：本次0已知漏洞；公开候选文件扫描通过，无远端/发布操作。该检查不等同生产安全认证。

可复查命令：

```powershell
.\\.venv\\Scripts\\python.exe -m pytest -q -rA --junitxml=reports/v2-01-1/pytest.xml
npm --prefix frontend test
npm --prefix frontend run build
```

## 证据与限制

| 本地运行证据 | 路径 |
|---|---|
| 后端测试/XML | reports/v2-01-1/pytest.log、pytest.xml |
| 前端测试/构建 | reports/v2-01-1/frontend_tests.log、build.log |
| 实际启动 | reports/v2-01-1/api.log、vite_retry.log、startup_check.log |
| 完整浏览器流程 | reports/v2-01-1/browser.log；脚本scripts/v211_browser_check.js |
| 旧版验证 | reports/v2-01-1/legacy_browser.log |
| CSV及独立核对 | reports/v2-01-1/filtered-monthly.csv、final_verification.json |
| 保护/安全/清单 | reports/v2-01-1/baseline.json、public_safety.json、npm_audit.json、modified_files.json |

未验证手机或其他分辨率、其他浏览器、全新OS、生产托管/并发/认证和完整WCAG符合性。四个未实现模块保持禁用而非空页面；没有新账户系统。历史观察窗口与非因果解释限制继续生效。没有公网部署、没有进入V2-02；视觉最终是否通过由用户验收。

## 文件修改清单

{files}

另新增本地忽略的reports/v2-01-1及output/playwright/v2-01-1证据；没有删除文件或目录。现有API、P1仓库、P3统计及旧版Streamlit保持不变。
'''
    (ROOT/'docs/V2-01-1_ACCEPTANCE_REPORT.md').write_text(report,encoding='utf-8')
    print('V2-01.1 acceptance report generated from completed execution evidence.')


if __name__=='__main__':main()
