# Architecture — Evidence-First Authorship Analysis

## 1. Purpose

This document defines the current technical architecture of Callus Project 2, an AI admissions-essay analysis application.

The architecture is built around five principles:

1. Produce measurable evidence rather than an unexplained AI verdict.
2. Keep the actual classification decision inside the project's own statistical model.
3. Treat uncertainty and insufficient evidence as first-class outcomes.
4. Keep analytical logic in the backend and presentation logic in the frontend.
5. Keep the core pipeline locally runnable and independent of paid AI services.

The architecture has been updated from the original experimental proposal to reflect the validated production system.

---

# 2. Current Architectural Position

The production system performs **document-level classification**.

It does not claim that an individual sentence was written by AI.

Sentence-level measurements are retained where the validated feature pipeline already provides them. The current Evidence Inspector uses these measurements to show **where relevant statistical evidence appears**, not to assign sentence-level authorship.

This distinction follows the results of EXP-007 through EXP-011, which did not justify reliable sentence-level attribution.

The current architecture is therefore:

```text
Essay
  ↓
Sentence Segmentation
  ↓
Validated Feature Extraction
  ↓
Four-Feature Vector
  ↓
StandardScaler + Logistic Regression
  ↓
Document Classification / Abstention
  ↓
Structured Evidence Response
  ↓
Evidence Inspector UI
```

---

# 3. Architectural Principles

## 3.1 No LLM-as-Judge

The system is not structured as:

```text
Essay → Chat Model → Verdict
```

A local causal language model is used as an **instrument** for perplexity measurement.

The final machine-associated / human-associated decision is produced by the project's persisted Logistic Regression model.

The frontend does not ask an LLM to explain or override the detector.

---

## 3.2 Evidence Over Verdict

A classification is accompanied by observable measurements:

- four feature values
- feature availability and reasons
- text statistics
- sentence-level perplexity evidence where available
- model metadata

The UI uses this information to explain what was measured rather than presenting an unexplained percentage.

---

## 3.3 Document Classification vs. Sentence Evidence

The production classifier operates on a four-feature **document-level vector**:

```text
perplexity
sentence_length_cv
mattr
pos_3gram_entropy
```

Sentence-level perplexity measurements are also retained.

These sentence measurements support the Evidence Inspector, but they do not constitute an independently trained sentence classifier.

The product therefore distinguishes:

```text
Document-level classification
        +
Sentence-level evidence observations
```

from:

```text
Sentence-level AI authorship prediction
```

The latter is not part of the production system.

---

## 3.4 Evidence Sufficiency and Abstention

The detector does not fabricate missing feature values.

If one or more required features are unavailable, the four-feature classifier is not invoked and the API returns:

```text
insufficient_evidence
```

Examples include:

- too few sentences for sentence-length CV
- too few lexical tokens for MATTR
- unavailable perplexity
- a sentence exceeding the supported language-model context

This behavior follows EXP-010 and the production robustness work.

---

## 3.5 Analysis and Presentation Are Separate

The backend produces structured analytical results.

The frontend is responsible for:

- rendering the essay
- rendering the result state
- presenting feature evidence
- showing sentence-level evidence observations
- applying visual highlighting
- communicating limitations

The frontend must not independently reproduce classifier mathematics.

---

# 4. System Layers

The current application has four practical layers:

```text
┌──────────────────────────────────────────────────────┐
│                    FRONTEND                          │
│             Vite + React + TypeScript                │
│                                                      │
│ Essay Input → Results → Feature Grid → Evidence      │
│ Inspector                                           │
└──────────────────────────┬───────────────────────────┘
                           │ HTTP
                           ▼
┌──────────────────────────────────────────────────────┐
│                       API                            │
│                     FastAPI                          │
│                                                      │
│ POST /api/analyze                                    │
│ Request Validation → Detector → Response Schema      │
└──────────────────────────┬───────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│                 DETECTION ENGINE                     │
│                                                      │
│ Sentence Segmentation                                │
│        ↓                                             │
│ Feature Extraction                                   │
│        ↓                                             │
│ Four-Feature Vector → Model Artifact                 │
│        │                                             │
│        └──────────→ Sentence Evidence                 │
│                                                      │
│        ↓                                             │
│ Classification / Abstention                          │
└──────────────────────────┬───────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│                 LOCAL ARTIFACTS                      │
│                                                      │
│ distilgpt2 / tokenizer                                │
│ StandardScaler + LogisticRegression artifact         │
│ experiment and dataset artifacts                     │
└──────────────────────────────────────────────────────┘
```

---

# 5. Frontend Layer

## 5.1 Technology

The current frontend uses:

- Vite
- React
- TypeScript
- CSS
- Vitest for frontend tests

It is intentionally lightweight and does not depend on a dashboard framework.

The visual direction is an editorial/brutalist research interface rather than a generic AI dashboard.

---

## 5.2 Primary Responsibilities

The frontend:

- accepts essay text
- submits the essay to `POST /api/analyze`
- displays document-level assessment
- displays model signal as a model signal, not calibrated authorship certainty
- displays available feature measurements
- displays insufficient-evidence states
- renders sentence-level evidence observations
- provides the Evidence Inspector
- highlights selected evidence sentences
- communicates methodological limitations

The frontend does not calculate the Logistic Regression result.

---

## 5.3 Current UI Flow

```text
Essay Input
    ↓
Analyze
    ↓
Analysis Result
    ├── Document assessment
    ├── Model signal
    ├── Evidence count
    ├── Text statistics
    ├── Evidence Inspector
    ├── Feature Grid
    └── Methodology explanation
```

The essay remains the primary document view.

---

# 6. API Layer

## 6.1 Technology

Python + FastAPI.

The API is the boundary between the frontend and the detection engine.

---

## 6.2 Current Route

```text
POST /api/analyze
```

Request:

```json
{
  "text": "essay text..."
}
```

The route remains thin.

Conceptually:

```text
HTTP Request
    ↓
Pydantic validation
    ↓
AuthorshipDetector.analyze()
    ↓
Pydantic response validation
    ↓
HTTP Response
```

Detection logic does not live directly inside the route handler.

---

## 6.3 Current Response Shape

The response includes:

```text
state
label
ai_probability
features[]
sentence_evidence[]
text_statistics
model_metadata
```

The frontend consumes the response through a typed TypeScript API client.

---

# 7. Detection Engine

## 7.1 Responsibility

`AuthorshipDetector` is the production orchestration layer.

Current responsibilities:

1. Validate empty/whitespace-only input.
2. Run the production feature extractor.
3. Build the ordered four-feature vector.
4. Abstain if required features are unavailable.
5. Score the vector with the saved model artifact.
6. Convert sentence-level perplexity measurements into API-safe sentence evidence.
7. Return structured metadata for the API/UI.

---

## 7.2 Current Production Structure

```text
backend/app/
├── api/
│   └── analyze.py
├── detector/
│   ├── engine.py
│   └── model_artifact.py
├── features/
│   ├── extraction.py
│   ├── experiment_reuse.py
│   └── resources.py
├── schemas/
│   └── analysis.py
├── training/
│   └── train_production_model.py
└── main.py
```

Production artifacts:

```text
backend/artifacts/
├── authorship_detector.joblib
└── authorship_detector.metadata.json
```

---

# 8. Segmentation

The production extractor uses spaCy sentence segmentation.

The segmentation layer preserves:

- sentence order
- sentence text
- sentence IDs
- sentence-level boundaries needed for evidence presentation

The production classifier does not use a separate passage classifier.

Sentence segmentation is required both for feature computation and for the Evidence Inspector.

---

# 9. Feature Extraction Layer

## 9.1 Production Feature Order

The production feature vector is fixed to:

```text
1. perplexity
2. sentence_length_cv
3. mattr
4. pos_3gram_entropy
```

The ordering is part of the saved model contract.

---

## 9.2 Perplexity

Perplexity is measured using a local causal language model.

The production implementation uses:

```text
Model: distilgpt2
Runtime: Hugging Face Transformers
Device: CPU
```

The perplexity calculation follows the validated causal-shift alignment established in EXP-001:

```text
input_ids[:, 1:]
labels scored by logits[:, :-1, :]
```

At the document level, valid sentence perplexities are aggregated using the median.

---

## 9.3 Sentence-Level Perplexity Evidence

The production extractor retains per-sentence measurements such as:

```text
sentence_id
token_count
usable_prediction_token_count
perplexity
perplexity_status
reason when unavailable
warnings
language_model_context_limit
```

These measurements are exposed through:

```text
sentence_evidence[]
```

in the API response.

They are used by the Evidence Inspector as **measurement-level evidence**.

They are not used to produce a separate sentence-level classifier.

---

## 9.4 Sentence-Length CV

Sentence-length coefficient of variation is calculated across the document:

```text
CV = standard deviation / mean
```

The current implementation uses the validated EXP-004 definition.

It is a document-level feature.

The production Evidence Inspector therefore does not pretend that an individual sentence has its own sentence-length CV score.

---

## 9.5 MATTR

MATTR is calculated using the validated EXP-004 moving-window definition.

The current window size is:

```text
25 lexical tokens
```

MATTR is a document-level lexical-diversity measurement.

---

## 9.6 POS 3-Gram Entropy

POS 3-gram entropy measures the entropy of three-tag grammatical sequences produced by the validated POS processing pipeline.

It is a document-level structural feature.

---

# 10. Production Model

## 10.1 Model

The production classifier is:

```text
StandardScaler
      ↓
LogisticRegression
```

The saved artifact is:

```text
backend/artifacts/authorship_detector.joblib
```

Metadata is stored in:

```text
backend/artifacts/authorship_detector.metadata.json
```

---

## 10.2 Model Source

The production classifier is derived from EXP-006.

Its four input features are defined by the validated EXP-004 feature implementations.

The saved artifact records:

- feature order
- model type
- random seed
- training row counts
- validation row counts
- source experiment
- reference validation metrics
- known validation-row verification

---

## 10.3 Model Signal

The API may expose:

```text
ai_probability
```

but the frontend labels it:

```text
MODEL SIGNAL
```

The value is not presented as calibrated authorship certainty.

The model metadata explicitly guards this interpretation:

```text
Classifier probabilities are model scores for machine association
within the EXP-005/EXP-006 distribution, not calibrated authorship certainty.
```

---

# 11. Evidence Sufficiency and Abstention

The production decision flow is:

```text
Raw Essay
   ↓
Feature Extraction
   ↓
Are all four required features available?
   │
   ├── NO → insufficient_evidence
   │
   └── YES
          ↓
     Logistic Regression
          ↓
       classified
```

There is no fabricated fallback value for missing features.

---

## 11.1 Short Text

Very short input may lack sufficient observations for:

- sentence-length CV
- MATTR
- POS 3-gram entropy

The detector abstains when required features are unavailable.

---

## 11.2 Oversized Language-Model Input

`distilgpt2` supports a 1024-token context.

During integration testing, an 867-word PERSUADE essay was treated as a single sentence containing 1134 language-model tokens.

The original implementation attempted inference and produced HTTP 500.

The production extractor now detects the context limit before invoking perplexity.

The result is:

```text
perplexity unavailable
reason = sentence_exceeds_language_model_context
```

If this prevents the required four-feature vector from being complete, the detector returns:

```text
insufficient_evidence
```

No silent truncation is performed.

---

# 12. Evidence Inspector

## 12.1 Purpose

The Evidence Inspector exists to satisfy the product requirement to show **where and why** without making unsupported sentence-level authorship claims.

The system does not display:

```text
Sentence 12 = AI
```

Instead it displays:

```text
Evidence
↓
Measured local pattern
↓
Where it appears
↓
Why that measurement matters
```

---

## 12.2 Current Evidence Source

The current production Evidence Inspector uses sentence-level perplexity measurements.

The strongest available sentence-level exemplars can be surfaced by ranking valid sentence perplexities.

The UI describes these as:

```text
Predictability Evidence
```

or equivalent evidence-oriented language.

A highlighted sentence means:

> This sentence exhibits a strong measured predictability pattern within this document.

It does not mean:

> This sentence was written by AI.

---

## 12.3 Why Only Perplexity Is Localized

The other three production features are document-level measurements:

- sentence-length CV
- MATTR
- POS 3-gram entropy

They do not currently have independently validated per-sentence values in the production classifier.

Therefore the UI must not invent sentence-level values for those features.

The Feature Grid can explain all four document-level measurements, while sentence highlighting currently focuses on the validated sentence-level perplexity evidence.

---

# 13. Rejected Local Attribution

Experiments EXP-007, EXP-008, and EXP-009 tested local anomaly and boundary-based approaches.

EXP-011 subsequently tested leave-one-sentence-out contribution using the production classifier on 20 synthetic hybrids.

Results:

```text
Top-10% capture: 22.5%
Top-25% capture: 42.5%

Median AI-sentence contribution:
-0.0001953670

Median human-sentence contribution:
-0.0011773087

AI − human median difference:
0.0009819416
```

These results were not strong enough to support production sentence-level authorship attribution.

Therefore:

```text
No sentence-level AI classifier
No leave-one-out AI heatmap
No local anomaly score in production
No definitive sentence attribution
```

The Evidence Inspector is deliberately more conservative.

---

# 14. Evidence Response Model

The API response preserves both document-level and sentence-level information.

Conceptually:

```text
AnalyzeResponse
│
├── state
├── label
├── ai_probability
├── features[]
│
├── sentence_evidence[]
│   ├── sentence_id
│   ├── text
│   ├── perplexity
│   ├── available
│   └── reason
│
├── text_statistics
└── model_metadata
```

This structure keeps analysis in the backend while allowing the frontend to render evidence without reproducing statistical logic.

---

# 15. API / Frontend Boundary

The frontend does not know:

- how distilgpt2 calculates perplexity
- how the Logistic Regression was trained
- how StandardScaler was fitted
- how MATTR is calculated
- how POS entropy is calculated
- how evidence sufficiency is determined

The API exposes the resulting measurements and states.

Likewise, the detector does not know:

- how the Evidence Inspector is visually styled
- how sentence highlighting is rendered
- which React component displays the evidence
- which CSS treatment is used

This separation keeps the analytical contract independent of the presentation layer.

---

# 16. Data and Training Boundary

Dataset construction and production inference remain separate.

Training/development:

```text
Raw / processed dataset
        ↓
Family-aware split
        ↓
Validated feature extraction
        ↓
StandardScaler fitting
        ↓
Logistic Regression fitting
        ↓
Validation
        ↓
Saved model artifact
```

Production inference:

```text
Essay
  ↓
Sentence segmentation
  ↓
Feature extraction
  ↓
Saved preprocessing + classifier
  ↓
Classification / abstention
  ↓
Evidence response
```

The application does not retrain the classifier on user submissions.

---

# 17. Dataset Boundary

The main controlled development corpus is treated as a student-writing proxy rather than a perfect admissions corpus.

The dataset strategy is documented separately in:

```text
docs/DATASET.md
```

The important architectural property is that:

- source provenance is tracked
- essay-family relationships are preserved
- related variants are split by family
- training and inference remain separate

The target-domain limitation is explicit rather than hidden.

---

# 18. Experimentation Boundary

Experimental code remains under:

```text
experiments/
```

Experiments answer questions such as:

- whether a measurement is stable
- whether a feature discriminates
- whether a local-analysis idea is reliable
- whether an abstention rule is justified
- whether a candidate method should enter production

Once a decision is made, the production implementation is updated and the decision is documented.

The experiments remain unchanged as historical evidence.

---

# 19. Production Tests

The backend has a dedicated test suite covering:

- empty input abstention
- whitespace-only input
- very short input
- complete-feature classification
- feature ordering
- EXP-004 feature reuse
- model artifact loading
- deterministic inference
- known validation-row verification
- API request validation and response serialization
- sentence evidence serialization

Current backend verification:

```text
10 passed
```

The test suite also verifies that `sentence_evidence` is present and ordered correctly in the API response.

---

# 20. Error Handling

The system distinguishes between:

### Insufficient evidence

The system successfully analyzed the request but did not have enough reliable measurements for a full classification.

Example:

```text
state = insufficient_evidence
```

### API / infrastructure failure

The system could not complete analysis because of an application or infrastructure error.

These should not be represented as the same user-facing state.

---

# 21. Performance Considerations

The project prioritizes correctness and explainability over maximum throughput.

Current runtime characteristics:

- local CPU inference
- small causal language model
- model loading through a reusable resource layer
- sentence-level perplexity measurements
- no LLM explanation call
- no external detection API

Experimental approaches that require repeated full-document inference, such as EXP-011, are not part of production inference.

The production pipeline therefore avoids the cost of leave-one-out attribution.

---

# 22. Security and Privacy

Essays may contain sensitive personal information.

The local-first design reduces unnecessary transmission of essay text to external services.

The default architecture does not require a paid external AI API for detection or explanation.

Unless persistence is explicitly required, essay text should be treated as ephemeral runtime data.

Logging should avoid storing complete user essays unnecessarily.

---

# 23. Reproducibility

The architecture supports reproduction of:

- validated feature extraction
- classifier training
- model artifact generation
- experiment results
- evaluation results
- API behavior
- sentence evidence generation

Relevant model and experiment metadata are retained with artifacts.

Random seeds and relevant software versions are recorded where applicable.

---

# 24. Current Locked Decisions

The following are now production decisions:

- `distilgpt2` is the local language model for perplexity extraction.
- The production feature vector contains four features:
  - perplexity
  - sentence-length CV
  - MATTR
  - POS 3-gram entropy
- StandardScaler + Logistic Regression is the production classifier.
- The classifier is document-level.
- Missing required features cause abstention.
- Model probability is presented as a model signal, not calibrated authorship certainty.
- Local anomaly / boundary-discontinuity methods are not in production.
- Leave-one-sentence-out attribution is not in production.
- Sentence-level perplexity measurements are surfaced as evidence observations.
- The Evidence Inspector does not make sentence-level authorship claims.
- The API remains thin.
- The frontend remains separate from detection logic.
- The core pipeline remains locally runnable.

---

# 25. Known Limitations

The architecture currently has several explicit limitations:

1. The production classifier is trained and validated within a bounded dataset distribution and should not be presented as universally accurate.
2. The primary development corpus is not a perfect admissions-essay corpus.
3. Sentence-level authorship attribution is not supported.
4. Only perplexity currently provides validated sentence-level evidence in the production pipeline.
5. Local anomaly methods tested in EXP-007 through EXP-011 were not reliable enough for production.
6. The classifier signal is not calibrated authorship certainty.
7. ELL/ESL bias requires explicit final evaluation.
8. Three confident failure cases still need to be documented for the final submission.

These limitations are part of the system design, not hidden failure states.

---

# 26. Repository Architecture

The implemented production repository currently follows this practical structure:

```text
project-2/
│
├── docs/
│   ├── PROJECT-2-PLAN.md
│   ├── ARCHITECTURE.md
│   ├── DETECTION-METHODOLOGY.md
│   ├── DECISIONS.md
│   ├── DATASET.md
│   ├── EVALUATION.md
│   ├── EXPERIMENT-LOG.md
│   ├── GENERATION-PROTOCOL.md
│   └── PRODUCTION-MILESTONE.md
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── detector/
│   │   ├── features/
│   │   ├── schemas/
│   │   ├── training/
│   │   └── main.py
│   ├── artifacts/
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── lib/
│   │   └── test/
│   ├── package.json
│   └── vite.config.ts
│
├── experiments/
│   ├── EXP-001-...
│   ├── ...
│   └── EXP-011-passage-attribution/
│
├── pytest.ini
└── ...
```

The exact repository may contain additional experiment artifacts and dataset files.

Production code and experimental code remain separated.

---

# 27. Architectural Evolution

The project deliberately evolved from its original architecture.

### Original proposal

The initial architecture included:

```text
Global machine association
+
Local stylistic anomaly
+
Passage-level attribution
```

### Experimental findings

EXP-007 through EXP-009 showed that local anomaly / boundary signals were too noisy for reliable production localization.

EXP-010 established evidence-sufficiency behavior.

EXP-011 tested leave-one-sentence-out attribution and found insufficient capture/separation for production sentence-level attribution.

### Current architecture

The production system therefore uses:

```text
Document-level machine association
        +
Evidence sufficiency
        +
Validated sentence-level perplexity observations
        +
Evidence Inspector presentation
```

The architecture changed because the evidence changed.

That is an intentional design property of the project.

---

# 28. Current Architecture Status

**Phase:** Production prototype / final integration.

**Status:** Core detector, API, frontend, Evidence Inspector, and backend tests are implemented.

Current verified capabilities:

- working essay input
- document-level classification
- four-feature evidence
- insufficient-evidence abstention
- long-context robustness
- sentence-level perplexity evidence
- Evidence Inspector
- structured API response
- human-associated demo case
- AI-associated demo case
- insufficient-evidence demo case

Remaining submission work:

- final evaluation set
- three confident failure cases and explanations
- ESL/non-native-English audit
- final documentation consistency pass
- final demo/presentation preparation
- final repository verification

The architecture is considered stable for submission unless final evaluation reveals a blocking issue.
