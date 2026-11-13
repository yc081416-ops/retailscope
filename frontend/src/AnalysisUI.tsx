import { useState, type ReactNode } from "react";
import {
  ArrowDownToLine,
  CalendarDays,
  RotateCcw,
  TriangleAlert,
  CircleHelp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import type { useAnalysis, AnalysisData, AnalysisPage, Row } from "./analysis";
import { scopeQuery, type AnalysisScope } from "./scope";
import {CategorySelect} from "./CategorySelect";
import { money, number } from "./charts";

export function AnalysisHeader({
  title,
  description,
  refresh,
  loading,
}: {
  title: string;
  description: string;
  refresh: () => void;
  loading: boolean;
}) {
  return (
    <>
      <section className="page-heading">
        <div>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
        <div className="heading-actions">
          <Button
            variant="outline"
            size="sm"
            onClick={refresh}
            disabled={loading}
            aria-label="刷新数据"
          >
            <RotateCcw size={14} />
            刷新
          </Button>
        </div>
      </section>
    </>
  );
}
export function Filters({ state }: { state: ReturnType<typeof useAnalysis> }) {
  return (
    <>
      <form
        className="filters"
        noValidate
        aria-label="分析筛选"
        onSubmit={(e) => {
          e.preventDefault();
          state.apply();
        }}
      >
        <div className="date-range">
          <CalendarDays size={14} />
          <input
            aria-label="开始日期"
            type="date"
            value={state.draft.start}
            onChange={(e) =>
              state.setDraft({ ...state.draft, start: e.target.value })
            }
          />
          <span>—</span>
          <input
            aria-label="结束日期"
            type="date"
            value={state.draft.end}
            onChange={(e) =>
              state.setDraft({ ...state.draft, end: e.target.value })
            }
          />
        </div>
        <select
          aria-label="客户州"
          value={state.draft.state ?? ""}
          onChange={(e) =>
            state.setDraft({ ...state.draft, state: e.target.value || null })
          }
        >
          <option value="">全部地区</option>
          {state.metadata?.states?.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <CategorySelect codes={state.metadata?.categories ?? []} value={state.draft.category} onChange={category=>state.setDraft({...state.draft,category})} />
        <Button
          type="submit"
          size="sm"
          disabled={state.loading || !state.draft.start || !state.draft.end}
        >
          应用筛选
        </Button>
        <Button
          type="button"
          size="sm"
          variant="outline"
          disabled={state.loading}
          onClick={state.reset}
        >
          重置
        </Button>
        <span className="filter-note">
          {state.pending ? "更改待应用" : "已应用"}
        </span>
      </form>
      {state.notice && (
        <p className="export-notice" role="status">
          {state.notice}
        </p>
      )}
    </>
  );
}
export function ResultState({
  loading,
  error,
  retry,
}: {
  loading: boolean;
  error: string;
  retry: () => void;
}) {
  return error ? (
    <section className="state-panel" role="alert">
      <TriangleAlert size={24} />
      <h2>数据暂时不可用</h2>
      <p>{error}</p>
      <Button variant="outline" onClick={retry}>
        重新连接
      </Button>
    </section>
  ) : loading ? (
    <section
      className="skeleton-chart"
      aria-label="正在加载分析数据"
      aria-busy="true"
    >
      正在加载数据…
    </section>
  ) : null;
}
export function Kpis({
  items,
}: {
  items: { label: string; value: string; note: string }[];
}) {
  return (
    <section className="kpis" aria-label="核心分析指标">
      {items.map((c, i) => (
        <article className="kpi" key={c.label}>
          <div className="kpi-label">{c.label}</div>
          <div
            className={`kpi-value tabular ${i === 0 ? "accent-value" : ""}`}
            data-testid={`analysis-kpi-${i}`}
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
          <p>{c.note}</p>
        </article>
      ))}
    </section>
  );
}
export function Panel({
  title,
  description,
  children,
  id,
}: {
  title: string;
  description: string;
  children: ReactNode;
  id?: string;
}) {
  return (
    <section className="panel analysis-panel" id={id}>
      <div className="panel-heading">
        <div>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>
      </div>
      {children}
    </section>
  );
}
export function Callout({ children }: { children: ReactNode }) {
  return <div className="analysis-callout">{children}</div>;
}
export function MetricNotes({children, title = "指标说明"}: {children: ReactNode; title?: string}) {
  return <details className="evidence-details metric-notes"><summary><CircleHelp size={14} aria-hidden="true" />{title}<span aria-hidden="true">⌄</span></summary><div className="method-content">{children}</div></details>;
}
export type Column = {
  key: string;
  label: string;
  kind?: "money" | "number" | "percent" | "decimal";
  render?: (row: Row) => ReactNode;
};
export function DataTable({
  rows,
  columns,
  label,
}: {
  rows: Row[];
  columns: Column[];
  label: string;
}) {
  const format = (row: Row, c: Column) => {
    if (c.render) return c.render(row);
    const v = row[c.key];
    if (v === null || v === undefined) return "NA";
    if (c.kind === "money") return money(Number(v));
    if (c.kind === "number") return number(Number(v));
    if (c.kind === "percent") return `${(Number(v) * 100).toFixed(4)}%`;
    if (c.kind === "decimal") return Number(v).toFixed(2);
    return String(v);
  };
  return (
    <div className="data-table-scroll">
      <table className="analysis-table" aria-label={label}>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key} className={c.kind ? "numeric" : ""}>
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length ? (
            rows.map((r, i) => (
              <tr key={i}>
                {columns.map((c) => (
                  <td key={c.key} className={c.kind ? "numeric tabular" : ""}>
                    {format(r, c)}
                  </td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={columns.length}>当前范围没有可展示的结果。</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
export function Export({
  page,
  data,
  tables,
}: {
  page: AnalysisPage;
  data: AnalysisData;
  tables: { key: string; label: string }[];
}) {
  const [table, setTable] = useState(tables[0].key),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState("");
  const download = async () => {
    setBusy(true);
    setNotice("");
    try {
      const response = await fetch(
        `/api/analysis/${page}/export?table=${table}&${page === "users" ? "" : scopeQuery(data.scope as AnalysisScope)}`,
      );
      if (!response.ok) throw Error();
      const link = document.createElement("a");
      const url = URL.createObjectURL(await response.blob());
      link.href = url;
      link.download = `retailscope-${page}-${table}.csv`;
      link.click();
      URL.revokeObjectURL(url);
      setNotice("导出成功。");
    } catch {
      setNotice("导出未完成，请确认数据服务正常后重试。");
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <section className="export-row">
        <div>
          <ArrowDownToLine size={16} />
          <strong>导出分析结果</strong>
          <span>
            {page === "users"
              ? "全样本"
              : "当前筛选范围"}
          </span>
        </div>
        <div>
          <select
            aria-label="导出内容"
            value={table}
            onChange={(e) => setTable(e.target.value)}
          >
            {tables.map((t) => (
              <option key={t.key} value={t.key}>
                {t.label}
              </option>
            ))}
          </select>
          <Button
            variant="outline"
            size="sm"
            onClick={download}
            disabled={busy}
          >
            导出 CSV
          </Button>
        </div>
      </section>
      {notice && (
        <p className="export-notice" role="status">
          {notice}
        </p>
      )}
    </>
  );
}
export function Footer() {
  return (
    <footer>
      <span>RetailScope · 电商经营分析</span>
    </footer>
  );
}
