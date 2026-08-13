import { FormEvent, useMemo, useRef, useState } from "react";
import type { AnalyzeResponse } from "./api/analysis";
import { AnalyzeApiError, analyzeText } from "./api/analysis";
import { ResultsPanel } from "./components/ResultsPanel";
import { countWords, estimateSentenceCount, formatInteger } from "./lib/analysisCopy";
import "./styles.css";

const sampleText =
  "I learned to listen before solving the problem. The habit changed how our team wrote, tested, and revised every plan. By spring we had built a routine that other students could maintain. That experience made careful collaboration feel more durable than a quick answer.";

export default function App() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const inputStats = useMemo(
    () => ({
      words: countWords(text),
      sentences: estimateSentenceCount(text),
      characters: text.length
    }),
    [text]
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    try {
      const nextResult = await analyzeText(text, controller.signal);
      setResult(nextResult);
    } catch (caught) {
      if (caught instanceof DOMException && caught.name === "AbortError") {
        return;
      }
      if (caught instanceof AnalyzeApiError) {
        setError(caught.message);
      } else {
        setError("The analysis could not be completed.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="hero-band" aria-labelledby="hero-title">
        <div className="hero-mark">PROJECT 2 · DETECTOR INTERFACE</div>
        <h1 id="hero-title">
          <span>AUTHORSHIP</span>
          <span>ANALYSIS</span>
        </h1>
        <p>See what the writing reveals.</p>
      </section>

      <section className="workspace" aria-label="Essay analysis workspace">
        <form className="essay-column" onSubmit={handleSubmit}>
          <div className="manuscript-head">
            <div>
              <span className="section-kicker">Manuscript</span>
              <h2>Essay input</h2>
            </div>
            <button className="sample-button" type="button" onClick={() => setText(sampleText)}>
              LOAD SAMPLE
            </button>
          </div>

          <label className="sr-only" htmlFor="essay-text">
            Essay text
          </label>
          <textarea
            id="essay-text"
            value={text}
            onChange={(event) => {
              setText(event.target.value);
              setError(null);
            }}
            placeholder="Paste or write the essay text here..."
            spellCheck="true"
          />

          <div className="input-footer">
            <div className="input-stats" aria-label="Input text statistics">
              <span>{formatInteger(inputStats.words)} WORDS</span>
              <span>{formatInteger(inputStats.sentences)} SENTENCES</span>
              <span>{formatInteger(inputStats.characters)} CHARACTERS</span>
            </div>
            <button className="analyze-button" type="submit" disabled={loading}>
              {loading ? "ANALYZING..." : "ANALYZE TEXT ->"}
            </button>
          </div>

          {text.trim().length === 0 && !loading ? (
            <div className="empty-state">Empty manuscript. Add text to begin an evidence-based analysis.</div>
          ) : null}

          <article className="essay-preview" aria-label="Essay display">
            <div className="section-kicker">Document view</div>
            <p>{text.trim() || "The analyzed essay will remain visible here as a readable document."}</p>
          </article>
        </form>

        <ResultsPanel result={result} error={error} loading={loading} />
      </section>
    </main>
  );
}
