# Detection Methodology — Evidence-First Authorship Analysis

## 1. Purpose

This document defines the **validated production methodology** used by Callus Project 2 to detect measurable characteristics associated with machine-generated writing in admissions-style essays.

The methodology is intentionally experiment-driven. Candidate features and localization methods were tested through EXP-001 through EXP-011 before being promoted, rejected, or deferred.

The production system does **not** attempt to prove authorship.

Instead, it estimates whether a document exhibits measurable characteristics associated with machine-generated writing within the project's development and validation distribution, while communicating evidence limitations explicitly.

---

# 2. Methodological Position

The system draws an important distinction between:

```text
Document-level machine association
            +
Sentence-level evidence observations
```

and:

```text
Sentence-level AI authorship attribution
```

The production classifier performs the first.

It does **not** perform the second.

This distinction was strengthened by EXP-007, EXP-008, EXP-009, and EXP-011, which showed that the tested local-attribution approaches were not reliable enough to justify sentence-level authorship claims.

The final product therefore asks:

> Does the document exhibit measurable characteristics associated with machine-generated writing?

and, where validated sentence-level measurements exist:

> Where in the document do these measurable patterns appear?

It does not claim:

> This sentence was written by AI.

---

# 3. Core Analytical Questions

The completed methodology addresses four questions.

### Q1 — Machine Association

Does the complete essay exhibit a measurable feature profile associated with machine-generated examples in the development distribution?

### Q2 — Evidence Location

Where do directly measurable local signals appear in the essay?

The current production answer is sentence-level perplexity evidence.

### Q3 — Evidence Sufficiency

Are all four features required by the trained classifier available and numerically valid?

If not, the system abstains.

### Q4 — Generalization and Limitations

How should the result be interpreted outside the development distribution, across writing styles, and under hybrid or ESL conditions?

These questions prevent the system from collapsing everything into an unexplained AI percentage.

---

# 4. Analytical Units

## 4.1 Document

The complete submitted essay.

The document is the primary unit for production classification.

The four-feature classifier operates on:

```text
perplexity
sentence_length_cv
mattr
pos_3gram_entropy
```

The resulting vector is normalized and passed to the persisted Logistic Regression classifier.

---

## 4.2 Sentence

Sentences are extracted using deterministic spaCy sentence segmentation.

Sentence-level data is retained for measurements that are genuinely computed at sentence level.

In the production system, sentence-level perplexity is preserved as structured evidence.

Sentence evidence is a measurement observation, not a sentence-level classification.

---

## 4.3 Passage

Passage-level AI attribution is **not a production classifier**.

Passages were important during the experimental phase because hybrid writing and local discontinuity were research questions.

However, EXP-007 through EXP-011 did not establish sufficiently reliable local attribution for production use.

The current UI therefore uses measured sentence evidence rather than assigning machine/human labels to arbitrary passage windows.

---

# 5. Production Methodology Pipeline

The current runtime pipeline is:

```text
Raw Essay
    │
    ▼
spaCy Sentence Segmentation
    │
    ▼
Validated Feature Extraction
    │
    ├── Document Perplexity
    ├── Sentence-Length CV
    ├── MATTR
    └── POS 3-Gram Entropy
    │
    ▼
Required-Feature Availability Check
    │
    ├── Missing feature → insufficient_evidence
    │
    └── Complete vector
            │
            ▼
       StandardScaler
            │
            ▼
      LogisticRegression
            │
            ▼
    Document Classification
            │
            ▼
    Structured Evidence Response
            │
            └── sentence-level perplexity observations
```

The frontend consumes this structured response through the FastAPI endpoint.

---

# 6. Evidence-First Principles

## 6.1 No LLM as Final Judge

The system never sends an essay to a chat model and asks for an authorship verdict.

A local causal language model is used as a measurement instrument for token probabilities and perplexity.

The final classification is produced by the project's own saved statistical model.

---

## 6.2 Evidence Over Verdict

A result is accompanied by:

- the document-level feature values
- feature availability and reasons
- sentence-level perplexity observations where available
- text statistics
- model metadata
- evidence-sufficiency state

The UI therefore presents measurable evidence rather than a bare percentage.

---

## 6.3 No False Precision

The classifier output field is named `ai_probability` in the API for compatibility with the saved model interface, but the frontend presents it as:

```text
MODEL SIGNAL
```

It is not presented as a calibrated probability that a human or AI actually authored the essay.

The production model metadata explicitly states that its probabilities are model scores for machine association within the EXP-005/EXP-006 distribution.

---

# 7. Perplexity Methodology

## 7.1 Definition

For token probabilities:

```text
PPL = exp(
    -(1/N) * Σ log P(x_i | x_<i)
)
```

Lower perplexity indicates that the language model considers the text more predictable.

This is a statistical measurement, not an authorship proof.

Human writing can also have low perplexity, particularly when it is formal, conventional, or heavily edited.

---

## 7.2 Local Model

The production perplexity measurement uses:

```text
Model: distilgpt2
Runtime: Hugging Face Transformers
Device: CPU
```

EXP-001 established the feasibility and reproducibility of sentence-level causal perplexity on the available hardware.

---

## 7.3 Causal Alignment

The validated scoring alignment is:

```text
input_ids[:, 1:]
labels scored by logits[:, :-1, :]
```

This avoids the off-by-one ambiguity that would otherwise make the perplexity calculation methodologically unclear.

---

## 7.4 Document Aggregation

Per-sentence perplexity is calculated first.

The document-level perplexity feature is the:

```text
median of valid sentence perplexities
```

This reduces sensitivity to an individual unusually high or low sentence.

---

## 7.5 Sentence-Level Perplexity Evidence

The extractor preserves sentence-level measurements including:

```text
sentence_id
token_count
usable_prediction_token_count
perplexity
perplexity_status
perplexity_reason_unavailable
perplexity_warnings
language_model_context_limit
```

The API exposes these through `sentence_evidence`.

The Evidence Inspector uses the measured sentence perplexities to identify strong predictability exemplars.

The wording is intentionally evidence-oriented:

> These sentences exhibit strong predictability measurements.

It does not say:

> These sentences were written by AI.

---

# 8. Context Limit Handling

`distilgpt2` supports a 1024-token context.

During production integration, an 867-word PERSUADE essay was treated as one sentence and produced 1134 language-model tokens.

The original implementation attempted to score that sentence and returned HTTP 500.

The production extractor was changed to check the model context limit before invoking perplexity.

When a sentence exceeds the supported context, perplexity becomes unavailable with:

```text
sentence_exceeds_language_model_context
```

If this makes the required four-feature vector incomplete, the detector returns:

```text
insufficient_evidence
```

The system does not silently truncate the user's sentence.

This preserves the validated perplexity definition.

---

# 9. Rhythm Feature — Sentence-Length CV

Sentence-length coefficient of variation is defined as:

```text
CV = σ / μ
```

where:

- `σ` = standard deviation of sentence lengths
- `μ` = mean sentence length

The production implementation uses the validated EXP-004 definition.

This feature is calculated at document level.

The Evidence Inspector therefore does not invent a separate sentence-level CV value.

---

# 10. Lexical Feature — MATTR

The production lexical-diversity feature is:

```text
Moving-Average Type-Token Ratio (MATTR)
```

The validated implementation uses a fixed window of:

```text
25 lexical tokens
```

MATTR is a document-level feature and requires enough lexical tokens for the windowed calculation.

When the required number of tokens is unavailable, the feature is marked unavailable and the classifier abstains if the complete four-feature vector cannot be formed.

---

# 11. Structural Feature — POS 3-Gram Entropy

The production structural feature is:

```text
POS 3-gram entropy
```

Part-of-speech tags are converted into sequences of three tags, and the empirical distribution of those trigrams is measured using entropy:

```text
H(X) = -Σ p(x) log p(x)
```

This is a document-level feature.

It is not independently interpreted as an AI score.

---

# 12. Production Feature Vector

The production feature order is fixed:

```text
1. perplexity
2. sentence_length_cv
3. mattr
4. pos_3gram_entropy
```

This ordering is part of the persisted model contract.

The production model will not accept an arbitrary feature ordering.

---

# 13. Feature Selection and Experimental Validation

Feature selection was not based solely on theoretical plausibility.

The project used controlled experiments to determine which candidate features were suitable for the final classifier.

The resulting production vector contains four features validated through the project's feature-development pipeline:

```text
Perplexity
Sentence-length CV
MATTR
POS 3-gram entropy
```

Other candidate ideas were not promoted simply because they sounded plausible.

This is consistent with the project's broader experiment-first methodology.

---

# 14. Production Classifier

The production classifier is:

```text
StandardScaler
      ↓
LogisticRegression
```

The model artifact is:

```text
backend/artifacts/authorship_detector.joblib
```

Its metadata is:

```text
backend/artifacts/authorship_detector.metadata.json
```

The artifact records:

- feature order
- model type
- random seed
- training and validation counts
- source experiment
- reference validation metrics
- known validation-row verification
- interpretation guardrail

---

# 15. Validation Result Used for Production Selection

EXP-006 produced the following saved validation metrics for the production four-feature classifier:

```text
Accuracy   0.9746835443
Precision  0.9523809524
Recall     1.0000000000
F1         0.9756097561
ROC-AUC    0.9955128205
```

These numbers are tied to the project's bounded validation distribution.

They must not be presented as universal admissions-domain accuracy.

The final evaluation must be reported separately from the development/validation result.

---

# 16. Evidence Sufficiency and Abstention

The production detector requires all four classifier inputs to be available.

The decision flow is:

```text
Feature Extraction
       │
       ▼
Are all four features available and finite?
       │
   ┌───┴────┐
   │        │
  NO       YES
   │        │
   ▼        ▼
ABSTAIN   CLASSIFY
```

The API returns:

```text
state = insufficient_evidence
```

when required evidence is unavailable.

This is preferable to fabricating a value, substituting an arbitrary default, or forcing every input into a binary classification.

---

# 17. EXP-010 — Evidence Sufficiency

EXP-010 was specifically used to investigate whether a universal numeric evidence threshold could be justified.

The experiment showed that short inputs can have unstable feature measurements and that evidence availability depends on the feature definitions.

The production decision is therefore conservative:

> classify only when the complete four-feature vector required by the trained model is available.

No unsupported universal word-count threshold is embedded into the production classifier.

---

# 18. Local Attribution Experiments

Several experiments investigated whether the system could reliably identify individual AI-written passages.

These experiments are important because the original project requirement asks for evidence about "where".

However, the experiments also established a boundary around what the system can honestly claim.

---

## 18.1 EXP-007 — Local Anomaly

A local anomaly signal was investigated using essay-relative statistics.

Result:

- useful exploratory signal in some cases
- insufficiently reliable localization for production use

Decision:

```text
Rejected for production attribution
```

---

## 18.2 EXP-008 — Window / Feature Sensitivity

Different local windows and feature behavior were investigated.

Result:

- localization remained noisy
- feature behavior was not stable enough to support a production sentence-level verdict

Decision:

```text
Rejected for production attribution
```

---

## 18.3 EXP-009 — Boundary Discontinuity

Boundary discontinuity was tested on controlled hybrids.

Result:

- some local signal existed
- separation was not strong enough to justify authoritative boundary detection

Decision:

```text
Rejected for production attribution
```

---

## 18.4 EXP-011 — Leave-One-Sentence-Out Attribution

A final feasibility test reused the production four-feature classifier.

For each sentence, the experiment removed that sentence, recomputed the document features, and measured the change in classifier signal.

Results across 20 controlled hybrids:

```text
Top-10% AI-sentence capture: 22.5%
Top-25% AI-sentence capture: 42.5%

Median AI-sentence contribution:    -0.0001953670
Median human-sentence contribution:  -0.0011773087
Median difference:                    0.0009819416
```

The separation was too weak to support a reliable production sentence-level attribution claim.

Decision:

```text
Rejected for production attribution
```

---

# 19. Production Answer to "Where?"

The production system therefore uses a narrower, evidence-first interpretation of "where".

It does not claim:

```text
"This sentence is AI."
```

Instead, where a validated sentence-level measurement exists, the UI shows:

```text
Where:
the sentence containing a strong local measurement

Why:
the measured property itself, such as low perplexity
```

The current production Evidence Inspector is therefore a **measurement inspector**, not a sentence-level authorship classifier.

---

# 20. Evidence Inspector

The Evidence Inspector is the frontend manifestation of the evidence-first methodology.

Current behavior:

1. The document receives a document-level classification.
2. The four document-level feature cards show the measured feature values.
3. Sentence-level perplexity observations are exposed separately.
4. The strongest valid perplexity exemplars can be highlighted.
5. The UI explains that the highlighted sentence is a statistical exemplar, not a proof of authorship.

This design satisfies the need to make evidence inspectable while remaining within what the experiments support.

---

# 21. Why Not an LLM Explainer?

An LLM was considered as a possible natural-language explanation layer.

It was intentionally not adopted.

Reasons:

- it would introduce a second model whose explanations would need validation
- it could invent reasons not present in the detector
- it could blur the boundary between instrumentation and judgment
- it could make the system look like an LLM wrapper
- the evidence is already available as structured measurements

The final explanation layer therefore uses deterministic data already produced by the detector.

---

# 22. Hybrid Writing

Hybrid writing remains a core research condition even though local attribution is not promoted to production.

The dataset and experiments distinguish:

### AI Polished

A human essay with selected passages edited by a local model.

### AI Spliced

A human essay with selected passages replaced by independently generated text.

These variants are useful for testing whether the document-level detector responds to partial machine assistance.

However, the system does not claim that the exact inserted passage can always be recovered.

That limitation is now explicit.

---

# 23. Dataset Relationship to Methodology

The detector is distribution-dependent.

The primary controlled development work used student-writing material as a proxy rather than assuming that it was equivalent to a representative admissions corpus.

The main production result therefore must be described with its source distribution and evaluation protocol.

The dataset documentation records:

- source provenance
- essay family relationships
- human/AI/hybrid roles
- generation model where applicable
- split information
- known domain limitations

---

# 24. Generalization

The methodology recognizes several important distribution shifts:

- topic shift
- generation-model shift
- hybrid writing
- essay-length differences
- ESL/non-native-English writing
- admissions-domain shift

The current production result does not imply universal generalization.

Final reporting should separate:

```text
Development / validation performance
```

from:

```text
Final evaluation
```

and from:

```text
Bias / OOD audits
```

---

# 25. ESL / Non-Native-English Bias

The project explicitly treats ESL/non-native-English writing as a risk condition.

Perplexity and other linguistic statistics can respond to writing regularity, lexical diversity, and grammatical structure.

Those properties may vary for reasons unrelated to AI use.

The required audit should therefore compare detector behavior on:

```text
general human writing
vs.
ELL/ESL control writing
```

The final submission should report the observed result rather than assuming either presence or absence of bias.

---

# 26. Failure Analysis

The final evaluation must include at least three confident failures, as required by the Callus brief.

For each failure, the project should record:

```text
Input type
Prediction
Model signal
Feature values
Evidence availability
Likely failure mechanism
Known limitation
```

The report must distinguish:

```text
Observed behavior
```

from:

```text
Hypothesized reason
```

This prevents post-hoc explanations from being presented as established facts.

---

# 27. Evaluation Metrics

The evaluation methodology does not rely on one number.

At minimum, report where applicable:

- accuracy
- precision
- recall
- F1
- ROC-AUC
- false-positive rate
- false-negative rate
- coverage / abstention behavior
- hybrid performance
- ESL false-positive behavior
- confident failure cases

The current EXP-006 validation values are reference development metrics, not final universal claims.

---

# 28. Coverage and Abstention

A detector that refuses to classify weak evidence is not necessarily weaker.

The important question is:

> How often does the system make a strong classification, and how reliable are those classifications within the evaluated distribution?

The production system therefore retains an explicit:

```text
insufficient_evidence
```

state rather than forcing a binary label onto incomplete feature vectors.

---

# 29. Interpretation Guardrails

The following statements are valid:

> The document exhibits characteristics associated with machine-generated writing within the evaluated distribution.

> This sentence has a comparatively low perplexity measurement under the local language model.

> The model returned a strong machine-association signal.

The following statements are not supported:

> This sentence was written by AI.

> This is 95% certainly AI-generated.

> The detector proves the author used ChatGPT.

> The model can identify every AI-written passage.

The UI and documentation must preserve this distinction.

---

# 30. Methodology Constraints

The production system must not:

- use a chat model as the final judge
- call an LLM to invent explanations
- present raw classifier probabilities as calibrated authorship certainty
- fabricate missing features
- silently truncate text to make unsupported perplexity measurements possible
- use the failed local-attribution methods as authoritative sentence labels
- claim universal detection
- hide dataset or domain limitations
- tune on the final evaluation set

---

# 31. Experiment-to-Production Traceability

The main production decisions trace back to the experiments as follows:

```text
EXP-001
Local perplexity feasibility
        ↓
Perplexity measurement accepted

EXP-002
Perplexity stability
        ↓
Short-text instability documented

EXP-003
Local generation feasibility
        ↓
Generation protocol established

EXP-004
Feature-definition validation
        ↓
Production feature mathematics fixed

EXP-005
Feature distributions
        ↓
Feature comparability / dataset checks

EXP-006
Baseline classification
        ↓
Four-feature Logistic Regression selected

EXP-007
Local anomaly
        ↓
Rejected for production attribution

EXP-008
Window / feature sensitivity
        ↓
Rejected for production attribution

EXP-009
Boundary discontinuity
        ↓
Rejected for production attribution

EXP-010
Evidence sufficiency
        ↓
Abstention when required features are unavailable

EXP-011
Leave-one-out attribution
        ↓
Rejected for production sentence attribution
        ↓
Evidence Inspector uses direct measurements instead
```

This traceability is a central part of the project's methodological story.

---

# 32. Current Methodology Status

**Status:** Production methodology established.

### Accepted

- evidence-first framing
- local causal model as a measurement instrument
- document-level four-feature classifier
- StandardScaler + Logistic Regression
- sentence-level perplexity as inspectable evidence
- abstention when required features are unavailable
- model-signal terminology rather than authorship certainty
- deterministic Evidence Inspector presentation

### Rejected

- LLM-as-judge
- local anomaly as production authorship evidence
- boundary discontinuity as production authorship evidence
- leave-one-out sentence attribution as production authorship evidence

### Deferred / Final Evaluation

- broader OOD evaluation
- ESL bias audit
- three confident failure cases
- any future expansion of sentence-level evidence beyond currently validated measurements

The methodology is now considered stable for the submission prototype. Remaining work is primarily final evaluation, failure/bias analysis, documentation consistency, and demo preparation.
