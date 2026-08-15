export function MethodologyPanel() {
  const steps = [
    "Segment the writing",
    "Extract four stylistic measurements",
    "Standardize the feature vector",
    "Evaluate it with Logistic Regression",
    "Report the available evidence",
    "Abstain when required measurements are unavailable"
  ];

  return (
    <details className="methodology-panel" open>
      <summary>How this analysis works</summary>
      <ol>
        {steps.map((step, index) => (
          <li key={step}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            {step}
          </li>
        ))}
      </ol>
      <p>
        This tool estimates machine-associated writing patterns. It does not establish authorship or prove that AI was
        used.
      </p>
    </details>
  );
}