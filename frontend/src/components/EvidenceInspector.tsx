import type { AnalyzeResponse } from "../api/analysis";

interface Props {
  result: AnalyzeResponse;
}

export function EvidenceInspector({ result }: Props) {
  if (!result.sentence_evidence?.length) {
    return null;
  }

  const ranked = [...result.sentence_evidence]
    .filter((item) => item.available && item.perplexity !== null)
    .sort((a, b) => (a.perplexity ?? 0) - (b.perplexity ?? 0))
    .slice(0, 3);

  return (
    <section className="evidence-panel">
      <div className="section-kicker">Evidence Inspector</div>

      <h3>Predictability Evidence</h3>

      <p>
        Lower perplexity indicates more predictable language patterns.
        These passages contributed the strongest machine-associated signal.
      </p>

      <div className="evidence-list">
        {ranked.map((sentence) => (
          <article
            key={sentence.sentence_id}
            className="evidence-card"
          >
            <div className="evidence-header">
              Sentence {sentence.sentence_id}
            </div>

            <blockquote>
              {sentence.text}
            </blockquote>

            <div className="evidence-metric">
              Perplexity: {sentence.perplexity?.toFixed(2)}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}