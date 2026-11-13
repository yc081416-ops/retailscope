import { useEffect, useState } from "react";
import { scopeQuery, validateScope, type AnalysisScope } from "./scope";
export type Row = Record<string, string | number | boolean | null>;
export type AnalysisPage = "users" | "products" | "delivery";
export type AnalysisData = {
  scope: AnalysisScope & { mode: string };
  metadata: {
    context: Row;
    bounds: { start: string; end: string };
    states?: string[];
    categories?: string[];
    read_only: boolean;
    query_sources: string[];
  };
} & Record<string, unknown>;
export const records = (data: AnalysisData, key: string) => data[key] as Row[];
export const numeric = (row: Row, key: string) => Number(row[key] ?? 0);
export const nullable = (row: Row, key: string) =>
  row[key] === null || row[key] === undefined ? null : Number(row[key]);
export const percent = (v: number | null, digits = 2) =>
  v === null ? "—" : `${(v * 100).toFixed(digits)}%`;
export function useAnalysis(page: AnalysisPage) {
  const [data, setData] = useState<AnalysisData | null>(null);
  const [metadata, setMetadata] = useState<AnalysisData["metadata"] | null>(
    null,
  );
  const [scope, setScope] = useState<AnalysisScope | null>(null);
  const [draft, setDraft] = useState<AnalysisScope>({
    start: "",
    end: "",
    state: null,
    category: null,
  });
  const [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [retry, setRetry] = useState(0);
  useEffect(() => {
    const abort = new AbortController();
    setLoading(true);
    setError("");
    setData(null);
    fetch(
      `/api/analysis/${page}?${page === "users" ? "" : scopeQuery(scope)}`,
      { signal: abort.signal },
    )
      .then(async (r) => {
        if (!r.ok)
          throw Error(
            r.status === 422
              ? "请检查日期、地区和类目是否有效。"
              : "数据暂时无法加载，请稍后重试。",
          );
        return r.json() as Promise<AnalysisData>;
      })
      .then((value) => {
        setData(value);
        setMetadata(value.metadata);
        if (!scope)
          setDraft({
            start: value.scope.start,
            end: value.scope.end,
            state: value.scope.state,
            category: value.scope.category,
          });
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
  }, [page, scope, retry]);
  const apply = (next = draft) => {
    setDraft(next);
    const issue = validateScope(next);
    if (issue) {
      setNotice(issue);
      return;
    }
    setNotice("");
    setScope({ ...next });
  };
  const reset = () => {
    if (metadata) {
      const full = { ...metadata.bounds, state: null, category: null };
      setDraft(full);
      setScope(full);
      setNotice("");
    }
  };
  const pending = Boolean(
    data &&
    (draft.start !== data.scope.start ||
      draft.end !== data.scope.end ||
      draft.state !== data.scope.state ||
      draft.category !== data.scope.category),
  );
  return {
    data,
    metadata,
    draft,
    setDraft,
    loading,
    error,
    notice,
    setNotice,
    apply,
    reset,
    pending,
    refresh: () => setRetry((n) => n + 1),
  };
}
