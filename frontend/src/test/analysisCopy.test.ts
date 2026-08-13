import { describe, expect, it } from "vitest";
import {
  availableFeatureCount,
  countWords,
  estimateSentenceCount,
  formatFeatureValue,
  resultExplanation,
  resultHeadline
} from "../lib/analysisCopy";
import type { AnalyzeResponse } from "../api/analysis";

const baseResult: AnalyzeResponse = {
  state: "classified",
  label: "human_associated",
  ai_probability: 0.12345,
  features: [
    { name: "perplexity", value: 42.93, available: true, reason: null, metadata: {} },
    { name: "sentence_length_cv", value: 0.298, available: true, reason: null, metadata: {} },
    { name: "mattr", value: 0.905, available: true, reason: null, metadata: {} },
    { name: "pos_3gram_entropy", value: 6.67, available: true, reason: null, metadata: {} }
  ],
  text_statistics: {
    char_count: 100,
    word_count: 20,
    sentence_count: 3,
    lexical_token_count: 20,
    spacy_token_count: 23,
    language_model_token_count: 24
  },
  model_metadata: {}
};

describe("analysis copy helpers", () => {
  it("counts user typing statistics without backend fields", () => {
    expect(countWords("  one two\nthree ")).toBe(3);
    expect(estimateSentenceCount("One. Two? Three")).toBe(3);
  });

  it("formats unavailable feature values distinctly", () => {
    expect(formatFeatureValue(null)).toBe("Unavailable");
    expect(formatFeatureValue(42.93217)).toBe("42.932");
  });

  it("keeps classifier output framed as evidence state, not proof", () => {
    expect(resultHeadline(baseResult)).toBe("HUMAN-ASSOCIATED EVIDENCE");
    expect(resultExplanation({ ...baseResult, label: "ai_associated" })).toContain("machine-associated examples");
    expect(resultHeadline({ ...baseResult, state: "insufficient_evidence", label: null, ai_probability: null })).toBe(
      "INSUFFICIENT EVIDENCE"
    );
  });

  it("counts feature availability without fabricating missing measurements", () => {
    expect(
      availableFeatureCount([
        baseResult.features[0],
        { ...baseResult.features[1], available: false, value: null, reason: "missing" }
      ])
    ).toBe(1);
  });
});
