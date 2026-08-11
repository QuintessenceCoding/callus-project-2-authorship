# Experiment Log — Evidence-First Authorship Analysis

This document is the chronological record of empirical experiments performed during Project 2.

The purpose is to preserve the reasoning behind methodological decisions.

Experiments should be recorded even when they fail or contradict the original hypothesis.

---

# 1. Experiment Lifecycle

Every meaningful experiment follows:

```text
Hypothesis
    ↓
Experiment Design
    ↓
Implementation
    ↓
Result
    ↓
Interpretation
    ↓
Decision
```

An experiment is not considered complete until its result and decision are recorded.

---

# 2. Experiment IDs

Experiments use sequential identifiers:

```text
EXP-001
EXP-002
EXP-003
...
```

The identifier must remain stable once assigned.

---

# 3. Experiment Status

Each experiment has one status:

* **Planned**
* **Running**
* **Completed**
* **Blocked**
* **Abandoned**

---

# 4. Experiment Record Template

```markdown
# EXP-XXX — Experiment Name

## Status
Planned

## Question

What specific question are we trying to answer?

## Hypothesis

What do we currently expect to happen?

## Motivation

Why does this question matter to the architecture?

## Dataset

- Dataset version:
- Number of essays:
- Number of sentences/passages:
- Relevant categories:
- Split:

## Configuration

- Model:
- Features:
- Parameters:
- Hardware/runtime:
- Random seed:

## Procedure

Describe exactly what was run.

## Metrics

List the metrics that will determine the outcome.

## Result

### Quantitative

Record actual measurements.

### Qualitative

Record important observations.

## Interpretation

What do the results mean?

Separate observations from hypotheses.

## Decision

- Accepted
- Rejected
- Revised
- Deferred

Explain why.

## Follow-up

What should happen next?
```

---

# 5. Phase 1 Experiments

The first experiments are intentionally small.

The goal is to eliminate technical uncertainty before building the full detector.

---

# EXP-001 — Local Perplexity Feasibility

## Status

Completed

## Question

Can we reliably calculate sentence-level perplexity using a locally runnable model on the available hardware?

## Hypothesis

A small causal language model should be capable of producing token-level log probabilities locally at a speed acceptable for interactive analysis.

## Why This Matters

Perplexity is the initial detection baseline.

If local inference is too slow or unreliable, the architecture needs to change before additional features are built.

## Variables

Test at least:

* very short sentence
* medium sentence
* long sentence
* short paragraph
* fictional admissions-style paragraph
* edge cases for empty, whitespace-only, extremely short, and one-usable-prediction inputs

Record:

* token count
* inference time
* tokens/second
* perplexity
* whether the output is numerically stable

Memory usage was not measured in this bounded run.

## Candidate Models

`distilgpt2` was used for this bounded feasibility experiment, as specified for EXP-001.

## Acceptance Criteria

The experiment should establish:

1. Token-level log probabilities can be obtained.
2. Sentence-level perplexity can be calculated.
3. Results are deterministic or reproducibly close under the same configuration.
4. Runtime is practical enough for development.
5. Memory usage is acceptable.

## Result

### Configuration

- Model: `distilgpt2`
- Runtime: Hugging Face Transformers
- Device: CPU, explicitly selected with `torch.device("cpu")`
- Python: `3.12.9`
- PyTorch: `2.13.0+cpu`
- Transformers: `5.15.0`
- Dependencies: `torch`, `transformers`
- Results artifact: `experiments/EXP-001-perplexity-feasibility/results/results.json`

### Quantitative

Final cached run:

| Test ID | Tokens | Usable predictions | Perplexity | Inference time (s) | Tokens/s | Status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `A-very-short` | 5 | 4 | 2589.029541 | 0.157552 | 25.39 | ok |
| `B-medium` | 20 | 19 | 139.890610 | 0.089811 | 211.56 | ok |
| `C-long` | 44 | 43 | 86.941147 | 0.105136 | 409.00 | ok |
| `D-paragraph` | 53 | 52 | 136.837708 | 0.122329 | 425.08 | ok |
| `E-admissions-style` | 88 | 87 | 65.279907 | 0.141792 | 613.57 | ok |

Performance summary:

- Cached model load time: `1.152793` seconds
- First successful inference time: `0.157552` seconds
- Median successful inference time: `0.113733` seconds
- Median tokens/second: `310.28`
- Total cached experiment runtime: `1.961918` seconds

Reproducibility:

- Repeated input: `A-very-short`
- Perplexities: `2589.029541015625`, `2589.029541015625`, `2589.029541015625`
- Maximum absolute difference: `0.0`
- Tolerance: `1e-9`

Edge cases:

| Test ID | Tokens | Usable predictions | Status | Result |
| --- | ---: | ---: | --- | --- |
| `EDGE-empty` | 0 | 0 | insufficient_input | no perplexity emitted |
| `EDGE-whitespace` | 9 | 8 | insufficient_input | no perplexity emitted because there is no lexical content |
| `EDGE-extremely-short` | 1 | 0 | insufficient_input | no perplexity emitted |
| `EDGE-one-usable-prediction` | 2 | 1 | ok | finite perplexity with warning that evidence is unstable |

### Qualitative

The first sandboxed run failed because `torch` was not installed. A local `.venv` was created and only `torch` and `transformers` were installed.

The first model-loading attempt then failed inside the sandbox because Hugging Face network access was blocked and `distilgpt2` was not cached. After approved network access, the model downloaded and ran. A later run loaded from the local cache successfully.

The implementation uses direct token-level logits and the causal language-model shift:

```python
shift_logits = logits[..., :-1, :].contiguous()
shift_labels = input_ids[..., 1:].contiguous()
```

This scores token `i` using the model context up to token `i-1`; the first token is excluded.

## Interpretation

Observation: `distilgpt2` can produce local token-level logits on CPU, and shifted sentence/paragraph perplexity can be calculated with finite results for valid prose inputs.

Observation: repeated evaluation of one input produced exactly identical perplexity in this environment.

Observation: empty, whitespace-only, and one-token inputs require intentional abstention or warnings. A finite value for a two-token input is mathematically computable but not strong evidence.

Interpretation: local perplexity extraction is technically feasible enough to proceed to the next planned feasibility question. This does not validate perplexity as an authorship detector, set thresholds, compare models, or establish minimum evidence requirements.

## Decision

`PROCEED`

Local sentence-level perplexity using `distilgpt2` is feasible as a measurement instrument for later experiments. Continue only after reviewing EXP-001; the appropriate follow-up is EXP-002, which should study perplexity stability by text length.

---

# EXP-002 — Perplexity Stability by Text Length

## Question

How stable is perplexity when calculated on very short versus longer text?

## Hypothesis

Very short sentences will produce noisier and less reliable perplexity measurements than paragraphs.

## Procedure

Evaluate text across increasing lengths:

```text
Very short sentence
        ↓
Short sentence
        ↓
Medium sentence
        ↓
Long sentence
        ↓
Paragraph
        ↓
Full essay
```

Record:

* token count
* perplexity
* runtime
* variance across comparable samples

## Purpose

Determine whether the detector requires minimum text lengths before presenting perplexity as meaningful evidence.

## Result

**TBD**

## Decision

**TBD**

---

# EXP-003 — Sentence Segmentation Feasibility

## Question

Can `spaCy` reliably segment admissions-style essays into usable sentences?

## Hypothesis

A standard English spaCy pipeline will provide sufficiently reliable sentence boundaries for the target domain.

## Procedure

Test against essays containing:

* abbreviations
* quotations
* punctuation-heavy sentences
* dialogue
* unusual formatting
* short fragments

Record obvious segmentation errors.

## Purpose

Sentence boundaries affect every downstream feature.

## Result

**TBD**

## Decision

**TBD**

---

# EXP-004 — Candidate Feature Extraction

## Question

Can the initial candidate features be extracted reliably and efficiently?

## Candidate Features

### Predictability

* sentence perplexity

### Rhythm

* sentence length
* sentence length variation
* punctuation distribution

### Lexical

* MATTR
* rare-word proportion

### Syntax

* POS n-gram entropy
* dependency statistics

## Metrics

Record:

* extraction time
* missing values
* numerical stability
* feature distributions
* implementation complexity

## Purpose

This is a technical feasibility experiment, not yet a classification experiment.

## Result

**TBD**

## Decision

**TBD**

---

# EXP-005 — Feature Distribution Sanity Check

## Question

Do candidate features produce sensible distributions across the available categories?

## Hypothesis

Some candidate features will show separation between human and machine-generated text, but significant overlap will remain.

## Procedure

Plot and summarize feature distributions across:

* human
* AI
* hybrid
* ESL/control where available

Inspect:

* overlap
* outliers
* suspiciously perfect separation
* length effects

## Important Constraint

A feature that perfectly separates the categories should be treated as suspicious rather than immediately celebrated.

Perfect separation may indicate:

* metadata leakage
* source artifacts
* topic confounding
* generation artifacts

## Result

**TBD**

## Decision

**TBD**

---

# EXP-006 — Perplexity Baseline

## Question

How well does perplexity alone classify the available data?

## Hypothesis

Perplexity should provide meaningful signal but will not reliably distinguish all human and machine-generated examples.

## Procedure

Train/select a threshold using training/validation data.

Evaluate on the appropriate held-out set.

Record:

* accuracy
* precision
* recall
* F1
* FPR
* FNR

## Result

**TBD**

## Decision

**TBD**

---

# EXP-007 — Local Baseline Stability

## Question

Can a local stylistic baseline be estimated reliably using robust statistics?

## Hypothesis

Median/MAD with leave-one-out exclusion will be more stable than mean/std when local outliers are present.

## Comparison

Compare:

### Method A

Mean + standard deviation

### Method B

Median + MAD

### Method C

Leave-one-out median + MAD

### Method D

Leave-one-out local-window median + MAD

## Test Conditions

Include:

* normal human essays
* AI-spliced essays
* AI-polished essays
* very short essays
* essays with few sentences

## Metrics

Record:

* baseline stability
* anomaly-score stability
* zero/near-zero MAD frequency
* ability to identify known transformed passages

## Result

**TBD**

## Decision

**TBD**

---

# EXP-008 — Local Window Size

## Question

What local context size provides the most stable and useful anomaly measurement?

## Candidate Windows

```text
±2 sentences
±3 sentences
±4 sentences
paragraph-level
whole-document
```

## Hypothesis

A local window should better capture stylistic discontinuities than a whole-document baseline while remaining sufficiently large for stable statistics.

## Result

**TBD**

## Decision

**TBD**

---

# EXP-009 — Evidence Sufficiency Thresholds

## Question

At what text/context sizes do the detector's measurements become too unstable to support a strong interpretation?

## Candidate Inputs

Vary:

* sentence length
* passage length
* number of neighboring sentences
* number of available baseline observations

Record:

* feature stability
* anomaly stability
* perplexity stability
* classification confidence

## Goal

Define conditions under which the system should return:

```text
Insufficient Evidence
```

rather than forcing a classification.

## Result

**TBD**

## Decision

**TBD**

---

# EXP-010 — Logistic Regression vs Random Forest

## Question

Does a nonlinear classifier provide meaningful value over a transparent linear classifier?

## Candidates

### Logistic Regression

Advantages:

* interpretable
* fast
* simple
* easy to calibrate

### Random Forest

Advantages:

* nonlinear relationships
* minimal distribution assumptions
* potentially stronger performance

## Comparison

Evaluate using the same:

* dataset
* features
* split
* evaluation metrics

## Decision Criteria

Consider:

* F1
* precision
* recall
* FPR
* calibration
* OOD performance
* computational cost
* interpretability

## Result

**TBD**

## Decision

**TBD**

---

# EXP-011 — Feature Ablation

## Question

Which candidate feature groups provide incremental value?

## Baseline

Perplexity only.

## Progression

```text
Perplexity
    ↓
+ Rhythm
    ↓
+ Lexical
    ↓
+ Syntax
    ↓
+ Repetition
    ↓
+ Local consistency
```

## Goal

Determine which feature groups:

* improve performance
* add redundancy
* hurt generalization
* increase bias
* increase computational cost without sufficient benefit

## Result

**TBD**

## Decision

**TBD**

---

# EXP-012 — Hybrid Detection

## Question

Can the detector identify localized machine-associated writing inside otherwise human essays?

## Test Cases

### AI Polishing

Selected human passages modified by a local model.

### AI Splicing

Selected passages replaced with newly generated text.

## Metrics

Evaluate:

* document-level classification
* sentence-level classification
* localization precision
* localization recall
* passage overlap
* false-positive spillover

## Result

**TBD**

## Decision

**TBD**

---

# EXP-013 — Global vs Local Signal

## Question

Does combining machine association with local stylistic anomaly improve interpretation of hybrid writing?

## Compare

### Global only

```text
S_global
```

### Local only

```text
S_local
```

### Combined

```text
S_global + S_local
```

## Important

The combination method should not be assumed beforehand.

Candidate methods may include:

* rule-based interpretation
* classifier input
* calibrated combination
* evidence matrix

The simplest defensible method should be preferred.

## Result

**TBD**

## Decision

**TBD**

---

# EXP-014 — Topic Generalization

## Question

Does the detector generalize to an unseen topic cluster?

## Procedure

Hold out a topic cluster from training.

Evaluate on that topic only.

## Result

**TBD**

## Decision

**TBD**

---

# EXP-015 — Unseen Model Generalization

## Question

Does the detector generalize to a generation model that was not present during training?

## Procedure

Train using available model families except one.

Evaluate on the held-out generation model.

## Interpretation

A performance drop should be documented rather than automatically treated as an implementation failure.

## Result

**TBD**

## Decision

**TBD**

---

# EXP-016 — ESL Bias Audit

## Question

Does the detector produce a disproportionately high false-positive rate on the ESL/non-native-English control set?

## Compare

* general human test set
* ESL/control set

Metrics:

* FPR
* machine-association score
* evidence strength
* feature distributions

## Result

**TBD**

## Decision

**TBD**

---

# EXP-017 — Confident Failure Analysis

## Question

What causes the detector's strongest incorrect predictions?

## Procedure

Select at least three confident failures.

For each:

1. inspect text
2. inspect feature vector
3. inspect global signal
4. inspect local signal
5. inspect evidence sufficiency
6. identify likely failure mechanism
7. determine whether mitigation is justified

## Result

**TBD**

## Decision

**TBD**

---

# 6. Experiment Promotion Rules

An experimental finding may influence the production system when:

1. The experiment is reproducible.
2. The result is recorded.
3. The interpretation is supported by the result.
4. The change does not compromise test-set integrity.
5. The resulting decision is documented.

A feature should not be promoted simply because it produces the highest score on one run.

---

# 7. Rejected Hypotheses

Rejected ideas remain documented.

Example:

```markdown
## EXP-XXX

Hypothesis:
POS entropy improves classification.

Result:
No meaningful improvement and increased ESL false positives.

Decision:
Rejected.

Reason:
The feature did not provide sufficient value relative to its
computational and bias cost.
```

This is useful engineering evidence.

---

# 8. Experiment Naming Convention

Use:

```text
EXP-XXX-short-description
```

Examples:

```text
EXP-001-perplexity-feasibility
EXP-002-perplexity-length-stability
EXP-007-local-baseline-stability
EXP-011-feature-ablation
```

Experiment outputs should use the same identifier.

---

# 9. Experiment Reproducibility

Every experiment should record enough information to rerun it.

At minimum:

* experiment ID
* code version / commit
* dataset version
* model
* model version
* feature configuration
* parameters
* random seed where applicable
* hardware
* runtime
* result artifacts

---

# 10. Experiment Artifacts

A possible structure:

```text
experiments/
├── EXP-001-perplexity-feasibility/
│   ├── README.md
│   ├── config.json
│   ├── results.json
│   └── output/
│
├── EXP-002-perplexity-length-stability/
│   ├── README.md
│   ├── config.json
│   └── output/
│
└── ...
```

The exact structure may change.

Experiments should remain separable from production application code.

---

# 11. Current Experiment Queue

| ID      | Experiment                           | Status  |
| ------- | ------------------------------------ | ------- |
| EXP-001 | Local perplexity feasibility         | Planned |
| EXP-002 | Perplexity stability by text length  | Planned |
| EXP-003 | Sentence segmentation feasibility    | Planned |
| EXP-004 | Candidate feature extraction         | Planned |
| EXP-005 | Feature distribution sanity check    | Planned |
| EXP-006 | Perplexity baseline                  | Planned |
| EXP-007 | Local baseline stability             | Planned |
| EXP-008 | Local window size                    | Planned |
| EXP-009 | Evidence sufficiency thresholds      | Planned |
| EXP-010 | Logistic Regression vs Random Forest | Planned |
| EXP-011 | Feature ablation                     | Planned |
| EXP-012 | Hybrid detection                     | Planned |
| EXP-013 | Global vs local signal               | Planned |
| EXP-014 | Topic generalization                 | Planned |
| EXP-015 | Unseen model generalization          | Planned |
| EXP-016 | ESL bias audit                       | Planned |
| EXP-017 | Confident failure analysis           | Planned |

The order may change based on feasibility results.

---

# 12. Current Status

**Phase:** 0 → Phase 1 transition

**Status:** Experiment framework established.

The next experiment to execute is:

> **EXP-001 — Local Perplexity Feasibility**

No production detection architecture should depend on a specific perplexity model until this experiment has been completed.
