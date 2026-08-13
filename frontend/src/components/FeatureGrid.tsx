import type { FeatureEvidence } from "../api/analysis";
import {
  FEATURE_EXPLANATIONS,
  FEATURE_LABELS,
  FEATURE_ORDER,
  availableFeatureCount,
  formatFeatureValue
} from "../lib/analysisCopy";

interface FeatureGridProps {
  features: FeatureEvidence[];
}

export function FeatureGrid({ features }: FeatureGridProps) {
  const byName = new Map(features.map((feature) => [feature.name, feature]));
  const available = availableFeatureCount(features);

  return (
    <section className="evidence-panel" aria-labelledby="feature-evidence-title">
      <div className="section-kicker">Evidence vector</div>
      <div className="section-headline-row">
        <h2 id="feature-evidence-title">Feature evidence</h2>
        <div className="availability-stamp">{available} / 4 FEATURES AVAILABLE</div>
      </div>

      <div className="feature-grid">
        {FEATURE_ORDER.map((name, index) => {
          const feature = byName.get(name);
          const isAvailable = feature?.available ?? false;
          return (
            <article className={`feature-tile ${isAvailable ? "" : "feature-tile--missing"}`} key={name}>
              <div className="feature-index">{String(index + 1).padStart(2, "0")}</div>
              <div className="feature-name">{FEATURE_LABELS[name]}</div>
              <div className="feature-value">{formatFeatureValue(feature?.value ?? null)}</div>
              <p>{FEATURE_EXPLANATIONS[name]}</p>
              <div className={isAvailable ? "availability available" : "availability unavailable"}>
                {isAvailable ? "AVAILABLE" : "UNAVAILABLE"}
              </div>
              {!isAvailable && feature?.reason ? (
                <div className="reason-block">{feature.reason}</div>
              ) : null}
            </article>
          );
        })}
      </div>
    </section>
  );
}
