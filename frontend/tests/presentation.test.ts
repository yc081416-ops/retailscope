import { describe, it, expect } from "vitest";
import {readP3Evidence} from "./p3Evidence";
import { visibleMonths, isFullScope, trendReading } from "../src/presentation";
import { monthlyOption, money } from "../src/charts";
import type { Month, Overview, Finding } from "../src/types";

const findings: Finding[] = readP3Evidence().findings;
const data = {
  scope: { start: "2016-09-04", end: "2018-10-17", state: null },
  metadata: { bounds: { start: "2016-09-04", end: "2018-10-17" } },
} as Overview;

describe("observation view and fixed-sample interpretation", () => {
  const months = [
    {
      month_start: "2016-09-01",
      orders: 1,
      users: 1,
      merchandise: "10.01",
      is_complete: false,
    },
    {
      month_start: "2017-01-01",
      orders: 5,
      users: 5,
      merchandise: "43.32",
      is_complete: true,
    },
  ] satisfies Month[];
  it("keeps early partial data by default without mutating the API response", () => {
    expect(visibleMonths(months, "all")).toBe(months);
    expect(visibleMonths(months, "complete")).toEqual([months[1]]);
    expect(months).toHaveLength(2);
  });
  it("handles empty and wholly unobserved windows", () => {
    expect(visibleMonths([], "complete")).toEqual([]);
    expect(visibleMonths([months[0]], "complete")).toEqual([]);
  });
  it("uses the exact accepted P3 F01 result and source", () => {
    const reading = trendReading(findings, data);
    expect(reading.result).toBe(findings.find((f) => f.id === "F01")!.result);
    expect(reading.source).toContain("P3_MONTHLY");
    expect(reading.title).toBe("全样本趋势");
    expect(reading.boundary).toContain("不是预测");
  });
  it.each([
    { ...data.scope, state: "SP" },
    { ...data.scope, start: "2017-01-01" },
    { ...data.scope, end: "2018-01-01" },
  ])("labels every local scope explicitly", (scope) => {
    const local = { ...data, scope };
    expect(isFullScope(local)).toBe(false);
    expect(trendReading(findings, local).boundary).toContain(
      "解读基于全样本",
    );
    expect(trendReading(findings, local).result).toBe(
      trendReading(findings, data).result,
    );
  });
  it("does not invent readings on missing snapshots", () => {
    expect(trendReading(null, data).result).toBeNull();
    expect(trendReading([], data).source).toBeNull();
  });
  it("preserves two zero-based axes, observation labels and exact tooltip amounts", () => {
    const option = monthlyOption(months) as {
      yAxis: { min: number }[];
      xAxis: { data: string[] }[];
      tooltip: { formatter: (v: unknown) => string };
    };
    expect(option.yAxis.map((a) => a.min)).toEqual([0, 0]);
    expect(option.xAxis[0].data).toEqual(["2016-09", "2017-01"]);
    expect(option.tooltip.formatter([{ dataIndex: 0 }])).toContain(
      "不完整观察月",
    );
    expect(option.tooltip.formatter([{ dataIndex: 1 }])).toContain("BRL 43.32");
    expect(option.tooltip.formatter([{ dataIndex: 1 }])).toContain(
      "完整观察月",
    );
    expect(money("13221498.11")).toBe("BRL 13,221,498.11");
  });
});
