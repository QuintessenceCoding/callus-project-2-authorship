export type AnalysisState = "insufficient_evidence" | "classified";
export type AnalysisLabel = "human_associated" | "ai_associated";
export type FeatureName =
  | "perplexity"
  | "sentence_length_cv"
  | "mattr"
  | "pos_3gram_entropy";

export interface FeatureEvidence {
  name: FeatureName;
  value: number | null;
  available: boolean;
  reason: string | null;
  metadata: Record<string, unknown>;
}

export interface TextStatistics {
  char_count: number;
  word_count: number;
  sentence_count: number;
  lexical_token_count: number;
  spacy_token_count: number;
  language_model_token_count: number | null;
}

export interface SentenceEvidence {
  sentence_id: number;
  text: string;
  perplexity: number | null;
  available: boolean;
  reason: string | null;
}

export interface AnalyzeResponse {
  state: AnalysisState;
  label: AnalysisLabel | null;
  ai_probability: number | null;
  features: FeatureEvidence[];
  sentence_evidence: SentenceEvidence[];
  text_statistics: TextStatistics;
  model_metadata: Record<string, unknown>;
}

export class AnalyzeApiError extends Error {
  readonly status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "AnalyzeApiError";
    this.status = status;
  }
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "";

export async function analyzeText(text: string, signal?: AbortSignal): Promise<AnalyzeResponse> {
  let response: Response;

  try {
    response = await fetch(`${apiBaseUrl}/api/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ text }),
      signal
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new AnalyzeApiError("The analysis service is unavailable. Check that the backend is running.");
  }

  if (!response.ok) {
    if (response.status === 422) {
      throw new AnalyzeApiError("The request was rejected by validation. Provide essay text and try again.", 422);
    }
    throw new AnalyzeApiError(`The analysis service returned HTTP ${response.status}.`, response.status);
  }

  return response.json() as Promise<AnalyzeResponse>;
}
