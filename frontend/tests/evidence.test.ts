import { describe, it, expect } from "vitest";
import {readP3Evidence} from "./p3Evidence";
import {
  topicFindings,
  sampleSummary,
  sourceTime,
  type EvidenceFinding,
  type Provenance,
} from "../src/evidence";

const facts: EvidenceFinding[] = readP3Evidence().findings;
describe("V2-03 fixed evidence presentation", () => {
  it("shows all seven accepted findings without altering their recorded values or order", () => {
    const original = JSON.stringify(facts),
      shown = topicFindings(facts, "全部专题");
    expect(shown).toHaveLength(7);
    expect(shown[0].id).toBe("F05");
    expect(JSON.stringify(facts)).toBe(original);
    for (const f of shown)
      expect(f).toEqual(facts.find((source) => source.id === f.id));
  });
  it.each([
    ["经营趋势", ["F01", "F02"]],
    ["履约体验", ["F05"]],
    ["用户与留存", ["F06", "F07"]],
  ])("filters %s only as a presentation selection", (topic, ids) => {
    expect(topicFindings(facts, String(topic)).map((f) => f.id)).toEqual(ids);
  });
  it("does not invent a finding or positive result for empty evidence", () => {
    expect(topicFindings([], "全部专题")).toEqual([]);
  });
  it("renders exact sample denominators, including nested MAD month pairs", () => {
    expect(sampleSummary(facts.find((f) => f.id === "F05")!)).toContain(
      "95,824",
    );
    expect(sampleSummary(facts.find((f) => f.id === "F02")!)).toContain(
      "金额可用月份对：18",
    );
    expect(sampleSummary(facts.find((f) => f.id === "F06")!)).toContain(
      "93,358",
    );
  });
  it("never promotes file mtime into an unrecorded audit execution time", () => {
    const source = {
      executed_at: null,
      execution_time_recorded: false,
      file_saved_at: "2026-11-13T01:00:00Z",
    } as Provenance;
    expect(sourceTime(source)).toContain("执行时间未记录");
    expect(sourceTime(source)).not.toContain(source.file_saved_at);
    expect(
      sourceTime({
        ...source,
        executed_at: "2026-11-12",
        execution_time_recorded: true,
      }),
    ).toBe("2026-11-12");
  });
});
