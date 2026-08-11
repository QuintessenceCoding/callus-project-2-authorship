# Architecture & Engineering Decisions

This document records significant decisions made during the development of Project 2.

The purpose is not to document every implementation detail. It records decisions that materially affect:

* architecture
* methodology
* dataset design
* evaluation
* reproducibility
* engineering trade-offs

Each decision should explain **why** it was made.

Decisions may be revised when new experimental evidence contradicts an earlier assumption. When that happens, the original decision should remain in the history and a new decision should supersede it.

---

# Decision Status

Each decision uses one of the following statuses:

* **Accepted** — currently adopted.
* **Proposed** — preferred direction, not yet validated.
* **Experimental** — actively being tested.
* **Rejected** — considered and intentionally not adopted.
* **Superseded** — previously accepted but replaced by a later decision.
* **Deferred** — intentionally postponed.

---

# DEC-001 — Evidence-First Detection Framing

**Status:** Accepted

## Context

Callus explicitly rejects a simple system that asks a chat model whether an essay is AI-generated.

A conventional "AI percentage" also provides little actionable evidence and can imply a level of certainty that the underlying detector cannot support.

## Decision

The system will not claim to determine definitive authorship.

Instead, it will estimate whether text exhibits **measurable characteristics associated with machine-generated writing**, while identifying stylistic anomalies and communicating uncertainty.

## Rationale

Authorship is not directly observable from text alone.

An evidence-first framing allows the system to:

* expose measurable signals
* explain classifications
* acknowledge uncertainty
* analyze hybrid writing
* document failure modes honestly

It also aligns directly with Callus's requirement to show where and why text was flagged.

## Consequences

The wording used throughout the project should avoid claims such as:

> "This sentence was written by AI."

Preferred language includes:

> "This passage exhibits machine-associated characteristics."

and:

> "This passage differs significantly from the surrounding writing."

---

# DEC-002 — Do Not Use an LLM as the Final Judge

**Status:** Accepted

## Context

Callus explicitly states that an application which sends an essay to a chat model and asks for an AI/human verdict is not sufficient.

## Decision

A language model may be used as an **instrument** for extracting measurable information, such as token probabilities, but it must not make the final classification decision.

The final decision must be produced by the project's own statistical/ML analysis.

## Rationale

This provides:

* measurable evidence
* reproducibility
* controllable experiments
* explainability
* separation between instrumentation and judgment

## Consequences

A local causal language model may be used for perplexity/token-probability extraction.

The classifier and decision layer remain under our control.

---

# DEC-003 — Zero-Cost Core System

**Status:** Accepted

## Context

The project must be completed within the available resources and should not depend on paid APIs.

Paid generation APIs would also introduce a dependency that makes reproducing the dataset more difficult.

## Decision

The complete core project must be buildable, runnable, evaluated, and demonstrated at **₹0**.

No paid API or proprietary detection service may be required.

## Rationale

A local-first pipeline provides:

* reproducibility
* independence from API credits
* predictable runtime behavior
* stronger systems engineering value

It also prevents the project from becoming dependent on access to paid model APIs.

## Consequences

The project will prefer:

* locally runnable models
* open-source/free software
* public datasets with appropriate usage rights
* local inference
* local training

Dataset size may be reduced if local generation becomes the bottleneck.

---

# DEC-004 — Local Model Generation for Synthetic Data

**Status:** Proposed

## Context

The dataset requires machine-generated and hybrid examples.

Using paid APIs would violate the zero-cost core-system constraint.

## Decision

Machine-generated dataset variants should be produced using locally runnable quantized language models.

A local inference interface such as Ollama may be used, but the dataset-generation architecture must not depend on Ollama specifically.

## Rationale

The important architectural property is:

> local model generation

rather than:

> dependence on a specific inference application.

This keeps the generation pipeline replaceable.

## Alternatives Considered

### Paid OpenAI/Anthropic APIs

Rejected because they violate the project's zero-cost requirement.

### One fixed local model

Possible, but limits model-family diversity.

### Multiple local models

Preferred if hardware and time permit.

## Consequences

Generation speed may constrain dataset size.

Controlled paired design takes priority over arbitrary dataset volume.

---

# DEC-005 — Perplexity as the Initial Baseline

**Status:** Proposed

## Context

Language-model predictability is one of the strongest practical candidate signals for machine-associated writing.

However, relying on perplexity alone is insufficient for the intended system.

## Decision

A perplexity-based detector will serve as an initial baseline against which additional features are evaluated.

A small locally runnable causal language model will provide token probabilities.

## Rationale

This gives us a measurable and relatively simple baseline before introducing additional linguistic features.

It allows the project to answer:

> Do our additional features actually improve on a simple predictability-based detector?

## Alternatives Considered

### LLM-as-judge

Rejected.

### Large local model

Deferred because of compute cost and uncertain incremental value.

### Small causal model

Preferred for the initial feasibility experiment.

## Consequences

The exact model remains pending experimentation.

Candidates may include small GPT-2-family or other locally runnable causal models.

---

# DEC-006 — Experiment Before Finalizing Features

**Status:** Accepted

## Context

Many linguistic characteristics have been proposed as possible indicators of machine-generated writing.

Not all will provide useful signal in the target domain.

## Decision

Candidate features will be treated as experimental hypotheses.

Features will only enter the final system after empirical evaluation demonstrates useful incremental value.

## Rationale

This prevents the project from becoming a collection of theoretically plausible metrics with no evidence that they work together.

It also creates a defensible feature-selection narrative.

## Evaluation Dimensions

Feature usefulness may be measured through:

* discrimination
* precision/recall
* F1
* calibration
* hybrid detection
* OOD performance
* ESL false-positive behavior
* computational cost

A feature does not need to improve overall F1 to be useful if it provides meaningful value in another required dimension.

---

# DEC-007 — Separate Global Machine Association from Local Stylistic Anomaly

**Status:** Accepted

## Context

A passage can exhibit machine-associated characteristics without being unusual within an essay.

Conversely, a passage can be stylistically unusual without resembling machine-generated writing.

These represent different phenomena.

## Decision

The detector will maintain two distinct analytical signals:

### Global / Machine Association

How closely the passage resembles the machine-associated training distribution.

### Local / Stylistic Anomaly

How strongly the passage deviates from the surrounding writing.

## Rationale

This distinction is particularly important for hybrid essays.

A polished AI paragraph may not be extreme enough on absolute machine-association features to trigger a global detector, but it may still represent a sharp local shift.

Likewise, a naturally formal human writer may score relatively machine-associated while remaining stylistically consistent throughout the essay.

## Consequences

The final system should preserve both signals through the analysis pipeline and API response.

---

# DEC-008 — Robust Statistics for Local Anomaly Detection

**Status:** Proposed

## Context

A naive local baseline using mean and standard deviation is vulnerable to outliers.

The passage being detected could itself distort the baseline.

## Decision

The initial local-anomaly approach will investigate:

* median
* Median Absolute Deviation (MAD)
* leave-one-out baselines
* local passage windows

## Rationale

Robust statistics reduce sensitivity to extreme observations.

Leave-one-out analysis prevents the target passage from substantially influencing the baseline against which it is evaluated.

## Consequences

The approach requires feasibility testing.

Minimum observation counts and zero-MAD handling must be established experimentally.

---

# DEC-009 — Leave-One-Out Baselines

**Status:** Proposed

## Context

When measuring whether a sentence is anomalous relative to an essay, including the sentence itself in the reference distribution can reduce the apparent magnitude of its deviation.

## Decision

Where sufficient observations exist, the target sentence/passage should be excluded from the baseline used to evaluate it.

## Rationale

This reduces self-contamination.

Example:

```text
S1 S2 S3 S4 S5 S6 S7

Target: S4

Baseline:
S1 S2 S3 S5 S6 S7
```

## Limitation

LOO does not solve the problem of insufficient observations.

Very short essays may require:

* passage-level analysis
* larger local windows
* reduced evidence strength
* abstention

---

# DEC-010 — Passage-Level Analysis Is a First-Class Requirement

**Status:** Accepted

## Context

Sentence-level analysis is valuable for highlighting, but individual sentences may be too short for stable statistical analysis.

Hybrid writing also frequently occurs at paragraph or passage level.

## Decision

The system will support both sentence-level and passage-level analysis.

## Rationale

Passage-level analysis provides:

* more stable statistics
* stronger contextual baselines
* better hybrid detection
* more reliable evidence for short sentences

Sentence-level analysis remains important for UI precision.

---

# DEC-011 — Evidence Sufficiency and Abstention

**Status:** Accepted

## Context

Statistical measurements can become unreliable when there is too little text or context.

Returning a numerical score regardless of evidence availability would create false precision.

## Decision

The detection system must explicitly evaluate evidence sufficiency and support abstention.

## Rationale

A detector that says:

> "Insufficient evidence"

is preferable to one that produces a mathematically unstable score and presents it as authoritative.

## Consequences

The system must define minimum requirements for:

* text length
* token count
* neighboring observations
* feature stability

These thresholds remain experimental.

---

# DEC-012 — Essay-Family Dataset Structure

**Status:** Accepted

## Context

A dataset containing a human essay and AI-generated variants creates strong relationships between documents.

Splitting variants independently would leak topic, vocabulary, narrative structure, and other information across train/test boundaries.

## Decision

The fundamental dataset unit will be an **Essay Family**.

An Essay Family contains:

* source human essay
* AI-generated variants
* AI-polished variants
* AI-spliced variants where available

## Rationale

The family structure makes the relationship between variants explicit and enables leakage-safe splitting.

---

# DEC-013 — Family-Level Train/Validation/Test Splitting

**Status:** Accepted

## Context

Document-level random splitting can place variants of the same source essay in different splits.

## Decision

All documents belonging to the same Essay Family must remain within the same dataset split.

## Correct

```text
Family A → TRAIN

Family B → VALIDATION

Family C → TEST
```

## Incorrect

```text
Family A Human → TRAIN
Family A AI    → TEST
```

## Rationale

This prevents related documents from leaking information across evaluation boundaries.

---

# DEC-014 — Hold Out Unseen Generation Models

**Status:** Proposed

## Context

A detector may learn the fingerprint of specific models instead of general machine-associated characteristics.

## Decision

Where dataset size permits, at least one generation model should be held out from training and validation and used for out-of-distribution evaluation.

## Rationale

This provides a stronger test of generalization.

A significant performance drop is not automatically a failure of the project; it is evidence about the detector's limitations.

---

# DEC-015 — Explicit Topic Holdout

**Status:** Proposed

## Context

A classifier may learn vocabulary or subject matter rather than writing characteristics.

## Decision

Where dataset size permits, a topic cluster should be held out for evaluation.

## Rationale

This tests whether the detector is dependent on topic-specific signals.

---

# DEC-016 — Hybrid Writing as a First-Class Evaluation Case

**Status:** Accepted

## Context

Real-world AI assistance often involves partial editing rather than completely machine-generated essays.

## Decision

The dataset and evaluation process will explicitly include hybrid writing.

At minimum:

* AI-polished human passages
* AI-spliced passages

## Rationale

This directly tests the project's local-anomaly hypothesis.

It also represents a more realistic use case than a binary human-vs-completely-AI dataset alone.

---

# DEC-017 — ESL Bias Audit

**Status:** Accepted

## Context

Statistical writing detectors may disproportionately flag non-native English writing.

## Decision

The project will explicitly evaluate false-positive behavior on an ESL/non-native-English control set where appropriate data is available and permitted for use.

## Rationale

This is both a known risk in the problem domain and an explicit concern in the Callus brief.

## Consequences

The evaluation must report observed behavior rather than assuming the system is unbiased.

---

# DEC-018 — No Test-Set Tuning

**Status:** Accepted

## Context

Repeatedly examining test results and modifying the model creates an effectively contaminated test set.

## Decision

The final test set must not be used to tune:

* features
* thresholds
* classifier hyperparameters
* evidence-sufficiency rules
* calibration

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

## Rationale

This preserves the meaning of the final evaluation.

---

# DEC-019 — Deterministic Evidence Generation

**Status:** Accepted

## Context

The project must explain why a passage was flagged.

Generating explanations by asking a language model to rationalize a classification would introduce a second opaque model into the evidence pipeline.

## Decision

Evidence shown to users must be derived from measured features and the actual analytical outputs.

## Rationale

The explanation should correspond to what the detector actually measured.

For example:

> "This passage has substantially lower perplexity than nearby passages."

is preferable to an LLM-generated statement such as:

> "The writing sounds polished and formal."

---

# DEC-020 — Thin API Layer

**Status:** Accepted

## Context

Business and analytical logic becomes difficult to test and maintain when embedded inside HTTP routes.

## Decision

FastAPI routes will remain thin.

The API layer will handle:

* request validation
* response serialization
* transport-level errors
* orchestration

Detection logic belongs in dedicated analysis services/components.

## Rationale

This keeps the detection engine independently testable and prevents transport code from becoming the architecture.

---

# DEC-021 — Frontend Does Not Implement Detection Logic

**Status:** Accepted

## Context

Duplicating analytical logic between Python and TypeScript would create inconsistent results and make methodology changes difficult.

## Decision

The backend/detection engine is the source of truth for analytical results.

The frontend only renders the structured response.

## Consequences

The frontend should not calculate:

* perplexity
* anomaly scores
* classifier decisions
* feature thresholds

It may calculate presentation-only values where appropriate.

---

# DEC-022 — Local-First Privacy Model

**Status:** Accepted

## Context

Admissions essays can contain sensitive personal information.

External API transmission is unnecessary for the core detection architecture.

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

Experiments will live separately from production detection components.

Experiments may investigate:

* feature usefulness
* model selection
* anomaly stability
* thresholds
* OOD behavior
* bias

Only validated results should be promoted into the production pipeline.

---

# DEC-024 — Hypothesis → Experiment → Result → Decision Workflow

**Status:** Accepted

## Context

The project contains many uncertain methodological assumptions.

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

This prevents the project from presenting theoretical assumptions as empirical facts.

It also creates an auditable research trail.

---

# DEC-025 — Documentation Is Part of the Implementation Process

**Status:** Accepted

## Context

Callus explicitly evaluates communication and documentation.

Documentation written only after implementation often fails to capture the reasoning behind decisions.

## Decision

Documentation should evolve alongside the project.

Important decisions should be documented before or during implementation.

## Consequences

The repository will maintain source-of-truth documents for:

* planning
* architecture
* methodology
* decisions
* dataset
* evaluation
* bias
* failure analysis

---

# DEC-026 — AI-Assisted Development Must Remain Reviewable

**Status:** Accepted

## Context

Callus explicitly permits AI coding tools and expects candidates to use them responsibly.

## Decision

AI tools may be used extensively, but generated code must be reviewed and understood before being retained.

Codex tasks should be bounded by:

* documented requirements
* explicit scope
* acceptance criteria
* verification instructions

## Rationale

The quality of the final repository should not depend on blindly trusting generated code.

The project should remain understandable to its author.

---

# DEC-027 — Feature Selection Must Consider Bias and Generalization

**Status:** Accepted

## Context

A feature may improve aggregate performance while harming generalization or increasing false positives for a specific group.

## Decision

Feature promotion must consider multiple evaluation dimensions.

A feature should not be retained solely because it improves aggregate F1.

## Evaluation considerations

* overall discrimination
* OOD performance
* hybrid detection
* calibration
* ESL false positives
* computational cost
* interpretability

---

# DEC-028 — No Universal Accuracy Claim

**Status:** Accepted

## Context

AI detection performance is highly dependent on:

* dataset
* model family
* prompting
* editing
* topic
* domain
* evaluation protocol

## Decision

The project will report performance within clearly defined evaluation conditions.

It will not claim:

> "The detector can reliably detect AI-generated text."

without qualification.

## Preferred framing

> "On our documented evaluation set, the system achieved X under Y conditions, with the following observed failure modes and limitations."

---

# DEC-029 — Local Generation Interface Must Be Replaceable

**Status:** Accepted

## Context

Local model inference tools such as Ollama are useful for development but should not become architectural dependencies.

## Decision

Dataset generation should interact with a model-generation abstraction rather than directly coupling the dataset pipeline to one application.

## Rationale

This allows:

* Ollama
* direct Transformers inference
* another local runtime

to be substituted without redesigning dataset construction.

---

# DEC-030 — Architecture Changes Must Be Recorded

**Status:** Accepted

## Context

The project is intentionally experiment-driven.

Some proposed ideas will likely be disproven or replaced.

## Decision

When experimental evidence causes a meaningful architectural change:

1. Record the result.
2. Mark the old decision as superseded if appropriate.
3. Add a new decision.
4. Update `ARCHITECTURE.md`.
5. Update `DETECTION-METHODOLOGY.md`.
6. Update affected implementation plans.

## Rationale

The repository should reflect the actual engineering process rather than pretending the final architecture was obvious from the beginning.

---

# Current Decision Summary

## Accepted

* Evidence-first detection framing
* No LLM-as-final-judge
* ₹0 core system
* Global machine association + local stylistic anomaly
* Passage-level analysis
* Evidence sufficiency and abstention
* Essay-family dataset structure
* Family-level dataset splitting
* Hybrid writing evaluation
* ESL bias audit
* No test-set tuning
* Deterministic evidence generation
* Thin API
* Backend as analytical source of truth
* Local-first privacy model
* Experiment/production separation
* Hypothesis → Experiment → Result → Decision workflow
* Documentation-first development
* Reviewable AI-assisted development
* Multi-dimensional feature evaluation
* No universal accuracy claims
* Replaceable local generation interface
* Recorded architecture evolution

## Proposed / Experimental

* Exact perplexity model
* Local generation model(s)
* LOO Median/MAD formulation
* Local window size
* Exact feature set
* Logistic Regression vs Random Forest
* Probability calibration
* Minimum text length
* Evidence-sufficiency thresholds
* Final decision thresholds
* Feature attribution method
* Topic/model holdout configuration

---

# Next Decision Review

The next major decisions should be made only after Phase 1 feasibility experiments.

Expected decisions include:

1. Perplexity model selection.
2. Feature set promotion/rejection.
3. Local anomaly formulation.
4. Minimum evidence requirements.
5. Classifier selection.
6. Calibration strategy.
7. Passage-window strategy.

Until those experiments are complete, the above items remain intentionally unresolved.
