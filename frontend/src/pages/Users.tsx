import {useState} from "react";
import {rfmRules} from "../rfmRules";
import { Chart } from "../Chart";
import { useAnalysis, records, numeric, nullable, percent } from "../analysis";
import {
  AnalysisHeader,
  ResultState,
  Kpis,
  Panel,
  Callout,
  MetricNotes,
  DataTable,
  Export,
  Footer,
} from "../AnalysisUI";
import { horizontal, bars } from "../analysisCharts";
import { cohortOption } from "../usersCharts";
import { number } from "../charts";

export default function Users() {
  const [cohortView,setCohortView]=useState<"focus"|"all">("focus");
  const state = useAnalysis("users"),
    data = state.data;
  const summary = data ? records(data, "summary")[0] : null,
    frequency = data ? records(data, "frequency") : [],
    segments = data ? records(data, "segments") : [],
    cohort = data ? records(data, "cohort") : [];
  const single = frequency
    .filter((r) => Number(r.frequency) === 1)
    .reduce((n, r) => n + numeric(r, "users"), 0);
  return (
    <main className="analysis-page">
      <AnalysisHeader
        title="用户价值分析"
        description="了解用户价值、复购与留存。"
        refresh={state.refresh}
        loading={state.loading}
      />
      <ResultState
        loading={state.loading}
        error={state.error}
        retry={state.refresh}
      />
      {data && !summary && (
        <div className="empty-notice" role="status">
          暂无用户分析数据，请稍后刷新。
        </div>
      )}
      {data && summary && (
        <>
          <Callout>
            <strong>全样本</strong> · {String(data.metadata.context.first_purchase)} — {String(data.metadata.context.last_purchase)} · 不随其他页面筛选变化
          </Callout>
          <Kpis
            items={[
              {
                label: "购买用户",
                value: number(numeric(summary, "users")),
                note: "跨订单去重",
              },
              {
                label: "复购用户",
                value: number(numeric(summary, "repeat_users")),
                note: "有效购买订单至少 2 单",
              },
              {
                label: "整体复购率",
                value: percent(nullable(summary, "repeat_rate"), 4),
                note: "复购用户 / 购买用户",
              },
              {
                label: "仅一次购买用户占比",
                value: percent(single / numeric(summary, "users"), 4),
                note: `${number(single)} 人仅购买一次`,
              },
            ]}
          />
          <Panel
            title="RFM 用户分层"
            description="人数与商品金额贡献"
          >
            <Chart
              option={horizontal(segments, "segment", "users")}
              label="RFM分层用户数"
              height={330}
            />
            <DataTable
              rows={segments}
              label="RFM人数与金额贡献"
              columns={[
                { key: "segment", label: "用户层",render:r=><abbr title={rfmRules[String(r.segment)]}>{String(r.segment)}</abbr> },
                { key: "users", label: "用户数 · 人", kind: "number" },
                { key: "user_share", label: "用户占比", kind: "percent" },
                {
                  key: "merchandise",
                  label: "商品成交额 · BRL",
                  kind: "money",
                },
                { key: "contribution", label: "商品金额贡献", kind: "percent" },
              ]}
            />
            <MetricNotes title="RFM分类规则">
              <ul>{Object.entries(rfmRules).filter(([label])=>label!=="数据待核对").map(([label,rule])=><li key={label}><strong>{label}</strong>：{rule}</li>)}</ul><p>按列示顺序判断；R越高表示购买越近，F为购买频次分，M为商品金额分。</p>
              RFM标签为规则分层，不代表营销效果。
              RFM基准日：{String(data.metadata.context.rfm_reference_date)}。Recency为距基准日的天数，Frequency为有效订单次数，Monetary为累计商品金额。大量Frequency=1使20/40/60/80%分位点重合；同值同分，F评分2–4为空是样本特征。
            </MetricNotes>
          </Panel>
          <Panel
            title="购买频次"
            description="按有效购买次数统计"
          >
            <Chart
              option={bars(frequency, "frequency", "users", true)}
              label="用户购买频次分布"
              height={285}
            />
            <MetricNotes>
              用户进入样本的时间不同，一次购买不能直接解释为流失。横轴：有效订单次数；纵轴：用户数（对数刻度，便于同时阅读大量一次购买用户与少量高频用户）。
            </MetricNotes>
          </Panel>
          <Panel
            title="同期群留存"
            description="浅灰空白：未观察（NA） · 0：已观察但未回购"
          >
            <div className="table-tools" role="group" aria-label="Cohort观察范围"><button type="button" aria-pressed={cohortView==="focus"} onClick={()=>setCohortView("focus")}>重点月份 M1–M6</button><button type="button" aria-pressed={cohortView==="all"} onClick={()=>setCohortView("all")}>全部月份 M0–M23</button></div>
            <div className="heatmap-scroll">
              <div className={`heatmap-content ${cohortView==="focus"?"heatmap-focus":""}`}>
                <Chart
                  option={cohortOption(cohort,cohortView)}
                  label="Cohort回购活跃留存热力图"
                  height={760}
                />
              </div>
            </div>
            <p className="panel-bottom">灰底空白：未观察 · 白格0%：已观察无回购 · M0使用独立灰绿色，不参与后续留存色阶。</p>
            <MetricNotes title="留存口径与色阶"><p data-testid="cohort-null-count">
              同一用户同月多单只计一次；留存为该月回购活跃，不要求连续回购。
              {cohort.filter((r) => r.retention === null).length}
              个未观察单元保留NULL。完整目标月区间：[
              {String(data.metadata.context.first_complete_month)},{" "}
              {String(data.metadata.context.observation_end_exclusive)}
              )。色阶在2%封顶，标签/悬停仍保留真实值；M0可为100%。首cohort存在左截断。窄屏可在图内横向滚动查看全部月龄。
            </p></MetricNotes>
          </Panel>
          <Panel
            title="新增购买用户"
            description="按样本内首次有效购买月份统计"
          >
            <Chart
              option={bars(
                records(data, "new_users").map((r) => ({
                  ...r,
                  cohort_month: String(r.cohort_month).slice(0, 7),
                })),
                "cohort_month",
                "new_users",
              )}
              label="每月观测新增用户"
              height={290}
            />
            <MetricNotes>新增用户指数据内首次有效购买，不等同平台真实历史首购；首尾月份未完整观察。</MetricNotes>
          </Panel>
          <Export
            page="users"
            data={data}
            tables={[
              { key: "segments", label: "RFM分层" },
              { key: "frequency", label: "购买频次" },
              { key: "cohort", label: "Cohort留存长表（含NA）" },
              { key: "new_users", label: "观测新增用户" },
              { key: "summary", label: "复购概要" },
            ]}
          />
        </>
      )}
      <Footer />
    </main>
  );
}
