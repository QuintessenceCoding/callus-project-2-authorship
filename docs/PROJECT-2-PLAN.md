# Project 2 Plan — Evidence-First Authorship Analysis

## 1. Project Overview

Callus Project 2 requires a working application that analyzes college admissions essays for characteristics associated with machine-generated text.

The project is implemented as an evidence-first statistical analysis system rather than an LLM-as-judge application.

The current application provides:

* document-level classification using an experimentally validated four-feature model
* visible feature evidence supporting the classification
* sentence-level perplexity measurements exposed as evidence exemplars
* evidence-sufficiency abstention when the complete production feature vector cannot be computed reliably
* a real web interface
* honest evaluation and explicit failure/limitation reporting

The system must not simply send an essay to a chat model and relay the model's judgment.

The production classifier is the four-feature Logistic Regression model validated in EXP-006. A local `distilgpt2` model is used as an instrument for perplexity extraction; it does not make the final classification decision.

---

## 2. Problem Definition

The system cannot directly observe who authored a piece of text.

Instead, it estimates whether the submitted document exhibits measurable characteristics associated with machine-generated writing within the project's training and evaluation distributions.

The production assessment is made at the **document level**. Sentence-level measurements are retained for evidence presentation, but they are not treated as sentence-level authorship judgments.

The system therefore makes no definitive claim that a person or model authored the text.

### Core system claim

> The system estimates whether a document exhibits measurable characteristics associated with machine-generated writing in the evaluated distribution, then exposes the underlying feature evidence and uncertainty without claiming definitive authorship.

This distinction is fundamental to the architecture, UI, evaluation methodology, and documentation.

---

## 3. Target Domain

The target domain is:

**College admissions essays**

The intended target characteristics include:

* approximately 500–1000 words in the normal use case
* narrative or reflective writing
* highly edited prose
* personal experiences and anecdotes
* relatively formal but individual writing styles

The detector is not intended to automatically generalize to unrelated domains such as:

* academic research papers
* social media posts
* creative fiction
* news articles
* short-form responses

Domain limitations must remain visible in the evaluation and final presentation.

The production classifier was developed on a controlled external student-writing / AI-writing dataset rather than a large representative admissions corpus. Admissions-domain generalization is therefore a stated limitation rather than an assumption.

---

## 4. Core Design Principles

### 4.1 Evidence Over Verdict

The system should show measurable evidence rather than provide an unexplained AI verdict.

A classification must be traceable to observable feature values and the validated classifier.

---

### 4.2 Uncertainty Over False Precision

The system must not manufacture precise-looking probabilities when the underlying evidence is weak or unavailable.

The production API therefore supports an explicit `insufficient_evidence` state.

A classification is produced only when the complete four-feature vector required by the production Logistic Regression model is available.

The displayed classifier probability is treated as a **model signal for machine association within the evaluated distribution**, not as calibrated authorship certainty.

---

### 4.3 Document Classification + Evidence Presentation

The project deliberately separates two questions:

**Document-level machine association**

> How closely does the document's measured feature vector resemble the machine-associated distribution learned by the classifier?

**Evidence presentation**

> Where are the directly measurable sentence-level patterns that a user can inspect when interpreting the document-level result?

The production system does **not** claim that a highlighted sentence was written by AI.

The current Evidence Inspector exposes sentence-level perplexity exemplars because perplexity is currently available as a validated sentence-level measurement. The other three production features are document-level statistics and are not artificially converted into sentence-level scores.

---

### 4.4 Experiment Before Promotion

Candidate features and localization methods are hypotheses, not assumptions.

A feature or analytical method enters production only after empirical evaluation demonstrates that its behavior is useful and defensible.

Evaluation considers more than aggregate F1, including where relevant:

* precision
* recall
* F1
* ROC-AUC
* reproducibility
* hybrid-writing behavior
* false-positive behavior
* ESL/non-native-English behavior
* domain/model generalization
* evidence sufficiency
* computational cost

---

### 4.5 Reproducibility

The core project must be reproducible without paid services.

Experiments and production artifacts record, where applicable:

* dataset/version provenance
* feature configuration
* model configuration
* random seeds
* train/validation split
* evaluation configuration
* software/model versions
* model artifact metadata

---

### 4.6 Honest Failure Reporting

Failure is an expected property of this problem.

The final evaluation will explicitly identify and document:

* confidently incorrect predictions
* false positives
* false negatives
* hybrid-writing failures
* domain/model generalization limitations
* potential ESL bias
* cases where evidence is insufficient

The final submission must include at least three confidently incorrect essays and an explanation of why they failed, as required by Callus.

---

## 5. Callus Requirements

The final project must satisfy the following requirements from the challenge brief.

### Functional

* Accept a college admissions essay through a real interface.
* Perform document-level classification using experimentally validated statistical features.
* Provide visible evidence supporting the document-level classification.
* Provide sentence-level evidence exemplars where a validated local measurement exists.
* Show why the classifier can reach its document-level result through measurable feature evidence.
* Communicate uncertainty and abstain when required measurements are unavailable.
* Avoid claiming definitive sentence-level AI authorship.

### Research / ML

* Do not use an LLM as the final judge.
* Use measurable linguistic/statistical signals.
* Build and document dataset provenance and limitations.
* Evaluate the detector honestly on held-out data and specialized audit sets.
* Report three confident failures.
* Investigate ESL/non-native-English false positives.

### Engineering

* Maintain clean separation between feature extraction, detection, API, and presentation.
* Document architectural and methodological decisions.
* Provide reproducible setup and execution instructions.
* Keep implementation understandable and defensible.

---

## 6. Non-Goals

The project does not attempt to:

* prove definitive authorship
* determine whether a person committed academic misconduct
* achieve universal AI detection
* guarantee a specific accuracy percentage
* detect every existing or future language model
* identify the exact model that generated text
* assign definitive authorship to individual sentences
* create a sentence-level AI probability that has not been experimentally validated
* use an LLM to make or override the final detector decision
* replace human review
* become a production-scale cloud service

The target is a technically credible, transparent research prototype.

---

## 7. Cost and Resource Constraints

### Zero-Cost Requirement

The complete core project must be buildable, runnable, evaluated, and demonstrated at **₹0**.

No paid API or proprietary detection service is required by the core system.

The production detector uses local inference and local model artifacts.

### Model and Dataset Licensing

"Free" does not automatically mean unrestricted.

For every external model or dataset used, documentation should record:

* source
* license or usage terms
* intended use
* whether redistribution is permitted
* relevant restrictions

---

## 8. Compute Constraint

The detection pipeline must run locally on consumer hardware.

The production perplexity instrument is:

* model: `distilgpt2`
* runtime: Hugging Face Transformers
* device: CPU

The production classifier is:

* preprocessing: `StandardScaler`
* classifier: `LogisticRegression`
* source experiment: EXP-006

For dataset generation, the project used a separate locally runnable generation pipeline. The current generation protocol records `Qwen/Qwen2.5-0.5B-Instruct` as the selected generation candidate after EXP-003 feasibility testing.

The generation model and detection model remain conceptually separate: the generation model produces controlled synthetic variants for research, while `distilgpt2` supplies the perplexity instrument used by the detector.

---

## 9. Production Architecture

The implemented production architecture is:

```text
                           ESSAY
                             │
                             ▼
                    Sentence Segmentation
                             │
                             ▼
                     Feature Extraction
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
      Perplexity       Sentence Length       MATTR
          │                  CV                  │
          └──────────────────┬──────────────────┘
                             │
                         POS 3-gram
                           Entropy
                             │
                             ▼
                   Complete Feature Vector?
                        │              │
                       No             Yes
                        │              │
                        ▼              ▼
                 Insufficient      StandardScaler
                   Evidence            │
                                        ▼
                               Logistic Regression
                                        │
                                        ▼
                              Document Classification
                                        │
                                        ▼
                               Structured Evidence
                                        │
                              ┌─────────┴─────────┐
                              ▼                   ▼
                       FastAPI Response     Evidence Inspector
                                                  │
                                                  ▼
                                             React / Vite UI
```

The frontend is implemented with React + Vite + TypeScript. The backend is implemented with FastAPI.

The API route is:

```text
POST /api/analyze
```

The route remains thin; feature extraction and classification are handled by the detector layer.

---

## 10. Production Feature Set

The final production feature vector is fixed to the four features validated through the experiment sequence:

1. **Perplexity** — language-model predictability.
2. **Sentence-length coefficient of variation** — document-level sentence rhythm variability.
3. **MATTR** — moving-average lexical diversity.
4. **POS 3-gram entropy** — variation in grammatical-tag sequences.

The four-feature order is fixed and recorded in the model artifact metadata.

The production extractor reuses the validated EXP-001 / EXP-004 feature mathematics rather than introducing new formulas during integration.

### 10.1 Perplexity

Perplexity is calculated sentence-by-sentence using the locally run causal language model and aggregated for the document using the median of valid sentence perplexities.

Lower perplexity indicates greater predictability under the language model.

However:

> **Low perplexity does not imply AI authorship.**

The sentence-level values are retained for evidence inspection, while the document-level aggregate is used as one input to the classifier.

### 10.2 Sentence-Length CV

Sentence-length CV is calculated across the document's sentence lengths.

It is a document-level rhythm statistic. The production implementation does not treat it as an independent per-sentence AI score.

### 10.3 MATTR

MATTR measures lexical diversity using a fixed moving window.

The production model uses MATTR as a document-level feature.

### 10.4 POS 3-Gram Entropy

POS 3-gram entropy measures variation in part-of-speech tag sequences.

The production model uses it as a document-level structural feature.

---

## 11. Rejected Local Attribution Approaches

The original project plan included explicit stylistic-anomaly and local attribution methods.

These were investigated rather than assumed to work.

### EXP-007 — Local Anomaly

Initial local anomaly scoring was tested for sentence/passage localization.

### EXP-008 — Local Sensitivity

Feature and window sensitivity were tested to determine whether local anomaly behavior could be made more stable.

### EXP-009 — Boundary Discontinuity

Boundary-based comparisons were evaluated around known hybrid insertion boundaries.

### EXP-011 — Leave-One-Sentence-Out Attribution

The production four-feature model was used in a leave-one-sentence-out contribution analysis on 20 controlled hybrids.

The experiment achieved:

* top-10% capture of known AI sentences: `22.5%`
* top-25% capture: `42.5%`
* median AI-vs-human sentence contribution difference: approximately `0.000982`

The result was judged insufficient for reliable sentence-level authorship attribution.

### Decision

These local attribution methods are **not used as production sentence-level verdicts**.

The final interface instead uses the validated global classifier plus evidence presentation based on directly measured sentence-level perplexity.

This prevents the UI from displaying a scientifically unsupported "AI sentence" heatmap.

---

## 12. Evidence Sufficiency and Abstention

Not every input supports all four production measurements.

The detector therefore checks whether the complete four-feature vector is available before classification.

Examples of insufficient evidence include:

* too few sentences for sentence-length CV
* too few lexical tokens for the MATTR window
* unavailable perplexity measurements
* language-model context violations
* other missing required feature values

### Short input

For example, `I like school.` does not provide enough evidence for all four production features and therefore produces:

```text
state: insufficient_evidence
```

### Long single-sentence input

The production language model has a 1024-token context limit.

A single sentence that exceeds that context is not truncated silently. Perplexity is marked unavailable with:

```text
sentence_exceeds_language_model_context
```

The detector then abstains rather than crashing or inventing a substitute measurement.

### Production rule

The current abstention behavior is intentionally simple:

> **No complete four-feature vector → no document classification.**

This preserves the validated feature definitions and follows the conclusions of EXP-010.

No unsupported universal word-count threshold is claimed.

---

## 13. Dataset Strategy

The project uses a controlled, provenance-aware dataset strategy with family relationships preserved for hybrid experiments and leakage prevention.

The project distinguishes between:

* controlled development/training data
* external validation data
* hybrid-writing experiments
* target-domain proxy/evaluation data
* ESL/non-native-English audit data

The production Logistic Regression artifact used for the current application was trained from the feature-distribution results associated with the DAIGT External dataset and EXP-005 / EXP-006.

PERSUADE and other human-writing sources are used as documented evaluation/proxy material where applicable; they are not treated as interchangeable with the target admissions domain.

### Essay Families

An Essay Family represents a human source essay and controlled variants derived from it.

```text
Essay Family
├── Human original
├── AI-generated variant
├── AI-polished variant
└── AI-spliced variant
```

The family relationship is retained in metadata so related variants are not split across training and evaluation boundaries.

---

## 14. Dataset Categories

### Human

Original human-authored essays used as the human baseline and evaluation material.

### AI

Machine-generated essays used as the machine-associated baseline.

### Hybrid — Polished

Human essays in which selected passages are transformed by a local generation model while preserving the underlying ideas, facts, and narrative.

### Hybrid — Spliced

Human essays containing selected machine-generated replacement passages with known ground-truth locations.

### ESL / Non-Native-English Control

Human writing reserved for the explicit false-positive/bias audit.

These categories are analytical labels. They do not imply that the detector will distinguish them perfectly.

---

## 15. Essay-Family Leakage Prevention

Dataset splitting must occur at the **Essay Family level**, not the individual-document level.

For example:

```text
CORRECT

Family A → TRAIN
  ├── Human
  ├── AI
  └── Hybrid

Family B → VALIDATION / TEST
  ├── Human
  ├── AI
  └── Hybrid
```

The following is prohibited:

```text
INCORRECT

Human Family A → TRAIN
AI Family A    → TEST
```

because variants derived from the same source essay can leak topic, vocabulary, narrative structure, and other information across splits.

---

## 16. Evaluation Strategy

Evaluation is treated as a separate phase from production implementation.

The experiment sequence has already established the production baseline and feature set.

### Completed core evaluation

EXP-006 established the production four-feature Logistic Regression baseline:

```text
Accuracy   0.974684
Precision  0.952381
Recall     1.000000
F1         0.975610
ROC-AUC    0.995513
```

These metrics are specific to the recorded held-out evaluation setup and must not be presented as universal admissions-domain accuracy.

### Completed methodology evaluation

The completed experiment sequence includes:

* local perplexity feasibility
* perplexity stability
* candidate feature validation
* feature distribution analysis
* four-feature baseline classification
* local anomaly testing
* local sensitivity testing
* boundary discontinuity testing
* evidence-sufficiency analysis
* passage-attribution feasibility testing

### Remaining final evaluation

Before submission, the project still needs:

* three confidently incorrect essays with explanations
* an explicit ESL/non-native-English bias audit
* final evaluation summary tied to the actual test/evaluation sets
* final limitation reporting

These remaining evaluations must not be hidden merely because the production prototype is already functional.

---

## 17. Evaluation Leakage Prevention

Final test data must not be used to repeatedly tune the classifier after the evaluation is locked.

The intended workflow is:

```text
TRAIN
  ↓
VALIDATION / EXPERIMENTS
  ↓
Model and feature decisions
  ↓
LOCK PRODUCTION ARTIFACT
  ↓
FINAL EVALUATION
  ↓
Report
```

Exploratory debugging performed after a test result must be documented and should not be presented as an untouched final estimate.

---

## 18. Failure Analysis

The final project must include at least three confidently incorrect essays.

For each failure, document:

* input category
* predicted category
* model signal
* feature values
* evidence availability
* likely reason for the failure
* whether the failure reflects domain shift, model dependence, or feature overlap
* potential mitigation
* whether mitigation was implemented or intentionally left unresolved

The goal is understanding rather than hiding failure.

---

## 19. Bias Analysis

The project will explicitly investigate potential false positives associated with ESL/non-native-English writing.

The analysis must remain empirical and must not assume that ESL writing has a single statistical style.

Where data permits, compare:

* general-human false-positive behavior
* ESL/control false-positive behavior
* model-signal distributions
* feature distributions
* representative failure cases

Any observed limitation will be documented rather than concealed.

---

## 20. UI Requirements

The essay itself is the primary interface.

The UI should avoid presenting an unexplained overall percentage as the central result.

### Essay View

The interface provides:

* original essay text
* readable document view
* input statistics
* classification state
* evidence-linked sentence exemplars where available

### Evidence Inspector

The current Evidence Inspector exposes **sentence-level perplexity evidence**.

It should communicate:

* which sentence is being shown
* its measured perplexity
* why that measurement is relevant
* that the sentence is an evidence exemplar, not an authorship verdict

Preferred wording:

> **These passages show the strongest predictability measurements in this document.**

Avoid wording such as:

> "This sentence was written by AI."

### Document-Level Feature Evidence

The UI also exposes all four production features:

* Perplexity
* Sentence-length CV
* MATTR
* POS 3-gram entropy

The three document-level features are explained as document-level statistics rather than being forced into unsupported sentence-level highlights.

### Uncertainty

The UI clearly communicates:

* insufficient evidence
* unavailable feature measurements
* model signal not evaluated when the classifier abstains
* the difference between evidence and authorship proof

---

## 21. API and Evidence Contract

The production API is:

```text
POST /api/analyze
```

The structured response contains:

* `state`
* `label` when classified
* `ai_probability` as a model signal when classified
* four feature measurements
* `sentence_evidence`
* text statistics
* model metadata

`sentence_evidence` currently contains:

* `sentence_id`
* sentence text
* sentence perplexity when available
* availability state
* unavailable-measurement reason

This field is intended for evidence presentation and does not imply sentence-level classification.

---

## 22. Documentation Strategy

Documentation is part of the engineering process, not a final submission task.

The repository maintains source-of-truth documents covering:

```text
docs/
├── PROJECT-2-PLAN.md
├── ARCHITECTURE.md
├── DETECTION-METHODOLOGY.md
├── DECISIONS.md
├── DATASET.md
├── EVALUATION.md
├── EXPERIMENT-LOG.md
├── GENERATION-PROTOCOL.md
└── PRODUCTION-MILESTONE.md
```

Additional documents may be added for final failure analysis, bias analysis, setup instructions, or submission materials.

Documents should describe the implemented system and record important rejected approaches rather than preserving obsolete design claims as if they were production behavior.

---

## 23. AI-Assisted Development Process

AI coding tools were used for bounded implementation tasks and were reviewed against the project's source-of-truth documentation and tests.

Each implementation slice follows:

```text
Plan
  ↓
Implement
  ↓
Test
  ↓
Review
  ↓
Document result
  ↓
Next slice
```

AI-generated implementation must be understood and verified before being retained.

The project does not depend on an AI coding tool being available at runtime.

---

## 24. Execution Phases

### Phase 0 — Project Foundation

**Status: Completed**

* repository setup
* documentation foundation
* architecture and methodology planning
* decision log

### Phase 1 — Research & Feasibility

**Status: Completed**

Validated through EXP-001 through EXP-011:

* local perplexity extraction
* feature extraction
* feature distribution behavior
* four-feature classification
* local anomaly feasibility
* boundary/local sensitivity behavior
* evidence sufficiency
* passage-attribution feasibility

### Phase 2 — Dataset Construction

**Status: Substantially completed for the current production baseline**

* source and provenance documentation
* controlled human/AI data
* feature-distribution dataset
* pair-aware splitting
* hybrid experiment material
* supporting evaluation/proxy sources

Specialized ESL and final failure-analysis datasets remain part of the final evaluation phase.

### Phase 3 — Detection Engine

**Status: Completed**

* four-feature extraction
* production Logistic Regression artifact
* model loading
* evidence sufficiency behavior
* context-limit robustness
* sentence-level perplexity evidence extraction

### Phase 4 — API

**Status: Completed**

* FastAPI service
* `/api/analyze`
* request validation
* typed response schema
* sentence evidence contract
* backend test coverage

### Phase 5 — UI

**Status: Core implementation completed; final polish pending**

* essay input
* analysis state
* feature evidence
* Evidence Inspector
* document view
* uncertainty states
* editorial/brutalist visual direction

Final copy/interaction polish may still be performed.

### Phase 6 — Final Evaluation

**Status: Pending**

* final evaluation summary
* three confident failures
* ESL bias audit
* final limitations

### Phase 7 — Submission / Demo Polish

**Status: Pending**

* documentation synchronization
* final screenshots/demo flow
* README/setup instructions
* AI-tool disclosure where required
* repository cleanup
* final end-to-end verification
* presentation/viva preparation

---

## 25. Known Risks and Current Disposition

### Dataset Leakage

Paired variants can leak source-specific information if split incorrectly.

**Mitigation:** family-level splitting and provenance metadata.

### Model Overfitting

The classifier may learn the statistical fingerprint of the evaluated generation/data distribution.

**Mitigation:** document the evaluated distribution, avoid universal accuracy claims, and perform specialized evaluations where feasible.

### Topic / Domain Overfitting

The detector may rely partly on topic or writing-domain characteristics.

**Mitigation:** paired data, external/proxy evaluation, and explicit admissions-domain limitation reporting.

### Short-Text Instability

Very short text can make required features unavailable or unstable.

**Mitigation:** evidence-sufficiency abstention and feature-availability reporting.

### Language-Model Context Limit

A single sentence can exceed the context supported by the perplexity model.

**Mitigation:** detect context overflow before inference and abstain rather than truncate or crash.

### Local Attribution Instability

The experimental local anomaly and leave-one-out approaches were not sufficiently reliable for production sentence-level authorship claims.

**Disposition:** rejected for production. The UI uses measured evidence exemplars instead.

### ESL False Positives

Some detector features may correlate with English-learning background.

**Disposition:** explicit audit required before final submission.

### Computational Cost

Repeated local language-model inference can be expensive on CPU.

**Mitigation:** small local model, sentence-level inference, structured feature reuse, and avoidance of unnecessary repeated attribution passes in production.

---

## 26. Remaining Questions Before Submission

The original research-loop questions have been narrowed to the remaining submission requirements.

1. What are the three most informative confident failures, and why did they fail?
2. Does the bounded ESL audit reveal elevated false-positive behavior?
3. What final evaluation metrics should be reported for each evaluated distribution?
4. Is the Evidence Inspector wording sufficiently clear that users understand it as evidence rather than authorship attribution?
5. Are the repository setup instructions sufficient for another engineer to reproduce the application?

No new feature-selection or localization research should be started unless a concrete blocker appears in final evaluation or integration testing.

---

## 27. Success Criteria

The project is successful if it produces a working application that:

* accepts college admissions-style essay text through a real interface
* performs document-level classification using validated measurable features
* provides transparent feature evidence
* provides sentence-level perplexity exemplars without claiming sentence-level authorship
* communicates uncertainty and abstains when the required evidence is unavailable
* uses a local language model as an instrument rather than as the final judge
* uses a documented and reproducible model artifact
* has documented dataset provenance and limitations
* reports evaluation results with the conditions under which they were measured
* documents at least three confident failures
* investigates ESL/non-native-English false positives
* has clean, understandable engineering structure
* provides documentation that allows another engineer to understand and reproduce the system

The project does **not** require perfect AI detection.

The quality of the methodology, engineering decisions, evidence presentation, documentation, and honesty about limitations are part of the deliverable.

---

## 28. Current Status

**Production milestone:** Completed

**Core detector:** Completed

**Backend/API:** Completed and tested

**Frontend:** Core Evidence Inspector implementation completed; final UI polish pending

**Experiments:** EXP-001 through EXP-011 completed

**Remaining work:**

1. Synchronize the remaining documentation with the implemented production architecture.
2. Run and document the final confident-failure analysis.
3. Run and document the ESL/non-native-English audit.
4. Perform final end-to-end testing and submission polish.
5. Prepare demo/viva materials and repository setup instructions.

The production architecture and four-feature model are now locked unless final evaluation exposes a concrete correctness issue. Further work should focus on evaluation, robustness, transparency, and presentation rather than reopening the feature-selection research loop.
