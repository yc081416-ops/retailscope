import {useState} from "react";
import {Button} from "@/components/ui/button";
import {categoryRows} from "../categories";
import {categoryName} from "../categories";
import { Chart } from "../Chart";
import { useAnalysis, records, numeric, percent } from "../analysis";
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
import {
  horizontal,
  categoryTrend,
  paretoOption,
  itemOrdersOption,
} from "../analysisCharts";
import { money, number } from "../charts";

export default function Products() {
  const [showAll,setShowAll]=useState(false),[search,setSearch]=useState(""),[sort,setSort]=useState("merchandise");
  const state = useAnalysis("products"),
    data = state.data;
  const kpi = data ? records(data, "kpis")[0] : null,
    categories = data ? records(data, "categories") : [];
  return (
    <main className="analysis-page">
      <AnalysisHeader
        title="商品与品类分析"
        description="了解品类贡献与销售结构。"
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
                label: "商品成交额",
                value: money(Number(kpi.merchandise)),
                note: "不含运费",
              },
              {
                label: "商品件数",
                value: number(numeric(kpi, "items")),
                note: "选中商品行数",
              },
              {
                label: "覆盖有效订单",
                value: number(numeric(kpi, "orders")),
                note: "订单去重",
              },
              {
                label: "商品运费",
                value: money(Number(kpi.freight)),
                note: "选中商品运费",
              },
            ]}
          />
          {!numeric(kpi, "items") ? (
            <div className="empty-notice" role="status">
              当前日期、地区与类目组合没有有效商品明细，请调整或重置筛选。
            </div>
          ) : (
            <>
              <Panel
                title="品类销售排行"
                description={`TOP5贡献 ${percent(categories.slice(0, 5).reduce((n, r) => n + numeric(r, "contribution"), 0))} · 点击类目筛选`}
              >
                <Chart
                  option={horizontal(
                    categories.slice(0, 10),
                    "category",
                    "merchandise",
                    undefined,
                    true,
                  )}
                  label="TOP10品类商品金额"
                  height={410}
                />
                <div className="table-tools"><input type="search" aria-label="搜索品类排行" placeholder="搜索品类" value={search} onChange={e=>setSearch(e.target.value)}/><select aria-label="品类排行排序" value={sort} onChange={e=>setSort(e.target.value)}><option value="merchandise">商品金额降序</option><option value="items">商品件数降序</option><option value="orders">订单数降序</option><option value="name">中文名称排序</option></select><Button variant="outline" size="sm" onClick={()=>setShowAll(!showAll)}>{showAll?"仅看TOP10":"查看全部品类"}</Button><span>{search?"搜索结果":showAll?"全部品类":"TOP10"} · 共{categories.length}类</span></div>
                <DataTable
                  rows={categoryRows(categories,search,sort,showAll)}
                  label="品类贡献排行"
                  columns={[
                    {
                      key: "category",
                      label: "商品类目",
                      render: (r) => (
                        <button
                          className="analysis-link category-label"
                          title={String(r.category)}
                          onClick={() =>
                            state.apply({
                              ...state.draft,
                              category: String(r.category),
                            })
                          }
                          aria-label={`筛选类目 ${r.category}`}
                        >
                          {categoryName(r.category)}
                        </button>
                      ),
                    },
                    {
                      key: "merchandise",
                      label: "商品成交额 · BRL",
                      kind: "money",
                    },
                    { key: "contribution", label: "贡献占比", kind: "percent" },
                    { key: "items", label: "商品件数", kind: "number" },
                    { key: "orders", label: "类目内去重订单", kind: "number" },
                  ]}
                />
                <MetricNotes>
                  金额、件数、运费统计选中类目的商品行；覆盖有效订单在所选范围重新去重。缺失类目/月不填0，不据不完整月份计算增长率。一个订单可能包含多个类目。类目内订单数不可相加作为总订单数；上方“覆盖有效订单”在选中商品范围内重新去重。商品金额不代表收入或利润。
                </MetricNotes>
              </Panel>
              <Panel
                title="累计贡献"
                description="商品成交额与累计贡献占比"
              >
                <Chart
                  option={paretoOption(categories)}
                  label="品类帕累托累计贡献"
                  height={350}
                />
              </Panel>
              <Panel
                title="品类月度趋势"
                description="TOP5品类 · 点击图例切换"
              >
                <Chart
                  option={categoryTrend(records(data, "monthly"), categories)}
                  label="品类月度金额趋势"
                  height={350}
                />
              </Panel>
              <Panel
                title="商品件数与订单数"
                description="TOP10品类 · 订单按类目分别去重"
              >
                <Chart
                  option={itemOrdersOption(categories)}
                  label="商品件数与类目订单对比"
                  height={440}
                />
              </Panel>
            </>
          )}
          <p className="export-notice">CSV保留全部品类与原始编码；金额单位为BRL。</p>
          <Export
            page="products"
            data={data}
            tables={[
              { key: "categories", label: "品类排行" },
              { key: "monthly", label: "品类月度趋势" },
              { key: "kpis", label: "商品指标（含去重订单）" },
            ]}
          />
        </>
      )}
      <Footer />
    </main>
  );
}
