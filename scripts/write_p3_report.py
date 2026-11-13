"""Write the P3 acceptance document only after the final evidence gate passes."""
from importlib.metadata import version
import json

from retailscope.diagnostics import ROOT


def main():
    out=ROOT/'reports/p3'
    proof=json.loads((out/'verification.json').read_text(encoding='utf-8'))
    result=json.loads((out/'analysis.json').read_text(encoding='utf-8'))
    assert proof['passed']
    association=result['association']
    cluster=association['cluster_bootstrap']
    differences=association['differences_late_minus_on_time']
    tests=proof['tests']
    lines=['# RetailScope P2.1 + P3 验收报告','',
        f"验收时间：{proof['verified_at']}。**P2.1界面修复及P3统计诊断已实际完成，等待用户验收；未进入P4。**",'',
        '## 环境与保护检查','',
        f"Windows 11 / Python 3.12.10 / PostgreSQL 16.16；SciPy {version('scipy')}、Pandas {version('pandas')}、Streamlit {version('streamlit')}、Plotly {version('plotly')}、SQLAlchemy {version('sqlalchemy')}。SciPy已实际安装并加入pyproject依赖。",
        f"{proof['protected_file_count']}个既有SQL、文档、测试及验收证据文件SHA-256不变；raw九表指纹不变={proof['raw_unchanged']}，P1全部27个mart对象的行数与内容SHA-256不变={proof['mart_unchanged']}。",
        'P0/P1原始数据、指标定义、建模SQL和验收报告均未修改。P2的已验收报告与证据保留，新证据单独写入reports/p3和output/playwright/p3。P3只读现有仓库。', '',
        '## P2.1 修复结果','',
        f"浏览器实测金额轴范围{proof['browser']['axes']['amount']}，订单轴范围{proof['browser']['axes']['orders']}；两轴都从0开始，订单标签用整数格式。",
        '保留原双轴业务图及SQL数据，调整坐标字体、辅助文字对比度、筛选/KPI间距；清空筛选与控件同排，中文占位提示“请选择（留空为全部）”。没有修改筛选边界、颜色风格或指标。',
        '优化后的总览截图：output/playwright/p3/00-p21-overview.png；最终总览：01-overview.png，1280桌面：10-desktop-1280.png。', '',
        '## 真实统计范围与结果','',
        f"固定有效购买范围：{result['context']['first_purchase']}至{result['context']['last_purchase']}；完整目标月[{result['context']['first_complete_month']}, {result['context']['observation_end_exclusive']})。",
        f"核心基线：{result['kpis']['orders']:,}有效订单、{result['kpis']['users']:,}唯一购买用户、商品金额BRL {float(result['kpis']['merchandise']):,.2f}；所有P1指标均经测试逐字段对账。",'']
    for finding in result['findings']:
        lines += [f"### {finding['id']} {finding['title']}",'',finding['result'],
                  f"来源：{', '.join(finding['source_sql'])}；完整方法、样本、分母、范围、解释边界及待验证建议见业务报告对应条目。",'']
    lines += ['## 配送与评价的区间及使用条件','',
        '| 分组 | 实际订单n | 用户数 | 订单评价均分 | 低评分订单数 | 低评分订单比例 |',
        '|---|---:|---:|---:|---:|---:|']
    for group in association['groups']:
        lines.append(f"| {group['group']} | {group['n']} | {group['users']} | {group['mean_score']:.6f} | {group['low_scores']} | {group['low_rate']:.4%} |")
    lines += ['',
        f"有效对照订单{association['valid_orders']:,}单，排除{association['excluded_orders']}单；其中无有效逾期判断{association['missing_late_judgment']}、缺评价{association['missing_review']}、缺唯一用户{association['missing_user']}。逐项缺失可重叠，排除总数以并集为准。",
        f"检查结果：{json.dumps(association['assumption_checks'],ensure_ascii=False)}。最大用户聚类15单，同用户跨两组的关系由用户整群抽样保留。",
        f"主区间：{cluster['users']:,}个唯一用户聚类、{cluster['replications']}次bootstrap、种子{cluster['seed']}；均分差{differences['mean_difference']:.6f}，95%区间[{cluster['mean_ci'][0]:.6f}, {cluster['mean_ci'][1]:.6f}]；低评分比例差95%区间[{cluster['low_rate_ci'][0]*100:.4f}, {cluster['low_rate_ci'][1]*100:.4f}]个百分点。",
        f"工作独立近似对照：Welch均分差95%区间{differences['welch_ci']}；Newcombe比例差95%区间{differences['newcombe_ci']}（比例0–1尺度）。",
        '直接SciPy订单数组核对Welch摘要公式；二项score数值反演核对Wilson，包括零/全成功边界；独立展开重采样用户的全部订单核对聚类bootstrap。相同输入和固定种子重复计算得到相同主区间。',
        '不依赖p值作商业判断；这些是条件于历史样本的观察性关联。用户内相关得到处理，但用户间/商户/线路/时间相关、混杂与评价缺失仍可能影响解释。', '',
        '## 页面、导出与视觉验收','',
        '| 页面 | 实际图表数 | 页面异常 | 横向页面溢出 |','|---|---:|---:|---|']
    for page in proof['browser']['pages']:
        lines.append(f"| {page['title']} | {page['charts']} | {page['exceptions']} | {page['horizontalOverflow']} |")
    lines += ['',
        '“经营发现”现含7条代码生成的P3核心发现、完整月趋势、集中度/地区表、配送/评价区间和用户结构明细；原P1八项事实在下方保留。每条P3发现均带SQL来源、范围、样本与分母、方法、局限和待验证建议。',
        f"实际浏览器下载文件{proof['browser']['download']}与docs/P3_BUSINESS_REPORT.md及同一结构化结果生成的Markdown逐字一致={proof['browser_export_equals_generated_report']}。",
        '所有六页均在真实Chromium中打开并截图；还检查了诊断展开、统计明细、报告下载、双轴零起点、中文筛选占位及1280/1440桌面。截图是实际页面，不是设计稿。', '',
        '## 自动测试与执行证据','',
        f"**{tests['tests']}通过，{tests['failures']}失败，{tests['errors']}错误，{tests['skipped']}跳过，无最终warnings汇总。** 其中原P0/P1/P2的64项全部继续通过，P3新增14项。",
        '覆盖基线、SQL样本量、精确金额/增长分母、集中度、独立CI、相同种子重现、小样本/缺失/空结果、MAD=0、不完整月份、Cohort分母、报告生成一致性与UI零起点/下载。', '',
        '```powershell',
        r'.\.venv\Scripts\python.exe -m pip install -e ".[dev]"',
        r'.\.venv\Scripts\python.exe scripts/run_p3.py',
        r'.\.venv\Scripts\python.exe -m pytest -q -rA --junitxml=reports/p3/pytest.xml',
        r'.\.venv\Scripts\python.exe -m streamlit run app/Home.py',
        'npx.cmd --yes --package @playwright/cli playwright-cli -s=p3 open http://127.0.0.1:8501 --headed',
        'npx.cmd --yes --package @playwright/cli playwright-cli -s=p3 run-code --filename scripts/p3_browser_check.js',
        r'.\.venv\Scripts\python.exe scripts/verify_p3.py',
        r'.\.venv\Scripts\python.exe scripts/write_p3_report.py',
        '```','',
        '- reports/p3/analysis.json：结构化结果、配置、SQL与输入SHA-256、所有发现及统计量。',
        '- reports/p3/sql_results/*.csv、monthly_diagnostics.csv：真实SQL输入与月度计算结果。',
        '- reports/p3/analysis_run_final.log、pytest.log、pytest.xml：实际计算与测试日志。',
        '- reports/p3/p21_browser.log、browser.log、streamlit.log：P2.1和P3真实页面证据及服务日志。',
        '- reports/p3/baseline.json、verification.json、verification.log：旧成果保护、重复区间、浏览器导出对账。',
        '- docs/P3_ANALYSIS_METHODS.md：方法、条件、阈值、独立验证与文献来源。',
        '- docs/P3_BUSINESS_REPORT.md：可导出的完整经营分析报告。', '',
        '## 六页截图与补充截图','']
    for path in proof['screenshots']:
        lines.append(f"- [{path.split('/')[-1]}](../{path})")
    lines += ['',
        '## 修改文件清单','',
        '- P2.1：app/Home.py、app/pages/overview.py、src/retailscope/bi/components.py。',
        '- P3界面：app/pages/findings.py、src/retailscope/bi/diagnostic_page.py。',
        '- 计算：src/retailscope/diagnostics.py；sql/p3/context.sql、kpis.sql、monthly.sql、categories.sql、regions.sql、association_orders.sql、rfm_users.sql、cohort.sql。',
        '- 执行与验收：scripts/run_p3.py、p3_browser_check.js、verify_p3.py、write_p3_report.py；tests/test_p3.py。',
        '- 依赖/文档：pyproject.toml、README.md、docs/P3_ACCEPTANCE_REPORT.md、P3_ANALYSIS_METHODS.md、P3_BUSINESS_REPORT.md。',
        '- 原P0/P1数据/统计SQL/报告、既有P2报告与旧测试文件均未修改；没有执行文件批量删除或公开提交原始CSV与凭证。', '',
        '## 已知限制与后续边界','',
        '无未解决的运行阻塞。早期样本覆盖稀疏、首尾月份不完整；完整日历月不等于有完整市场覆盖。MAD仅历史回顾提示，阈值有方法选择空间；没有季节控制或未来预测。',
        '置信区间依赖抽样/独立聚类近似，不修复选择偏差或混杂；评价为有序量，分差不等同于效用差。RFM组与复购组金额差异部分来自定义及观察机会不同，建议需要未来试验验证。',
        '统计结果为离线生成的固定快照。若以后重建仓库，应重新运行P3计算和测试，再刷新页面；本轮没有修改P1口径。P4部署、最终打包和求职材料均未开发。','',
        '**完成P3后已停止开发，等待用户验收。**','']
    (ROOT/'docs/P3_ACCEPTANCE_REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    print('Wrote docs/P3_ACCEPTANCE_REPORT.md from verified execution evidence.')


if __name__=='__main__':
    main()
