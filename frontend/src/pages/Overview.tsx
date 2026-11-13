import { useEffect, useState } from "react";
import { validateScope, withDraftState } from "../scope";
import {
  ArrowDownToLine,
  ArrowRight,
  CalendarDays,
  Database,
  Layers3,
  Loader2,
  RotateCcw,
  Sparkles,
  TriangleAlert,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { MetricNotes, Footer } from "../AnalysisUI";
import { Chart } from "../Chart";
import { money, monthlyOption, number, statusOption } from "../charts";
import type { Finding, Overview, Scope } from "../types";
import {
  visibleMonths,
  trendReading,
  isFullScope,
  type MonthView,
} from "../presentation";

function query(scope: Scope | null) {
  const p = new URLSearchParams();
  if (scope) {
    p.set("start", scope.start);
    p.set("end", scope.end);
    if (scope.state) p.set("state", scope.state);
  }
  return p.toString();
}
const shortDate = (d: string) => d.slice(0, 10).replaceAll("-", ".");

export default function Overview({
  onOpenFindings,
}: {
  onOpenFindings: () => void;
}) {
  const [data, setData] = useState<Overview | null>(null);
  const [metadata, setMetadata] = useState<Overview["metadata"] | null>(null);
  const [draft, setDraft] = useState<Scope>({
    start: "",
    end: "",
    state: null,
  });
  const [applied, setApplied] = useState<Scope | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const [exportTable, setExportTable] = useState("monthly");
  const [exporting, setExporting] = useState(false);
  const [notice, setNotice] = useState("");
  const [monthView, setMonthView] = useState<MonthView>("all");
  const [allRegions, setAllRegions] = useState(false);
  const [facts, setFacts] = useState<Finding[] | null>(null);
  const [factsError, setFactsError] = useState("");

  useEffect(() => {
    const abort = new AbortController();
    setLoading(true);
    setError("");
    setData(null);
    setNotice("");
    fetch(`/api/overview?${query(applied)}`, { signal: abort.signal })
      .then(async (r) => {
        if (!r.ok)
          throw new Error(
            r.status === 503
              ? "数据暂时无法加载，请稍后重试。"
              : "查询未完成，请检查日期范围和地区后重试。",
          );
        return r.json() as Promise<Overview>;
      })
      .then((value) => {
        setData(value);
        setMetadata(value.metadata);
        if (!applied) setDraft(value.scope);
      })
      .catch((e) => {
        if (e.name !== "AbortError")
          setError(
            e.message === "Failed to fetch"
              ? "数据服务暂时无法连接，请稍后重试。"
              : e.message,
          );
      })
      .finally(() => {
        if (!abort.signal.aborted) setLoading(false);
      });
    return () => abort.abort();
  }, [applied, retry]);

  useEffect(() => {
    const abort = new AbortController();
    setFacts(null);
    setFactsError("");
    fetch("/api/findings", { signal: abort.signal })
      .then(async (r) => {
        if (!r.ok) throw new Error("分析快照暂时无法读取，请稍后重试。");
        return r.json();
      })
      .then((result) => setFacts(result.findings))
      .catch((e) => {
        if (e.name !== "AbortError")
          setFactsError("分析快照暂时无法读取，请稍后重试。");
      });
    return () => abort.abort();
  }, []);

  const pending = Boolean(
    data && JSON.stringify(draft) !== JSON.stringify(data.scope),
  );
  const applyScope = (next = draft) => {
    setDraft(next);
    const issue = validateScope(next);
    if (issue) {
      setNotice(issue);
      return;
    }
    setApplied({ ...next });
  };
  const reset = () => {
    if (metadata) {
      const full = { ...metadata.bounds, state: null };
      setDraft(full);
      setApplied(full);
    }
  };
  const download = async () => {
    if (!data) return;
    setExporting(true);
    setNotice("");
    try {
      const r = await fetch(
        `/api/overview/export?${query(data.scope)}&table=${exportTable}`,
      );
      if (!r.ok) throw new Error();
      const url = URL.createObjectURL(await r.blob());
      const a = document.createElement("a");
      a.href = url;
      a.download = `retailscope-${exportTable}.csv`;
      a.click();
      URL.revokeObjectURL(url);
      setNotice("已导出当前已应用筛选范围的数据。");
    } catch {
      setNotice("导出未完成，请确认数据服务正常后重试。");
    } finally {
      setExporting(false);
    }
  };
  const activeStates = data?.scope.state ?? "全部地区";
  const fullOrders = data?.statuses.reduce((n, r) => n + r.orders, 0) ?? 0;
  const cards = data
    ? [
        {
          label: "商品成交额",
          value: money(data.kpis.merchandise),
          unit: "商品明细金额，不含运费",
          tag: "",
        },
        {
          label: "有效订单",
          value: number(data.kpis.orders),
          unit: "已送达 · 按订单去重",
          tag: "单",
        },
        {
          label: "唯一购买用户",
          value: number(data.kpis.users),
          unit: "跨订单去重",
          tag: "人",
        },
        {
          label: "平均订单商品金额",
          value: money(data.kpis.average_order_value),
          unit: "商品成交额 / 有效订单",
          tag: "/ 单",
        },
      ]
    : [];

  return (
    <>
      <main id="top">
        <section className="page-heading">
          <div>
            <h1>经营总览</h1>
            <p>聚焦经营规模、月度表现与地区贡献。</p>
          </div>
          <div className="heading-actions">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setRetry((n) => n + 1)}
              disabled={loading}
              aria-label="刷新数据"
            >
              <RotateCcw size={14} />
              刷新
            </Button>
          </div>
        </section>
        <form
          className="filters"
          noValidate
          onSubmit={(e) => {
            e.preventDefault();
            applyScope();
          }}
          aria-label="全局筛选"
        >
          <div className="filter-label">
            <Layers3 size={15} />
            <span>分析范围</span>
          </div>
          <div className="date-range">
            <CalendarDays size={14} />
            <input
              aria-label="开始日期"
              type="date"
              required
              value={draft.start}
              onChange={(e) => setDraft({ ...draft, start: e.target.value })}
            />
            <span className="muted">—</span>
            <input
              aria-label="结束日期"
              type="date"
              required
              min={draft.start}
              value={draft.end}
              onChange={(e) => setDraft({ ...draft, end: e.target.value })}
            />
          </div>
          <select
            aria-label="客户州"
            value={draft.state ?? ""}
            onChange={(e) =>
              setDraft({ ...draft, state: e.target.value || null })
            }
          >
            <option value="">全部地区</option>
            {metadata?.states.map((s) => (
              <option key={s} value={s}>
                {s} · 客户州
              </option>
            ))}
          </select>
          <Button
            size="sm"
            type="submit"
            disabled={loading || !draft.start || !draft.end}
          >
            应用筛选
          </Button>
          <Button
            variant="outline"
            size="sm"
            type="button"
            onClick={reset}
            disabled={loading || !metadata}
          >
            重置
          </Button>
          <span className="filter-note">
            {pending ? "更改待应用" : "已应用"}
          </span>
        </form>
        {notice && (
          <div className="export-notice" role="status">
            {notice}
            <button aria-label="关闭提示" onClick={() => setNotice("")}>
              <X size={13} />
            </button>
          </div>
        )}
        {error ? (
          <section role="alert" className="state-panel error-panel">
            <TriangleAlert size={26} />
            <h2>数据暂时不可用</h2>
            <p>{error}</p>
            <Button variant="outline" onClick={() => setRetry((n) => n + 1)}>
              重新连接
            </Button>
          </section>
        ) : loading ? (
          <section
            className="loading-state"
            aria-label="正在加载经营数据"
            aria-busy="true"
          >
            <div className="skeleton-kpis">
              {[0, 1, 2, 3].map((n) => (
                <div key={n} />
              ))}
            </div>
            <div className="skeleton-chart">
              <Loader2 size={20} className="spinner" />
              正在查询经营数据…
            </div>
          </section>
        ) : (
          data && (
            <>
              <div className="applied-scope">
                <CalendarDays size={14} />
                <span>
                  已选：{shortDate(data.scope.start)} —{" "}
                  {shortDate(data.scope.end)} · {activeStates}
                </span>

              </div>
              <section className="kpis" aria-label="核心经营指标">
                {cards.map((c, i) => (
                  <article className="kpi" key={c.label}>
                    <div className="kpi-label" title={i === 1 ? "仅计有效已送达订单；全状态分布包含取消、运输中等订单。" : c.unit}>
                      {c.label}
                      <span>{c.tag}</span>
                    </div>
                    <div
                      className={`kpi-value tabular ${i === 0 ? "accent-value" : ""}`}
                      data-testid={`kpi-${i}`}
                    >
                      {c.value.startsWith("BRL ") ? (
                        <>
                          <span className="currency-prefix">BRL </span>
                          {c.value.slice(4)}
                        </>
                      ) : (
                        c.value
                      )}
                    </div>
                    <p>{c.unit}</p>
                  </article>
                ))}
              </section>
              <MetricNotes>
                核心指标统计有效已送达订单；订单状态分布包含取消、运输中等全部状态。商品成交额为商品明细金额，不含运费，不等于财务收入或利润；运费 {money(data.kpis.freight)} 单列。唯一购买用户按跨订单用户标识去重。
                <p>数据日期：{metadata?.bounds.start} — {metadata?.bounds.end}（全状态）；{metadata?.context.first_purchase} — {metadata?.context.last_purchase}（已送达）。日期含起止日。</p>
              </MetricNotes>
              {!data.kpis.orders && (
                <div className="empty-notice" role="status">
                  <Database size={18} />
                  <div>
                    <strong>当前范围没有有效订单</strong>
                    <p>
                      请调整日期或地区。
                    </p>
                  </div>
                  <Button variant="outline" size="sm" onClick={reset}>
                    清空筛选
                  </Button>
                </div>
              )}
              <section className="panel trend-panel" id="trends">
                <div className="panel-heading">
                  <div>
                    <h2>月度经营趋势</h2>
                    <p>商品成交额与有效订单</p>
                  </div>
                  <div className="chart-legend">
                    <span>
                      <i className="purple" />
                      商品成交额
                    </span>
                    <span>
                      <i className="teal" />
                      有效订单
                    </span>
                  </div>
                </div>
                <div className="trend-toolbar">
                  <div
                    className="month-switch"
                    role="group"
                    aria-label="月份观察范围"
                  >
                    <button
                      aria-pressed={monthView === "all"}
                      onClick={() => setMonthView("all")}
                    >
                      全部月份
                    </button>
                    <button
                      aria-pressed={monthView === "complete"}
                      onClick={() => setMonthView("complete")}
                    >
                      完整月份
                    </button>
                  </div>
                  <span data-testid="month-count">
                    显示 {visibleMonths(data.monthly, monthView).length} /{" "}
                    {data.monthly.length} 个月
                  </span>
                </div>
                <div className="chart-unit">商品金额 · BRL</div>
                {visibleMonths(data.monthly, monthView).length ? (
                  <>
                    <Chart
                      option={monthlyOption(
                        visibleMonths(data.monthly, monthView),
                      )}
                      label="月度商品成交额与订单趋势"
                      height={284}
                    />
                  </>
                ) : (
                  <div className="chart-empty">
                    当前视图没有可展示的月份，请查看全部月份或调整筛选
                  </div>
                )}
                <div className="chart-note"><span className="amber-dot" />浅色柱 / 琥珀色点：未完整观察的月份</div>
                <MetricNotes title="月份与解读说明">
                  完整月须处于数据集观察区间 [{metadata?.context.first_complete_month}, {metadata?.context.observation_end_exclusive})，且当前日期覆盖整月。地区筛选不改变该边界。完整月份切换仅影响图表，KPI与导出保留已选范围；不完整月份保留但不参与增长比较。
                  <p>{trendReading(facts, data).boundary}</p><p>{trendReading(facts, data).source}</p>
                </MetricNotes>
                <details className="evidence-details" open={isFullScope(data)}><summary>{isFullScope(data)?"全样本趋势解读":"全样本趋势参考（非当前筛选）"}</summary>
                <div
                  className={`trend-reading ${!isFullScope(data) ? "local-reading" : ""}`}
                  aria-label="趋势解读"
                >
                  <div>
                    <Badge variant="outline">
                      {trendReading(facts, data).title}
                    </Badge>
                    <button onClick={() => onOpenFindings()}>
                      方法与来源
                      <ArrowRight size={14} />
                    </button>
                  </div>
                  {!isFullScope(data) && <p className="reading-boundary">全样本解读，不随当前筛选变化</p>}
                  {trendReading(facts, data).result ? (
                    <>
                      <p className="reading-result">
                        {trendReading(facts, data).result}
                      </p>

                    </>
                  ) : (
                    <p>{factsError || "正在加载趋势解读…"}</p>
                  )}
                </div>
                </details>
              </section>
              <div className="lower-grid">
                <section className="panel" id="statuses">
                  <div className="panel-heading">
                    <div>
                      <h2>订单状态分布</h2>
                      <p>全部状态</p>
                    </div>
                    <span className="panel-total tabular">
                      {number(fullOrders)} <small>单</small>
                    </span>
                  </div>
                  {data.statuses.length ? (
                    <Chart
                      option={statusOption(data.statuses)}
                      label="全部订单状态分布"
                      height={238}
                    />
                  ) : (
                    <div className="chart-empty">当前范围没有订单记录</div>
                  )}

                </section>
                <section className="panel" id="regions">
                  <div className="panel-heading">
                    <div>
                      <h2>地区销售贡献</h2>
                      <p>已送达订单 · 点击地区筛选</p>
                    </div>
                    <Badge variant="secondary">
                      {allRegions ? "全部地区" : "TOP 5"}
                    </Badge>
                  </div>
                  <div className="region-head">
                    <span>客户州</span>
                    <span>商品成交额 · BRL</span>
                    <span>贡献占比</span>
                  </div>
                  {data.regions.length ? (
                    <div className="region-list">
                      {data.regions
                        .slice(0, allRegions ? 27 : 5)
                        .map((r, i) => (
                          <div className="region-row" key={r.state}>
                            <div className="region-name">
                              <span className="rank">
                                {String(i + 1).padStart(2, "0")}
                              </span>
                              <button
                                className="state-filter"
                                aria-label={`筛选客户州 ${r.state}`}
                                onClick={() => {
                                  applyScope(withDraftState(draft, r.state));
                                  window.scrollTo({
                                    top: 0,
                                    behavior: "instant",
                                  });
                                }}
                              >
                                {r.state}
                                <ArrowRight size={12} />
                              </button>
                            </div>
                            <span className="tabular region-money">
                              {Number(r.merchandise).toLocaleString("en-US", {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2,
                              })}
                            </span>
                            <div className="region-share">
                              <div className="share-track">
                                <i
                                  style={{
                                    width: `${Math.max(1, Number(r.contribution) * 100)}%`,
                                  }}
                                />
                              </div>
                              <span className="tabular">
                                {(Number(r.contribution) * 100).toFixed(1)}%
                              </span>
                            </div>
                          </div>
                        ))}
                    </div>
                  ) : (
                    <div className="chart-empty">
                      当前范围没有有效订单地区贡献
                    </div>
                  )}
                  <button
                    className="table-more"
                    onClick={() => setAllRegions((v) => !v)}
                  >
                    {allRegions ? "收起地区" : "查看全部地区"}
                    <ArrowRight size={13} />
                  </button>
                </section>
              </div>
              <section className="insight-entry">
                <div className="insight-icon">
                  <Sparkles size={18} />
                </div>
                <div>
                  <h2>进一步了解经营表现</h2>
                  <p>
                    7 项经营发现 · 全样本分析
                  </p>
                </div>
                <Button variant="ghost" onClick={() => onOpenFindings()}>
                  查看经营发现
                  <ArrowRight size={15} />
                </Button>
              </section>
              <section className="export-row" id="export">
                <div>
                  <ArrowDownToLine size={16} />
                  <strong>导出当前查询结果</strong>
                  <span>当前筛选范围</span>
                </div>
                <div>
                  <select
                    aria-label="导出内容"
                    value={exportTable}
                    onChange={(e) => setExportTable(e.target.value)}
                  >
                    <option value="monthly">月度趋势</option>
                    <option value="kpis">核心指标</option>
                    <option value="statuses">订单状态</option>
                    <option value="regions">地区贡献</option>
                  </select>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={exporting}
                    onClick={download}
                  >
                    {exporting ? (
                      <Loader2 size={14} className="spinner" />
                    ) : (
                      <ArrowDownToLine size={14} />
                    )}
                    导出 CSV
                  </Button>
                </div>
              </section>
            </>
          )
        )}
        <Footer />
      </main>
    </>
  );
}
