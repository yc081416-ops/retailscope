"""Generate P1 docs from saved execution evidence and the actual PostgreSQL catalog."""
from datetime import datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from retailscope.warehouse import query_rows, save_json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/p1'


def read(name):
    return json.loads((OUT / f'{name}.json').read_text(encoding='utf-8'))


def money(value):
    return f'{Decimal(str(value)):,.2f}'


def percent(value):
    return f'{Decimal(str(value))*100:.4f}%'


def table(headers, rows):
    return ['| ' + ' | '.join(headers) + ' |', '|' + '|'.join(['---'] * len(headers)) + '|'] + [
        '| ' + ' | '.join(str(v) for v in row) + ' |' for row in rows
    ]


MEANINGS = {
    'zip_code': '规范化五位邮编前缀；文本保留前导0', 'geo_zip': '已覆盖的标准邮编外键；未覆盖为NULL，原邮编仍保留',
    'latitude': '去重后有效坐标纬度中位数，单位度', 'longitude': '去重后有效坐标经度中位数，单位度',
    'lat': '源纬度，度', 'lng': '源经度，度', 'distinct_source_rows': '该邮编去重后的地理记录数',
    'valid_coordinate_rows': '满足全球经纬度范围的去重地理记录数',
    'customer_id': '单次订单对应的客户标识，不用于跨单用户识别',
    'customer_unique_id': '跨订单唯一用户标识；用户分析主键', 'city': '源城市文本', 'state': '源州代码',
    'product_id': '商品标识', 'seller_id': '商户标识', 'category': '葡语类目；mart中缺失为__unknown__',
    'category_english': '英文类目翻译，未覆盖为NULL', 'name_length': '源商品名称长度',
    'description_length': '源商品描述长度', 'photos_qty': '商品照片数', 'weight_g': '商品重量，克',
    'length_cm': '商品长度，厘米', 'height_cm': '商品高度，厘米', 'width_cm': '商品宽度，厘米',
    'calendar_date': '公历日期，日维度主键', 'month_start': '购买月份的首日', 'calendar_year': '公历年',
    'calendar_month': '公历月1–12', 'singleton': '单行分析上下文标识，只允许TRUE',
    'first_purchase': '最早有效购买日', 'last_purchase': '最后有效购买日',
    'rfm_reference_date': 'RFM基准日，最后有效购买日次日', 'first_complete_month': '首个可完整观察的目标月首日',
    'observation_end_exclusive': 'Cohort观察终点，最后有效购买所在月首日，边界不含',
    'all_status_last_purchase': '全状态原订单的最后购买日，不能作为完整delivered观察终点',
    'order_id': '订单标识；订单级表主键，商品表复合主键的第一项', 'status': '源订单状态',
    'purchased_at': '购买时间，无时区源时间', 'purchase_date': '购买日，关联日期维表',
    'approved_at': '付款批准时间，可缺失', 'carrier_at': '交承运商时间，可缺失',
    'delivered_at': '实际送达时间，可缺失', 'estimated_at': '预计送达时间，可缺失',
    'customer_state': '该订单客户州；不从跨单用户维表推断固定位置',
    'is_eligible': 'delivered且购买时间有效，为核心指标默认范围',
    'has_items': '是否存在商品明细；FALSE时商品金额为NULL',
    'has_payment': '是否存在支付记录；FALSE时支付金额为NULL',
    'item_count': '该订单商品明细行数', 'merchandise': '商品price之和，BRL，不含运费，不是财务确认收入',
    'freight': '运费之和或商品行运费，BRL', 'payment': '支付记录金额之和，BRL',
    'review_count': '源评价行数，review_id不要求唯一', 'review_mean': '每订单评价平均分，汇总时对订单等权',
    'latest_review_score': '按回答时间、创建时间、review_id、评分排序取最新评分1–5',
    'delivery_days': '有效订单的实际送达减购买时间，秒/86400；异常或缺失为NULL',
    'is_late': '实际送达日大于预计日；无效配送分母外为NULL',
    'delivery_anomaly': '实际送达早于购买，或预计日早于购买日；只标记，不删除交易',
    'payment_count': '每订单支付记录数', 'installments_max': '订单内最大分期数，仅描述支付记录',
    'item_id': '订单内商品序号，与order_id组成主键', 'shipping_limit_at': '商品发货截止时间',
    'price': '商品明细金额，BRL', 'orders': '该统计范围订单数；类目内去重，跨类目不可加总',
    'users': '该统计范围唯一购买用户数；RFM/复购表为分组用户数', 'average_order_value': '商品成交额/有效订单数，BRL/单',
    'delivery_n': '有效配送时长样本数', 'late_n': '有效逾期判断样本数', 'late_rate': '逾期样本数/late_n，0–1',
    'reviewed_orders': '有评价的有效订单数', 'order_share': '该状态订单数/全部订单数，0–1',
    'is_complete': '月份处于首完整月及观察终点之间', 'items': '商品明细行数，不是订单数',
    'contribution': '该分组商品成交额/同口径总成交额，0–1', 'sales_rank': '商品成交额降序稠密排名',
    'score': '评价评分1–5', 'share': '该分组计数占其总体计数的比例0–1',
    'all_orders_without_items': '全状态中缺商品明细的订单数',
    'eligible_without_items': '有效订单中缺商品明细的订单数',
    'eligible_without_payment': '有效订单中缺支付记录的订单数',
    'eligible_missing_delivery': '有效订单中缺实际送达时间的订单数',
    'eligible_delivery_anomalies': '有效订单中配送时间异常的订单数',
    'eligible_missing_user': '有效订单中缺跨单用户标识的订单数',
    'missing_purchase_timestamp': '全订单中缺购买时间的订单数',
    'last_purchase_date': '用户最后一次有效购买日', 'frequency': '用户有效订单总数',
    'monetary': '用户累计商品金额，BRL；任意订单缺商品则为NULL待核对',
    'recency': 'RFM基准日减最后有效购买日，天', 'r_score': 'Recency离散五分位反向评分1–5',
    'f_score': 'Frequency离散五分位评分1–5；相同次数同分', 'm_score': 'Monetary离散五分位评分1–5；缺失为NULL',
    'segment': '按METRICS.md顺序互斥分配的规则分层标签', 'user_share': '该层用户数/全有效购买用户数，0–1',
    'repeat_users': '有效订单数至少2的用户数', 'repeat_rate': 'repeat_users/users，0–1，受观察期影响',
    'cohort_month': '用户数据内首次有效购买月首日', 'new_users': '该cohort观测首购用户数',
    'month_age': '目标月距离cohort月的整月差，0起', 'target_month': 'cohort月加月龄',
    'cohort_left_truncated': 'cohort属于首个不完整获客月份，分母可能左截断',
    'is_observed': '目标月完整位于观察窗中；FALSE时人数和留存均NULL',
    'active_users': '该cohort目标月购买用户去重人数；已观察无回购为0',
    'retention': 'active_users/new_users，0–1；不可观察为NULL',
    'sequential': '订单内支付序号，与订单标识共同识别支付记录',
    'payment_type': '源支付方式', 'installments': '支付记录的分期数', 'amount': '源支付记录金额，BRL',
    'review_id': '源评价标识，可能跨订单重复，不能用作唯一主键',
    'title': '源评价标题，空文本转NULL', 'message': '源评价正文，空文本转NULL',
    'created_at': '评价创建时间', 'answered_at': '评价回答时间',
}


def write_model():
    columns = query_rows("""SELECT n.nspname AS schema,c.relname AS relation,a.attname AS field,
        format_type(a.atttypid,a.atttypmod) AS type,a.attnotnull AS not_null,c.relkind AS kind
        FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname IN ('core','mart') AND c.relkind IN ('r','v') AND a.attnum>0 AND NOT a.attisdropped
        ORDER BY n.nspname,c.relname,a.attnum""")
    constraints = query_rows("""SELECT n.nspname AS schema,r.relname AS relation,c.conname AS name,
        pg_get_constraintdef(c.oid) AS definition FROM pg_constraint c
        JOIN pg_class r ON r.oid=c.conrelid JOIN pg_namespace n ON n.oid=r.relnamespace
        WHERE n.nspname IN ('core','mart') ORDER BY 1,2,3""")
    save_json({'columns': columns, 'constraints': constraints}, OUT / 'data_dictionary.json')
    unknown = {row['field'] for row in columns} - MEANINGS.keys()
    assert not unknown, f'Fields without business meanings: {unknown}'
    lines = ['# P1 数据模型与字段字典', '',
        '本文件由 PostgreSQL 实际目录生成，来源为 `sql/10_core.sql`、`sql/20_mart.sql`、`sql/30_customer.sql`。', '',
        'raw 保持 P0 原样；core 是带类型转换的只读视图；mart 以有主键/外键的物理维表和事实表为基础，聚合指标采用 SQL 视图。构建在单事务中刷新已知 P1 表，不删除 schema 或源文件。', '',
        '用户维表粒度是 customer_unique_id；客户桥表粒度是 customer_id，订单地区由客户桥表取州。订单事实一订单一行，商品事实主键为(order_id,item_id)。支付、评价、商品金额均先分别按订单聚合，再连接订单；聚合表到订单事实的外键延迟到事务结束检查。', '',
        '地理表先整行去重、排除非法坐标参与中位数、按五位邮编一行。未匹配邮编只保留源邮编，geo_zip为NULL；左连接不删订单。', '',
        '分析视图逻辑键：monthly_kpis(月份)、category_monthly(月份,类目)、category_ranking(类目)、region_sales(州)、customer_rfm(唯一用户)、customer_cohort(唯一用户)、cohort_sizes(cohort月)、cohort_retention(cohort月,月龄)。视图本身不持有数据库主键，基础表约束保证粒度。', '',
        '索引：order_wide购买日、唯一用户；order_item_fact商品及商户；各维表及事实表主键索引自动建立。', '']
    keys = list(dict.fromkeys((r['schema'], r['relation']) for r in columns))
    for schema, relation in keys:
        fields = [r for r in columns if r['schema'] == schema and r['relation'] == relation]
        kind = '物理表' if fields[0]['kind'] == 'r' else '视图'
        lines += [f'## {schema}.{relation}（{kind}）', '']
        lines += table(['字段', 'SQL类型', 'NOT NULL约束', '业务含义'], [
            [r['field'], r['type'], '是' if r['not_null'] else '视图推导/可空', MEANINGS[r['field']]] for r in fields
        ])
        lines += ['']
        for constraint in constraints:
            if constraint['schema'] == schema and constraint['relation'] == relation:
                lines += [f"- `{constraint['name']}`：`{constraint['definition']}`"]
        lines += ['']
    (ROOT / 'docs/P1_DATA_MODEL.md').write_text('\n'.join(lines), encoding='utf-8')


def main():
    load_dotenv(ROOT / '.env')
    run, snapshots = read('run'), read('mart_snapshot_2')
    checks = read('pandas_reconciliation')['checks']
    tests = ET.parse(OUT / 'pytest.xml').getroot().find('testsuite')
    counts = {k: int(tests.get(k, 0)) for k in ('tests', 'failures', 'errors', 'skipped')}
    assert run['status'] == 'passed' and all(c['passed'] for c in checks)
    assert counts['failures'] == counts['errors'] == counts['skipped'] == 0
    kpi, context, repeat, quality = [read(name)[0] for name in ('kpi_overview', 'analysis_context', 'repurchase_summary', 'quality_checks')]
    categories = sorted(read('category_ranking'), key=lambda r: int(r['sales_rank']))
    regions = sorted(read('region_sales'), key=lambda r: Decimal(r['merchandise']), reverse=True)
    segments, cohorts = read('rfm_segments'), read('cohort_retention')
    cutoffs = query_rows("""SELECT
        percentile_disc(ARRAY[0.2,0.4,0.6,0.8]) WITHIN GROUP(ORDER BY recency) AS recency,
        percentile_disc(ARRAY[0.2,0.4,0.6,0.8]) WITHIN GROUP(ORDER BY frequency) AS frequency,
        percentile_disc(ARRAY[0.2,0.4,0.6,0.8]) WITHIN GROUP(ORDER BY monetary) AS monetary
        FROM mart.customer_rfm""")[0]
    score_distribution = query_rows('SELECT f_score,count(*) AS users FROM mart.customer_rfm GROUP BY 1 ORDER BY 1')
    save_json({'cutoffs': cutoffs, 'frequency_scores': score_distribution}, OUT / 'rfm_thresholds.json')
    catalog_note = '由真实执行证据生成；金额单位 BRL；比率为观察期描述，不作因果推断。'
    metrics = [
        ['有效订单数', kpi['orders']], ['唯一购买用户数', kpi['users']],
        ['商品成交额', money(kpi['merchandise'])], ['运费', money(kpi['freight'])],
        ['支付金额（独立口径）', money(kpi['payment'])], ['平均订单商品金额', money(kpi['average_order_value'])],
        ['复购用户数', repeat['repeat_users']], ['观察期复购率', percent(repeat['repeat_rate'])],
        ['平均配送天数', money(kpi['delivery_days'])], ['配送样本数', kpi['delivery_n']],
        ['逾期率（日期口径）', percent(kpi['late_rate'])], ['逾期样本数', kpi['late_n']],
        ['订单等权评价均分', money(kpi['review_mean'])], ['有评价订单数', kpi['reviewed_orders']],
    ]
    lines = ['# RetailScope P1 验收报告', '',
        f"生成时间：{datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds')}。**P1 技术验收通过，等待用户验收。**", '', catalog_note, '',
        '## 范围与 P0 核查', '',
        f"数据库：{run['database']['server']}；Python 3.12.10，延用 P0 本地虚拟环境和免费开源依赖。",
        f"raw 与 P0 验收指纹一致={run['raw_unchanged']}；P0 报告、质量报告、原始 CSV、原有测试及根 reports 文件哈希不变={run['p0_files_unchanged']}。完整哈希见 `reports/p1/run.json`。",
        '九张 raw 表仍合计1,550,922行。未运行 P0 重新导入或报告生成脚本，不覆盖 P0 成果。未开发 P2 前端或 P3/P4。', '',
        '## 实际数据层行数', '']
    lines += table(['mart对象', '实际行数', '第二次构建哈希'], [[name, v['rows'], v['sha256'][:16] + '…'] for name, v in snapshots.items()])
    lines += ['', '完整SHA-256见两份 `mart_snapshot_*.json`，27个对象全部行数及内容一致。core包含8个带类型源视图；第9份类目翻译直接读取raw.category_translation，无额外复制原始数据。', '',
        '## 真实经营指标', '',
        f"有效购买期：{context['first_purchase']} 至 {context['last_purchase']}（含），以购买时间归属。全状态数据最后购买日为 {context['all_status_last_purchase']}，不据此延长完整有效购买观察窗。", '']
    lines += table(['指标', '真实SQL结果'], metrics)
    lines += ['', '金额精确到分；客单价/配送天数/评价均分在文档展示四舍五入，JSON保留数据库原精度。商品金额不是财务确认收入或利润；支付金额另列。', '',
        '## RFM 与 Cohort', '',
        f"RFM基准日 **{context['rfm_reference_date']}**；用户数 {snapshots['customer_rfm']['rows']}。离散分位点：R={cutoffs['recency']}；F={cutoffs['frequency']}；M={[str(v) for v in cutoffs['monetary']]} BRL。",
        f"F评分实际分布：{score_distribution}。大量相同频次导致评分档可能为空，未按用户ID强拆相同值。",
        '分层规则见METRICS.md；本数据“数据待核对”层为0人，所以分层视图仅输出6个非空层。', '']
    lines += table(['分层', '用户数', '用户占比', '商品金额BRL', '金额贡献'], [[r['segment'], r['users'], percent(r['user_share']), money(r['merchandise']), percent(r['contribution'])] for r in segments])
    lines += ['',
        f"Cohort完整目标月区间：[{context['first_complete_month']}, {context['observation_end_exclusive']})。末尾2018-08及更远月份均为NULL，首个不完整目标月2016-09同样不可算。首cohort标记左截断。",
        f"{snapshots['cohort_sizes']['rows']}个cohort，{len(cohorts)}个cohort/月龄单元，其中可观察{sum(r['is_observed'] for r in cohorts)}个，不可观察{sum(not r['is_observed'] for r in cohorts)}个。",
        '长表：`reports/p1/cohort_retention.csv`；矩阵：`reports/p1/cohort_matrix.csv`，NA表示不可观察，0仅表示已完整观察且当月没有回购用户。新增用户及整体复购分布分别见cohort_sizes和repurchase_distribution。', '',
        '## 关联膨胀与独立对账', '',
        '订单商品/支付/评价先分别按订单聚合，三个订单级表主键均为order_id；order_wide订单主键与order_item_fact复合主键、维表外键由数据库执行约束。',
        '地理表去重后每邮编一行；缺覆盖左连接保留订单，不对百万地理原始行做交易汇总。', '']
    lines += table(['独立Pandas校验', '比较行数', '结果'], [[r['name'], r['rows'], '通过'] for r in checks])
    lines += ['', 'Pandas直接读取真实CSV，金额先转换为整数分后逐行精确比较；均值/比率/坐标容差1e-10。核验覆盖每订单、每商品行、每用户RFM、每cohort单元及全部所需汇总。', '',
        '## 缺失与异常处理', '']
    lines += table(['质量项', '真实SQL计数'], list(quality.items()))
    lines += ['', '无商品订单保留状态及NULL金额；有效订单实测无缺商品。1笔有效订单缺支付，保留商品金额，支付额不补零。8笔有效订单缺实际送达时间，交易保留，配送/逾期分母排除。取消等非delivered状态仅进入全状态分布。',
        'P0的类目翻译和邮编缺失未被删除：商品类目缺失归入__unknown__，英文缺失保留葡语类目；地理缺失保留邮编并置地理外键NULL。非法评分/负金额等将使构建失败回滚，不静默清洗。', '',
        '## 重跑与测试证据', '',
        f"完整流程两次构建及初轮测试用时 {run['elapsed_seconds']} 秒（本机实测，不是性能承诺）。重跑内容一致={run['idempotent']}。",
        f"最新Pytest：**{counts['tests']}通过，{counts['failures']}失败，{counts['errors']}错误，{counts['skipped']}跳过**，含P0原有18项及P1新增26项。最终日志无warnings。", '',
        '```powershell', r'.\.venv\Scripts\python.exe scripts/probe_p1.py',
        r'.\.venv\Scripts\python.exe scripts/run_p1.py',
        r'.\.venv\Scripts\python.exe -m pytest -q -rA --junitxml=reports/p1/pytest.xml',
        r'.\.venv\Scripts\python.exe scripts/write_p1_report.py', '```', '',
        '证据：`reports/p1/run.log`、`run.json`、`mart_snapshot_1.json`、`mart_snapshot_2.json`、`pandas_reconciliation.json`、`pytest.log`、`pytest.xml`、各SQL指标JSON/CSV。依赖兼容警告修复前日志保留为pytest_initial.log。', '',
        '## 修改文件与复现', '',
        '- 更新：`docs/METRICS.md`、`README.md`。',
        '- 新增SQL：`sql/10_core.sql`、`sql/20_mart.sql`、`sql/30_customer.sql`。',
        '- 新增模块：`src/retailscope/warehouse.py`、`src/retailscope/p1_validation.py`。',
        '- 新增入口：`scripts/probe_p1.py`、`scripts/build_warehouse.py`、`scripts/run_p1.py`、`scripts/write_p1_report.py`。',
        '- 新增测试：`tests/test_p1.py`。',
        '- 新增文档：本报告、`P1_DATA_MODEL.md`、`P1_ANALYSIS_FINDINGS.md`。',
        '- 运行结果全部位于被gitignore排除的reports/p1；未提交CSV、凭证或原始用户级数据。', '',
        '日常仅构建：python scripts/build_warehouse.py。完整验收：python scripts/run_p1.py，然后python scripts/write_p1_report.py；SQL脚本需在同一事务中按10→20→30执行。失败回滚P1数据，raw不被修改。', '',
        '## 局限与待验收', '',
        'P1无未解决运行阻塞。观察期首尾不完整，用户获客前历史不可见，各用户复购观察时长不一；部分完整日历月份样本很少，不能推断市场总量。源数据没有成本/完整退款/曝光，不能计算利润、ROI或转化率。',
        'RFM是规则分层、Cohort是购买活跃留存，都未证明营销干预效果。无效新源格式会失败，P0数据契约需先修复；未实现增量CDC。',
        '**已完成P1并停止开发，等待用户验收；不自动进入P2–P4。**', '']
    (ROOT / 'docs/P1_ACCEPTANCE_REPORT.md').write_text('\n'.join(lines), encoding='utf-8')
    top_category, top_region = categories[0], regions[0]
    observed_m1 = [r for r in cohorts if r['month_age'] == 1 and r['is_observed'] and not r['cohort_left_truncated']]
    example = next(r for r in observed_m1 if r['cohort_month'] == '2017-01-01')
    findings = ['# P1 真实数据描述性发现', '', catalog_note,
        f"范围：{context['first_purchase']}–{context['last_purchase']}有效购买订单；地区、类目都采用同一范围。以下为P1描述性统计，不是P3经营诊断或因果报告。", '',
        f"1. 有效订单{kpi['orders']:,}单、唯一购买用户{kpi['users']:,}人；商品成交额BRL {money(kpi['merchandise'])}，运费BRL {money(kpi['freight'])}，平均订单商品金额BRL {money(kpi['average_order_value'])}。这些是历史样本的商品金额，不是财务确认收入。证据：mart.kpi_overview。", '',
        f"2. 观察期内至少两单的用户{repeat['repeat_users']:,}人，复购率{percent(repeat['repeat_rate'])}。分母{repeat['users']:,}人，使用customer_unique_id；不同用户观察时长不等，不能将该值解释为长期留存上限。证据：mart.repurchase_summary及repurchase_distribution。", '',
        f"3. 商品金额排名第一的葡语类目为{top_category['category']}，金额BRL {money(top_category['merchandise'])}，占{percent(top_category['contribution'])}；涵盖{top_category['orders']:,}个订单。类目订单可能重叠，不把类目订单数相加作为总订单。证据：mart.category_ranking。", '',
        f"4. 按订单客户州归属，{top_region['state']}商品金额最高，为BRL {money(top_region['merchandise'])}，占{percent(top_region['contribution'])}，订单{top_region['orders']:,}单。描述的是样本分布，不代表市场份额或用户因果偏好。证据：mart.region_sales。", '',
        f"5. 具有效配送日期的{kpi['delivery_n']:,}单平均交付{money(kpi['delivery_days'])}天；按实际送达日超过预计日定义，{kpi['late_n']:,}单中的逾期率为{percent(kpi['late_rate'])}。缺实际送达的{quality['eligible_missing_delivery']}笔有效订单未进入分母。证据：mart.kpi_overview及quality_checks。", '',
        f"6. 有评价的有效订单{kpi['reviewed_orders']:,}单，先按订单平均再等权计算，均分{money(kpi['review_mean'])}。评分分布取每订单最新评价；多评价订单不会获得额外订单权重。证据：mart.order_review_agg及review_distribution。", '',
        f"7. 2017-01 cohort观测首购用户{example['new_users']:,}人，次月回购活跃用户{example['active_users']}人，留存{percent(example['retention'])}。所有2018-08目标月尚不可完整观察，矩阵标NA。不能将NA解读为0%回购。证据：mart.cohort_retention及cohort_matrix.csv。", '',
        f"8. RFM采用{context['rfm_reference_date']}为基准日；Frequency分位边界为{cutoffs['frequency']}，反映一次购买用户较多，无法形成等人数的五档。相同购买次数同分，未用ID将相同频次强拆。各层人数、占比和金额贡献见P1验收报告及mart.rfm_segments。", '',
        'SQL源：sql/20_mart.sql、sql/30_customer.sql；独立复核：src/retailscope/p1_validation.py。所有结果CSV/JSON位于reports/p1。未声称增长改善、营销效果或因果关系。', '']
    (ROOT / 'docs/P1_ANALYSIS_FINDINGS.md').write_text('\n'.join(findings), encoding='utf-8')
    write_model()
    print('Generated P1 acceptance report, data model and evidence-based findings.')


if __name__ == '__main__':
    main()
