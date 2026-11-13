"""Generate the V2-02 aggregate delivery report from completed execution evidence."""
from datetime import datetime
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/v2-02'


def main():
    result=json.loads((OUT/'final_verification.json').read_text(encoding='utf-8'))
    assert result['passed']
    modified=['README.md','api/README.md','api/main.py','frontend/src/App.tsx','frontend/src/types.ts','frontend/vite.config.ts']
    added=['api/analysis.py','api/queries.py','frontend/src/AnalysisUI.tsx','frontend/src/Findings.tsx',
        'frontend/src/analysis.ts','frontend/src/analysisCharts.ts','frontend/src/usersCharts.ts','frontend/src/analysis.css','frontend/src/scope.ts',
        'frontend/src/pages/Overview.tsx','frontend/src/pages/Users.tsx','frontend/src/pages/Products.tsx','frontend/src/pages/Delivery.tsx',
        'frontend/tests/analysis.test.ts','tests/test_v2_analysis.py','scripts/v202_browser_check.js','scripts/verify_v202.py','scripts/write_v202_report.py',
        'docs/V2-02_API_AND_SCOPE.md','docs/V2-02_ACCEPTANCE_REPORT.md',
        *sorted('docs/screenshots/v2-02/'+name for name in result['screenshots'])]
    changes={'modified':modified,'added':added,'local_ignored':['reports/v2-02/','output/playwright/v2-02/'],
        'preserved':'src/retailscope、sql、data/raw、mart内容、.env、旧版Streamlit、历史报告、overview.css/index.css冻结样式'}
    (OUT/'modified_files.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
    files='\n'.join('- `'+p+'`' for p in modified+added)
    chunks='\n'.join(f"| {name} | {r['bytes']/1000:.2f} KB | 是 |" for name,r in result['page_chunks'].items())
    report=f'''# RetailScope V2-02 三个核心分析页面验收报告

日期：{datetime.now():%Y-%m-%d}。三个新版页面及真实只读接口已完成，技术与浏览器验证通过，等待用户验收。仅到V2-02，没有进入V2-03、推送GitHub或部署公网。

## 实际交付与设计冻结

1. **用户价值分析**：固定全样本RFM六类分层、人数/占比/商品金额贡献、购买频次、复购、Cohort热力图与新增购买用户；按“价值结构→购买频次→同期群→新增用户”组织。
2. **商品与品类分析**：真实日期/州/类目筛选、商品行KPI与跨类目去重订单、TOP10及完整排行、帕累托、月度结构、商品件数与订单覆盖；排行可点击应用当前草稿。
3. **履约与评价分析**：同类筛选但使用订单包含类目的语义；配送/逾期/评价KPI、各自分母及缺失、配送与评分分布、州级表现、小样本提示、逾期评价描述性关联。
4. 三页导航由待开放改为实际链接；支持直接访问、浏览器前进/后退。经营发现仍为P3已验收对话框，数据质量中心继续明确禁用，不提供假链接或空页面。

**冻结样式保护：**frontend/src/overview.css与index.css的SHA-256未变。继续复用白底、低饱和紫/青、29px标题、14px正文/导航、12px辅助/坐标、13px重要说明及原KPI/筛选/按钮/边框规则。新增analysis.css只补充表格、热力图内部滚动与分析页布局，不覆盖总览的颜色、字体和整体布局。

## 总览两项小修

- 表单应用与地区点击共用applyScope校验。地区点击合并**当前draft**并应用，保留尚未应用的起止日期；草稿日期非法/为空时提示并停止查询。实测：编辑为2017-05-10—2017-06-20但未按应用，点击SP后实际请求仍使用这两个日期，未回退到旧结果日期。
- “完整月份”改为“当前范围完整月”。明确完整月须同时满足全数据集完整目标月区间[2016-10-01,2018-08-01)与当前日期窗口覆盖整月；州筛选不重定义全数据集观察边界。上述局部日期只有2个部分月份，因此当前范围完整月为0，不将全数据集22个完整月误用于局部选择。
- 全部月仍保留早期与局部不完整月份；仅切换图表，不改变KPI或导出范围。其余总览视觉及原四项KPI未变。

## API与统计复用

新增/api/analysis/users、products、delivery及各自/export接口。共享api/queries.py承接原数据库连接和参数化访问函数，业务SQL仍直接引用retailscope.bi.data的SCOPE/FILTERED/FIXED；没有修改P1数仓SQL、RFM/Cohort算法或P3统计模型。

SQLAlchemy连接继续使用REPEATABLE READ只读事务、有限连接池、5秒连接/20秒语句超时。州和类目来自白名单，page/table受枚举或白名单控制；非法组合422，数据库失败返回脱敏503，错误日志不记录连接串或密码。金额/比例为精确Decimal字符串，日期为ISO，NULL仍是null。

除原SQL外，仅新增一条相同SCOPE、相同分组条件的参数化只读计数查询，为关联表提供最新评分有效分母与低评分订单数，不改变任何已有均值/比例定义。详细契约见[V2-02_API_AND_SCOPE.md](V2-02_API_AND_SCOPE.md)。

### 用户页固定全样本

- 有效购买期2016-09-15—2018-08-29，RFM基准日2018-08-30，customer_unique_id去重。
- 购买用户93,358；复购用户2,801；复购率3.0003%；一次购买用户90,557，占96.9997%。
- 六个RFM层的全部行、人数、商品金额和贡献与P1 JSON逐项一致。Frequency分位点大量重合，评分2–4缺失属于数据特征，界面说明其原因。
- Cohort全部552行与P1逐项一致；298个未观察单元保留NULL，热力图为空格、CSV为空字段。已观察且无购买才为0；同用户同月多单只计一次，回购活跃留存不要求连续回购。
- 色阶在2%封顶，但标签/悬停保留实际比例，M0可能100%。未用假0补观察窗；2016-09首cohort左截断继续披露。
- 本页无伪局部筛选控件，接口拒绝日期/地区/类目参数。浏览器从局部筛选页返回用户页仍显示全样本。

### 商品页粒度与去重

默认商品金额BRL13,221,498.11，商品件数110,197，覆盖有效订单96,478，运费BRL2,198,275.64。类目选择只取所选商品行；总订单在这些商品行范围内重新COUNT(DISTINCT order_id)。

自动测试确认各类目内订单数之和大于总去重订单数，而商品金额之和准确对账，界面不把类目订单数相加作为总数。帕累托仅对真实贡献占比做累计展示；月度不存在的类目记录保留缺失，不伪造零销售。

### 履约评价样本与解释

默认平均配送12.56天、逾期率6.7731%、订单等权评价4.16、有效订单96,478；有效配送/逾期判断样本各96,470单，评价样本95,832单。对应缺失/无效为8、8、646单，缺失项目可能交叠，不能相加作为排除总数。

分组比较有效样本95,824单：未逾期89,443、逾期6,381；低评分订单合计12,272。界面同时展示订单均分分母、最新评分分母、低评分订单及比例，低评分定义为最新评分≤2。地区配送少于100单提示谨慎比较。

均分先订单内平均再对订单等权，评分分布每单取最新评分，二者均无多评价额外加权。当前筛选只作描述性关联，不推断因果；不将P3全样本置信区间套到局部筛选。原P3七项发现与推断方法继续通过经营发现入口按固定全样本复用。

## 实际筛选与导出

浏览器以2017-05-10—2017-06-20、SP、beleza_saude作组合验证：

| 页面 | 真实筛选结果 |
|---|---|
| 商品 | BRL15,182.76；142件；135个去重订单；商品运费BRL1,637.27 |
| 履约评价 | 平均7.62天；逾期率5.1852%；评价4.18；135个订单 |

商品页通过点击排行类目应用当前日期/州草稿，结果与独立SQL一致；履约页通过表单应用同一组合。两页重置恢复全样本，2020-01-01—2020-01-02真实SQL零样本显示清晰空状态。

实际下载三份CSV并逐列对账当前API/SQL：用户Cohort552行（298个空留存）、商品筛选排行1行、履约筛选分组2行。所有CSV包含scope_mode/start/end/state/category，采用已应用范围，不从截断表格拼导出。自动测试另覆盖11种页面/table组合及空表头。

## 页面级加载与性能范围

React.lazy/Suspense对四个实际页面和Findings分别加载。生产manifest证明各页面是动态入口；首次打开总览的浏览器网络记录只包含总览和共享代码，未加载Users/Products/Delivery代码块，也未请求隐藏分析页API。

| 页面代码块（非全部依赖） | 实际构建大小 | 动态入口 |
|---|---:|---|
{chunks}

当前入口JS约232KB，共享ECharts/基础图表包约538KB（gzip约184KB），仍触发500KB告警。不能把入口文件变小等同总体首屏仅232KB，或声称生产性能/并发已验收。用户热力图扩展仅在用户页代码块加载；API返回聚合结果，没有一次读取全部原始订单到浏览器。

## 测试与真实浏览器结果

- 后端Pytest：**129 passed，0 failed，0 errors，0 skipped**，保留原103项断言，新增26项接口用例。
- 前端Vitest：**13 passed，0 failed**，原8项与新增5项；覆盖草稿合并、非法日期、真实Cohort NULL、累计贡献和缺失类目/月不造0。
- TypeScript与生产构建通过。旧源码/SQL/模型、raw/mart指纹和冻结CSS均通过最终只读核对。
- 三页各在1440×1000与1280×900验证，均4个真实ECharts SVG图，0整页横向溢出、0 KPI截断，导航高亮正确；完整过程0 pageerror。
- 三页503显示中文重连并隐藏旧KPI；解除拦截后恢复真实API。固定用户页空概要也显示合理提示。边界验证范围明确：这些503和用户空概要是浏览器拦截测试，不是本阶段真实停库或伪造正向业务数据；商品/履约空结果为真实SQL。
- 原版Streamlit实际重新打开：默认四项KPI、3张Plotly图、0异常组件。P0–P4测试仍通过。

## 实际截图与运行入口

三页生产构建预览：

- [用户价值分析](http://127.0.0.1:5174/users)
- [商品与品类分析](http://127.0.0.1:5174/products)
- [履约与评价分析](http://127.0.0.1:5174/delivery)

正常开发入口仍为5173，API8000、旧版8501；实际浏览器截图来自本机生产预览5174，不是公网部署。

| 页面 | 1440px首屏 | 1280px首屏 | 1440px全页 | 1280px全页 |
|---|---|---|---|---|
| 用户 | [截图](screenshots/v2-02/users-1440.png) | [截图](screenshots/v2-02/users-1280.png) | [截图](screenshots/v2-02/users-1440-full.png) | [截图](screenshots/v2-02/users-1280-full.png) |
| 商品 | [截图](screenshots/v2-02/products-1440.png) | [截图](screenshots/v2-02/products-1280.png) | [截图](screenshots/v2-02/products-1440-full.png) | [截图](screenshots/v2-02/products-1280-full.png) |
| 履约 | [截图](screenshots/v2-02/delivery-1440.png) | [截图](screenshots/v2-02/delivery-1280.png) | [截图](screenshots/v2-02/delivery-1440-full.png) | [截图](screenshots/v2-02/delivery-1280-full.png) |

另有[完整Cohort热力图](screenshots/v2-02/users-cohort.png)、[筛选后帕累托](screenshots/v2-02/products-pareto.png)、[筛选后履约关联](screenshots/v2-02/delivery-association.png)，合计15张真实聚合截图。热力图窄屏允许图内横向滚动；长表在表内滚动，不造成整页溢出。

```powershell
# 两个终端分别启动现有开发服务
powershell -NoProfile -ExecutionPolicy Bypass -File .\\start-v2.ps1 -Action api
powershell -NoProfile -ExecutionPolicy Bypass -File .\\start-v2.ps1 -Action web
# 生产构建及本地预览（独立第三个终端）
npm --prefix frontend run build
npm --prefix frontend run preview -- --port 5174
```

## 数据保护、安全及证据

{result['protected_files_unchanged']}个受保护历史文档、src统计代码、SQL、.env及冻结CSS文件SHA-256一致；九张raw与mart内容指纹一致。没有重建数据库、修改指标或重新开发统计模型。Git候选文件安全扫描通过，原始CSV、用户级导出、.env/凭证、node_modules、dist及日志均忽略；Git无暂存/远端/发布，npm audit本次0已知漏洞。扫描不是全部秘密类型或生产安全认证。

| 内容 | 本地证据路径 |
|---|---|
| 后端完整测试/XML | reports/v2-02/pytest.log、pytest.xml |
| 前端测试/构建 | reports/v2-02/frontend_tests.log、build.log |
| 启动/实际服务 | reports/v2-02/api.log、api_final.log、preview.log、startup_check.log |
| 浏览器全部交互 | reports/v2-02/browser.log；scripts/v202_browser_check.js |
| 旧版浏览器 | reports/v2-02/legacy_browser.log |
| 三种实际下载 | reports/v2-02/users-cohort.csv、products-filtered.csv、delivery-filtered.csv |
| 数据/设计保护与对账 | reports/v2-02/baseline.json、final_verification.json、final_verification.log |
| 分包证据 | frontend/dist/.vite/manifest.json（本地构建产物）、final_verification.json、浏览器首页asset请求列表 |
| 安全和修改清单 | reports/v2-02/public_safety.json、npm_audit.json、modified_files.json |

## 已知限制与阶段控制

1. 仅本机Chrome/Chromium内核和上述两种桌面尺寸，未验证手机、Safari/Firefox、全新OS、生产并发或公网托管。
2. 共享图表包仍有大小告警。若未来更换托管需配置SPA路径回退；本阶段无公网部署或身份账户系统。
3. 用户固定全样本不局部重算；Cohort观察窗口、首尾月份、用户进入时间差异和非因果边界继续有效。
4. 商品/履约当前支持单个州与单个类目组合，界面和接口一致，不宣称多选已完成。
5. 固定P3推断只在经营发现中按原范围复用，局部履约页不伪造置信区间或预测。
6. 数据质量中心仍明确待开放；没有提前开发V2-03。等待用户验收，不自动进入下一阶段。

## 文件修改清单

{files}

另有本地忽略的reports/v2-02和output/playwright/v2-02运行证据；没有删除既有文件或目录，旧版Streamlit保留。
'''
    (ROOT/'docs/V2-02_ACCEPTANCE_REPORT.md').write_text(report,encoding='utf-8')
    print('V2-02 report generated from completed verification evidence.')


if __name__=='__main__':main()
