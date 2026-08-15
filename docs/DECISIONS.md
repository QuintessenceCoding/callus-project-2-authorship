# Architecture & Engineering Decisions

This document records significant decisions made during the development of Project 2.

The purpose is not to document every implementation detail. It records decisions that materially affect:

- architecture
- methodology
- dataset design
- evaluation
- reproducibility
- engineering trade-offs

Each decision explains **why** it was made.

When new experimental evidence contradicts an earlier assumption, the original decision remains in the history and a later decision supersedes it where appropriate.

---

# Decision Status

Each decision uses one of the following statuses:

- **Accepted** — currently adopted in the project.
- **Proposed** — preferred direction, not yet validated.
- **Experimental** — actively being tested.
- **Rejected** — intentionally not adopted.
- **Superseded** — previously accepted or proposed, but replaced by later evidence.
- **Deferred** — intentionally postponed.

---

# DEC-001 — Evidence-First Detection Framing

**Status:** Accepted

## Context

Callus explicitly rejects a simple system that asks a chat model whether an essay is AI-generated.

A conventional "AI percentage" also provides little actionable evidence and can imply a level of certainty that the underlying detector cannot support.

## Decision

The system will not claim to determine definitive authorship.

Instead, it estimates whether text exhibits **measurable characteristics associated with machine-generated writing**, while exposing the underlying evidence and communicating uncertainty.

## Rationale

Authorship is not directly observable from text alone.

An evidence-first framing allows the system to:

- expose measurable signals
- explain classifications
- acknowledge uncertainty
- evaluate hybrid writing
- document failure modes honestly

## Consequences

The wording used throughout the project should avoid claims such as:

> "This sentence was written by AI."

Preferred language includes:

> "This document exhibits machine-associated characteristics."

and:

> "This passage contains a strong measured predictability signal."

The project does not use sentence-level evidence as proof of authorship.

---

# DEC-002 — Do Not Use an LLM as the Final Judge

**Status:** Accepted

## Context

Callus explicitly states that an application which sends an essay to a chat model and asks for an AI/human verdict is not sufficient.

## Decision

A language model may be used as an **instrument** for extracting measurable information, such as token probabilities, but it must not make the final classification decision.

The final decision is produced by the project's own statistical/ML analysis.

## Rationale

This provides:

- measurable evidence
- reproducibility
- controllable experiments
- separation between instrumentation and judgment

## Consequences

The production pipeline uses a local causal language model for perplexity extraction.

The persisted Logistic Regression classifier and decision layer remain under project control.

---

# DEC-003 — Zero-Cost Core System

**Status:** Accepted

## Context

The project must be completed within the available resources and should not depend on paid APIs.

## Decision

The complete core project must be buildable, runnable, evaluated, and demonstrated at **₹0**.

No paid API or proprietary detection service is required.

## Consequences

The project prefers:

- locally runnable models
- open/free software
- public datasets with appropriate usage rights
- local inference
- local training

---

# DEC-004 — Local Model Generation for Synthetic Data

**Status:** Accepted

## Context

The dataset requires machine-generated and hybrid examples while maintaining the zero-cost constraint.

## Decision

Machine-generated dataset variants should be produced using locally runnable language models.

The generation interface must remain replaceable and must not depend architecturally on one specific runtime.

## Rationale

The important architectural property is:

> local model generation

rather than:

> dependence on a specific inference application.

This allows the dataset-generation implementation to change without redesigning the project.

---

# DEC-005 — Perplexity as a Validated Measurement Instrument

**Status:** Accepted

## Context

Perplexity was initially treated as a baseline candidate feature.

EXP-001 established that local sentence-level causal perplexity could be measured reproducibly with `distilgpt2`.

## Decision

Perplexity is used as one of the four production features and as the only currently exposed sentence-level evidence measurement.

Production configuration:

```text
Model: distilgpt2
Runtime: Hugging Face Transformers
Device: CPU
```

## Rationale

Perplexity provides a measurable, locally reproducible signal and integrates cleanly into the feature-based classifier.

## Consequences

Perplexity is never treated as proof of AI authorship.

---

# DEC-006 — Experiment Before Finalizing Features

**Status:** Accepted

## Context

Many linguistic characteristics have been proposed as indicators of machine-generated writing.

## Decision

Candidate features are treated as experimental hypotheses and only promoted after empirical evaluation.

## Rationale

This prevents the project from becoming a collection of theoretically plausible metrics with no evidence that they work together.

Evaluation considers more than aggregate F1, including:

- discrimination
- precision/recall
- F1
- generalization
- hybrid behavior
- ESL/non-native-English behavior
- computational cost
- interpretability

---

# DEC-007 — Separate Document-Level Machine Association from Local Evidence

**Status:** Accepted

## Context

A document can exhibit machine-associated characteristics without any individual sentence being reliably attributable to AI.

The local-attribution experiments also showed that sentence-level anomaly and contribution signals were not sufficiently reliable for production use.

## Decision

The production system separates:

### Document-level machine association

The four-feature Logistic Regression estimates whether the complete essay exhibits characteristics associated with the machine-generated training distribution.

### Sentence-level evidence observation

Where validated sentence-level measurements exist, the system shows where those measurements occur.

The current implementation uses sentence-level perplexity observations.

## Rationale

This preserves the distinction between:

> "The document has a machine-associated feature profile"

and:

> "This exact sentence was written by AI."

The first is supported by the production model.

The second is not.

## Consequences

The API and UI must not describe sentence evidence as sentence-level authorship classification.

---

# DEC-008 — Robust Local Anomaly Detection Was an Experimental Direction

**Status:** Superseded

## Context

The original methodology proposed Median/MAD, leave-one-out baselines, and local windows for sentence-level anomaly detection.

## Original Decision

The project would investigate robust local anomaly scores as a production evidence signal.

## Superseding Evidence

EXP-007, EXP-008, and EXP-009 found the resulting local signals too noisy for reliable production localization.

EXP-011 further tested leave-one-sentence-out contribution and did not provide sufficient separation or capture.

## New Decision

These local-attribution methods are retained as experimental history but are not production features.

## Consequences

The final production detector does not expose:

- local anomaly scores
- local anomaly labels
- leave-one-out authorship heatmaps
- definitive sentence attribution

---

# DEC-009 — Leave-One-Out Attribution Rejected for Production

**Status:** Rejected

## Context

Leave-one-out contribution was investigated as a direct way to estimate how much each sentence affected the document-level classifier.

## Experiment

EXP-011 evaluated 20 controlled hybrids.

Results:

```text
Top-10% AI-sentence capture: 22.5%
Top-25% AI-sentence capture: 42.5%

Median AI-sentence contribution:   -0.0001953670
Median human-sentence contribution: -0.0011773087
Median difference:                  0.0009819416
```

## Decision

Leave-one-sentence-out attribution is not used as a production sentence-level authorship mechanism.

## Rationale

The observed localization performance was too weak to support an authoritative sentence-level claim.

## Consequences

The feature remains documented as a rejected experiment rather than being disguised as a production capability.

---

# DEC-010 — Passage-Level AI Attribution Is Not a Production Classifier

**Status:** Superseded

## Context

Passage-level analysis was originally considered a first-class runtime capability because it could provide more stable statistics than individual sentences.

## Original Decision

The system would support sentence-level and passage-level classification.

## New Evidence

The local attribution experiments did not establish reliable passage boundaries or passage-level authorship labels.

## New Decision

Passages remain important for dataset construction and experimental evaluation, but the production system does not assign AI/human labels to arbitrary passages.

The production UI instead shows validated sentence-level evidence observations.

---

# DEC-011 — Evidence Sufficiency and Abstention

**Status:** Accepted

## Context

Statistical measurements can become unreliable when there is too little text or when one or more required features are unavailable.

## Decision

The detector must explicitly support insufficient evidence.

A production classification is produced only when the complete four-feature vector required by the trained model is available and numerically valid.

Otherwise:

```text
state = insufficient_evidence
```

## Rationale

It is preferable to abstain than to fabricate a feature value or present an unstable score as authoritative.

## Consequences

Examples include:

- insufficient sentences for sentence-length CV
- insufficient lexical tokens for MATTR
- unavailable perplexity
- language-model context overflow

---

# DEC-012 — Essay-Family Dataset Structure

**Status:** Accepted

## Context

A dataset containing a human essay and AI-derived variants creates strong relationships between documents.

## Decision

The fundamental dataset unit is an **Essay Family**.

An Essay Family can contain:

- source human essay
- AI-generated variants
- AI-polished variants
- AI-spliced variants where available

## Rationale

The family structure makes related documents explicit and enables leakage-safe splitting.

---

# DEC-013 — Family-Level Train/Validation/Test Splitting

**Status:** Accepted

## Context

Document-level random splitting can place variants of the same source essay in different splits.

## Decision

All documents belonging to the same Essay Family must remain within the same dataset split.

```text
Family A → TRAIN
Family B → VALIDATION
Family C → TEST
```

This prevents related documents from leaking topic, vocabulary, narrative structure, and source-specific characteristics across evaluation boundaries.

---

# DEC-014 — Hold Out Unseen Generation Models

**Status:** Deferred

## Context

A detector may learn the fingerprint of specific generation models rather than general machine-associated writing characteristics.

## Decision

Unseen-model evaluation remains desirable, but its exact configuration is deferred to final evaluation because the current production classifier and submission timeline are already locked.

## Rationale

The experiment remains important as a limitation/generalization question, but it is not allowed to reopen the production model without evidence and time to evaluate it properly.

---

# DEC-015 — Explicit Topic Holdout

**Status:** Deferred

## Context

A classifier may learn vocabulary or subject matter rather than writing characteristics.

## Decision

Topic-holdout evaluation remains a useful generalization test, but is treated as final-evaluation work rather than a production architecture dependency.

---

# DEC-016 — Hybrid Writing as a First-Class Evaluation Case

**Status:** Accepted

## Context

Real-world AI assistance often involves partial editing rather than completely machine-generated essays.

## Decision

The dataset and evaluation process explicitly include:

- AI-polished human passages
- AI-spliced passages

## Rationale

These cases are important for testing whether the document-level detector remains useful under partial machine assistance.

## Consequence

Hybrid ground truth is retained for experimentation even though exact passage attribution is not a production claim.

---

# DEC-017 — ESL Bias Audit

**Status:** Accepted

## Context

Statistical writing detectors may disproportionately flag non-native English writing.

## Decision

The project will explicitly evaluate false-positive behavior on an ESL/non-native-English control set where appropriate data is available and permitted for use.

## Rationale

This is both a known risk in the problem domain and an explicit concern in the Callus brief.

---

# DEC-018 — No Test-Set Tuning

**Status:** Accepted

## Context

Repeatedly examining test results and modifying the model creates an effectively contaminated test set.

## Decision

The final test set must not be used to tune:

- features
- thresholds
- classifier hyperparameters
- evidence-sufficiency rules
- calibration

## Workflow

```text
TRAIN
  ↓
VALIDATION
  ↓
Tune / decide
  ↓
LOCK
  ↓
FINAL TEST
  ↓
Report
```

---

# DEC-019 — Deterministic Evidence Generation

**Status:** Accepted

## Context

The project must explain why a document received its classification.

Generating explanations by asking another language model to rationalize the result would introduce an additional opaque model.

## Decision

Evidence shown to users must be derived from measured features and analytical outputs already produced by the detector.

## Rationale

The explanation should correspond to what the detector actually measured.

For example:

> "This sentence has a comparatively low perplexity measurement."

is preferable to an LLM-generated statement such as:

> "The prose sounds unusually polished."

---

# DEC-020 — Thin API Layer

**Status:** Accepted

## Context

Business and analytical logic becomes difficult to test and maintain when embedded inside HTTP routes.

## Decision

FastAPI routes remain thin.

The API handles:

- request validation
- response serialization
- transport-level errors
- detector orchestration

Detection logic belongs in dedicated components.

---

# DEC-021 — Frontend Does Not Implement Detection Logic

**Status:** Accepted

## Context

Duplicating analytical logic between Python and TypeScript would create inconsistent results.

## Decision

The backend/detection engine is the source of truth for analytical results.

The frontend only renders the structured response and performs presentation-only operations.

The frontend must not independently calculate:

- perplexity
- classifier decisions
- detection thresholds
- anomaly scores

---

# DEC-022 — Local-First Privacy Model

**Status:** Accepted

## Context

Admissions essays can contain sensitive personal information.

## Decision

The core analysis pipeline should run locally and should not require transmitting submitted essays to third-party AI providers.

## Consequences

The application should avoid persistent storage of submitted essays unless explicitly required.

Logging should not accidentally record full essay contents.

---

# DEC-023 — Experiment/Production Separation

**Status:** Accepted

## Context

Experimental code changes frequently and should not contaminate stable application logic.

## Decision

Experiments live separately from production detection components.

Only validated decisions are promoted into production code.

Historical experiments remain unchanged so the methodological trail is preserved.

---

# DEC-024 — Hypothesis → Experiment → Result → Decision Workflow

**Status:** Accepted

## Decision

Significant methodological decisions should follow:

```text
Hypothesis
    ↓
Experiment
    ↓
Result
    ↓
Interpretation
    ↓
Decision
```

## Rationale

This prevents theoretical assumptions from being presented as empirical facts and creates an auditable research trail.

---

# DEC-025 — Documentation Is Part of the Implementation Process

**Status:** Accepted

## Context

Callus evaluates communication and documentation as part of the engineering work.

## Decision

Documentation evolves alongside the project.

Important decisions are recorded before or during implementation where practical.

Source-of-truth documents include:

- project plan
- architecture
- methodology
- decisions
- dataset
- evaluation
- experiment log
- generation protocol
- production milestone

---

# DEC-026 — AI-Assisted Development Must Remain Reviewable

**Status:** Accepted

## Context

Callus permits AI coding tools.

## Decision

AI tools may be used extensively, but generated code must be reviewed and understood before being retained.

Tasks should be bounded by:

- documented requirements
- explicit scope
- acceptance criteria
- verification instructions

## Rationale

The final repository must remain understandable to its author rather than depending on blindly trusted generated code.

---

# DEC-027 — Feature Selection Must Consider Bias and Generalization

**Status:** Accepted

## Context

A feature can improve aggregate performance while harming generalization or increasing false positives for a specific group.

## Decision

Feature promotion considers:

- overall discrimination
- OOD behavior
- hybrid behavior
- calibration
- ESL false positives
- computational cost
- interpretability

A feature is not retained solely because it improves aggregate F1.

---

# DEC-028 — No Universal Accuracy Claim

**Status:** Accepted

## Context

AI detection performance depends on dataset, generation model, prompting, editing, topic, domain, and evaluation protocol.

## Decision

The project will report performance within clearly defined evaluation conditions.

It will not claim universal detection capability.

Preferred framing:

> "On our documented evaluation set, the system achieved X under Y conditions, with the following observed failure modes and limitations."

---

# DEC-029 — Local Generation Interface Must Be Replaceable

**Status:** Accepted

## Context

Local model inference tools are useful for development but should not become architectural dependencies.

## Decision

Dataset generation should interact with a model-generation abstraction rather than directly coupling the pipeline to one application.

This keeps the generation architecture replaceable.

---

# DEC-030 — Architecture Changes Must Be Recorded

**Status:** Accepted

## Decision

When experimental evidence causes a meaningful architectural change:

1. Record the result.
2. Mark the old decision as superseded or rejected where appropriate.
3. Add the new decision.
4. Update `ARCHITECTURE.md`.
5. Update `DETECTION-METHODOLOGY.md`.
6. Update affected implementation plans.

## Rationale

The repository should reflect the actual engineering process rather than pretending the final architecture was obvious from the beginning.

---

# DEC-031 — Evidence Inspector for "Where and Why"

**Status:** Accepted

## Context

The Callus brief requires the application to show users **where** relevant evidence occurs and **why** the system reached its result.

The project cannot responsibly satisfy this by assigning unsupported AI labels to individual sentences.

## Decision

The product uses an **Evidence Inspector**.

The document receives a document-level classification from the production model.

Where validated sentence-level measurements exist, the UI surfaces the strongest measured exemplars and explains the corresponding property.

Current production implementation:

```text
Document classification
        +
Sentence-level perplexity evidence
        ↓
Evidence Inspector
```

## Rationale

This approach satisfies the need for inspectable evidence without converting weak local-attribution results into false certainty.

## Consequences

The UI may say:

> "This sentence has a strong predictability measurement."

It must not say:

> "This sentence is AI-generated."

---

# DEC-032 — Four-Feature Production Classifier

**Status:** Accepted

## Context

EXP-004 and EXP-006 validated a compact production feature set.

## Decision

The production feature vector is fixed to:

1. Perplexity
2. Sentence-length coefficient of variation
3. MATTR
4. POS 3-gram entropy

The production model is:

```text
StandardScaler
      ↓
LogisticRegression
```

The saved artifact is:

```text
backend/artifacts/authorship_detector.joblib
```

## Rationale

The four-feature model provides a compact, reproducible, classical ML detector with a transparent pipeline.

## Reference Validation Metrics

EXP-006 validation:

```text
Accuracy   0.9746835443
Precision  0.9523809524
Recall     1.0000000000
F1         0.9756097561
ROC-AUC    0.9955128205
```

These are distribution-specific validation results, not universal accuracy claims.

---

# DEC-033 — Long-Sentence Context Guardrail

**Status:** Accepted

## Context

During integration, an 867-word PERSUADE essay was interpreted as one sentence containing 1134 language-model tokens, exceeding the 1024-token context supported by `distilgpt2`.

The initial implementation returned HTTP 500.

## Decision

The production extractor checks the language-model context limit before attempting perplexity.

Oversized sentences receive:

```text
sentence_exceeds_language_model_context
```

and perplexity becomes unavailable.

If the complete required feature vector cannot be formed, the detector returns:

```text
insufficient_evidence
```

## Rationale

This prevents crashes and avoids silently truncating the text, which would change the validated measurement definition.

---

# DEC-034 — Model Signal Is Not Authorship Certainty

**Status:** Accepted

## Context

The Logistic Regression classifier exposes a numeric probability-like score, but that score is learned within a bounded development distribution.

## Decision

The frontend labels the value:

```text
MODEL SIGNAL
```

rather than:

```text
AI PROBABILITY
```

or:

```text
PROBABILITY OF AI AUTHORSIP
```

The underlying API field may remain `ai_probability` for compatibility with the model interface.

## Rationale

This preserves implementation clarity without suggesting that the value is a calibrated probability that AI authored the essay.

---

# Current Decision Summary

## Accepted

- Evidence-first detection framing
- No LLM-as-final-judge
- ₹0 core system
- Local model generation with replaceable interface
- Perplexity as a validated production measurement
- Experiment-before-promotion
- Document-level machine association
- Sentence-level perplexity as inspectable evidence
- Evidence sufficiency and abstention
- Four-feature StandardScaler + Logistic Regression classifier
- Essay-family dataset structure
- Family-level dataset splitting
- Hybrid writing evaluation
- ESL bias audit
- No test-set tuning
- Deterministic evidence generation
- Thin API
- Backend as analytical source of truth
- Frontend separated from detection logic
- Local-first privacy model
- Experiment/production separation
- Hypothesis → Experiment → Result → Decision workflow
- Documentation as part of implementation
- Reviewable AI-assisted development
- Multi-dimensional feature evaluation
- No universal accuracy claims
- Evidence Inspector for "where and why"
- Long-sentence context guardrail
- Model signal terminology
- Recorded architecture evolution

## Superseded / Rejected

- Production local stylistic anomaly scoring
- Production leave-one-out sentence attribution
- Production passage-level AI attribution
- Sentence-level AI authorship claims

## Deferred

- Unseen-generation-model evaluation configuration
- Explicit topic holdout configuration
- Probability calibration
- Expanded local evidence beyond currently validated sentence-level perplexity
- Further passage-level attribution research

---

# Current Project State

The production methodology and architecture are now locked for the submission prototype.

The core detector, API, frontend, Evidence Inspector, and backend tests are implemented.

Remaining work is primarily:

- final evaluation
- three confident failure cases and explanations
- ESL/non-native-English audit
- documentation consistency
- demo/presentation preparation
- final repository verification
