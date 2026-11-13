# 发给 Codex：第二阶段（P1）—— PostgreSQL 分层数据仓库与核心指标

前置条件：P0 已验收通过。读取 `docs/PRD.md`、`docs/METRICS.md`、`docs/ACCEPTANCE.md`，以真实数据开发 P1，不要跳过数据质量。

1. 实现 `raw`→`core`→`mart` SQL/ETL，建立合理主键、外键/软校验、索引及迁移初始化命令。
2. 实现按订单先独立聚合商品金额/运费、支付、评价，再关联到 `mart.order_wide`，严格一单一行。
3. 按 `METRICS.md` 实现订单数、完成订单商品成交额、客单价、购买用户数、复购率、配送时长、逾期配送率等指标；结果可通过 SQL 独立运行。
4. 实现 customer_unique_id 的 RFM 和 cohort；不完整观察月份不能误填 0。
5. 用 Pandas 对 SQL 做独立交叉核验；金额统一到分，报告差异，测试 ETL 幂等。
6. 更新 `docs/data_dictionary.md`，把每一项数据口径和差异写清。

硬约束：不得把 payment_value 当商品销售额，不得对一对多支付/评价记录与订单商品明细直接多表连接后 SUM；不得用 customer_id 识别复购。若某些统计不可算，显示原因，不造数字。

完成后暂停，汇报修改文件、运行命令、核心结果（真实值）、SQL/Pandas 对账、测试结果、待解决问题和 P1 验收逐项结果。
