"""Write the issue ledger and final UI evidence index from real saved checks."""
import difflib
import json
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/ui-final'

ISSUES=[
('Q01','已确认问题','葡语编码与unknown直接展示','已修复','74项映射覆盖；中文展示、原码查询；未分类与未翻译明确区分。'),
('Q02','已确认问题','长下拉框难定位类目','已修复','搜索中文、官方英文或原码；Enter选择、Escape返回、方向键导航。'),
('Q03','已确认问题','品类明细默认长表','已修复','默认TOP10，支持查看全部、搜索、排序；仅改变表格行，不改完整集合分母。'),
('Q04','已确认问题','帕累托横轴标签密集','已修复','稀疏排名刻度，Tooltip包含真实排名、中文名称、原码、金额、累计贡献。'),
('Q05','已确认问题','Cohort默认24列密集','已修复','默认M1–M6；全部月份保留M0–M23及552单元，完整CSV不截断。'),
('Q06','已确认问题','正的小留存显示0.0%','已修复','0.0187336%等真实正值显示0.02%；更小正值使用<0.01%，真实0单独标0%。'),
('Q07','已确认问题','M0共用后续留存色阶','已修复','M0退出visualMap映射、使用独立灰绿色；后续色阶仍0–2%封顶，真实值未截断。'),
('Q08','已确认问题','Cohort Tooltip缺分母与观察月','已修复','保留真实率、活跃人数、首购人数、观察月份/月龄、左截断说明。'),
('Q09','已确认问题','ISO微秒时间直接显示','已修复','显式时区转换为北京时间、精确到分钟；未记录继续未记录，时区未知不擅自假定。'),
('Q10','已确认问题','总览金额重复BRL','已修复','移除金额卡片右上重复单位，保留数值前BRL和每单单位。'),
('Q11','已确认问题','局部图表附近固定全样本发现易混淆','已修复','局部筛选默认折叠全样本参考，入口明确标“非当前筛选”。'),
('Q12','已确认问题','RFM名称不便查看规则','已修复','表格悬停、图表Tooltip、可键盘展开的分类规则，顺序与原SQL一致。'),
('Q13','已确认问题','地区图按配送时长突出小样本州','已修复','按有效配送样本量排序，图默认≥100单；可含小样本，完整表和导出保留全部地区。'),
('Q14','已确认问题','F07默认摘要过长','已修复','摘要只展示已验证的加权次月留存，完整结果和分母仍在分析依据。'),
('Q15','已确认问题','侧边栏署名块占位','已修复','集中到键盘可展开“关于数据”，保留Olist/Kaggle、年份、许可及非商业属性。'),
('Q16','已确认问题','帮助入口像普通小链接','已修复','沿用原生details，增加帮助与展开图标、可见焦点；不增加长篇默认说明。'),
('Q17','已确认问题','1280px/125%商品长金额拥挤','已修复','仅CSS视口≤1100时分析页两列KPI，筛选日期单行，按钮同组。'),
('Q18','已确认问题','中文长名称与弹出选项存在裁切风险','已修复','选项与类目表格换行，弹层右对齐；搜索、长名称与窄屏截图已核验。'),
('Q19','已确认问题','125%原生全页截图右侧裁切','已修复（取证方式）','Chromium fullPage缩放捕获问题；125%交付真实首屏，正常缩放提供完整页面；失败原图本地保留。'),
('Q20','语义证据不足','cool_stuff、la_cuisine、seguros_e_servicos中文业务含义','尚需验证','采用未翻译（一/二/三），不猜测；须数据提供方或更细商品描述确认。非阻塞展示/统计。'),
('Q21','兼容范围','其他浏览器、移动端、读屏器全面适配','尚需验证','本次实际范围为Windows Chromium两桌面尺寸、100%/125%；不扩称跨浏览器验收。'),
('Q22','保留取舍','全部月份在窄屏需横向滚动','非阻塞优化','全部552单元未删除，M1–M6默认无需滚动；横向滚动仅限图表容器。'),
('Q23','保留取舍','CSV保留英文原始列名和原编码','非阻塞优化','与旧接口逐字段相同；页面注明金额单位BRL，中文译名核对表可追溯；未改API导出契约。'),
]


def main():
    rows='\n'.join('| '+' | '.join(v.replace('|','\\|') for v in r)+' |' for r in ISSUES)
    (ROOT/'docs/UI_FINAL_ISSUES.md').write_text('''# RetailScope 最终UI问题清单

“已确认问题”为本轮发现记录；“已修复”需结合真实截图和运行日志；“尚需验证”不冒充通过；“非阻塞优化”为保留取舍。最终视觉验收仍由用户决定。

| 编号 | 确认情况 | 问题 | 当前状态 | 处理及边界 |
|---|---|---|---|---|
'''+rows+'\n',encoding='utf-8')
    diff=[]
    for new in sorted((ROOT/'frontend/src').rglob('*')):
        if not new.is_file():continue
        relative=new.relative_to(ROOT/'frontend/src');old=OUT/'before'/relative
        diff.extend(difflib.unified_diff(old.read_text(encoding='utf-8').splitlines(True) if old.exists() else [],new.read_text(encoding='utf-8').splitlines(True),fromfile='before/'+relative.as_posix(),tofile='after/'+relative.as_posix()))
    (OUT/'frontend.diff').write_text(''.join(diff),encoding='utf-8')
    if not (OUT/'verification.json').exists():print('Issue ledger/diff saved; final verification pending.');return
    v=json.loads((OUT/'verification.json').read_text(encoding='utf-8'));assert v['passed']
    manual=json.loads((OUT/'manual_review.json').read_text(encoding='utf-8'));assert manual['reviewed']
    changed=[]
    for p in sorted((ROOT/'frontend/src').rglob('*')):
        if p.is_file():
            before=OUT/'before'/p.relative_to(ROOT/'frontend/src')
            if not before.exists() or p.read_bytes()!=before.read_bytes():changed.append(p.relative_to(ROOT).as_posix())
    changed+=['frontend/tests/findingCopy.test.ts','frontend/tests/finalQa.test.ts',
        'scripts/ui_final_zoom_probe.js','scripts/ui_final_screens.js','scripts/ui_final_browser.js','scripts/ui_final_states.js','scripts/ui_final_details.js','scripts/verify_ui_final.py','scripts/write_ui_final_report.py',
        'docs/UI_CATEGORY_TRANSLATIONS.md','docs/UI_FINAL_ISSUES.md','docs/UI_FINAL_QA_REPORT.md']
    (OUT/'change_manifest.json').write_text(json.dumps({'source_and_documents':changed,'screenshots':sorted(v['screenshots']),'local_evidence':'reports/ui-final (ignored)'},ensure_ascii=False,indent=2),encoding='utf-8')
    change_list='\n'.join(f'- `{name}`' for name in changed)
    shots='\n'.join(f'| {label} | [首屏](screenshots/ui-final/{key}-1440-z100.png) / [全页](screenshots/ui-final/{key}-1440-z100-full.png) | [首屏](screenshots/ui-final/{key}-1280-z100.png) / [全页](screenshots/ui-final/{key}-1280-z100-full.png) | [1440](screenshots/ui-final/{key}-1440-z125.png) / [1280](screenshots/ui-final/{key}-1280-z125.png) | [修改前](screenshots/ui-copy/{key}-1440-full.png) |' for key,label in [('overview','经营总览'),('users','用户价值'),('products','商品品类'),('delivery','履约评价'),('findings','经营发现'),('quality','数据质量')])
    report=f'''# RetailScope 最终UI品质审查报告

生成：{datetime.now().astimezone().isoformat(timespec='seconds')}。**本轮定向修复与技术核验完成，等待用户最终视觉验收。** 不宣称全部完美，待验证项与保留取舍见[问题清单](UI_FINAL_ISSUES.md)。

## 范围与实际环境

只调整前端显示、搜索/表格/帮助交互和窄视口响应；未改PostgreSQL、API业务代码、SQL、RFM/Cohort或统计方法。沿用紫色/青色、全局字体与整体导航布局，无新业务模块/依赖服务，旧Streamlit保留。本次实际使用Windows 11、Python3.12.10、PostgreSQL16.16、React/FastAPI、Chromium本地生产构建预览5174和API8000。

## 四项必要修复及前后对照

| 项目 | 修改前 | 修改后 | 证据 |
|---|---|---|---|
| 品类名称 | 葡语编码、__unknown__ | 74项展示映射：70项中文语义译名、1未分类、3明确未翻译 | [逐项映射表](UI_CATEGORY_TRANSLATIONS.md)、真实原CSV与API选项覆盖测试 |
| 类目选择 | 长原生下拉框逐项寻找 | 中文/英文/原码搜索；键盘选择、Escape返回；查询值仍为原码 | 搜索/键盘浏览器记录与长标签局部图 |
| 排行密度 | 默认全部74行 | 默认TOP10，查看全部/搜索/排序；统计图和贡献分母仍为完整集合 | 全量CSV74行、完整帕累托金额/占比对账 |
| 帕累托标签 | 横轴密集 | 稀疏排名刻度，Tooltip给真实排名、中文、原码与贡献 | 图表截图/既有全量分母测试 |
| Cohort | 默认24列，正小值显示0.0%，M0共用色阶 | 默认M1–M6，全部月龄可切换；两位小数/极小正值特殊标签；M0独立灰绿 | 552单元/298NULL原值测试与实际渲染 |
| Cohort悬停 | 仅留存率与月龄 | 观察月份、真实率、活跃人数、首购人数及左截断 | 真实小比例单元悬停截图 |
| 日期 | ISO、UTC偏移、微秒 | 显式北京时间，分钟精度；执行未知仍未记录，保存时间单列 | 时间边界测试、质量页与详情截图 |

类目中文优先复用官方71行中英对照，核对本机实际74个选项（含未分类标识）。两个官方未收录项按原词补充译名；cool_stuff、la_cuisine与seguros_e_servicos语义不足或翻译歧义，保留“未翻译（一/二/三）”，没有推断商品内容。中文不是Olist官方译名；核对来源、处理理由与全部编码详见映射文档。以后新增编码回退“未翻译”，须补映射。

原始category与scope_category、CSV列和所有原统计值保留；本轮不在API追加中文列，避免改导出契约。页面中文名、原码提示及映射文档支持追溯。CSV金额单位BRL，完整数据导出不受TOP10/搜索/排序的显示限制影响。

## 其他定向优化

总览删除右上重复BRL，局部筛选默认折叠“全样本趋势参考（非当前筛选）”；不把旧全样本结论伪装为局部计算。RFM规则按原SQL优先级展示，表格/图表可查并可键盘展开。地区图按有效配送样本量排序，默认至少100单，可显示小样本；完整表与导出不删除小州。F07摘要只显示已有加权次月留存，分母及完整原文仍在依据详情。侧边栏署名集中到“关于数据”，许可与来源保持可访问。帮助入口增加图标/展开提示与键盘焦点。

实际125%检查发现1280宽度时商品长金额拥挤：仅CSS视口≤1100采用两列KPI，并使日期行与筛选按钮分组。正常1280/1440主布局保持。首次M0颜色没有正确呈现，后改为逐项退出visualMap并指定中性色，实际截图复核，不只检查配置。全站改动可由`reports/ui-final/frontend.diff`逐行对照修改前备份；历史报告/截图未覆盖。

## 真实浏览器与目视检查

两种目标内容区域1440×1000、1280×900，分别100%与**浏览器原生125%**。Playwright页面按键首次未改变缩放（证据保留）；改用Windows原生Chrome控件，观察到“缩放比例：125%”，页面devicePixelRatio≈1.25、1440目标内容区CSS宽1152，1280目标内容区CSS宽1024，完成后恢复100%。没有用CSS zoom或缩小截图冒充原生缩放。

- 六页面直达、导航及前进/后退实际通过；24组默认尺寸/缩放检查无页面横向溢出和KPI截断。
- 总览、商品、履约分别在四种尺寸/缩放组合测试日期/州/类目、待应用、应用、真实2020空结果及重置；结果与原SQL一致。
- RFM/Cohort为固定全样本，局部日期筛选不适用；两尺寸/两缩放检查规则展开与重点月份。经营发现测试专题与依据展开，质量测试历史详情与缺失字段空态。
- 排行默认10行/全74行、搜索、金额/件数/名称排序、类目原码请求、键盘Enter与Escape恢复焦点通过。长中文选项/表格截图检查；全量明细在内部滚动，不放大页面。
- 全部/重点Cohort切换；最小真实正值为2017-12 cohort的M7（观察2018-07），1 / 5338 = 0.018733608...%，显示0.02%，Tooltip保留精细真实值和分母；NULL灰底空白与白格0%区分。
- 七发现完整原文、方法、局限、建议和F05区间逐项核对；CSV/Markdown/JSON真实下载；六页加载/503/恢复测试通过。本轮使用受控API错误状态，未重复执行真实停库。

本次助手**实际查看生成截图**：默认首屏/全页、1280及125%接触表、长名称、筛选/空态、规则/统计依据、Cohort全月与Tooltip；并在首次截图发现拥挤和M0颜色问题后修复。记录在`manual_review.json`。这是目视复核，仍待用户最终审美判断；不是把overflow=false或测试通过等同视觉完美。

## 截图索引

| 页面 | 1440正常缩放 | 1280正常缩放 | 原生125%首屏 | 修改前 |
|---|---|---|---|---|
{shots}

放大局部：[Cohort全部月份](screenshots/ui-final/cohort-all.png)、[小比例Tooltip](screenshots/ui-final/cohort-small-tooltip.png)、[类目搜索](screenshots/ui-final/category-search-long.png)、[长名称表格](screenshots/ui-final/category-long-table.png)、[中文Tooltip](screenshots/ui-final/category-tooltip.png)、[小样本切换](screenshots/ui-final/delivery-sample-toggle.png)、[质量时间](screenshots/ui-final/quality-date-source.png)。筛选、空态和展开截图按`页面-状态-宽度-z缩放.png`保留同目录。

Chromium原生125%的fullPage捕获会裁切右侧，失败截图未用作验收，移到本地`reports/ui-final/capture-issues`保存；125%采用真实首屏，100%提供完整全页。未删除这些问题证据。全部正式PNG经格式校验，可用普通图片查看器打开；正常全页内容宽可能因滚动条少15px。

## 测试、数据与导出

| 实际检查 | 结果 |
|---|---|
| 完整后端Pytest | **144 passed，0失败/错误/跳过**，103.96秒 |
| 完整前端Vitest | **27 passed**；原23项保留，新增4项定向回归 |
| TypeScript / Vite | 均通过 |
| 受保护源码/配置 | {v['protected_sources_unchanged']}项Python/SQL/API/.env哈希一致 |
| 原始/仓库数据 | Raw/Mart全表行数、内容指纹与既有验收一致；13项P0原文件SHA一致 |
| 业务结果 | 五个核心接口完整响应与修改前相同；包括RFM、552个Cohort单元、7项P3发现 |
| 下载 | 7个CSV逐字段对账；Markdown与原文件字节一致；质量JSON来源/九表规模一致 |

有效订单96,478、购买用户93,358、商品金额BRL13,221,498.11、平均订单商品金额BRL137.04不变。新测试覆盖全部原类目/官方英文映射、排行仅展示与不变分母、时区/未知时间、Cohort精度/窗口/全量/Tooltip及M0退出色阶。仅更新原F07摘要测试的文案期望，原始统计证据不改。

日志在`reports/ui-final/`：`pytest.log/xml`、`frontend_tests.log`、`typecheck.log`与`typecheck_result.json`、`build.log`、`browser.log`、`screens_100/125.log`、`states_100/125.log`、`details.log`、`native_zoom.log`、`verification.json/log`、`manual_review.json`。浏览器与核查脚本在`scripts/ui_final_*.js`、`verify_ui_final.py`。

## 修改文件与待验证项

修改前端：`AnalysisUI.tsx`、`App.tsx`、`analysisCharts.ts`、`usersCharts.ts`、`analysis.css`、`findingCopy.ts`及六个页面；`frontend/tests/findingCopy.test.ts`摘要断言。新增：`CategorySelect.tsx`、`categories.ts`、`categoryLabels.json`、`dateTime.ts`、`rfmRules.ts`、`frontend/tests/finalQa.test.ts`；新增QA脚本、映射文档、两份报告与本轮截图。完整差异与修改前文件保留在本地证据目录。

尚需数据提供方确认三个模糊类目中文业务语义；目前正确回退未翻译，非阻塞统计。其他浏览器/移动端/读屏器完整适配未验收。全月份窄屏保留内部横滚；CSV保留英文原列名和原码作为兼容取舍。本轮未做干净系统重装、公网负载或部署，未推送GitHub或公开数据。

### 完整源码与文档修改清单

{change_list}

另有{len(v['screenshots'])}张正式PNG，逐项文件名/尺寸见`reports/ui-final/verification.json`，结构化文件清单为`change_manifest.json`。运行日志、修改前备份与失败捕获只在本地证据目录保留。

**完成后停止开发，等待最终验收。**
'''
    (ROOT/'docs/UI_FINAL_QA_REPORT.md').write_text(report,encoding='utf-8')
    print('Final report and issue ledger written.')


if __name__=='__main__':main()
