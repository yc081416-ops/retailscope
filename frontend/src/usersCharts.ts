import * as echarts from "echarts/core";
import { HeatmapChart } from "echarts/charts";
import { VisualMapComponent } from "echarts/components";
import type { EChartsCoreOption } from "echarts/core";
import { axisStyle, tipStyle } from "./analysisCharts";
import type { Row } from "./analysis";
echarts.use([HeatmapChart, VisualMapComponent]);
/** Missing observation is '-', never 0; only observed zero activity has value 0. */
export const retentionLabel=(value:number|null)=>value===null?'NA':value===0?'0%':value>=.1?`${(value*100).toFixed(0)}%`:value<.0001?'<0.01%':`${(value*100).toFixed(2)}%`;
export function cohortOption(rows: Row[], view:'all'|'focus'='all'): EChartsCoreOption {
  const cohorts = [
    ...new Set(rows.map((r) => String(r.cohort_month).slice(0, 7))),
  ].sort();
  const ages = [...new Set(rows.map((r) => Number(r.month_age)))].filter(age=>view==="all"||(age>=1&&age<=6)).sort(
    (a, b) => a - b,
  );
  return {
    tooltip: {
      ...tipStyle,
      trigger: "item",
      formatter: (p: { data: { row: Row } }) => {
        const r=p.data.row;
        return `首购月份 ${String(r.cohort_month).slice(0,7)}<br/>观察月份 ${String(r.target_month).slice(0,7)} · M${r.month_age}<br/>回购活跃留存 ${r.retention===null?'NA · 未完整观察':`${(Number(r.retention)*100).toFixed(6)}%`}<br/>活跃人数 ${r.active_users===null?'NA':r.active_users} 人<br/>首购人数 ${r.new_users} 人${r.cohort_left_truncated?'<br/>首购月存在左截断':''}`;
      },
    },
    grid: {
      left: 90,
      right: 25,
      top: 45,
      bottom: 75,
      show: true,
      backgroundColor: "#f5f4f8",
      borderWidth: 0,
    },
    xAxis: {
      ...axisStyle,
      type: "category",
      data: ages.map((n) => `M${n}`),
      position: "top",
      axisLabel: { fontSize: 12, interval: 0 },
      splitLine: { show: false },
    },
    yAxis: {
      ...axisStyle,
      type: "category",
      inverse: true,
      data: cohorts,
      axisLabel: { fontSize: 12, interval: 0 },
      splitLine: { show: false },
    },
    visualMap: {
      min: 0,
      max: 0.02,
      dimension: 3,
      outOfRange: {color:"#dce6e4"},
      orient: "horizontal",
      left: "center",
      bottom: 10,
      text: ["≥2%", "0%"],
      textStyle: { fontSize: 12, color: "#565d69" },
      inRange: {
        color: ["#ffffff", "#c3bce8", "#9488d7", "#7065d8", "#5145ac"],
      },
      calculable: false,
    },
    series: [
      {
        type: "heatmap",
        data: rows.filter(r=>ages.includes(Number(r.month_age))).map((r) => ({
          row:r,
          visualMap:Number(r.month_age)!==0,
          itemStyle:Number(r.month_age)===0?{color:'#dce6e4'}:undefined,
          value: [
            ages.indexOf(Number(r.month_age)),
            cohorts.indexOf(String(r.cohort_month).slice(0, 7)),
            r.retention === null ? "-" : Number(r.retention),
            Number(r.month_age)===0?-1:r.retention===null?-1:Number(r.retention),
          ],
        })),
        label: {
          show: true,
          fontSize: 12,
          formatter: (p: { data: { value: (number | string)[] } }) => {
            const v = p.data.value[2];
            return v === "-" ? "" : retentionLabel(Number(v));
          },
        },
        itemStyle: { borderWidth: 1, borderColor: "#fff" },
        emphasis: { itemStyle: { borderColor: "#777", borderWidth: 1 } },
      },
    ],
  };
}
