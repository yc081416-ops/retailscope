import { useEffect, useState } from "react";
import type { Finding } from "./types";
export type Json =
  string | number | boolean | null | Json[] | { [key: string]: Json };
export type Provenance = {
  kind: string;
  path: string;
  executed_at: string | null;
  execution_time_recorded: boolean;
  available: boolean;
  file_saved_at?: string;
  sha256?: string;
  error?: string;
};
export type EvidenceFinding = Finding & {
  sample: Record<string, Json>;
  statistics: Record<string, Json>;
};
export type FindingsData = {
  scope: string;
  context: Record<string, Json>;
  findings: EvidenceFinding[];
  source: Provenance;
  report: Provenance & { matches_snapshot: boolean };
  read_only: boolean;
};
export const topics = [
  { label: "全部专题", ids: [] },
  { label: "经营趋势", ids: ["F01", "F02"] },
  { label: "商品集中度", ids: ["F03"] },
  { label: "地区表现", ids: ["F04"] },
  { label: "履约体验", ids: ["F05"] },
  { label: "用户与留存", ids: ["F06", "F07"] },
];
export function topicFindings(rows: EvidenceFinding[], topic: string) {
  const selected = topics.find((t) => t.label === topic) ?? topics[0];
  return rows
    .filter((f) => !selected.ids.length || selected.ids.includes(f.id))
    .sort((a, b) =>
      a.id === "F05" ? -1 : b.id === "F05" ? 1 : a.id.localeCompare(b.id),
    );
}
export function sampleSummary(f: EvidenceFinding) {
  const labels: Record<string, string> = {
    current_orders: "本月订单",
    baseline_orders: "比较月订单",
    categories: "类目数",
    merchandise: "商品金额（BRL）",
    orders: "订单数",
    delivery_n: "有效配送样本",
    late_n: "逾期判断样本",
    users: "购买用户",
    repeat_users: "复购用户",
    valid_orders: "关联有效订单",
    excluded_orders: "排除订单",
    eligible_cohorts: "合格cohort数",
    active_users: "活跃用户",
    baseline_users: "首购分母",
  };
  const parts = Object.entries(f.sample)
    .filter(([key]) => key in labels)
    .map(
      ([key, value]) =>
        `${labels[key]}：${typeof value === "number" ? value.toLocaleString("en-US") : String(value)}`,
    );
  const pairs = f.sample.usable_pairs as
    Record<string, { usable_pairs: number }> | undefined;
  if (pairs)
    for (const [key, value] of Object.entries(pairs))
      parts.push(
        `${key === "merchandise" ? "金额" : "订单"}可用月份对：${value.usable_pairs}`,
      );
  return parts.join(" · ");
}
export function sourceTime(source: Provenance) {
  return source.execution_time_recorded
    ? String(source.executed_at)
    : "执行时间未记录；文件保存时间不是执行时间";
}
export function useEvidence<T>(path: string) {
  const [data, setData] = useState<T | null>(null),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true),
    [retry, setRetry] = useState(0);
  useEffect(() => {
    const abort = new AbortController();
    setLoading(true);
    setError("");
    setData(null);
    fetch(path, { signal: abort.signal })
      .then(async (response) => {
        if (!response.ok) throw Error();
        return response.json() as Promise<T>;
      })
      .then(setData)
      .catch((e) => {
        if (e.name !== "AbortError")
          setError(
            "数据暂时无法加载，请稍后重试。",
          );
      })
      .finally(() => {
        if (!abort.signal.aborted) setLoading(false);
      });
    return () => abort.abort();
  }, [path, retry]);
  return { data, error, loading, refresh: () => setRetry((n) => n + 1) };
}
export async function downloadEvidence(path: string, filename: string) {
  const response = await fetch(path);
  if (!response.ok) throw Error("下载失败");
  const url = URL.createObjectURL(await response.blob());
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
