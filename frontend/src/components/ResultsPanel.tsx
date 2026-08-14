import type { AnalyzeResponse } from "../api/analysis";
import {
  availableFeatureCount,
  formatInteger,
  formatSignal,
  resultExplanation,
  resultHeadline
} from "../lib/analysisCopy";
import { FeatureGrid } from "./FeatureGrid";
import { MethodologyPanel } from "./MethodologyPanel";
import { EvidenceInspector } from "./EvidenceInspector";

interface ResultsPanelProps {
  result: AnalyzeResponse | null;
  error: string | null;
  loading: boolean;
}

function metadataLine(result: AnalyzeResponse): string {
  const version = result.model_metadata.artifact_version;
  const source = result.model_metadata.source_experiment;
  const versionText = typeof version === "string" ? version : "model artifact";
  const sourceText = typeof source === "string" ? source : "recorded methodology";
  return `${versionText} · ${sourceText}`;
}

export function ResultsPanel({ result, error, loading }: ResultsPanelProps) {
  return (
    <aside className="analysis-column" aria-live="polite">
      <section className="result-block" aria-labelledby="result-title">
        <div className="section-kicker">Analysis</div>
        <h2 id="result-title">{loading ? "ANALYZING TEXT" : resultHeadline(result)}</h2>
        <p>{loading ? "Extracting measurements and requesting the classifier output." : resultExplanation(result)}</p>

        {error ? <div className="api-error" role="alert">{error}</div> : null}

        {result ? (
          <>
            <div className="result-facts">
              <div>
                <span>MODEL SIGNAL</span>
                <strong>{formatSignal(result.ai_probability)}</strong>
              </div>
              <div>
                <span>STATE</span>
                <strong>{result.state.replace("_", " ")}</strong>
              </div>
              <div>
                <span>EVIDENCE</span>
                <strong>{availableFeatureCount(result.features)} / 4</strong>
              </div>
            </div>

            {result.state === "insufficient_evidence" ? (
              <div className="insufficient-note">
                <strong>Try a longer passage.</strong>
                <span>Unavailable measurements are shown below with their API-provided reasons.</span>
              </div>
            ) : null}

            <div className="text-stat-strip">
              <div>
                <span>WORD COUNT</span>
                <strong>{formatInteger(result.text_statistics.word_count)}</strong>
              </div>
              <div>
                <span>SENTENCE COUNT</span>
                <strong>{formatInteger(result.text_statistics.sentence_count)}</strong>
              </div>
              <div>
                <span>CHARACTER COUNT</span>
                <strong>{formatInteger(result.text_statistics.char_count)}</strong>
              </div>
            </div>

            <div className="model-meta">{metadataLine(result)}</div>
          </>
        ) : (
          <div className="empty-analysis">
            Paste an essay and run the detector to inspect the measured evidence.
          </div>
        )}
      </section>

      {result ? <EvidenceInspector result={result} /> : null}
      {result ? <FeatureGrid features={result.features} /> : null}
      <MethodologyPanel />
    </aside>
  );
}
