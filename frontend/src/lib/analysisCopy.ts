import type { AnalyzeResponse, FeatureEvidence, FeatureName } from "../api/analysis";

export const FEATURE_ORDER: FeatureName[] = [
  "perplexity",
  "sentence_length_cv",
  "mattr",
  "pos_3gram_entropy"
];

export const FEATURE_LABELS: Record<FeatureName, string> = {
  perplexity: "Perplexity",
  sentence_length_cv: "Sentence-length CV",
  mattr: "MATTR",
  pos_3gram_entropy: "POS 3-gram entropy"
};

export const FEATURE_EXPLANATIONS: Record<FeatureName, string> = {
  perplexity: "How predictable the text is to the language model.",
  sentence_length_cv: "How much sentence lengths vary.",
  mattr: "A measure of lexical diversity.",
  pos_3gram_entropy: "How varied grammatical-tag sequences are."
};

export function countWords(text: string): number {
  const trimmed = text.trim();
  return trimmed ? trimmed.split(/\s+/).length : 0;
}

export function estimateSentenceCount(text: string): number {
  const trimmed = text.trim();
  if (!trimmed) {
    return 0;
  }
  const matches = trimmed.match(/[^.!?]+[.!?]+|[^.!?]+$/g);
  return matches ? matches.filter((part) => part.trim().length > 0).length : 0;
}

export function formatInteger(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

export function formatFeatureValue(value: number | null): string {
  if (value === null) {
    return "Unavailable";
  }
  if (Math.abs(value) >= 100) {
    return value.toFixed(2);
  }
  if (Math.abs(value) >= 10) {
    return value.toFixed(3);
  }
  return value.toFixed(4).replace(/0+$/, "").replace(/\.$/, "");
}

export function formatSignal(value: number | null): string {
  return value === null ? "Not reported" : value.toFixed(3);
}

export function availableFeatureCount(features: FeatureEvidence[]): number {
  return features.filter((feature) => feature.available).length;
}

export function resultHeadline(result: AnalyzeResponse | null): string {
  if (!result || result.state === "insufficient_evidence") {
    return "INSUFFICIENT EVIDENCE";
  }
  if (result.label === "ai_associated") {
    return "AI-ASSOCIATED EVIDENCE";
  }
  return "HUMAN-ASSOCIATED EVIDENCE";
}

export function resultExplanation(result: AnalyzeResponse | null): string {
  if (!result) {
    return "Submit a passage to inspect the available measurements.";
  }
  if (result.state === "insufficient_evidence") {
    return "The text does not contain enough usable information for reliable stylistic analysis.";
  }
  if (result.label === "ai_associated") {
    return "The measured writing characteristics are more consistent with the machine-associated examples used by the model.";
  }
  return "The measured writing characteristics are more consistent with the human-associated examples used by the model.";
}
