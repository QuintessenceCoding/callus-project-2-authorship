# Project 2 Plan — Evidence-First Authorship Analysis

## 1. Project Overview

Callus Project 2 requires a working application that analyzes college admissions essays for characteristics associated with machine-generated text.

The application must provide:

* sentence-level analysis
* passage-level analysis
* visible evidence supporting classifications
* uncertainty when evidence is weak or conflicting
* a real user interface
* honest evaluation and documented failure cases

The system must not simply send an essay to a chat model and relay the model's judgment.

This project therefore treats AI detection as an **evidence-based statistical analysis problem**, rather than a definitive authorship-classification problem.

---

## 2. Problem Definition

The system cannot directly observe who authored a piece of text.

Instead, it estimates whether individual sentences and passages exhibit **measurable characteristics associated with machine-generated text**, while also identifying stylistic anomalies and communicating uncertainty.

The system therefore makes no definitive claim that a person or model authored a passage.

### Core system claim

> The system estimates whether individual sentences and passages exhibit measurable characteristics associated with machine-generated text, while identifying stylistic anomalies and communicating uncertainty rather than claiming definitive authorship.

This distinction is fundamental to the architecture, UI, evaluation methodology, and documentation.

---

## 3. Target Domain

The target domain is:

**College admissions essays**

The expected characteristics of this domain include:

* approximately 500–1000 words
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

Domain limitations will be documented and evaluated explicitly.

---

## 4. Core Design Principles

### 4.1 Evidence Over Verdict

The system should show measurable evidence rather than provide an unexplained AI verdict.

A classification must be traceable to observable features.

---

### 4.2 Uncertainty Over False Precision

The system must not manufacture precise-looking probabilities when the underlying evidence is weak.

If evidence is:

* insufficient
* internally conflicting
* statistically unstable
* based on too little text

the system should be able to abstain or report an uncertain result.

---

### 4.3 Global + Local Analysis

The detector evaluates two different questions.

**Machine Association**

> How closely does this passage's measured behavior resemble machine-associated writing in the training distribution?

**Stylistic Anomaly**

> How strongly does this passage differ from the surrounding writing in the same essay?

These signals must remain conceptually separate.

A passage can resemble machine-generated writing without being unusual relative to the rest of the essay, and a passage can be stylistically unusual without resembling machine-generated text.

---

### 4.4 Experiment Before Promotion

Candidate features are hypotheses, not assumptions.

A feature should not enter the final detection system merely because it appears in existing AI-detection literature.

Candidate features must be experimentally evaluated for incremental value.

Evaluation should consider more than aggregate F1, including where relevant:

* precision
* recall
* calibration
* hybrid-writing detection
* false-positive behavior
* ESL/non-native-English behavior
* robustness to unseen topics
* robustness to unseen generation models

---

### 4.5 Reproducibility

The core project must be reproducible without paid services.

Experiments should record:

* dataset version
* feature configuration
* model configuration
* random seeds where applicable
* train/validation/test split
* evaluation configuration
* relevant software/model versions

---

### 4.6 Honest Failure Reporting

Failure is an expected property of this problem.

The project will deliberately identify and document:

* confidently incorrect predictions
* false positives
* false negatives
* hybrid-writing failures
* domain/model generalization failures
* potential ESL bias

The final evaluation must include at least three confidently incorrect essays as required by Callus.

---

## 5. Callus Requirements

The final project must satisfy the following requirements from the challenge brief.

### Functional

* Accept a college admissions essay through a real interface.
* Analyze text at sentence and passage levels.
* Highlight passages exhibiting machine-associated characteristics.
* Show measurable evidence for highlighted passages.
* Communicate uncertainty.
* Provide passage-level and overall assessment.

### Research / ML

* Do not use an LLM as the final judge.
* Build the detection methodology from measurable signals.
* Construct and document a dataset.
* Evaluate the detector honestly.
* Investigate ESL/non-native-English false positives.

### Engineering

* Maintain clean project structure.
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
* detect every possible adversarial evasion technique
* replace human review
* become a production-scale cloud service

The target is a technically credible, transparent research prototype.

---

## 7. Cost and Resource Constraints

### Zero-Cost Requirement

The complete project must be buildable, runnable, evaluated, and demonstrated at **₹0**.

No paid service may be required by the core system.

This includes:

* LLM APIs
* embedding APIs
* proprietary detection APIs
* paid datasets
* paid inference services
* paid hosting
* paid observability services

The project should rely on locally runnable software and publicly accessible data with appropriate usage rights.

### Model and Dataset Licensing

"Free" does not automatically mean "open source" or unrestricted.

For every external model or dataset used, documentation should record:

* source
* license or usage terms
* intended use
* whether redistribution is permitted
* any relevant restrictions

---

## 8. Compute Constraint

The detection pipeline must be capable of running locally on consumer hardware.

Small language models should be preferred for token-probability/perplexity extraction.

Potential candidates include:

* DistilGPT-2
* GPT-2
* other small locally runnable causal language models

The final model will be selected through a feasibility experiment rather than assumed in advance.

AI-text generation for dataset construction may use locally runnable quantized open-weight models through a local inference interface such as Ollama or another equivalent mechanism.

The generation interface must remain replaceable; the project should not depend architecturally on one local inference application.

If local generation limits dataset size, experimental quality and controlled paired design take priority over arbitrary dataset volume.

---

## 9. Conceptual Architecture

```text
                         ESSAY
                           │
                           ▼
                 Sentence / Passage
                    Segmentation
                           │
                           ▼
                  Feature Extraction
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
      Machine Association        Stylistic Anomaly
          Analysis                    Analysis
              │                         │
              ▼                         ▼
       Global Signal             Local Signal
              │                         │
              └────────────┬────────────┘
                           ▼
                  Evidence Sufficiency
                           │
                    ┌──────┴──────┐
                    ▼             ▼
              Classification    Abstention
                    │             │
                    └──────┬──────┘
                           ▼
                     Evidence Layer
                           │
                           ▼
                       Web UI
```

The architecture is conceptual at this stage.

Implementation details may change as feasibility experiments provide evidence.

---

## 10. Machine Association Analysis

The global analysis estimates how closely a passage resembles the machine-associated writing distribution learned from training data.

Candidate signals include:

### Predictability

* sentence/passsage perplexity
* mean token log probability
* perplexity variation

### Rhythm

* sentence length
* sentence length coefficient of variation
* punctuation distribution
* clause-related statistics

### Lexical characteristics

* MATTR
* rare-word proportion
* repetition
* repeated n-grams or constructions

### Structural characteristics

* POS n-gram entropy
* dependency-based statistics
* syntactic variation

These are candidate features only.

No feature is guaranteed to appear in the final model.

---

## 11. Stylistic Anomaly Analysis

The local analysis measures how unusual a sentence or passage is relative to the surrounding essay.

The initial statistical direction is:

* robust statistics
* Median / Median Absolute Deviation
* leave-one-out baselines
* local passage windows

The system should avoid allowing the passage being evaluated to substantially distort its own baseline.

For sentence-level analysis, a leave-one-out strategy may be used where sufficient surrounding observations exist.

For passage-level analysis, surrounding sentences or passages may be used as the reference window.

Exact statistical formulation and thresholds remain experimental questions.

No fixed anomaly threshold will be assumed without validation.

---

## 12. Evidence Sufficiency

Not every text segment contains enough information to support a meaningful analysis.

The system must therefore evaluate whether sufficient evidence exists before producing a strong classification.

Potential causes of insufficient evidence include:

* very short sentences
* very short passages
* insufficient neighboring text
* unstable variance estimates
* conflicting feature signals
* missing feature values

Possible outputs include:

* sufficient evidence
* limited evidence
* uncertain
* insufficient evidence

The exact thresholds will be determined experimentally.

---

## 13. Dataset Strategy

The dataset will be organized around **Essay Families**.

An Essay Family represents a source essay and controlled variants derived from it.

Conceptually:

```text
Essay Family
├── Human original
├── AI-generated variant(s)
├── AI-polished variant(s)
└── AI-spliced variant(s)
```

The purpose is to control topic and narrative content while allowing writing characteristics to vary.

### Why paired data?

If all human essays discuss one set of topics and all AI essays discuss another, the classifier may learn topic differences rather than authorship-related characteristics.

Paired construction reduces this risk by keeping the underlying prompt/topic/narrative more comparable.

---

## 14. Dataset Categories

The planned dataset categories are:

### Human

Original human-authored admissions/student essays.

### AI

AI-generated variants based on controlled prompts or source-essay constraints.

### Hybrid — Polished

Human-written essays in which selected passages are substantially revised or polished by a local language model.

### Hybrid — Spliced

Human essays in which selected passages are replaced with newly generated machine text.

### ESL / Non-Native-English Control

Human-written essays used to investigate whether the detector disproportionately flags writing associated with English-learning backgrounds.

The exact dataset size will be determined after source availability and local-generation feasibility are established.

---

## 15. Essay-Family Leakage Prevention

Dataset splitting must occur at the **Essay Family level**, never at the individual-document level.

For example:

```text
CORRECT

Family A → TRAIN
  ├── Human
  ├── AI
  └── Hybrid

Family B → TEST
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

because variants derived from the same source essay can leak topic, vocabulary, narrative structure, and stylistic information across splits.

---

## 16. Evaluation Strategy

Evaluation will contain multiple experiments rather than relying on one aggregate accuracy value.

### Baseline 1 — Majority / Always-Human

A deliberately simple baseline used to establish a lower bound.

### Baseline 2 — Perplexity Threshold

A simple detector based primarily on language-model predictability.

### Experimental Model

A classifier combining selected linguistic/statistical features.

### Ablation

Candidate features will be added or removed to determine their incremental value.

### Topic Holdout

Evaluate performance on a topic distribution not represented in training.

### Model Holdout

Evaluate performance on machine-generated text from a generation model not represented in training, where feasible.

### Hybrid Evaluation

Measure performance on:

* AI-polished passages
* AI-spliced passages
* potentially human-edited AI text if time permits

### Bias Evaluation

Evaluate false-positive behavior on the ESL/non-native-English control set.

---

## 17. Evaluation Leakage Prevention

Final test data must not be used to tune:

* feature selection
* thresholds
* classifier hyperparameters
* evidence-sufficiency rules
* interpretation boundaries

The intended workflow is:

```text
TRAIN
  ↓
VALIDATION
  ↓
Model / feature / threshold decisions
  ↓
LOCK
  ↓
FINAL TEST
  ↓
Report
```

The final test set should represent an evaluation of the completed methodology rather than an additional tuning set.

---

## 18. Failure Analysis

The final project will include at least three essays that the detector confidently classifies incorrectly.

For each failure, document:

* input category
* predicted category
* confidence/evidence strength
* relevant feature values
* why the prediction may have occurred
* whether the failure represents a known limitation
* potential mitigation
* whether mitigation was implemented or intentionally left unresolved

The goal is understanding, not hiding failure.

---

## 19. Bias Analysis

The project will explicitly investigate potential false positives associated with ESL/non-native-English writing.

The analysis will avoid assuming that ESL writing necessarily has particular characteristics.

Instead, the project will formulate this as an empirical hypothesis:

> Some features used by the detector may correlate with English-learning background and therefore increase false-positive rates.

Where data permits, compare:

* overall human false-positive rate
* ESL/control false-positive rate
* feature-level differences
* evidence-strength distributions

Any observed limitation will be documented rather than concealed.

---

## 20. UI Requirements

The essay itself should be the primary interface.

The UI should avoid presenting an unexplained overall percentage as the central result.

The interface should provide:

### Essay view

* original essay text
* sentence/passage highlighting
* clear distinction between normal, machine-associated, and uncertain regions

### Evidence view

When a passage is selected:

* machine-association signal
* stylistic anomaly signal
* evidence sufficiency
* driving feature values
* concise explanation of the interpretation

### Uncertainty

The UI must clearly communicate when:

* evidence is insufficient
* signals conflict
* the passage is too short
* the result is uncertain

The UI should explicitly distinguish:

> **Evidence of machine-associated characteristics**

from:

> **Proof of AI authorship**

---

## 21. Documentation Strategy

Documentation is part of the engineering process, not a final submission task.

The repository will maintain source-of-truth documents covering:

```text
docs/
├── PROJECT-2-PLAN.md
├── ARCHITECTURE.md
├── DETECTION-METHODOLOGY.md
├── DECISIONS.md
├── DATASET.md
├── EVALUATION.md
├── BIAS-ANALYSIS.md
└── FAILURE-ANALYSIS.md
```

Additional experiment documentation may be created as needed.

Documents should evolve alongside implementation.

Decisions should be recorded before or during implementation rather than reconstructed after the fact.

---

## 22. Codex Development Process

AI coding tools are explicitly permitted by Callus.

However, the project will use AI-assisted development through bounded, reviewable tasks.

Codex should receive:

1. Context
2. Current project state
3. Relevant source-of-truth documentation
4. Specific objective
5. Requirements
6. Constraints
7. Acceptance criteria
8. Verification instructions
9. Documentation-update requirements

Large "build the entire application" prompts should be avoided.

Each implementation slice should be:

```text
Plan
  ↓
Document
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

AI-generated implementation must be reviewed and understood before being retained.

---

## 23. Execution Phases

### Phase 0 — Project Foundation

* repository setup
* documentation foundation
* architecture and methodology planning
* decision log

### Phase 1 — Research & Feasibility

Validate:

* local perplexity extraction
* candidate language-model performance
* feature extraction
* LOO robust anomaly behavior
* minimum evidence requirements

### Phase 2 — Dataset Construction

* source human data
* document provenance and usage rights
* create essay families
* generate controlled AI variants locally
* construct hybrid variants
* create control sets
* perform family-level splitting

### Phase 3 — Detection Engine

* feature extraction
* baseline models
* classifier
* local anomaly analysis
* evidence aggregation
* uncertainty handling

### Phase 4 — API

* FastAPI service
* analysis endpoint
* validation
* response schema
* error handling

### Phase 5 — UI

* essay input
* passage highlighting
* evidence display
* uncertainty states
* global/local visualization

### Phase 6 — Evaluation

* baseline comparison
* ablation
* OOD testing
* hybrid evaluation
* ESL bias audit
* final test evaluation

### Phase 7 — Failure Analysis & Polish

* three confident failures
* limitations
* bias findings
* methodology refinement
* README
* screenshots/demo
* AI-tool disclosure
* final repository review

---

## 24. Known Risks

### Dataset Leakage

Paired variants may leak information across splits.

**Mitigation:** family-level splitting and explicit provenance metadata.

### Model Overfitting

The classifier may learn the statistical fingerprint of specific generation models rather than machine-associated characteristics generally.

**Mitigation:** model holdouts and cross-model evaluation.

### Topic Overfitting

The classifier may learn topic-specific vocabulary.

**Mitigation:** paired data and topic holdouts.

### Short-Text Instability

Sentence-level statistics may become unreliable for short sentences.

**Mitigation:** evidence-sufficiency rules and passage-level analysis.

### Local Anomaly Instability

Robust statistics may become unstable when too few observations are available.

**Mitigation:** minimum observation requirements, fallback behavior, and feasibility testing.

### ESL False Positives

Some features may correlate with English-learning background.

**Mitigation:** explicit bias evaluation and feature-level investigation.

### Computational Cost

Local language-model inference and repeated feature extraction may be too slow for interactive use.

**Mitigation:** small models, caching, batching, and simplified fallback analysis where appropriate.

### Generation Cost in Time

Local AI generation may limit dataset size.

**Mitigation:** prioritize controlled paired families and experimental coverage over arbitrary dataset volume.

---

## 25. Open Questions

These questions must be resolved through research or feasibility experiments rather than assumed.

1. Which local language model provides the best perplexity/speed tradeoff?
2. What minimum text length provides sufficient evidence?
3. Which candidate linguistic features provide meaningful incremental value?
4. How stable is LOO Median/MAD across essay lengths?
5. Should local anomaly use sentence neighborhoods, passage windows, or both?
6. What normalization is appropriate for feature distributions?
7. How should global and local signals interact?
8. Should classification probabilities be calibrated?
9. What threshold should trigger abstention?
10. How well does the methodology generalize to an unseen generation model?
11. How does the detector behave on hybrid writing?
12. Which features contribute most to ESL false positives?

Open questions must remain visibly marked until resolved.

---

## 26. Success Criteria

The project is successful if it produces a working application that:

* performs sentence and passage-level analysis
* provides measurable evidence
* distinguishes machine association from stylistic anomaly
* communicates uncertainty
* handles hybrid writing as a first-class case
* is built entirely with free/local resources
* uses a documented and reproducible dataset
* demonstrates meaningful evaluation beyond a single accuracy number
* documents at least three confident failures
* investigates ESL/non-native-English bias
* has clean, understandable engineering structure
* provides documentation that allows another engineer to understand and reproduce the system

The project does **not** require perfect AI detection.

The quality of the methodology, engineering decisions, evidence, documentation, and honesty about limitations are part of the deliverable.

---

## 27. Current Status

**Phase:** 0 — Project Foundation

**Status:** Planning complete; feasibility experiments pending.

The next phase begins with small, isolated experiments designed to validate the technical assumptions behind the proposed architecture.

No final feature set, classifier, threshold, or local language model is considered permanently locked until supported by experimental evidence.
