import {beijingTime} from "../dateTime";
import { useState } from "react";
import { ArrowDownToLine, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  AnalysisHeader,
  ResultState,
  Callout,
  DataTable,
  Footer,
} from "../AnalysisUI";
import {findingCopy, findingHeadline} from "../findingCopy";
import { Chart } from "../Chart";
import { associationOption } from "../analysisCharts";
import {
  useEvidence,
  topics,
  topicFindings,
  sampleSummary,
  downloadEvidence,
  type FindingsData,
  type EvidenceFinding,
  type Json,
} from "../evidence";

type Association = {
  groups: {
    group: string;
    n: number;
    users: number;
    mean_score: number;
    low_scores: number;
    low_rate: number;
  }[];
  eligible_orders: number;
  valid_orders: number;
  excluded_orders: number;
  differences_late_minus_on_time: {
    mean_difference: number;
    difference: number;
  };
  cluster_bootstrap: {
    mean_ci: number[];
    low_rate_ci: number[];
    replications: number;
    seed: number;
  };
};
function AssociationEvidence({ finding }: { finding: EvidenceFinding }) {
  const s = finding.statistics as unknown as Association;
  if (!Array.isArray(s.groups) || !s.cluster_bootstrap?.mean_ci)
    return (
      <p className="panel-bottom">
        关联分析详情暂不可用。
      </p>
    );
  const rows = s.groups.map((g) => ({
    delivery_group: g.group,
    orders: g.n,
    users: g.users,
    review_mean: g.mean_score,
    low_scores: g.low_scores,
    low_rate: g.low_rate,
  }));
  return (
    <section className="association-proof" aria-label="配送逾期与评价统计证据">
      <div className="ci-summary">
        <div>
          <span>评分均值差 · 逾期减未逾期</span>
          <strong data-testid="mean-difference">
            {s.differences_late_minus_on_time.mean_difference.toFixed(4)} 分
          </strong>
        </div>
        <div>
          <span>用户整群 Bootstrap · 95%置信区间</span>
          <strong data-testid="mean-ci">
            [{s.cluster_bootstrap.mean_ci.map((v) => v.toFixed(4)).join(", ")}]
          </strong>
        </div>
      </div>
      <Chart
        option={associationOption(rows)}
        label="全样本逾期与评价均分"
        height={260}
      />
      <DataTable
        rows={rows}
        label="逾期评价样本与评分"
        columns={[
          { key: "delivery_group", label: "配送分组" },
          { key: "orders", label: "订单数 · 单", kind: "number" },
          { key: "users", label: "去重用户 · 人", kind: "number" },
          {
            key: "review_mean",
            label: "订单评价均分（订单等权）",
            render: (r) => Number(r.review_mean).toFixed(4),
          },
          { key: "low_scores", label: "低评分订单 · 单", kind: "number" },
          { key: "low_rate", label: "低评分率", kind: "percent" },
        ]}
      />
      <p className="panel-bottom">
        有效比较 {s.valid_orders.toLocaleString("en-US")} 单 / 有效订单{" "}
        {s.eligible_orders.toLocaleString("en-US")} 单；排除 {s.excluded_orders}{" "}
        单。均分先在订单内平均，再对订单等权；低评分比例单独使用每单最新评分≤2。低评分率差的95%区间为 [
        {s.cluster_bootstrap.low_rate_ci
          .map((v) => (v * 100).toFixed(2))
          .join(", ")}
        ] 个百分点。按唯一用户整群重采样 {s.cluster_bootstrap.replications}{" "}
        次，种子 {s.cluster_bootstrap.seed}
        ；两组差异为统计关联，可能受地区、商品与用户结构影响，不能据此推断因果。
      </p>
    </section>
  );
}
export default function FindingsPage() {
  const state = useEvidence<FindingsData>("/api/evidence/findings"),
    [topic, setTopic] = useState(topics[0].label),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState("");
  const data = state.data,
    visible = data ? topicFindings(data.findings, topic) : [];
  const download = async () => {
    setBusy(true);
    setNotice("");
    try {
      await downloadEvidence(
        "/api/evidence/findings/report",
        "RetailScope_P3_BUSINESS_REPORT.md",
      );
      setNotice("报告下载成功。");
    } catch {
      setNotice("报告暂时无法下载，请稍后重试。");
    } finally {
      setBusy(false);
    }
  };
  return (
    <main className="analysis-page evidence-page">
      <AnalysisHeader
        title="经营发现"
        description="浏览经营表现与业务线索。"
        refresh={state.refresh}
        loading={state.loading}
      />
      <ResultState
        loading={state.loading}
        error={state.error}
        retry={state.refresh}
      />
      {data && (
        <>
          <Callout>
            <strong>全样本分析</strong> · {String(data.context.first_purchase)} — {String(data.context.last_purchase)} · 不随其他页面筛选变化
          </Callout>
          <section className="findings-overview">
            <div>
              <h2>发现概览</h2>
            </div>
            <div>
              <label htmlFor="topic-filter">分析专题</label>
              <select
                id="topic-filter"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
              >
                {topics.map((t) => (
                  <option key={t.label}>{t.label}</option>
                ))}
              </select>
              <Button variant="outline" onClick={download} disabled={busy}>
                <ArrowDownToLine size={15} />
                下载 Markdown 报告
              </Button>
            </div>
          </section>
          <p className="findings-count" role="status">
            当前显示 {visible.length} / {data.findings.length} 项发现
          </p>
          {!data.findings.length && (
            <div className="empty-notice" role="status">
              暂无经营发现。
            </div>
          )}
          {visible.map((f) => (
            <article
              className={`finding-card ${f.id === "F05" ? "priority-finding" : ""}`}
              key={f.id}
              id={f.id}
              data-testid={`finding-${f.id}`}
            >
              <header>
                <h2>{findingCopy[f.id]?.title ?? f.title}</h2>
                {f.id === "F05" && <span>履约体验重点</span>}
              </header>
              <p className="finding-result">{findingHeadline(f)}</p>
              <p className="finding-meaning">{findingCopy[f.id]?.meaning}</p>
              <details className="evidence-details" data-testid={`evidence-${f.id}`}>
                <summary><FileText size={15} />查看分析依据</summary>
                <p className="finding-result">{f.result}</p>
              <p className="finding-sample">{sampleSummary(f)}</p>
              <dl className="finding-meta">
                <dt>观察区间</dt>
                <dd>{f.scope}</dd>
                <dt>计算分母</dt>
                <dd>{String(f.sample.denominator ?? "详见聚合证据")}</dd>
                <dt>SQL来源</dt>
                <dd>{f.source_sql.join(" / ")}</dd>
              </dl>
              {f.id === "F05" && <AssociationEvidence finding={f} />}
              <div className="finding-explanation">
                <section>
                  <h3>统计方法</h3>
                  <p>{f.method}</p>
                </section>
                <section>
                  <h3>业务解释与边界</h3>
                  <p>{f.limitations}</p>
                </section>
                <section>
                  <h3>待验证建议</h3>
                  <p>{f.suggestion}</p>
                </section>
              </div>
              <p className="evidence-provenance">生成时间：{beijingTime(data.source.executed_at)} · 分析来源：{data.source.path}</p>
              <details className="evidence-details"><summary>聚合统计数据</summary>
                <pre>
                  {JSON.stringify(
                    { sample: f.sample, statistics: f.statistics } as Record<
                      string,
                      Json
                    >,
                    null,
                    2,
                  )}
                </pre>
              </details>
              </details>
            </article>
          ))}
          {notice && (
            <p className="export-notice" role="status">
              {notice}
            </p>
          )}
        </>
      )}
      <Footer />
    </main>
  );
}
