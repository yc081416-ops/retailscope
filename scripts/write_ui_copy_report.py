"""Write the product-copy comparison and acceptance from saved execution evidence."""
import difflib
import json
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/ui-copy'

CHANGES=[
('全站','六个分析模块均基于真实历史样本与可复核证据。','移除','侧边栏删除重复自证说明'),
('全站','每页来源行、来源徽章及许可页脚','侧边栏统一 Olist / Kaggle、历史年份、许可与非商业属性','质量页详情保留数据版本'),
('全站','真实数据，可复核的经营分析','电商经营分析','页脚去重复声明'),
('全站','历史数据 · 按需查询','移除','保留顶栏“历史数据分析”'),
('全站','正在查询真实分析数据…','正在加载数据…','加载提示'),
('全站','请确认本地API / PostgreSQL正常后重试','数据暂时无法加载，请稍后重试。','统一错误提示，保留重试操作'),
('全站','已导出当前已应用范围；NULL留存保留为空。','导出成功。','导出逻辑与NULL保持不变'),
('总览','全状态订单数据期、有效订单购买期、来源行','指标说明','保留两类实际日期及全状态/已送达区别'),
('总览','当前全状态订单筛选：…；核心交易指标仅计有效已送达订单','已选：日期 · 地区','有效订单口径移入KPI标题提示和指标说明'),
('总览','核心指标仅含有效 delivered订单；商品成交额不代表财务确认收入或利润。','指标说明','保留商品金额、运费与收入/利润区别'),
('总览','当前范围全部月 / 当前范围完整月','全部月份 / 完整月份','筛选与图表行为不变'),
('总览','显示…个月 · 仅切换图表，不改变 KPI 或导出范围','显示…个月','详细范围关系移入“月份与解读说明”'),
('总览','完整月须同时满足数据集完整目标月区间…金额与订单纵轴均从0开始。','浅色柱 / 琥珀色点：未完整观察的月份','保留完整月条件至详情，移除实现性坐标说明'),
('总览','P3 固定全样本解读','全样本趋势','局部筛选时默认仍明确全样本不联动'),
('总览','当前日期与地区 · 全状态订单（含取消等状态）','全部状态','详情保留全部状态与交易指标的差异'),
('总览','有效已送达订单 · 点击客户州时同时应用当前草稿日期','已送达订单 · 点击地区筛选','草稿条件应用逻辑不变'),
('总览','查看 P3 已验证的7项统计发现、数据来源与解释边界…','7项经营发现 · 全样本分析','保留发现入口'),
('用户','先识别用户结构，再观察购买频次与月度回购活跃留存。','了解用户价值、复购与留存。','副标题'),
('用户','固定 P1 全样本…RFM基准日…本页不受其他页面筛选影响','全样本 · 观察日期 · 不随其他页面筛选变化','RFM基准日移入指标说明'),
('用户','customer_unique_id 去重','跨订单去重','不改变唯一用户含义'),
('用户','01 · 识别用户价值结构','RFM 用户分层','移除流程编号'),
('用户','RFM 六类规则分层…标签不代表营销效果','人数与商品金额贡献','RFM定义、同值同分、F=1及标签边界在指标说明'),
('用户','同一用户同月多单只计一次；留存是当月再次活跃…','浅灰空白：未观察（NA） · 0：已观察但未回购','同月去重、完整窗口、298个NULL、左截断与色阶均保留在说明'),
('用户','数据内首次有效购买，不等同平台真实历史首购…','按样本内首次有效购买月份统计','首次购买与不完整首尾月份限制移入指标说明'),
('商品','从品类贡献定位重点，再查看累计集中度与月度结构。','了解品类贡献与销售结构。','副标题'),
('商品','当前商品范围…只统计选中类目的商品行…','已选：日期 · 地区 · 类目','范围规则移入指标说明'),
('商品','跨所选商品重新去重','订单去重','重新去重逻辑及跨类目不可相加在详情保留'),
('商品','01 · 找到品类贡献重点','品类销售排行','TOP5贡献来自当前查询'),
('商品','按金额降序展示全部品类…两条纵轴均从0开始…','商品成交额与累计贡献占比','移除坐标实现说明'),
('商品','当前金额排名TOP5的月度商品金额…缺失类目/月不填0…','TOP5品类 · 点击图例切换','缺失与完整月份规则移入指标说明'),
('履约','先核对配送与评价样本，再比较地区表现及逾期关联。','了解配送效率与评价表现。','副标题'),
('履约','当前订单范围…类目筛选表示订单包含该类目…','已选：日期 · 地区 · 类目','订单/类目范围及有效分母规则移入指标说明'),
('履约','配送时长缺失/无效…逾期判断缺失…评价缺失…','指标说明','真实缺失数量、可重叠与同日送达规则保留'),
('履约','每订单取最新评分，仅纳入有有效评分订单，避免多评价放大权重。','每单取最新有效评分','订单等权均分与最新评分的区别仍在说明'),
('履约','只比较有有效逾期判断且有订单评价…不能断言配送延迟导致差评','两组订单评价表现','样本条件、混杂、非因果解释和全样本区间入口在详情'),
('发现','固定P3全样本…这是历史描述性统计，不是实时预测或干预效果','全样本分析 · 观察日期 · 不随其他页面筛选变化','范围默认保留，方法边界在逐项详情'),
('发现','F01—F07编号、长标题及默认完整方法/样本','短标题、关键结果、一句话业务解读、查看分析依据','7项完整原文与统计数据均保留'),
('发现','默认展示 Bootstrap、95%区间、样本量与SQL','查看分析依据','F05样本表、订单均分/最新低评口径、两组区间、重采样次数与种子保留'),
('发现','分析文件生成…来源…报告与该快照一致…','逐项分析依据中的来源与生成时间','下载仍返回原报告字节'),
('发现','概览总数与当前显示数量重复','当前显示数量','保留专题筛选后的有效计数'),
('质量','证据分层：当前SQL…P0…P1/P3…刷新不会重建…','当前数据 / 历史审计 / 分析快照状态','不重复显示开发流程描述'),
('质量','P0审计 / P1建仓 / P3快照','历史审计状态与分析快照可用性','不把历史检查冒充当前执行'),
('质量','当前SQL记录数 / P0历史记录数','当前记录数 / 历史审计记录数','九表当前/历史对照保留'),
('质量','默认展示审计、关联、架构、构建与测试长表','缺失与重复 / 关联关系与异常 / 数据架构与约束 / 构建与对账记录 / 运行检查记录','默认折叠，原有查询与缺失筛选保留'),
('质量','查看文件SHA-256','移除UI哈希展示','原始文件与JSON导出中的哈希未改动'),
('质量','最近完整后端日志：阶段、通过/失败/跳过数量','最近运行检查：状态与执行时间（详情内）','页面不再展示测试数量；完整日志保留在文件与JSON导出'),
('质量','下载聚合质量证据 / 含明确来源时间历史当前标记','导出质量报告 / JSON · 含来源与检查时间','下载内容不变'),
]


def main():
    rows='\n'.join('| '+' | '.join(v.replace('|','\\|').replace('\n',' ') for v in row)+' |' for row in CHANGES)
    (ROOT/'docs/UI_COPY_BEFORE_AFTER.md').write_text('''# 全站UI文案修改前后对照

本轮仅调整前端文案、默认信息层级和原生展开帮助。颜色、字号、图表和业务查询沿用既有实现；下表列出默认文案及信息迁移，完整修改前源文件本地保存在`reports/ui-copy/before`，逐文件差异见`reports/ui-copy/frontend.diff`。

| 页面 | 修改前 | 修改后 | 保留与迁移 |
|---|---|---|---|
'''+rows+'\n',encoding='utf-8')
    diff=[]
    for old in sorted((OUT/'before').rglob('*')):
        if old.is_file():
            relative=old.relative_to(OUT/'before');new=ROOT/'frontend/src'/relative
            if new.exists():diff.extend(difflib.unified_diff(old.read_text(encoding='utf-8').splitlines(True),new.read_text(encoding='utf-8').splitlines(True),fromfile='before/'+relative.as_posix(),tofile='after/'+relative.as_posix()))
    new=ROOT/'frontend/src/findingCopy.ts'
    diff.extend(difflib.unified_diff([],new.read_text(encoding='utf-8').splitlines(True),fromfile='/dev/null',tofile='after/findingCopy.ts'))
    (OUT/'frontend.diff').write_text(''.join(diff),encoding='utf-8')
    result_path=OUT/'verification.json'
    if not result_path.exists():print('Wrote copy comparison; acceptance awaits verification.');return
    result=json.loads(result_path.read_text(encoding='utf-8'));assert result['passed']
    screenshots='\n'.join(f'| {label} | [首屏](screenshots/ui-copy/{key}-1440.png) / [全页](screenshots/ui-copy/{key}-1440-full.png) | [首屏](screenshots/ui-copy/{key}-1280.png) / [全页](screenshots/ui-copy/{key}-1280-full.png) | [修改前](screenshots/v2-04/{key}-1440-full.png) |' for key,label in [('overview','经营总览'),('users','用户价值'),('products','商品品类'),('delivery','履约评价'),('findings','经营发现'),('quality','数据质量')])
    report=f'''# RetailScope 全站UI文案精简验收报告

生成时间：{datetime.now().astimezone().isoformat(timespec='seconds')}。**文案与交互技术检查通过，等待视觉验收。**

## 完成内容

统一删除重复来源行、自证式导航说明、开发阶段徽标与重复页脚许可；Olist/Kaggle来源、2016–2018历史样本、CC BY-NC-SA 4.0和非商业属性集中在侧边栏，质量详情保留数据版本。保留原有六页面、配色、字体、导航、图表、筛选和导出。

总览保留四KPI、已选范围、月度切换和趋势；交易/状态区别、两类数据日期与完整月条件收进“指标说明”和“月份与解读说明”，局部筛选仍默认标明全样本趋势不联动。用户页保留全样本标识及NA/0图例，RFM基准/分位规则、同月去重与观察窗口收进说明。商品和履约优先显示结果，跨类目订单去重、有效分母、缺失、订单均分与每单最新评分区别在展开说明保留。

经营发现默认显示短标题、从真实结果提取的关键摘要、一句业务解读和“查看分析依据”。7项完整结果原文、样本量、分母、日期、SQL标识、方法、局限、建议、原聚合统计JSON均在详情保留。F05均分和低评分口径、样本表、95%区间、整群Bootstrap次数/种子及非因果解释完整保留，展开后图表正常显示。没有新统计计算。

质量中心默认展示九表规模、当前/历史对照、历史审计与分析快照状态；缺失重复、关联、架构约束、构建对账、运行检查分组折叠。UI不再展示哈希、阶段编号、测试数量；运行详情仅显示状态/时间/来源，完整历史记录和哈希仍保留在原文件与JSON导出。审计执行时间未记录仍如实显示“未记录”，文件保存时间单列。

[全站修改前后对照](UI_COPY_BEFORE_AFTER.md)覆盖{len(CHANGES)}项文案及迁移。旧阶段报告/截图未覆盖，原始修改前前端源码和逐文件diff保存在本地证据目录。

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
| 受保护源码/配置 | {result['protected_sources_unchanged']}项Python/SQL/API/.env哈希未变 |
| 原始数据/仓库 | Raw/Mart行数及全表内容指纹与已验收V2-04一致 |
| P0原验收文件 | {result['accepted_p0_files_unchanged']}项原CSV/审计文件SHA与P1保存值一致 |
| 核心业务接口 | 总览、用户、商品、履约、7项发现五个完整响应与修改前逐值相同 |

KPI仍为96,478有效订单、93,358购买用户、商品金额BRL13,221,498.11、平均订单商品金额BRL137.04；RFM、Cohort和P3结果未更改。后端代码/API业务逻辑、SQL、数据库和统计模型没有改动。

前端曾有4个旧标题/边界句的文本断言失败，更新为精简后的文字期望后通过，保留原统计结果、来源和局部范围检查；新增1项摘要不改变原证据的回归（含缺证据兜底）。本轮未删除原统计测试。后端144项全部真实执行通过。

## 最新实际截图

| 页面 | 1440×1000 | 1280×900 | 修改前参考 |
|---|---|---|---|
{screenshots}

另见[F05展开依据](screenshots/ui-copy/findings-evidence.png)。{len(result['screenshots'])}张PNG已逐张格式/尺寸verify，可由普通查看器打开；全页图按内容高度保存，浏览器原生滚动条可能使内容宽度少15px。首屏尺寸严格为1440×1000或1280×900。

## 日志与修改文件

本地`reports/ui-copy/`：`baseline.json`、`before/`、`frontend.diff`、`pytest.log/xml`、`frontend_tests.log`、`typecheck.log`（成功无输出）/`typecheck_result.json`、`build.log`、`browser.log`、`screens.log`、`verification.json/log`及实际下载文件。浏览器脚本`scripts/ui_copy_browser.js`、最终截图脚本`scripts/ui_copy_screens.js`、独立核查`scripts/verify_ui_copy.py`可复核执行动作。

修改：`frontend/src/App.tsx`、`AnalysisUI.tsx`、`presentation.ts`、`analysis.ts`、`evidence.ts`、`evidence.css`、`overview.css`、六个`pages/*.tsx`；`frontend/tests/presentation.test.ts`仅文案断言。
新增：`frontend/src/findingCopy.ts`、`frontend/tests/findingCopy.test.ts`、`scripts/ui_copy_browser.js`、`scripts/ui_copy_screens.js`、`scripts/verify_ui_copy.py`、`scripts/write_ui_copy_report.py`，本报告与对照表、`docs/screenshots/ui-copy/`最新截图。

CSS仅为原生详情正文补充既有字号/色值和间距，并修正总览删去重复说明后“已选范围”的对齐选择器，没有更改全局字体、颜色、图表配置与页面网格。没有删除文件、引入付费服务或新业务功能，没有推送GitHub或部署公网。

## 验证范围

本轮验证当前本机Chromium两种桌面尺寸及既有数据，未重做干净系统安装、移动端或公网负载验收。详情由用户点击展开；简化了默认展示，没有删除分析依据。最终视觉判断等待用户验收，完成后停止开发。
'''
    (ROOT/'docs/UI_COPY_ACCEPTANCE_REPORT.md').write_text(report,encoding='utf-8')
    print('Wrote acceptance and',len(CHANGES),'copy comparison rows.')


if __name__=='__main__':main()
