import type { EChartsCoreOption } from "echarts/core";
import type { Month, Overview } from "./types";
export const money = (n: string | number | null) =>
  n === null
    ? "—"
    : `BRL ${Number(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
export const number = (n: number) => n.toLocaleString("en-US");
const compact = (n: number) =>
  n >= 1e6
    ? `${+(n / 1e6).toFixed(1)}m`
    : n >= 1000
      ? `${+(n / 1000).toFixed(0)}k`
      : String(n);
const axis = {
  axisLine: { show: false },
  axisTick: { show: false },
  axisLabel: { color: "#626771", fontSize: 12 },
  splitLine: { lineStyle: { color: "#eeeff2", type: "dashed" } },
};
const tooltip = {
  trigger: "axis",
  backgroundColor: "#fff",
  borderColor: "#e6e7eb",
  textStyle: { color: "#202327", fontSize: 12 },
  extraCssText:
    "box-shadow:0 4px 20px #20232714;border-radius:8px;padding:12px;",
};

export function monthlyOption(rows: Month[]): EChartsCoreOption {
  const amounts = rows.map((r) => ({
    value: Number(r.merchandise),
    itemStyle: { color: r.is_complete ? "#7065d8" : "#b6afde" },
  }));
  const orders = rows.map((r) => ({
    value: r.orders,
    symbolSize: r.is_complete ? 4 : 7,
    itemStyle: { color: r.is_complete ? "#3f8d86" : "#b07a27" },
  }));
  const x = rows.map((r) => r.month_start.slice(0, 7));
  return {
    tooltip: {
      ...tooltip,
      formatter: (params: unknown) => {
        const item = (params as { dataIndex: number }[])[0];
        const r = rows[item.dataIndex];
        return `<strong>${r.month_start.slice(0, 7)} · ${r.is_complete ? "完整观察月" : "不完整观察月"}</strong><br/>商品成交额　${money(r.merchandise)}<br/>有效订单　${number(r.orders)} 单`;
      },
    },
    axisPointer: { link: [{ xAxisIndex: [0, 1] }] },
    grid: [
      { left: 66, right: 20, top: 12, height: "48%" },
      { left: 66, right: 20, top: "68%", bottom: 30 },
    ],
    xAxis: [
      {
        ...axis,
        type: "category",
        data: x,
        gridIndex: 0,
        axisLabel: { show: false },
        axisPointer: { show: true },
      },
      {
        ...axis,
        type: "category",
        data: x,
        gridIndex: 1,
        axisLabel: {
          color: "#626771",
          fontSize: 12,
          interval: Math.max(0, Math.ceil(rows.length / 10) - 1),
          formatter: (v: string) => v.replace("-", "/"),
        },
      },
    ],
    yAxis: [
      {
        ...axis,
        type: "value",
        min: 0,
        gridIndex: 0,
        splitNumber: 3,
        axisLabel: { color: "#626771", formatter: compact },
      },
      {
        ...axis,
        type: "value",
        min: 0,
        gridIndex: 1,
        name: "订单数 · 单",
        nameLocation: "end",
        nameGap: 14,
        nameTextStyle: { color: "#565d69", fontSize: 12, align: "left" },
        splitNumber: 2,
        minInterval: 1,
        axisLabel: { color: "#626771", formatter: compact },
      },
    ],
    series: [
      {
        name: "商品成交额 · BRL",
        type: "bar",
        data: amounts,
        xAxisIndex: 0,
        yAxisIndex: 0,
        barMaxWidth: 28,
        itemStyle: { borderRadius: [3, 3, 0, 0] },
      },
      {
        name: "有效订单 · 单",
        type: "line",
        data: orders,
        xAxisIndex: 1,
        yAxisIndex: 1,
        smooth: false,
        lineStyle: { color: "#3f8d86", width: 2 },
        showSymbol: true,
      },
    ],
  };
}
export const statusNames: Record<string, string> = {
  delivered: "已送达",
  shipped: "运输中",
  canceled: "已取消",
  unavailable: "无法履约",
  invoiced: "已开票",
  processing: "处理中",
  created: "已创建",
  approved: "已批准",
};
export function statusOption(data: Overview["statuses"]): EChartsCoreOption {
  return {
    grid: { left: 73, right: 64, top: 8, bottom: 10 },
    tooltip: {
      ...tooltip,
      formatter: (items: unknown) => {
        const i = (items as { dataIndex: number }[])[0].dataIndex;
        return `${statusNames[data[i].status] ?? data[i].status}　${number(data[i].orders)} 单`;
      },
    },
    xAxis: { ...axis, type: "value", show: false },
    yAxis: {
      ...axis,
      type: "category",
      inverse: true,
      data: data.map((r) => statusNames[r.status] ?? r.status),
      splitLine: { show: false },
    },
    series: [
      {
        type: "bar",
        barWidth: 12,
        data: data.map((r, i) => ({
          value: r.orders,
          itemStyle: {
            color: i === 0 ? "#7065d8" : "#c7c3e0",
            borderRadius: 3,
          },
        })),
        label: {
          show: true,
          position: "right",
          color: "#505560",
          fontSize: 12,
          formatter: (p: { value: number }) => number(p.value),
        },
      },
    ],
  };
}
