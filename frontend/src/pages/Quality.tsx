import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  AnalysisHeader,
  ResultState,
  Panel,
  DataTable,
  Footer,
} from "../AnalysisUI";
import type { Row } from "../analysis";
import {
  useEvidence,
  downloadEvidence,
  type Provenance,
} from "../evidence";
import {beijingTime} from "../dateTime";
import { number } from "../charts";

type AuditTable = {
  table: string;
  audit_rows: number;
  full_duplicate_rows: number;
  logical_key: string[];
  key_duplicates: number | null;
  missing_key_rows: number | null;
  malformed_rows: number;
  invalid_numeric: number;
  invalid_date: number;
};
type TestRecord = {
  stage: string;
  tests: number;
  passed: number;
  failures: number;
  errors: number;
  skipped: number;
  successful: boolean;
  source: Provenance;
  note: string;
};
type QualityData = {
  read_at: string;
  read_only: boolean;
  dataset: {
    name: string;
    url: string;
    license: string;
    version: string | null;
    source: Provenance;
  };
  live: {
    status: string;
    as_of: string;
    raw_counts: Row[];
    objects: Row[];
    constraints: Row[];
    warehouse_checks: Row[];
    error?: string;
    note?: string;
    query_ids?: string[];
  };
  historical: {
    source: Provenance;
    tables: AuditTable[];
    missing: Row[];
    relations: Row[];
    nonunique_references: Row[];
    has_blocking_issues: boolean | null;
    note: string;
  };
  warehouse: {
    source: Provenance;
    status: string | null;
    idempotent: boolean | null;
    raw_unchanged_at_run: boolean | null;
    pandas_passed: boolean | null;
  };
  reconciliation: {
    source: Provenance;
    passed: boolean | null;
    checks: Row[];
    money_comparison: string | null;
  };
  runtime: {
    source: Provenance;
    record_present: boolean;
    expected_raw_rows: Record<string, number>;
    note: string;
  };
  analysis_snapshot: {
    available: boolean;
    source?: Provenance;
    findings?: number;
    report_matches?: boolean;
    report_source?: Provenance;
    note: string;
  };
  tests: {
    history: TestRecord[];
    latest: TestRecord | null;
    selection: string;
  };
};

function Source({ source, label }: { source: Provenance; label: string }) {
  return (
    <div className="source-evidence">
      <Badge variant="outline">{label}</Badge>
      <span>来源：{source.path}</span>
      <span>执行时间：{source.execution_time_recorded ? beijingTime(source.executed_at) : "未记录"}</span>
      {source.file_saved_at && (
        <span>文件保存时间：{beijingTime(source.file_saved_at)}</span>
      )}
      {!source.available && <strong>记录暂不可用</strong>}
    </div>
  );
}
const boolText = (v: boolean | null) =>
  v === null ? "未记录" : v ? "是" : "否";
export default function Quality() {
  const state = useEvidence<QualityData>("/api/evidence/quality"),
    [table, setTable] = useState("ALL"),
    [onlyMissing, setOnlyMissing] = useState(true),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false);
  const data = state.data;
  const download = async () => {
    setBusy(true);
    try {
      await downloadEvidence(
        "/api/evidence/quality/export",
        "retailscope-quality-all.json",
      );
      setNotice("质量报告下载成功。");
    } catch {
      setNotice("报告暂时无法下载，请稍后重试。");
    } finally {
      setBusy(false);
    }
  };
  const liveCounts = new Map(
    data?.live.raw_counts.map((r) => [String(r.table_name), Number(r.rows)]),
  );
  const countRows = (
    data?.historical.tables.length
      ? data.historical.tables.map((r) => r.table)
      : (data?.live.raw_counts.map((r) => String(r.table_name)) ?? [])
  ).map((name) => {
    const audit = data?.historical.tables.find((r) => r.table === name),
      live = liveCounts.get(name);
    return {
      table: name,
      current_rows: live ?? null,
      historical_rows: audit?.audit_rows ?? null,
      comparison:
        live === undefined
          ? "当前值不可用"
          : audit
            ? live === audit.audit_rows
              ? "行数一致"
              : "行数变化"
            : "无历史记录",
    };
  });
  return (
    <main className="analysis-page evidence-page">
      <AnalysisHeader
        title="数据质量中心"
        description="查看数据规模、质量与更新状态。"
        refresh={state.refresh}
        loading={state.loading}
      />
      <ResultState
        loading={state.loading}
        error={state.error}
        retry={state.refresh}
      />
      {data && (
        <>
          <section className="trust-status" aria-label="质量状态来源">
            <div>
              <Badge variant="outline">当前数据</Badge>
              <strong>
                {data.live.status === "available"
                  ? `${data.live.raw_counts.length}张原始表 · ${number(data.live.raw_counts.reduce((n, r) => n + Number(r.rows), 0))}条记录`
                  : "当前查询不可用"}
              </strong>
              <span>查询时间：{beijingTime(data.live.as_of)}</span>
            </div>
            <div>
              <Badge variant="outline">历史审计</Badge>
              <strong>{data.historical.has_blocking_issues === null ? "状态未记录" : data.historical.has_blocking_issues ? "有待核查项" : "无阻断项"}</strong>
              <span>分析快照：{data.analysis_snapshot.available && data.analysis_snapshot.report_matches ? "可用" : "需核查"}</span>
            </div>
          </section>
          {data.live.status !== "available" && (
            <p className="export-notice" role="status">
              当前数据暂不可用，仍可查看历史记录。
            </p>
          )}
          <Panel
            title="原始数据规模"
            description="当前查询与历史审计对照"
          >
            <details className="evidence-details"><summary>数据版本与来源</summary>
            <p className="quality-intro">
              <a href={data.dataset.url} target="_blank" rel="noreferrer">
                {data.dataset.name}
              </a>{" "}
              · Kaggle版本 {data.dataset.version ?? "未记录"} ·{" "}
              {data.dataset.license} ·
              2016–2018 历史样本。
            </p>
            <Source source={data.dataset.source} label="下载校验记录" />
            </details>
            <DataTable
              rows={countRows}
              label="九张原始表当前与历史记录数"
              columns={[
                { key: "table", label: "原始表" },
                { key: "current_rows", label: "当前记录数", kind: "number" },
                {
                  key: "historical_rows",
                  label: "历史审计记录数",
                  kind: "number",
                },
                { key: "comparison", label: "比较说明" },
              ]}
            />
            <details className="evidence-details"><summary>查询说明</summary><p className="method-content">计数相同仅表示行数一致；当前查询不等同于源文件内容审计。查询标识：{data.live.query_ids?.join(" / ") ?? "查询不可用"}</p></details>
          </Panel>
          <details className="evidence-details"><summary>缺失与重复 · 历史审计</summary>
          <Panel
            title="缺失与重复 · 历史审计"
            description="历史源文件审计；执行时间未记录。"
          >
            <Source source={data.historical.source} label="历史审计快照" />
            <p className="panel-bottom">
              {data.historical.note} 历史阻断标记：
              {data.historical.has_blocking_issues === null
                ? "未核实"
                : data.historical.has_blocking_issues
                  ? "存在"
                  : "无"}
              。
            </p>
            <DataTable
              rows={data.historical.tables.map((r) => ({
                ...r,
                logical_key:
                  r.logical_key.join(" + ") || "未设逻辑唯一键（保留源数据）",
              }))}
              label="P0重复与唯一键历史检查"
              columns={[
                { key: "table", label: "表" },
                { key: "logical_key", label: "审计逻辑唯一键" },
                {
                  key: "full_duplicate_rows",
                  label: "整行重复",
                  kind: "number",
                },
                { key: "key_duplicates", label: "逻辑键重复", kind: "number" },
                {
                  key: "missing_key_rows",
                  label: "逻辑键缺失",
                  kind: "number",
                },
                { key: "malformed_rows", label: "格式异常", kind: "number" },
                { key: "invalid_numeric", label: "非法数值", kind: "number" },
                { key: "invalid_date", label: "非法日期", kind: "number" },
              ]}
            />
            <div className="quality-field-filter">
              <label htmlFor="audit-table">字段缺失范围</label>
              <select
                id="audit-table"
                value={table}
                onChange={(e) => setTable(e.target.value)}
              >
                <option value="ALL">全部原始表</option>
                {data.historical.tables.map((r) => (
                  <option key={r.table}>{r.table}</option>
                ))}
              </select>
              <label>
                <input
                  type="checkbox"
                  checked={onlyMissing}
                  onChange={(e) => setOnlyMissing(e.target.checked)}
                />
                仅显示有缺失字段
              </label>
            </div>
            <DataTable
              rows={data.historical.missing.filter(
                (r) =>
                  (table === "ALL" || r.table === table) &&
                  (!onlyMissing || Number(r.missing_rows) > 0),
              )}
              label="P0历史字段缺失"
              columns={[
                { key: "table", label: "表" },
                { key: "column", label: "字段" },
                { key: "missing_rows", label: "缺失记录", kind: "number" },
                { key: "missing_rate", label: "历史缺失率", kind: "percent" },
              ]}
            />
          </Panel>
          </details>
          <details className="evidence-details"><summary>关联关系与异常</summary>
          <Panel
            title="关联关系与异常"
            description="历史关联检查与当前仓库检查分别列出"
          >
            <h3 className="quality-subtitle">历史关联检查</h3>
            <DataTable
              rows={data.historical.relations}
              label="P0历史关联异常"
              columns={[
                { key: "check", label: "历史检查标识" },
                { key: "rows", label: "记录/订单数", kind: "number" },
              ]}
            />
            <h3 className="quality-subtitle">历史非唯一引用字段</h3>
            <DataTable
              rows={data.historical.nonunique_references}
              label="历史非唯一引用字段"
              columns={[
                { key: "check", label: "历史引用检查" },
                { key: "rows", label: "重复记录", kind: "number" },
              ]}
            />
            <p className="panel-bottom">
              review_id、邮编前缀和customer_unique_id不应被误设为Raw唯一主键；多支付、多评价是合法一对多现象。缺翻译、缺邮编覆盖、取消等状态无商品明细应结合既定口径解释。
            </p>
            <h3 className="quality-subtitle">当前仓库检查</h3>
            <DataTable
              rows={data.live.warehouse_checks.flatMap((r) =>
                Object.entries(r).map(([check, value]) => ({ check, value })),
              )}
              label="当前仓库异常查询"
              columns={[
                { key: "check", label: "检查标识" },
                { key: "value", label: "当前仓库记录数", kind: "number" },
              ]}
            />
          </Panel>
          </details>
          <details className="evidence-details"><summary>数据架构与约束</summary>
          <Panel
            title="数据架构与约束"
            description="当前数据库对象与约束"
          >
            <div className="warehouse-layers">
              {["raw", "core", "mart"].map((schema) => (
                <section key={schema}>
                  <h3>{schema.toUpperCase()}</h3>
                  <p>
                    {schema === "raw"
                      ? "保留源值与源重复"
                      : schema === "core"
                        ? "类型规范化只读视图"
                        : "维表、事实表与分析聚合"}
                  </p>
                  <span>
                    {data.live.status === "available"
                      ? data.live.objects.filter((r) => r.schema === schema)
                          .length
                      : "NA"}{" "}
                    个当前对象
                  </span>
                </section>
              ))}
            </div>
            <details className="evidence-details">
              <summary>展开当前表与视图目录</summary>
              <DataTable
                rows={data.live.objects}
                label="当前架构对象目录"
                columns={[
                  { key: "schema", label: "Schema" },
                  { key: "object", label: "对象" },
                  { key: "type", label: "类型" },
                ]}
              />
            </details>
            <details className="evidence-details">
              <summary>展开当前主键、外键及唯一约束</summary>
              <DataTable
                rows={data.live.constraints}
                label="当前数据库主外键约束"
                columns={[
                  { key: "schema", label: "Schema" },
                  { key: "object", label: "对象" },
                  { key: "type", label: "约束类型" },
                  { key: "definition", label: "数据库目录定义" },
                ]}
              />
            </details>
          </Panel>
          </details>
          <details className="evidence-details"><summary>构建与对账记录</summary>
          <Panel
            title="构建与对账记录"
            description="历史构建结果与分析快照"
          >
            <Source source={data.warehouse.source} label="历史构建" />
            <p className="quality-intro">
              历史状态：{data.warehouse.status ?? "未记录"} · 两次构建一致：
              {boolText(data.warehouse.idempotent)} · 当次Raw保留：
              {boolText(data.warehouse.raw_unchanged_at_run)} · 独立Pandas通过：
              {boolText(data.warehouse.pandas_passed)}
            </p>
            <Source source={data.runtime.source} label="初始化历史清单" />
            <p className="quality-intro">{data.runtime.note}</p>
            {data.analysis_snapshot.source && (
              <Source
                source={data.analysis_snapshot.source}
                label="分析快照"
              />
            )}
            <p className="quality-intro">
              分析文件：
              {data.analysis_snapshot.available
                ? `${data.analysis_snapshot.findings}项发现；报告配对一致`
                : "不可用或不一致"}
              。{data.analysis_snapshot.note}
            </p>
            <Source
              source={data.reconciliation.source}
              label="历史独立对账结果"
            />
            <p className="quality-intro">
              {data.reconciliation.money_comparison ?? "未记录对账方法"}
              。单项对账执行时间未单独记录，不假定等于页面读取时间。
            </p>
            <DataTable
              rows={data.reconciliation.checks.map((r) => ({
                ...r,
                status:
                  r.passed === true
                    ? "当次通过"
                    : r.passed === false
                      ? "当次失败"
                      : "未记录",
              }))}
              label="P1独立对账记录"
              columns={[
                { key: "name", label: "对账检查标识" },
                { key: "status", label: "历史结果" },
                { key: "rows", label: "核对行数", kind: "number" },
              ]}
            />
          </Panel>
          </details>
          <details className="evidence-details"><summary>运行检查记录</summary>
          <Panel
            title="运行检查记录"
            description="已有运行日志"
          >
            <p className="quality-intro" data-testid="latest-test-record">
              {data.tests.latest ? `最近运行检查：${data.tests.latest.successful ? "通过" : "需核查"} · ${beijingTime(data.tests.latest.source.executed_at)}` : "暂无运行记录"}
            </p>

            <DataTable
              rows={data.tests.history.map((r) => ({
                status: r.successful ? "通过" : "需核查",
                tests: r.tests,
                passed: r.passed,
                failures: r.failures,
                errors: r.errors,
                skipped: r.skipped,
                executed: beijingTime(r.source.executed_at),
                saved: beijingTime(r.source.file_saved_at),
                source: r.source.path,
              }))}
              label="历史完整测试记录"
              columns={[
                { key: "status", label: "结果" },
                { key: "executed", label: "执行时间（北京时间）" },
                { key: "source", label: "来源文件" },
              ]}
            />
          </Panel>
          </details>
          <section className="export-row">
            <div>
              <strong>导出质量报告</strong>
              <span>JSON · 含来源与检查时间</span>
            </div>
            <Button variant="outline" onClick={download} disabled={busy}>
              下载 JSON
            </Button>
          </section>
          {notice && (
            <p className="export-notice" role="status">
              {notice}
            </p>
          )}
        </>
      )}
      <Footer />
    </main>
  );
}
