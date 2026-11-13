import { useEffect, useRef } from "react";
import * as echarts from "echarts/core";
import { BarChart, LineChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
} from "echarts/components";
import { SVGRenderer } from "echarts/renderers";
import type { EChartsCoreOption } from "echarts/core";
echarts.use([
  BarChart,
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  SVGRenderer,
]);

export function Chart({
  option,
  label,
  height,
}: {
  option: EChartsCoreOption;
  label: string;
  height: number;
}) {
  const container = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const chart = echarts.init(container.current!, undefined, {
      renderer: "svg",
    });
    chart.setOption({
      ...option,
      animation: false,
      textStyle: {
        fontFamily: "Inter, Segoe UI, Microsoft YaHei, sans-serif",
        color: "#626771",
        fontSize: 12,
      },
    });
    const observer = new ResizeObserver(() => chart.resize());
    observer.observe(container.current!);
    return () => {
      observer.disconnect();
      chart.dispose();
    };
  }, [option]);
  return (
    <div
      role="img"
      aria-label={label}
      ref={container}
      style={{ height, width: "100%", minWidth: 0 }}
    />
  );
}
