# RetailScope V2 API

## V2-02 新增分析接口

- GET `/api/analysis/users`：固定P1全样本的RFM、频次、复购、Cohort与观测新增用户；拒绝局部日期/州/类目参数。
- GET `/api/analysis/products`：日期、州、单一类目参数；返回商品行KPI、排行与月度结构，订单总数在所选商品范围内重新去重。
- GET `/api/analysis/delivery`：同类筛选表示订单包含该类目；返回订单级配送、评价及逾期关联，包含分母。
- GET `/api/analysis/{page}/export?table=…`：各页白名单结果CSV，含scope_mode/start/end/state/category；未观察留存留空。

共享SQLAlchemy只读连接及参数化查询现在位于api/queries.py；P1/P2 SQL定义仍直接复用，不重写。新接口细节见[口径文档](../docs/V2-02_API_AND_SCOPE.md)。


只读适配现有P1/P2 SQL和P3预计算发现，未增加业务算法或改写数仓。所有服务仅绑定本地。

## 启动

先按根README准备既有Python3.12环境、.env和PostgreSQL16数据仓库，不重新导入已验收数据。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start-v2.ps1 -Action install
# 终端一
powershell -NoProfile -ExecutionPolicy Bypass -File .\start-v2.ps1 -Action api
# 终端二
powershell -NoProfile -ExecutionPolicy Bypass -File .\start-v2.ps1 -Action web
# 任意第三个终端
powershell -NoProfile -ExecutionPolicy Bypass -File .\start-v2.ps1 -Action check
```

前端http://127.0.0.1:5173；API文档http://127.0.0.1:8000/docs；旧版http://127.0.0.1:8501继续用start.ps1 -Action start启动。V2两个终端各按Ctrl+C停止，不停止/删除数据卷。

Node/npm采用本次实际验证的Node24.15.0、npm11.12.1。frontend/package-lock.json与api/requirements-lock.txt锁定新增依赖。安装基础环境后再安装API锁定依赖；安装过程不读取/改写.env密码。

## 接口契约

| GET接口 | 行为 |
|---|---|
| /api/overview | 默认全样本；返回scope、metadata、kpis、monthly、statuses、regions |
| /api/overview?start=2017-05-10&end=2017-06-20&state=SP | 日期含首尾日；state可省略，不接受任意SQL或可选列 |
| /api/overview/export?table=monthly&start=…&end=…&state=… | table只能为kpis/monthly/statuses/regions；UTF-8 BOM CSV含scope_start/end/state |
| /api/findings | 只读已验收P3七项发现；固定全样本，不受总览筛选影响 |

金额用Decimal精确字符串传输；浏览器仅在展示/绘图时转数值。无记录平均订单金额为null。开始晚于结束、非法日期/州/导出表返回422。数据库错误返回503和脱敏中文提示，错误响应不含密码或SQL。

数据库通过SQLAlchemy连接；default_transaction_read_only=on、statement_timeout=20s、connect_timeout=5s、有限连接池。总览各查询使用同一REPEATABLE READ只读事务。SQL直接引用retailscope.bi.data中的SCOPE/FILTERED/FIXED，保留预聚合订单粒度；不用用户输入构造SQL字段。

本地Vite代理/api至8000，前后端同源，不开放跨域访问或公网监听。没有生产身份鉴权、并发容量或公网部署承诺。

## 验证

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm --prefix frontend run build
```

官方参考：[FastAPI参数校验](https://fastapi.tiangolo.com/tutorial/query-params-str-validations/)、[shadcn/ui](https://ui.shadcn.com/docs/installation/manual)、[Tailwind Vite](https://tailwindcss.com/docs/installation/using-vite)。


## V2-03 只读证据接口

- GET `/api/evidence/findings`：七项P3发现完整聚合证据、固定观察范围、来源/生成时间/SHA以及报告配对状态。
- GET `/api/evidence/findings/report`：已生成且与快照一致的Markdown原文件，字节不改写；不运行统计模型。报告不一致/越界时拒绝返回。
- GET `/api/evidence/quality`：九表当前真实COUNT、目录/约束、当前Mart检查与明确标注的历史P0/P1/P3证据、完整后端测试XML摘要。
- GET `/api/evidence/quality/export?section=all|historical|tests`：白名单聚合JSON，不接受文件路径，不暴露运行配置或用户级记录。

当前DB查询失败时quality保留历史证据，并将live标为unavailable、当前行数置为不可用而非假0。P0审计未记录执行时间时executed_at=null；file_saved_at独立保留。P3状态只表示当前文件可读并与原报告配对，不冒充对当前全库输入的重审计。后端测试列表来自固定白名单XML并核对逐项数量，页面不执行测试。

前端`/findings`与`/quality`为正式独立懒加载页面，原经营发现入口迁移至`/findings`；原`/api/findings`契约保留兼容总览与历史测试。
