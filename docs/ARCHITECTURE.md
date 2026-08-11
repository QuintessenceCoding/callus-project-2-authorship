# Architecture — Evidence-First Authorship Analysis

## 1. Purpose

This document defines the technical architecture of the Callus Project 2 AI admissions-essay analysis system.

The architecture is designed around five requirements:

1. Analyze text at sentence and passage levels.
2. Produce measurable evidence rather than an unexplained AI verdict.
3. Separate machine-associated characteristics from essay-relative stylistic anomalies.
4. Represent uncertainty explicitly.
5. Keep the detection pipeline reproducible, locally runnable, and independent of paid AI services.

This document describes the **system boundaries and responsibilities**.

Specific model choices, feature sets, thresholds, and statistical formulations remain experimental unless explicitly marked as accepted decisions.

---

# 2. Architectural Principles

## 2.1 Detection Is an Analysis Pipeline

The system should not be structured as:

```text
Essay → AI model → Verdict
```

Instead:

```text
Essay
  ↓
Segmentation
  ↓
Feature Extraction
  ↓
Machine Association Analysis
  ↓
Stylistic Anomaly Analysis
  ↓
Evidence Sufficiency
  ↓
Classification / Abstention
  ↓
Evidence Aggregation
  ↓
API Response
  ↓
UI
```

Each stage has a defined responsibility.

---

## 2.2 The Detector Does Not Establish Authorship

The detection engine estimates measurable characteristics associated with machine-generated writing.

It does not establish:

* who wrote the text
* whether an AI system was actually used
* which model generated the text
* whether the writer intentionally used AI

The architecture therefore uses terminology such as:

* machine association
* stylistic anomaly
* evidence sufficiency
* uncertain
* insufficient evidence

rather than treating a model score as proof of authorship.

---

## 2.3 Evidence Must Flow With the Classification

A classification without its supporting measurements is incomplete.

The internal representation should therefore preserve:

```text
classification
+
machine association signal
+
stylistic anomaly signal
+
evidence sufficiency
+
driving features
```

This allows the UI to explain a result without asking another language model to generate an explanation.

---

## 2.4 Analysis and Presentation Must Be Separated

The detection engine should produce structured analytical results.

The frontend should be responsible for:

* rendering text
* highlighting passages
* displaying evidence
* presenting uncertainty
* visualizing scores

The frontend must not independently reproduce detection logic.

---

## 2.5 Experimental Components Must Remain Replaceable

The following components are expected to change during experimentation:

* perplexity model
* candidate feature set
* classifier
* local anomaly formulation
* thresholds
* calibration method

Therefore, these components should have clear interfaces rather than being tightly coupled throughout the application.

---

# 3. High-Level System

The proposed system consists of four primary layers:

```text
┌──────────────────────────────────────────────────────────┐
│                        FRONTEND                          │
│                    Next.js / React                       │
│                                                          │
│  Essay Input → Highlighted Analysis → Evidence Panel    │
└──────────────────────────┬───────────────────────────────┘
                           │ HTTP
                           ▼
┌──────────────────────────────────────────────────────────┐
│                          API                             │
│                       FastAPI                            │
│                                                          │
│  Request Validation → Analysis Orchestration → Response │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                    DETECTION ENGINE                      │
│                                                          │
│  Segmentation                                           │
│       ↓                                                  │
│  Feature Extraction                                      │
│       ↓                                                  │
│  ┌────────────────────┬──────────────────────┐           │
│  │ Machine Association│ Stylistic Anomaly   │           │
│  │ Analysis           │ Analysis             │           │
│  └──────────┬─────────┴──────────┬───────────┘           │
│             ▼                    ▼                       │
│          Evidence Sufficiency + Decision Layer          │
│                           ↓                              │
│                     Evidence Model                       │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                     MODELS / DATA                        │
│                                                          │
│ Local Language Model │ Classifier │ Feature Config      │
│ Dataset │ Model Artifacts │ Evaluation Artifacts        │
└──────────────────────────────────────────────────────────┘
```

---

# 4. Frontend Layer

## Technology

* Next.js
* React
* TypeScript
* Tailwind CSS
* Recharts or equivalent open-source visualization library

The frontend is responsible for presentation, not statistical computation.

---

## 4.1 Primary Responsibilities

The frontend should:

* accept essay text
* submit analysis requests
* render the returned essay
* highlight analyzed passages
* show passage-level assessments
* display evidence
* communicate uncertainty
* display document-level assessment
* visualize machine association vs stylistic anomaly where useful
* explain limitations to the user

---

## 4.2 Essay-Centered Interface

The essay itself is the primary interface.

The user should not need to interpret a dashboard before understanding the result.

Conceptually:

```text
┌─────────────────────────────────────────────────────────┐
│ Analysis: Mixed Evidence                                │
│ Evidence strength: Moderate                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Essay text                                             │
│                                                         │
│  Normal passage...                                      │
│                                                         │
│  [Machine-associated passage]                           │
│                                                         │
│  [Uncertain passage]                                    │
│                                                         │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
                   Selected Passage
                   ─────────────────
                   Machine association: High
                   Stylistic anomaly: High
                   Evidence: High

                   Why?
                   • unusually predictable
                   • low sentence variation
                   • differs from nearby writing
```

The UI should avoid making a single overall percentage the primary result.

---

# 5. API Layer

## Technology

Python + FastAPI.

The API is the boundary between the frontend and the detection engine.

---

## 5.1 Responsibilities

The API should:

* validate incoming requests
* enforce input limits
* invoke the analysis pipeline
* return structured results
* expose predictable errors
* avoid embedding statistical logic directly in route handlers

Routes should remain thin.

Conceptually:

```text
POST /api/analyze
        │
        ▼
Request validation
        │
        ▼
Analysis service
        │
        ▼
Detection engine
        │
        ▼
Response schema
```

The API should not contain:

```text
if perplexity > X:
    return "AI"
```

or other detection logic directly inside transport code.

---

# 6. Detection Engine

The detection engine is the core of the project.

It should be implemented as a collection of independently testable components.

Conceptually:

```text
Analysis Engine
│
├── Segmentation
│
├── Feature Extraction
│   ├── Predictability
│   ├── Rhythm
│   ├── Lexical
│   ├── Repetition
│   └── Syntax
│
├── Machine Association
│   └── Classifier
│
├── Stylistic Anomaly
│   └── Robust local analysis
│
├── Evidence Sufficiency
│
├── Decision / Abstention
│
└── Evidence Aggregation
```

---

# 7. Segmentation Component

## Responsibility

Convert the raw essay into analyzable units.

The initial hierarchy is:

```text
Document
  │
  ├── Passage
  │     ├── Sentence
  │     ├── Sentence
  │     └── ...
  │
  ├── Passage
  │     └── ...
  │
  └── ...
```

Sentence segmentation will initially use spaCy or another deterministic NLP segmentation method.

Passage boundaries may be derived from:

* paragraphs
* sentence windows
* adjacent sentence groups

The exact passage-window strategy is an experimental decision.

---

## 7.1 Segmentation Requirements

Segmentation should preserve:

* original text
* character offsets
* sentence ordering
* paragraph relationships
* sentence IDs
* passage IDs

This is required so the frontend can map analytical results back onto the original essay.

---

# 8. Feature Extraction Layer

Feature extraction converts each analysis unit into structured numerical measurements.

Conceptually:

```text
Sentence / Passage
        │
        ▼
Feature Extractor
        │
        ▼
Feature Vector
```

A feature vector may contain:

```text
{
    perplexity: ...,
    sentence_length: ...,
    lexical_diversity: ...,
    repetition: ...,
    syntactic_entropy: ...
}
```

The exact feature set is not permanently locked.

---

# 9. Feature Categories

Candidate features are organized into five major groups.

## 9.1 Predictability

Potential signals:

* mean token log probability
* perplexity
* perplexity variation

A small locally runnable causal language model will be used for token-probability extraction.

The model choice is determined through Phase 1 feasibility experiments.

---

## 9.2 Rhythm

Potential signals:

* sentence length
* sentence length variance
* sentence length coefficient of variation
* punctuation distribution
* clause-related statistics

These attempt to capture writing rhythm and pacing.

---

## 9.3 Lexical Characteristics

Potential signals:

* MATTR
* rare-word proportion
* lexical repetition
* repeated n-grams

These describe vocabulary diversity and reuse.

---

## 9.4 Structural Characteristics

Potential signals:

* POS n-gram entropy
* dependency statistics
* syntactic variation
* structural repetition

These measure patterns in grammatical construction.

---

## 9.5 Local Consistency Characteristics

Potential signals:

* deviation from local feature distribution
* deviation from essay-level robust baseline
* neighboring passage feature shifts
* changes in predictability or rhythm

These are particularly relevant to hybrid-writing detection.

---

# 10. Machine Association Analysis

The machine-association component estimates how strongly a passage's feature vector resembles machine-associated examples in the training distribution.

Conceptually:

```text
Feature Vector
      │
      ▼
Normalization / preprocessing
      │
      ▼
Trained classifier
      │
      ▼
Machine Association Signal
```

Potential classifiers include:

* Logistic Regression
* Random Forest
* other classical models if experimentally justified

The classifier will not be selected solely by theoretical preference.

It will be benchmarked against baselines.

---

## 10.1 Baseline

The first meaningful baseline is:

```text
Perplexity
    ↓
Simple threshold
    ↓
Human / Machine-associated
```

The purpose is to determine whether the multi-feature detector provides useful improvement over a simple predictability-based approach.

---

# 11. Stylistic Anomaly Analysis

The stylistic anomaly component answers a different question:

> How unusual is this passage relative to the writing surrounding it?

It does not directly estimate AI authorship.

---

## 11.1 Robust Statistics

The initial approach is based on robust statistics rather than ordinary mean/std estimation.

Potential components include:

* median
* Median Absolute Deviation (MAD)
* leave-one-out baselines
* local passage windows

Conceptually:

```text
Essay
│
├── surrounding observations
│
│      establish baseline
│
└── target passage
       │
       ▼
  deviation from baseline
       │
       ▼
 Stylistic Anomaly Signal
```

The exact statistical formulation remains a feasibility question.

---

## 11.2 Leave-One-Out Principle

When calculating the anomaly of a unit, that unit should not substantially determine its own baseline.

Conceptually:

```text
S1 S2 S3 S4 S5 S6 S7 S8

Analyze S4

Baseline:
S1 S2 S3    S5 S6 S7 S8
```

This reduces self-contamination of the reference distribution.

---

# 12. Local vs Global Analysis

The two analytical signals are deliberately separate.

```text
                     MACHINE ASSOCIATION
                            HIGH
                              │
                              │
          Stylistic           │       Machine-associated
          shift               │       anomaly
                              │
──────────────────────────────┼──────────────────────────────
                              │
          Consistent          │       Consistently
          human-like          │       machine-associated
                              │
                              │
                            LOW
                              │
                         MACHINE ASSOCIATION
```

The four regions are interpretive categories, not hard-coded ground truth.

For example:

### Low machine association + low anomaly

> Consistent with the human-writing distribution and internally consistent.

### High machine association + low anomaly

> Machine-associated characteristics appear consistently across the analyzed text.

### High machine association + high anomaly

> Machine-associated characteristics coincide with a localized stylistic deviation.

### Low machine association + high anomaly

> The passage differs from surrounding writing but does not strongly resemble the machine-associated distribution.

This last case should generally produce an uncertain or stylistic-shift interpretation rather than an AI accusation.

---

# 13. Evidence Sufficiency Layer

The evidence-sufficiency layer prevents unstable statistics from becoming authoritative classifications.

```text
Raw Analysis
     │
     ▼
Are sufficient observations available?
     │
 ┌───┴────┐
 │        │
 YES      NO
 │        │
 ▼        ▼
Continue  Limited /
analysis  insufficient
          evidence
```

Potential reasons for insufficient evidence:

* sentence too short
* passage too short
* insufficient neighboring observations
* unstable variance/MAD
* unavailable feature
* conflicting signals

The system should degrade gracefully rather than invent a score.

---

# 14. Decision and Abstention Layer

This component converts analytical signals into a user-facing assessment.

It is deliberately separate from feature extraction and model inference.

Possible states include:

```text
machine_associated
human_consistent
uncertain
insufficient_evidence
```

The exact vocabulary may change during UI design.

The decision layer may consider:

* machine association
* stylistic anomaly
* evidence sufficiency
* model confidence/calibration
* signal agreement
* passage length

No final thresholds are locked yet.

---

# 15. Evidence Aggregation Layer

The evidence layer converts raw numerical outputs into structured, explainable evidence.

It must not ask an LLM:

> "Why was this sentence classified as AI?"

Instead, explanations are generated deterministically from the features that contributed to the analysis.

Conceptually:

```text
Classifier Output
+
Feature Values
+
Local Anomaly
+
Evidence Sufficiency
        │
        ▼
Evidence Record
```

Example:

```json
{
  "feature": "perplexity",
  "value": 12.4,
  "relative_interpretation": "high_predictability",
  "contribution": "machine_associated"
}
```

The exact contribution calculation depends on the final classifier.

---

# 16. Analysis Result Model

The internal result should preserve enough information for both the API and UI.

Conceptually:

```text
AnalysisResult
│
├── document_assessment
├── evidence_strength
├── passages[]
│
└── metadata
```

Each passage may contain:

```text
PassageResult
│
├── passage_id
├── text
├── start_offset
├── end_offset
├── machine_association
├── stylistic_anomaly
├── evidence_sufficiency
├── assessment
└── evidence[]
```

Each evidence item may contain:

```text
Evidence
├── feature
├── raw_value
├── normalized_value
├── direction
└── interpretation
```

This structure is conceptual and will be finalized during API/schema design.

---

# 17. Data and Model Layer

The core system depends on several local artifacts.

```text
models/
├── language-model/
├── classifier/
└── preprocessing/

data/
├── raw/
├── processed/
├── manifests/
└── splits/

experiments/
├── baselines/
├── ablations/
├── ood/
└── bias/
```

Exact repository organization may change after implementation begins.

---

# 18. Dataset Boundary

Dataset construction is separate from runtime inference.

The training/evaluation pipeline should be able to:

```text
Raw data
   ↓
Normalization
   ↓
Essay-family construction
   ↓
Feature extraction
   ↓
Family-level split
   ↓
Training
   ↓
Model artifact
```

Runtime analysis should only need:

```text
Essay
  ↓
Segmentation
  ↓
Feature extraction
  ↓
Stored model/artifacts
  ↓
Analysis
```

The application should not retrain the classifier every time a user submits an essay.

---

# 19. Experimentation Boundary

Experiments should remain separate from production application code.

Experimental code may answer questions such as:

* Which features help?
* Which classifier performs best?
* Which perplexity model is practical?
* How stable is LOO/MAD?
* What minimum text length is sufficient?
* How does performance change on unseen models?
* Which features contribute to ESL false positives?

Once an experimental result justifies a production decision, the decision should be documented and the relevant implementation moved into the detection engine.

---

# 20. Training Pipeline vs Inference Pipeline

These are separate concerns.

## Training

```text
Dataset
  ↓
Feature extraction
  ↓
Training split
  ↓
Preprocessing/scaling
  ↓
Classifier training
  ↓
Validation
  ↓
Calibration / threshold selection
  ↓
Model artifact
```

## Inference

```text
Essay
  ↓
Segmentation
  ↓
Feature extraction
  ↓
Saved preprocessing
  ↓
Saved classifier
  ↓
Machine association
  ↓
Local anomaly
  ↓
Evidence sufficiency
  ↓
Decision
```

The inference pipeline must use the same preprocessing assumptions as the trained model.

---

# 21. API Boundary

The frontend should not know:

* which language model is used
* how perplexity is calculated
* how MAD is calculated
* which classifier is used
* how feature normalization works

The API exposes analysis results, not internal implementation details.

Likewise, the detection engine should not know:

* how text is visually highlighted
* which chart library is used
* which frontend component displays evidence

This separation allows each layer to evolve independently.

---

# 22. Error Handling

Errors should be classified into meaningful categories.

Potential categories:

### Invalid input

Examples:

* empty essay
* unsupported request format
* input exceeds configured limits

### Analysis limitations

Examples:

* insufficient text
* unavailable feature
* model unavailable

### Infrastructure errors

Examples:

* model loading failure
* unexpected internal exception

The API should return structured errors.

The frontend should distinguish:

> **The system could not analyze this input**

from:

> **The system analyzed it but did not have sufficient evidence.**

These are not the same condition.

---

# 23. Performance Considerations

The project prioritizes correctness and explainability over maximum throughput.

However, the runtime should remain practical for interactive essay analysis.

Potential optimizations include:

* loading models once at process startup
* batching tokenization
* caching repeated computations
* avoiding unnecessary model calls
* reusing feature calculations between sentence and passage analysis
* using small local models
* limiting expensive experimental features in production inference

No optimization should obscure the detection methodology.

---

# 24. Security and Privacy Considerations

Essays may contain sensitive personal information.

The local-first architecture is therefore beneficial because the default system does not need to transmit essay text to external paid AI services.

The application should avoid unnecessary persistence of submitted essays.

Unless persistence is explicitly required, analysis should be treated as ephemeral runtime data.

Any logging must avoid accidentally storing complete user essays.

---

# 25. Reproducibility

The architecture should support reproduction of:

* feature extraction
* classifier training
* evaluation
* dataset splits
* model artifacts
* experiment results

Relevant configuration should be explicit rather than hidden inside application code.

Where randomness exists, seeds should be recorded where practical.

---

# 26. Architecture Decision Boundaries

The following are **not permanently locked**:

* exact local language model
* exact feature set
* final classifier
* feature scaling strategy
* anomaly-distance formulation
* minimum text length
* passage-window size
* probability calibration method
* decision thresholds
* exact API response schema

These will be finalized through research and feasibility experiments.

The following are currently architectural principles:

* local/free core pipeline
* evidence-first analysis
* separation of global and local signals
* explicit evidence sufficiency
* deterministic evidence generation
* family-level dataset splitting
* replaceable experimental components
* thin API layer
* frontend separated from detection logic

---

# 27. Expected Repository Architecture

The final repository is expected to evolve toward a structure similar to:

```text
project-2/
│
├── README.md
│
├── docs/
│   ├── PROJECT-2-PLAN.md
│   ├── ARCHITECTURE.md
│   ├── DETECTION-METHODOLOGY.md
│   ├── DECISIONS.md
│   ├── DATASET.md
│   ├── EVALUATION.md
│   ├── BIAS-ANALYSIS.md
│   └── FAILURE-ANALYSIS.md
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── analysis/
│   │   ├── features/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   └── tests/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── ...
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── manifests/
│   └── splits/
│
├── experiments/
│   ├── feasibility/
│   ├── baselines/
│   ├── ablations/
│   ├── ood/
│   └── bias/
│
├── models/
│   └── ...
│
└── scripts/
    └── ...
```

This is an **initial target**, not a command to create every directory immediately.

Folders should be introduced when their responsibilities become concrete.

---

# 28. Architectural Evolution

Architecture changes are expected during the project.

When a feasibility experiment invalidates an architectural assumption:

1. Record the result.
2. Explain why the original approach was insufficient.
3. Update `DECISIONS.md`.
4. Update this document if the architectural boundary changes.
5. Update implementation plans.
6. Verify that dependent components remain consistent.

Architecture should reflect what we learn rather than forcing experiments to conform to the original plan.

---

# 29. Current Architecture Status

**Phase:** 0 — Project Foundation

**Status:** Conceptually defined; implementation details pending feasibility experiments.

### Locked architectural principles

* Evidence-first detection
* Machine association separated from stylistic anomaly
* Evidence sufficiency and abstention
* Local/free core pipeline
* Replaceable ML components
* Thin API
* Essay-centered UI
* Deterministic evidence generation
* Family-level dataset isolation
* Experiment-driven feature selection

### Pending decisions

* local language model
* exact feature set
* classifier
* anomaly formulation
* evidence thresholds
* calibration
* passage-window strategy
* final API schemas

The next implementation work should begin with **Phase 1 feasibility experiments**, not with construction of the complete production pipeline.
