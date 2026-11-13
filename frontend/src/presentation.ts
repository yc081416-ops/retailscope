import type { Finding, Month, Overview } from "./types";

export type MonthView = "all" | "complete";
/** View-only selection: keep the original SQL response and all KPI/export denominators intact. */
export function visibleMonths(rows: Month[], view: MonthView): Month[] {
  return view === "all" ? rows : rows.filter((row) => row.is_complete);
}

export function isFullScope(data: Overview): boolean {
  return (
    !data.scope.state &&
    data.scope.start === data.metadata.bounds.start &&
    data.scope.end === data.metadata.bounds.end
  );
}

export function trendReading(facts: Finding[] | null, data: Overview) {
  const finding = facts?.find((fact) => fact.id === "F01");
  return {
    title: "全样本趋势",
    result: finding?.result ?? null,
    source: finding
      ? `${finding.scope} · ${finding.source_sql.join(" / ")}`
      : null,
    boundary: isFullScope(data)
      ? "基于完整历史观察月的描述性分析，不是预测。月份视图切换不重算此发现。"
      : "当前为局部筛选；解读基于全样本，当前表现请参阅筛选后的图表。",
  };
}
