import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { withDraftState, validateScope, scopeQuery } from "../src/scope";
import { cohortOption } from "../src/usersCharts";
import { categoryTrend, paretoOption } from "../src/analysisCharts";
import type { Row } from "../src/analysis";

describe("V2-02 filtering and analytical presentation", () => {
  it("ranking click applies current draft dates without replacing them with old results", () => {
    const draft = {
      start: "2017-05-10",
      end: "2017-06-20",
      state: null,
      category: "beleza_saude",
    };
    const next = withDraftState(draft, "SP");
    expect(next).toEqual({ ...draft, state: "SP" });
    expect(draft.state).toBeNull();
    expect(scopeQuery(next)).toContain("start=2017-05-10");
    expect(scopeQuery(next)).toContain("category=beleza_saude");
  });
  it("blocks applying invalid or empty draft dates for both form and ranking actions", () => {
    expect(
      validateScope({ start: "2018-02-01", end: "2017-01-01", state: "SP" }),
    ).toContain("不能晚于");
    expect(validateScope({ start: "", end: "", state: null })).toContain(
      "请选择",
    );
    expect(
      validateScope({ start: "2017-01-01", end: "2017-01-01", state: null }),
    ).toBeNull();
  });
  it("preserves all real Cohort NULL cells as unobserved rather than zero", () => {
    const rows: Row[] = JSON.parse(
      readFileSync(
        new URL("../../reports/p1/cohort_retention.json", import.meta.url),
        "utf8",
      ),
    );
    const option = cohortOption(rows) as {
      series: { data: { value: (number | string)[] }[] }[];
    };
    const values = option.series[0].data.map((p) => p.value[2]);
    expect(values.filter((v) => v === "-")).toHaveLength(298);
    expect(values.filter((v) => v === 0)).toHaveLength(
      rows.filter((r) => r.retention !== null && Number(r.retention) === 0)
        .length,
    );
  });
  it("uses true contribution fractions for all-category Pareto without adding category order counts", () => {
    const rows: Row[] = JSON.parse(
      readFileSync(
        new URL("../../reports/p1/category_ranking.json", import.meta.url),
        "utf8",
      ),
    );
    const option = paretoOption(rows) as {
      series: { data: number[] }[];
      yAxis: { min: number; max?: number }[];
    };
    expect(option.series[1].data.at(-1)).toBeCloseTo(1, 12);
    expect(option.series[0].data.reduce((n, v) => n + v, 0)).toBeCloseTo(
      13221498.11,
      6,
    );
    expect(option.yAxis.map((a) => a.min)).toEqual([0, 0]);
  });
  it("does not invent zero sales for missing category/month observations", () => {
    const monthly = [
      { category: "A", month_start: "2017-01-01", merchandise: "4.01" },
      { category: "B", month_start: "2017-02-01", merchandise: "2.12" },
    ];
    const option = categoryTrend(monthly, [
      { category: "A" },
      { category: "B" },
    ]) as { series: { data: (number | null)[] }[] };
    expect(option.series[0].data).toEqual([4.01, null]);
    expect(option.series[1].data).toEqual([null, 2.12]);
  });
});
