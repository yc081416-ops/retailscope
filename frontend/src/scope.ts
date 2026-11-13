import type { Scope } from "./types";
export type AnalysisScope = Scope & { category: string | null };
export function validateScope(scope: Scope): string | null {
  if (!scope.start || !scope.end) return "请选择开始日期与结束日期。";
  if (scope.start > scope.end)
    return "开始日期不能晚于结束日期，请调整后再应用。";
  return null;
}
/** A ranking click is an apply action over the current draft, never the previous result. */
export function withDraftState<T extends Scope>(draft: T, state: string): T {
  return { ...draft, state };
}
export function scopeQuery(scope: AnalysisScope | null): string {
  const p = new URLSearchParams();
  if (scope) {
    p.set("start", scope.start);
    p.set("end", scope.end);
    if (scope.state) p.set("state", scope.state);
    if (scope.category) p.set("category", scope.category);
  }
  return p.toString();
}
