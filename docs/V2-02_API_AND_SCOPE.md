# V2-02 分析接口与范围约定

新增三个分析页面，复用已冻结的V2-01.1视觉变量和P1/P3分析成果。没有修改src/retailscope、sql、原始CSV或统计模型；旧版Streamlit继续可用。

## 公共访问层

api/queries.py承接原api/main.py中的数据库连接、标量序列化、参数校验及查询函数。main.py继续向旧测试暴露相同函数，并注册新增分析路由；旧总览响应不变。

- PostgreSQL16、SQLAlchemy、REPEATABLE READ事务。
- default_transaction_read_only=on，连接超时5秒、查询超时20秒，有限连接池。
- 金额/比例以Decimal字符串返回，日期以ISO字符串返回，NULL仍为JSON null。
- 动态值均绑定参数；州白名单、类目取已有维表白名单、page/table受白名单约束；不接受任意SQL。
- 不返回数据库密码或连接串；异常中间件仅记录请求路径和异常类型，返回脱敏503。

## 三个GET分析接口

### /api/analysis/users

固定全样本，不接受start/end/state/category局部过滤，传入会返回422，避免虚假联动。

返回segments、frequency、summary、cohort、new_users、scope及metadata，直接对应FIXED中的rfm、frequency、repurchase、cohort、new_users。没有返回用户ID级明细。

- 唯一用户使用customer_unique_id；有效购买范围2016-09-15—2018-08-29。
- RFM基准日2018-08-30，分箱/规则与既有mart.rfm_segments完全一致。
- Frequency大量为1，同值同分造成评分2–4为空，不是程序错误。
- Cohort为首次有效购买月份；同一用户同月只计一次。回购活跃留存允许中断后返回，不是连续订阅留存。
- 未完整观察单元retention/active_users保持NULL，已观察无购买才为0；本样本298个NULL。
- 热力图为视图转换，NULL传给ECharts为缺失标记“-”，不强转为0；色阶2%封顶，悬停与文字保留实际比例。

### /api/analysis/products

参数start/end含首尾日，state为一个客户州，category为一个已有类目；不传为全范围。

返回kpis、categories、monthly以及过滤选项/范围。使用原FILTERED product_kpis、categories、category_monthly。

- 类目选择只统计该类目的商品行。
- 商品金额和商品运费分开，件数为商品行数。
- kpis.orders在选中商品范围内COUNT(DISTINCT order_id)，不能把各类目内订单数相加作为总订单数。
- 品类排序/贡献、累计贡献展示沿用已有统计定义；月度缺失类目不填0，不根据不完整窗口算增长率。
- 页内排行点击是“应用当前草稿”的动作，不覆盖用户尚未应用的日期、地区条件。

### /api/analysis/delivery

同样支持日期/州/单一类目。使用原FILTERED overview、delivery_histogram、reviews、delivery_regions、late_reviews。

- 类目选择表示订单包含此类目，通过EXISTS过滤；订单一行，不按商品或评价条数放大。
- 配送均值以delivery_n为分母；逾期率以late_n为分母；订单等权评分以reviewed_orders为分母。
- 时长缺失/异常、逾期不可判断、评价缺失分开说明，缺失项可重叠；同日到达不算逾期。
- 均分先在订单内平均，再订单等权；评价分布每订单取最新有效评分，两种展示口径不同且均不多评价加权。
- association按原late_reviews的“逾期判断有效且订单评价有效”范围分组；另加一条同范围只读参数化SQL，暴露最新评分分母low_score_n与低评分订单low_score_orders。low_score_rate分母是最新评分有效订单，不笼统当作总订单数。
- 分组结果是描述性关联，保留样本选择、地区、类目、时间和用户差异局限，不推断配送延误的因果效应。
- 不为局部筛选重新估计P3置信区间；已验收的P3七项发现与完整方法仍通过经营发现入口按固定全样本查看。

## CSV导出

`GET /api/analysis/{page}/export?table=...`，筛选参数与对应页面一致。UTF-8 BOM，所有CSV都含scope_mode、scope_start、scope_end、scope_state、scope_category；NULL导出为空字段。

| 页面 | table白名单 |
|---|---|
| users | segments、frequency、summary、cohort、new_users |
| products | kpis、categories、monthly |
| delivery | kpis、histogram、reviews、regions、association |

导出读取已应用范围；仍在编辑的草稿不会混入导出。页面与下载均为真实查询结果，不从前端截断表格反推导出数据。

## 总览两项修正

1. 表单应用与地区点击共用applyScope校验。地区点击合并当前draft并应用，保留尚未应用的日期；非法/空日期显示提示，不查询。新的商品排行点击沿用同一原则。
2. 完整月份标签改为“当前范围完整月”，完整性须同时满足数据集完整目标月边界及当前日期覆盖整月。地区变化不重定义数据集观察边界。全部月仍保留早期/局部不完整月份；切换只影响图表，不改变KPI或导出。

## 页面加载与边界

React.lazy + Suspense加载Overview、Users、Products、Delivery及Findings对话框，History API支持导航、前进/后退与直接访问。Vite开发/预览服务具有SPA回退；将来采用其他托管方式需配置相同回退，但本阶段没有公网部署。

生产构建manifest及浏览器请求记录验证首页没有加载Users/Products/Delivery代码块或请求分析API。共享ECharts核心仍是大包，未把入口文件较小等同整体首屏已完成性能优化。
