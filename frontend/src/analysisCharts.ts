import type { EChartsCoreOption } from "echarts/core";
import type { Row } from "./analysis";
import {categoryName,wrapCategoryLabel} from "./categories";
import {rfmRules} from "./rfmRules";
import { money, number } from "./charts";
export const chartColors = [
  "#7065d8",
  "#3f8d86",
  "#ad8250",
  "#7c8ea7",
  "#a57799",
  "#6d9480",
  "#9390b2",
  "#b18570",
  "#658b9e",
  "#8f9264",
];
export const axisStyle = {
  axisLine: { show: false },
  axisTick: { show: false },
  axisLabel: { color: "#626771", fontSize: 12 },
  splitLine: { lineStyle: { color: "#eeeff2", type: "dashed" } },
};
export const tipStyle = {
  trigger: "axis",
  backgroundColor: "#fff",
  borderColor: "#e6e7eb",
  textStyle: { color: "#202327", fontSize: 12 },
  valueFormatter: (value: unknown) =>
    value === null
      ? "NA"
      : typeof value === "number"
        ? number(value)
        : String(value),
  extraCssText:
    "box-shadow:0 4px 20px #20232714;border-radius:8px;padding:12px;",
};
export function horizontal(
  rows: Row[],
  label: string,
  value: string,
  color = chartColors[0],
  isMoney = false,
): EChartsCoreOption {
  return {
    grid: { left: 180, right: 75, top: 12, bottom: 35 },
    tooltip: {
      ...tipStyle,
      formatter: (params: unknown) => {
        const r = rows[(params as { dataIndex: number }[])[0].dataIndex];
        return `${label==="category"?categoryName(r[label]):r[label]}<br/>${label==="category"?`原编码 ${r[label]}<br/>`:""}${label==="segment"?`${rfmRules[String(r[label])] ?? ""}<br/>`:""}${isMoney ? money(Number(r[value])) : number(Number(r[value]))}`;
      },
    },
    xAxis: {
      ...axisStyle,
      type: "value",
      min: 0,
      axisLabel: {
        color: "#626771",
        fontSize: 12,
        formatter: (v: number) =>
          v >= 1000 ? `${+(v / 1000).toFixed(0)}k` : String(v),
      },
    },
    yAxis: {
      ...axisStyle,
      type: "category",
      inverse: true,
      data: rows.map((r) => label==="category"?categoryName(r[label]):String(r[label])),
      axisLabel: {
        color: "#626771",
        fontSize: 12,
        width: 160,
        overflow: label === "category" ? "break" : "truncate",
        lineHeight: 16,
        formatter:label==='category'?wrapCategoryLabel:undefined,
      },
      splitLine: { show: false },
    },
    series: [
      {
        type: "bar",
        data: rows.map((r) => (r[value] === null ? null : Number(r[value]))),
        barMaxWidth: 22,
        itemStyle: { color, borderRadius: [0, 3, 3, 0] },
        label: {
          show: !isMoney,
          position: "right",
          color: "#565d69",
          fontSize: 12,
          formatter: (p: { value: number }) => number(p.value),
        },
      },
    ],
  };
}
export function bars(
  rows: Row[],
  label: string,
  value: string,
  log = false,
  color = chartColors[0],
): EChartsCoreOption {
  return {
    grid: { left: 70, right: 25, top: 18, bottom: 42 },
    tooltip: {
      ...tipStyle,
      valueFormatter: (v: number | null) =>
        v === null
          ? "NA"
          : value === "delivery_days"
            ? `${v.toFixed(2)} 天`
            : number(v),
    },
    xAxis: {
      ...axisStyle,
      type: "category",
      data: rows.map((r) => label==="category"?categoryName(r[label]):String(r[label])),
      axisLabel: { color: "#626771", fontSize: 12, hideOverlap: true },
    },
    yAxis: {
      ...axisStyle,
      type: log ? "log" : "value",
      min: log ? 1 : 0,
      minInterval: 1,
    },
    series: [
      {
        type: "bar",
        name:
          value === "delivery_days"
            ? "平均配送天数 · 天"
            : value === "users" || value === "new_users"
              ? "用户数 · 人"
              : "订单数 · 单",
        data: rows.map((r) => (r[value] === null ? null : Number(r[value]))),
        barMaxWidth: 32,
        itemStyle: { color, borderRadius: [3, 3, 0, 0] },
      },
    ],
  };
}
export function categoryTrend(
  monthly: Row[],
  categories: Row[],
): EChartsCoreOption {
  const months = [
    ...new Set(monthly.map((r) => String(r.month_start).slice(0, 7))),
  ].sort();
  const top = categories.slice(0, 5).map((r) => String(r.category));
  return {
    color: chartColors,
    grid: { left: 75, right: 25, top: 65, bottom: 35 },
    legend: {
      type: "scroll",
      top: 5,
      textStyle: { fontSize: 12, color: "#565d69" },
      data: top.map(categoryName),
    },
    tooltip: { ...tipStyle, valueFormatter: (v: number) => money(v) },
    xAxis: { ...axisStyle, type: "category", data: months },
    yAxis: {
      ...axisStyle,
      type: "value",
      min: 0,
      name: "商品金额 · BRL",
      nameTextStyle: { fontSize: 12, color: "#565d69" },
    },
    series: top.map((category) => ({
      name: categoryName(category),
      type: "line",
      showSymbol: false,
      connectNulls: false,
      data: months.map((month) => {
        const row = monthly.find(
          (r) =>
            r.category === category && String(r.month_start).startsWith(month),
        );
        return row ? Number(row.merchandise) : null;
      }),
    })),
  };
}
export function paretoOption(categories: Row[]): EChartsCoreOption {
  let total = 0;
  const cumulative = categories.map((r) => {
    total += Number(r.contribution);
    return total;
  });
  return {
    grid: { left: 75, right: 75, top: 40, bottom: 35 },
    tooltip: {
      ...tipStyle,
      formatter: (params: unknown) => {
        const i = (params as { dataIndex: number }[])[0].dataIndex;
        return `第${i+1}名 · ${categoryName(categories[i].category)}<br/>原编码 ${categories[i].category}<br/>商品金额 ${money(Number(categories[i].merchandise))}<br/>累计贡献 ${(cumulative[i] * 100).toFixed(2)}%`;
      },
    },
    xAxis: {
      ...axisStyle,
      type: "category",
      data: categories.map((_, i) => String(i + 1)),
      axisLabel: {fontSize:12,color:"#626771",interval:9,showMinLabel:true,showMaxLabel:true},
      name: "品类排名",
      nameLocation: "middle",
      nameGap: 24,
      nameTextStyle: { fontSize: 12 },
    },
    yAxis: [
      {
        ...axisStyle,
        type: "value",
        min: 0,
        name: "商品金额 · BRL",
        nameTextStyle: { fontSize: 12 },
      },
      {
        ...axisStyle,
        type: "value",
        min: 0,
        max: 1,
        name: "累计贡献",
        nameTextStyle: { fontSize: 12 },
        axisLabel: {
          fontSize: 12,
          formatter: (v: number) => `${(v * 100).toFixed(0)}%`,
        },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: "商品金额 · BRL",
        type: "bar",
        data: categories.map((r) => Number(r.merchandise)),
        itemStyle: { color: chartColors[0] },
        barMaxWidth: 20,
      },
      {
        name: "累计贡献",
        type: "line",
        yAxisIndex: 1,
        data: cumulative,
        showSymbol: false,
        lineStyle: { color: chartColors[1], width: 2 },
      },
    ],
  };
}
export function itemOrdersOption(categories: Row[]): EChartsCoreOption {
  const top = categories.slice(0, 10);
  return {
    color: chartColors,
    grid: { left: 180, right: 30, top: 45, bottom: 25 },
    legend: { top: 5, textStyle: { fontSize: 12, color: "#565d69" } },
    tooltip: { ...tipStyle },
    xAxis: { ...axisStyle, type: "value", min: 0 },
    yAxis: {
      ...axisStyle,
      type: "category",
      inverse: true,
      data: top.map((r) => categoryName(r.category)),
      axisLabel: { fontSize: 12, width: 160, overflow: "break", lineHeight: 16,formatter:wrapCategoryLabel },
    },
    series: [
      {
        name: "商品件数",
        type: "bar",
        data: top.map((r) => Number(r.items)),
        barMaxWidth: 12,
      },
      {
        name: "类目内去重订单数",
        type: "bar",
        data: top.map((r) => Number(r.orders)),
        barMaxWidth: 12,
      },
    ],
  };
}
export function associationOption(rows: Row[]): EChartsCoreOption {
  return {
    grid: { left: 60, right: 35, top: 20, bottom: 40 },
    tooltip: {
      ...tipStyle,
      formatter: (params: unknown) => {
        const r = rows[(params as { dataIndex: number }[])[0].dataIndex];
        return `${r.delivery_group}<br/>订单等权均分 ${Number(r.review_mean).toFixed(4)}<br/>有效评价 ${number(Number(r.orders))} 单`;
      },
    },
    xAxis: {
      ...axisStyle,
      type: "category",
      data: rows.map((r) => r.delivery_group),
    },
    yAxis: { ...axisStyle, type: "value", min: 0, max: 5 },
    series: [
      {
        type: "bar",
        data: rows.map((r) => Number(r.review_mean)),
        barMaxWidth: 70,
        itemStyle: { color: chartColors[0], borderRadius: [3, 3, 0, 0] },
      },
    ],
  };
}
