import {useState} from "react";
import {Button} from "@/components/ui/button";
import {categoryName} from "../categories";
import { Chart } from "../Chart";
import { useAnalysis, records, numeric, nullable, percent } from "../analysis";
import {
  AnalysisHeader,
  Filters,
  ResultState,
  Kpis,
  Panel,
  Callout,
  MetricNotes,
  DataTable,
  Export,
  Footer,
} from "../AnalysisUI";
import { bars, associationOption } from "../analysisCharts";
import { number } from "../charts";

export default function Delivery() {
  const [includeSmall,setIncludeSmall]=useState(false);
  const state = useAnalysis("delivery"),
    data = state.data;
  const kpi = data ? records(data, "kpis")[0] : null;
  return (
    <main className="analysis-page">
      <AnalysisHeader
        title="履约与评价分析"
        description="了解配送效率与评价表现。"
        refresh={state.refresh}
        loading={state.loading}
      />
      <Filters state={state} />
      <ResultState
        loading={state.loading}
        error={state.error}
        retry={state.refresh}
      />
      {data && kpi && (
        <>
          <Callout>
            已选：{data.scope.start} — {data.scope.end} ·{" "}
            {data.scope.state ?? "全部地区"} ·{" "}
            {data.scope.category ? categoryName(data.scope.category) : "全部类目"}

          </Callout>
          <Kpis
            items={[
              {
                label: "平均配送天数",
                value:
                  nullable(kpi, "delivery_days") === null
                    ? "—"
                    : `${Number(kpi.delivery_days).toFixed(2)} 天`,
                note: `有效配送 ${number(numeric(kpi, "delivery_n"))} 单`,
              },
              {
                label: "逾期率",
                value: percent(nullable(kpi, "late_rate"), 4),
                note: `可判断逾期 ${number(numeric(kpi, "late_n"))} 单`,
              },
              {
                label: "订单等权评价均分",
                value:
                  nullable(kpi, "review_mean") === null
                    ? "—"
                    : Number(kpi.review_mean).toFixed(2),
                note: `有评价 ${number(numeric(kpi, "reviewed_orders"))} 单`,
              },
              {
                label: "有效订单",
                value: number(numeric(kpi, "orders")),
                note: "已送达订单",
              },
            ]}
          />
          <MetricNotes><p data-testid="delivery-missing">类目筛选统计包含该类目的订单，每单只计一次；配送与评价各自使用有效样本。
            配送时长缺失/无效{" "}
            {number(numeric(kpi, "orders") - numeric(kpi, "delivery_n"))}{" "}
            单；逾期判断缺失{" "}
            {number(numeric(kpi, "orders") - numeric(kpi, "late_n"))}{" "}
            单；评价缺失{" "}
            {number(numeric(kpi, "orders") - numeric(kpi, "reviewed_orders"))}{" "}
            单。缺失项可重叠，不直接相加为排除总数；同日送达不算逾期。均分先在订单内平均，再对订单等权；评分分布和低评分率使用每单最新评分。
          </p></MetricNotes>
          {!numeric(kpi, "orders") ? (
            <div className="empty-notice" role="status">
              当前筛选没有有效订单，请调整日期、地区或类目。
            </div>
          ) : (
            <>
              <div className="lower-grid">
                <Panel
                  title="配送时长分布"
                  description="有效配送订单 · 每5天一组"
                >
                  <Chart
                    option={bars(
                      records(data, "histogram").map((r) => ({
                        ...r,
                        day_range: `[${r.day_start}, ${Number(r.day_start) + 5})`,
                      })),
                      "day_range",
                      "orders",
                    )}
                    label="配送时长分布"
                    height={280}
                  />
                  <MetricNotes>配送时长每5天一组，左闭右开；仅含实际配送日期有效的订单。</MetricNotes>
                </Panel>
                <Panel
                  title="最新评分分布"
                  description="每单取最新有效评分"
                >
                  <Chart
                    option={bars(
                      records(data, "reviews"),
                      "score",
                      "orders",
                      false,
                      "#3f8d86",
                    )}
                    label="订单最新评分分布"
                    height={280}
                  />
                </Panel>
              </div>
              <Panel
                title="地区配送表现"
                description="按有效配送样本量排序 · 默认展示不少于100单的地区"
              >
                <div className="table-tools"><Button variant="outline" size="sm" aria-pressed={includeSmall} onClick={()=>setIncludeSmall(!includeSmall)}>{includeSmall?"排除小样本地区":"含小样本地区"}</Button></div>
                <Chart
                  option={bars(
                    [...records(data, "regions")].filter(r=>includeSmall||numeric(r,"delivery_n")>=100).sort((a,b)=>numeric(b,"delivery_n")-numeric(a,"delivery_n")),
                    "state",
                    "delivery_days",
                  )}
                  label="各州平均配送天数"
                  height={300}
                />
                <DataTable
                  rows={[...records(data, "regions")].sort((a,b)=>numeric(b,"delivery_n")-numeric(a,"delivery_n"))}
                  label="地区配送表现及样本量"
                  columns={[
                    { key: "state", label: "客户州" },
                    { key: "orders", label: "有效订单", kind: "number" },
                    {
                      key: "delivery_days",
                      label: "平均配送 · 天",
                      kind: "decimal",
                    },
                    { key: "delivery_n", label: "配送分母", kind: "number" },
                    { key: "late_rate", label: "逾期率", kind: "percent" },
                    { key: "late_n", label: "逾期分母", kind: "number" },
                    {
                      key: "sample_note",
                      label: "样本提示",
                      render: (r) =>
                        numeric(r, "delivery_n") < 100
                          ? "少于100单"
                          : "—",
                    },
                  ]}
                />
              </Panel>
              <Panel
                title="逾期与评价"
                description="两组订单评价表现"
              >
                <Chart
                  option={associationOption(records(data, "association"))}
                  label="逾期与订单评价关联"
                  height={280}
                />
                <DataTable
                  rows={records(data, "association")}
                  label="逾期评价关联分组样本"
                  columns={[
                    { key: "delivery_group", label: "配送分组" },
                    {
                      key: "orders",
                      label: "订单均分分母 · 单",
                      kind: "number",
                    },
                    {
                      key: "review_mean",
                      label: "订单等权均分",
                      kind: "decimal",
                    },
                    {
                      key: "low_score_n",
                      label: "最新评分分母 · 单",
                      kind: "number",
                    },
                    {
                      key: "low_score_orders",
                      label: "低评分订单 · 单",
                      kind: "number",
                    },
                    {
                      key: "low_score_rate",
                      label: "低评分率",
                      kind: "percent",
                    },
                  ]}
                />
                <MetricNotes title="样本与评分口径">
                  均分先在订单内平均，再对订单等权；低评分为每单最新评分≤2，比例分母仅为该组有最新有效评分的订单。当前关联比较纳入
                  {number(
                    records(data, "association").reduce(
                      (n, r) => n + numeric(r, "orders"),
                      0,
                    ),
                  )}
                  单；与总有效订单的差额是缺少可比较配送/评价的订单，可能涉及交叠缺失。本表为当前筛选的描述性比较。地区、类目、时间及用户差异可能影响结果，不能据此推断因果。全样本置信区间见经营发现。
                </MetricNotes>
              </Panel>
            </>
          )}
          <Export
            page="delivery"
            data={data}
            tables={[
              { key: "association", label: "逾期评价分组（含分母）" },
              { key: "regions", label: "地区配送表现" },
              { key: "histogram", label: "配送时长分布" },
              { key: "reviews", label: "最新评分分布" },
              { key: "kpis", label: "履约评价指标与样本量" },
            ]}
          />
        </>
      )}
      <Footer />
    </main>
  );
}
