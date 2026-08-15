# Callus Project 2 — Evidence-First AI Authorship Detector

> A real admissions-essay analysis application that combines local language-model measurements with a classical machine-learning classifier, then shows the evidence behind the document-level result.

## What this project does

Paste an essay into the web application and receive a document-level assessment of whether its writing characteristics are more associated with the human or machine-generated examples in the development distribution.

The system is intentionally **not** an LLM wrapper and does **not** ask a chat model to decide whether an essay is AI-generated.

Instead:

```text
Essay
  ↓
Sentence segmentation
  ↓
Validated linguistic feature extraction
  ↓
Four-feature vector
  ↓
StandardScaler + Logistic Regression
  ↓
Document-level assessment
  ↓
Evidence Inspector
```

The application also exposes directly measured sentence-level perplexity observations so the user can inspect **where measurable evidence appears and why it matters**.

The Evidence Inspector does **not** claim that a highlighted sentence was written by AI.

---

# Why we built it this way

The Callus brief specifically asks for more than:

```text
73% AI
```

A useful detector needs to show:

1. **What the system measured**
2. **Where relevant evidence appears**
3. **Why that evidence matters**
4. **When the evidence is insufficient**
5. **Where the detector is wrong**

Our design therefore separates:

```text
Document-level classification
```

from:

```text
Sentence-level evidence observations
```

Several experiments tested local attribution approaches. EXP-007, EXP-008, EXP-009, and EXP-011 did not support reliable sentence-level authorship claims, so those methods were rejected for production.

That research result directly shaped the final UI.

---

# Final evaluation

The production model was evaluated on a **locked held-out set** that was not used for model fitting or validation.

### Held-out set

```text
Total source pairs:      2,421
Development pairs:        200
Untouched pairs:         2,221
Final held-out pairs:      200
Final essays:              400
```

Composition:

```text
200 human essays
200 AI-generated essays
```

### Final results

| Metric | Result |
|---|---:|
| Accuracy | **98.49%** |
| Precision | **98.99%** |
| Recall | **98.00%** |
| F1 | **98.49%** |
| ROC-AUC | **99.83%** |
| False-positive rate | **1.01%** |
| False-negative rate | **2.00%** |
| Coverage | **99.50%** |

Confusion matrix:

```text
                 Predicted
                Human     AI

Actual Human      196      2
Actual AI           4    196
```

These are results on the documented held-out evaluation set. They are **not** presented as universal AI-detection accuracy.

Full report:

→ [`docs/evaluation/FINAL-EVALUATION.md`](docs/evaluation/FINAL-EVALUATION.md)

Raw metrics:

→ [`data/final_evaluation/metrics.json`](data/final_evaluation/metrics.json)

Predictions:

→ [`data/final_evaluation/predictions.csv`](data/final_evaluation/predictions.csv)

Frozen evaluation manifest:

→ [`data/final_evaluation_manifest.json`](data/final_evaluation_manifest.json)

---

# Three confident failures

The Callus brief explicitly asks for three essays that the detector gets confidently wrong.

We selected three representative failures from the locked held-out set:

| Pair | Actual | Predicted | Model signal |
|---|---|---|---:|
| `B6A5721D64C1` | AI | Human | 0.0069 |
| `F3550CF50ABC` | AI | Human | 0.1047 |
| `B046D31B68F0` | Human | AI | 0.7536 |

These demonstrate that:

- AI-generated prose can overlap the human-associated feature distribution.
- Human prose can overlap the machine-associated feature distribution.
- High model confidence does not guarantee correct authorship classification.

Full analysis:

→ [`docs/evaluation/CONFIDENT-FAILURES.md`](docs/evaluation/CONFIDENT-FAILURES.md)

---

# ESL / non-native-English audit

Because the brief explicitly calls out the risk of false positives on writers who learned English as a second language, we ran a separate audit on PERSUADE.

### Audit set

```text
701 ELL essays
701 non-ELL essays
1,402 essays total
```

Both groups were from the same:

```text
Text dependent
```

task category.

### Observed results

| Metric | ELL | Non-ELL |
|---|---:|---:|
| Coverage | 100.00% | 99.86% |
| Flagged as AI | 15 | 17 |
| False-positive rate | **2.14%** | **2.43%** |
| Median model signal | 0.00151 | 0.00621 |

Observed difference:

```text
ELL FPR - non-ELL FPR = -0.29 percentage points
```

Therefore:

> **No elevated ELL false-positive rate was observed in this audit sample.**

This is an observed result for this corpus and evaluation protocol, not a universal fairness guarantee.

Full audit:

→ [`docs/evaluation/ESL-AUDIT.md`](docs/evaluation/ESL-AUDIT.md)

Raw metrics:

→ [`data/esl_audit/metrics.json`](data/esl_audit/metrics.json)

Predictions:

→ [`data/esl_audit/predictions.csv`](data/esl_audit/predictions.csv)

Audit manifest:

→ [`data/esl_audit_manifest.json`](data/esl_audit_manifest.json)

---

# Core methodology

## Production features

The detector uses four validated features:

### 1. Perplexity

A local causal language model measures token-level predictability.

```text
Model: distilgpt2
Runtime: Hugging Face Transformers
Device: CPU
```

Validated causal scoring alignment:

```text
input_ids[:, 1:]
labels scored by logits[:, :-1, :]
```

Per-sentence perplexities are aggregated to document-level perplexity using the median of valid sentence values.

### 2. Sentence-length coefficient of variation

```text
CV = standard deviation / mean
```

This is a document-level rhythm feature.

### 3. MATTR

Moving-Average Type-Token Ratio using the validated:

```text
window size = 25 lexical tokens
```

This is a document-level lexical-diversity feature.

### 4. POS 3-gram entropy

Entropy over three-tag part-of-speech sequences.

This is a document-level structural feature.

---

# Production model

The final classifier is:

```text
StandardScaler
      ↓
LogisticRegression
```

Saved artifact:

```text
backend/artifacts/authorship_detector.joblib
```

Metadata:

```text
backend/artifacts/authorship_detector.metadata.json
```

Source experiment:

```text
EXP-006
```

The feature order is fixed:

```text
perplexity
sentence_length_cv
mattr
pos_3gram_entropy
```

The model output is a **model score for machine association within the evaluated distribution**, not calibrated authorship certainty.

---

# Evidence Inspector

The production application intentionally does not show:

```text
Sentence 14 = 87% AI
```

Instead, it shows:

```text
Document assessment
        ↓
Measured evidence
        ↓
Evidence Inspector
        ↓
Highlighted supporting sentences
```

The current local evidence source is sentence-level perplexity.

When a sentence is highlighted, the UI means:

> This sentence contains a strong measured predictability pattern.

It does **not** mean:

> This sentence was written by AI.

This distinction follows the results of the local-attribution experiments.

---

# Experimental path

The repository contains the complete experiment trail.

```text
EXP-001  Local perplexity feasibility
EXP-002  Perplexity stability by text length
EXP-003  Local generation feasibility
EXP-004  Feature extraction laboratory
EXP-005  Feature distribution sanity check
EXP-006  Baseline classification
EXP-007  Hybrid local-anomaly feasibility
EXP-008  Local window & feature sensitivity
EXP-009  Boundary discontinuity feasibility
EXP-010  Evidence sufficiency & empirical abstention
EXP-011  Passage attribution feasibility
```

Important methodological conclusion:

```text
EXP-007/008/009
→ local attribution not reliable enough

EXP-011
→ leave-one-sentence-out attribution rejected

Final product
→ document-level classifier + direct evidence observations
```

Full experiment history:

→ [`docs/EXPERIMENT-LOG.md`](docs/EXPERIMENT-LOG.md)

---

# Abstention and robustness

The detector does not force a classification when required evidence cannot be computed reliably.

The API can return:

```text
insufficient_evidence
```

Examples include:

- too few sentences for sentence-length CV
- too few lexical tokens for MATTR
- unavailable perplexity
- a sentence exceeding the supported `distilgpt2` context length

The production language-model context guardrail handles inputs exceeding the model's 1024-token context rather than silently truncating them.

---

# Application architecture

```text
┌──────────────────────────────────────────────────┐
│                 React + TypeScript               │
│                                                  │
│ Essay Input → Results → Evidence Inspector       │
└───────────────────────┬──────────────────────────┘
                        │ HTTP
                        ▼
┌──────────────────────────────────────────────────┐
│                     FastAPI                      │
│                                                  │
│ POST /api/analyze → AuthorshipDetector           │
└───────────────────────┬──────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────┐
│                Detection Engine                  │
│                                                  │
│ spaCy → Feature Extraction → Model Artifact      │
│                         ↓                        │
│                  Sentence Evidence               │
└───────────────────────┬──────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────┐
│              Local Model / Artifacts             │
│                                                  │
│ distilgpt2 + saved sklearn pipeline              │
└──────────────────────────────────────────────────┘
```

Detailed architecture:

→ [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

Methodology:

→ [`docs/DETECTION-METHODOLOGY.md`](docs/DETECTION-METHODOLOGY.md)

Engineering decisions:

→ [`docs/DECISIONS.md`](docs/DECISIONS.md)

Project plan:

→ [`docs/PROJECT-2-PLAN.md`](docs/PROJECT-2-PLAN.md)

Evaluation methodology:

→ [`docs/EVALUATION.md`](docs/EVALUATION.md)

Dataset documentation:

→ [`docs/DATASET.md`](docs/DATASET.md)

Generation protocol:

→ [`docs/GENERATION-PROTOCOL.md`](docs/GENERATION-PROTOCOL.md)

Production milestone:

→ [`docs/PRODUCTION-MILESTONE.md`](docs/PRODUCTION-MILESTONE.md)

---

# Repository structure

```text
project-2/
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
│   └── EXP-001 ... EXP-011
│
├── data/
│   ├── final_evaluation/
│   ├── esl_audit/
│   └── raw/
│
├── docs/
│   ├── evaluation/
│   ├── ARCHITECTURE.md
│   ├── DATASET.md
│   ├── DECISIONS.md
│   ├── DETECTION-METHODOLOGY.md
│   ├── EVALUATION.md
│   ├── EXPERIMENT-LOG.md
│   ├── GENERATION-PROTOCOL.md
│   ├── PROJECT-2-PLAN.md
│   └── PRODUCTION-MILESTONE.md
│
├── scripts/
│   ├── prepare_esl_audit.py
│   ├── prepare_final_evaluation.py
│   ├── run_esl_audit.py
│   └── run_final_evaluation.py
│
└── pytest.ini
```

---

# Quick start

## Prerequisites

- Python 3.12+
- Node.js / npm
- Git
- enough disk space for the local models and project artifacts

The exact Python dependencies are listed in:

```text
backend/requirements.txt
```

Frontend dependencies are listed in:

```text
frontend/package.json
```

---

## 1. Backend setup

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

Start the API:

```powershell
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Primary endpoint:

```text
POST /api/analyze
```

Request:

```json
{
  "text": "Your essay here..."
}
```

---

## 2. Frontend setup

In another terminal:

```powershell
cd frontend
npm install
npm run dev -- --port 5173
```

Open:

```text
http://127.0.0.1:5173
```

The Vite development server proxies `/api` requests to the FastAPI backend.

---

# Verification

## Backend tests

From the repository root:

```powershell
python -m pytest backend/tests -q
```

Current result:

```text
10 passed
```

The test suite covers:

- invalid input
- insufficient evidence
- feature ordering
- feature-definition reuse
- model loading
- deterministic inference
- known validation-row verification
- API serialization
- sentence evidence serialization

## Frontend production build

From `frontend/`:

```powershell
npm run build
```

The production TypeScript check and Vite build should both pass.

---

# Manual demo flow

For a quick demonstration:

```text
1. Start FastAPI on port 8000
2. Start Vite on port 5173
3. Paste an essay
4. Analyze
5. Show the document-level result
6. Open the Evidence Inspector
7. Inspect the highlighted evidence
8. Open the Feature Grid
9. Explain that evidence ≠ sentence-level authorship
10. Show the methodology / limitations section
```

For judging, the recommended explanation is:

> "The classifier makes a document-level decision using four measured linguistic features. We do not claim that individual sentences are AI-written. The Evidence Inspector instead shows where directly measured statistical evidence occurs and why it matters."

---

# Important implementation decisions

## No LLM-as-judge

The system never sends the essay to a chat model and asks it for a verdict.

A local causal model is only used as a measurement instrument for perplexity.

The final decision is produced by the saved Logistic Regression pipeline.

## No fabricated evidence

If a required feature cannot be computed, the detector abstains.

## No sentence-level authorship claims

The experiments did not justify reliable sentence-level attribution.

## No universal accuracy claim

All performance numbers are tied to documented datasets and evaluation protocols.

## Evidence is deterministic

The UI explanation is derived from actual detector outputs rather than an LLM-generated rationale.

---

# Evaluation and research artifacts

For anyone reviewing the project, the fastest path is:

```text
README
  ↓
docs/evaluation/FINAL-EVALUATION.md
  ↓
docs/evaluation/CONFIDENT-FAILURES.md
  ↓
docs/evaluation/ESL-AUDIT.md
  ↓
docs/DETECTION-METHODOLOGY.md
  ↓
docs/EXPERIMENT-LOG.md
```

This provides:

```text
What we built
    ↓
How well it worked
    ↓
Where it failed
    ↓
Whether ESL false-positive behavior was observed
    ↓
Why the methodology looks the way it does
    ↓
How we got there experimentally
```

---

# Limitations

The current system is intentionally bounded.

It does not guarantee:

- universal AI detection;
- reliable sentence-level authorship attribution;
- reliable recovery of exact AI-spliced passages;
- generalization to every generation model;
- calibration as factual authorship probability;
- universal fairness across all populations and domains.

The main production claim is narrower:

> The system provides a reproducible, evidence-first document-level classifier whose signals and limitations are inspectable.

---

# Status

**Project 2 — Production prototype / final submission**

Completed:

- validated feature pipeline
- production four-feature classifier
- FastAPI backend
- React/Vite frontend
- Evidence Inspector
- insufficient-evidence handling
- long-input robustness guardrail
- final held-out evaluation
- three confident failure analysis
- ESL/non-native-English audit
- experiment documentation
- evaluation artifacts

The project is ready for final submission/demo preparation.
