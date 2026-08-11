# Evaluation Strategy — Evidence-First Authorship Analysis

## 1. Purpose

This document defines how Project 2 will measure whether the detection system works, where it fails, and whether individual methodological decisions are justified.

Evaluation is treated as part of the system design rather than a final reporting step.

The evaluation process must answer:

1. Does the detector outperform simple baselines?
2. Which features actually contribute useful signal?
3. Does the detector generalize beyond the training distribution?
4. Can it detect hybrid writing?
5. Does it disproportionately flag ESL/non-native-English writing?
6. When the detector makes a strong claim, how reliable is that claim?
7. What are the detector's known failure modes?

The evaluation must not be designed to guarantee a favorable result.

---

# 2. Evaluation Philosophy

## 2.1 No Single Number

A single accuracy or F1 score is insufficient to characterize an AI detector.

Performance must be reported together with:

* precision
* recall
* F1
* false-positive rate
* false-negative rate
* coverage
* abstention behavior
* OOD performance
* hybrid performance
* bias results
* failure analysis

---

## 2.2 Evaluation Is Distribution-Specific

A detector's performance depends on:

* writing domain
* essay length
* topic
* generation model
* prompting
* degree of human editing
* dataset construction

Therefore, results must always be reported with the evaluation conditions.

Avoid statements such as:

> "The detector is 95% accurate at detecting AI."

Prefer:

> "On dataset version X, under evaluation protocol Y, the detector achieved Z F1 on the held-out test set."

---

## 2.3 Failure Is a Result

A poor result is not automatically evidence that the project failed.

For example:

```text id="4d5u7v"
Validation F1: 0.86
Unseen-model F1: 0.64
```

This may demonstrate meaningful model-family dependence.

The correct response is to document the limitation rather than tune repeatedly until the unseen-model result improves by chance.

---

# 3. Evaluation Hierarchy

Evaluation proceeds from simple to increasingly difficult conditions.

```text id="x5q1ve"
Trivial Baseline
      ↓
Perplexity Baseline
      ↓
Multi-Feature Model
      ↓
Ablation
      ↓
Hybrid Evaluation
      ↓
Topic Holdout
      ↓
Unseen Model
      ↓
ESL Bias Audit
      ↓
Confident Failure Analysis
```

Each stage answers a different question.

---

# 4. Dataset Splits

The project uses:

* training
* validation
* final test

with additional specialized evaluation sets where possible.

All splits must respect Essay Family boundaries.

---

## 4.1 Training Set

Used for:

* classifier fitting
* feature scaling fitting
* model training

No final test information may enter training.

---

## 4.2 Validation Set

Used for development decisions:

* feature selection
* model comparison
* threshold selection
* calibration
* evidence-sufficiency rules
* local anomaly parameters

Validation results may influence design decisions.

---

## 4.3 Final Test Set

Reserved for final evaluation.

It should be evaluated only after:

* feature selection
* model selection
* threshold selection
* preprocessing decisions
* calibration decisions

have been finalized.

---

# 5. Test-Set Protection

The final test set must not be used for iterative tuning.

Incorrect workflow:

```text id="9u0j0x"
Test
 ↓
See result
 ↓
Change model
 ↓
Test again
 ↓
Repeat
```

Correct workflow:

```text id="j71vbc"
Train
 ↓
Validation
 ↓
Tune
 ↓
LOCK
 ↓
Final Test
 ↓
Report
```

If exploratory test analysis is performed for debugging, that must be documented and the affected test evaluation should not be presented as an untouched final estimate.

---

# 6. Baselines

At least two baselines should be established.

---

## 6.1 Baseline 0 — Always Human

Predict the majority/negative class for every sample.

Purpose:

* establish a trivial reference
* detect misleading class imbalance

This baseline is intentionally weak.

---

## 6.2 Baseline 1 — Perplexity Threshold

Use a language-model perplexity measurement as the primary signal.

Possible procedure:

```text id="t6s4ae"
Text
 ↓
Perplexity
 ↓
Threshold
 ↓
Human / Machine-associated
```

The threshold must be selected using training/validation data, not the final test set.

Purpose:

> Determine how much useful signal can be obtained from predictability alone.

---

# 7. Primary Experimental Model

The primary experimental model combines validated linguistic features.

Potential input groups:

* predictability
* rhythm
* lexical characteristics
* structural characteristics
* repetition
* local consistency

The exact feature set is determined by ablation experiments.

---

# 8. Classification Metrics

## 8.1 Accuracy

[
Accuracy = \frac{TP + TN}{TP + TN + FP + FN}
]

Useful as a general metric but potentially misleading under class imbalance.

---

## 8.2 Precision

[
Precision = \frac{TP}{TP + FP}
]

Answers:

> When the system flags machine-associated text, how often is that prediction correct?

Important for limiting false accusations.

---

## 8.3 Recall

[
Recall = \frac{TP}{TP + FN}
]

Answers:

> How much of the target machine-associated text does the system identify?

---

## 8.4 F1

[
F1 = 2\frac{Precision \cdot Recall}{Precision + Recall}
]

Provides a balanced summary of precision and recall.

F1 should not be treated as the sole optimization target.

---

# 9. False-Positive Rate

False positives are especially important for this application.

[
FPR = \frac{FP}{FP + TN}
]

A detector that aggressively flags human writing may have attractive recall while being unsuitable for real-world use.

False-positive behavior should therefore be reported prominently.

---

# 10. Confusion Matrix

Each major evaluation should include a confusion matrix where appropriate.

```text id="m5l8ka"
                 Predicted
               Human   Machine

Actual Human    TN       FP

Actual Machine  FN       TP
```

This provides more information than a single summary metric.

---

# 11. Confidence and Calibration

If the classifier produces probabilities, those probabilities must not automatically be presented as factual authorship probabilities.

The project may evaluate calibration.

Potential methods:

* reliability diagrams
* Brier score
* Expected Calibration Error (ECE)

Potential calibration methods:

* Platt scaling
* isotonic regression

Calibration should be performed using validation data.

The final test set remains untouched during calibration.

---

# 12. Abstention Evaluation

Because the system supports insufficient/uncertain states, evaluation should consider **coverage**.

Define coverage as:

[
Coverage =
\frac{\text{Number of non-abstained predictions}}
{\text{Total inputs}}
]

The evaluation should ask:

> How accurate is the system when it chooses to make a strong prediction?

rather than forcing every sample into a binary classification.

---

# 13. Selective Performance

Where practical, report performance at different evidence thresholds.

Conceptually:

```text id="y3v5pk"
Low evidence threshold
    ↓
High coverage
Potentially lower precision

Higher evidence threshold
    ↓
Lower coverage
Potentially higher precision
```

This allows us to evaluate the trade-off between:

* making more decisions
* making more reliable decisions

The goal is not necessarily maximum coverage.

---

# 14. Ablation Study

Ablation determines which features contribute useful information.

Example:

```text id="qj7l6a"
Model A
Perplexity only

        ↓

Model B
Perplexity + Rhythm

        ↓

Model C
Perplexity + Rhythm + Lexical

        ↓

Model D
Perplexity + Rhythm + Lexical + Syntax

        ↓

Model E
Validated features + Local consistency
```

All models should be evaluated using the same split and protocol.

---

# 15. Ablation Interpretation

A feature should be considered useful only if it provides meaningful incremental value.

Potential outcomes:

### Positive

Performance improves consistently.

### Neutral

No meaningful change.

### Negative

Performance decreases.

### Trade-off

Overall F1 remains similar but another important metric improves.

Example:

> F1 unchanged, but ESL false-positive rate decreases.

This may justify retaining the feature.

---

# 16. Repeated Evaluation

Where computationally practical, important experiments should be repeated across multiple random seeds or splits.

Report:

* mean
* standard deviation
* individual results where useful

This helps distinguish genuine improvements from random variation.

If the dataset is too small for statistically meaningful repeated splitting, that limitation should be documented.

---

# 17. Hybrid Evaluation

Hybrid text receives dedicated evaluation.

---

## 17.1 AI-Polished Evaluation

Measure:

* whether modified passages are detected
* whether surrounding human passages remain unflagged
* localization accuracy
* false-positive spillover into neighboring text

---

## 17.2 AI-Spliced Evaluation

Measure:

* whether inserted passages are detected
* whether local anomaly increases
* whether the system correctly localizes the inserted region
* whether surrounding human text remains stable

---

# 18. Localization Metrics

Passage-level detection requires more than document-level classification.

Where ground-truth transformation boundaries are available, evaluate:

* sentence-level precision
* sentence-level recall
* passage overlap
* boundary accuracy

For example, if ground truth identifies:

```text id="m7b0yq"
S4–S5 = AI-modified
```

and the detector highlights:

```text id="o4j1zz"
S4–S6
```

the system has identified the relevant region but over-highlighted one sentence.

Localization metrics should capture this distinction.

---

# 19. Topic Generalization

A topic-holdout evaluation should be used where dataset size permits.

Procedure:

```text id="g5h6ry"
Training topics
├── Topic A
├── Topic B
├── Topic C
└── Topic D

Held-out topic
└── Topic E
```

Question:

> Does the detector still work when topic-specific vocabulary changes?

A substantial performance drop should be documented as a limitation.

---

# 20. Generation-Model Generalization

A model-family holdout should be used where practical.

Example:

```text id="u6i2tq"
TRAIN
├── Model A
└── Model B

TEST
└── Model C
```

Question:

> Does the detector generalize beyond the models it encountered during training?

A performance drop is valuable evidence about model dependence.

---

# 21. Hybrid Distribution Shift

The system should ideally be tested on hybrid writing that differs from the exact transformation patterns used during training.

For example:

```text id="pl0j6h"
Train:
AI replaces full paragraph

Test:
AI edits selected sentences
```

This tests whether the system learned a general concept of local discontinuity rather than a specific transformation artifact.

---

# 22. ESL / Non-Native-English Evaluation

The bias audit should report at least:

* false-positive rate
* machine-association score distribution
* evidence-strength distribution
* relevant feature distributions

Where sample sizes permit, compare the ESL/control group with the human test group.

The goal is to identify whether the detector disproportionately flags the control group.

---

# 23. Bias Interpretation

An observed difference does not automatically establish causation.

For example:

```text id="4b8h9k"
ESL FPR > General Human FPR
```

does not prove that:

> "ESL status causes false positives."

It establishes an observed association within the evaluation dataset.

Potential explanations should be treated as hypotheses unless tested.

---

# 24. Confident Failure Set

The final evaluation must include at least three essays the detector gets confidently wrong.

The selection should favor cases where:

* evidence strength is high
* classification is clearly incorrect
* the failure is informative

For each failure, document:

```text id="8t3v7k"
Essay
 ↓
Expected category
 ↓
Predicted category
 ↓
Evidence strength
 ↓
Machine-association signal
 ↓
Local-anomaly signal
 ↓
Important features
 ↓
Likely failure mechanism
 ↓
Potential mitigation
```

---

# 25. Failure Categories

Failures should be categorized where possible.

Potential categories:

* formal human prose
* unusual human style
* ESL/non-native-English writing
* AI-polished human writing
* human-edited AI text
* unseen model
* topic shift
* short-text instability
* feature conflict
* dataset artifact

A single failure may belong to multiple categories.

---

# 26. Evaluation of Evidence Quality

The project should not evaluate only whether the final label is correct.

It should also evaluate whether the evidence corresponds to the observed behavior.

Questions include:

* Did highlighted passages actually contain the relevant feature patterns?
* Does the local anomaly correspond to a measurable discontinuity?
* Are explanations derived from the model's real inputs?
* Does the evidence strength decrease when data becomes insufficient?
* Are contradictory signals represented honestly?

This is important because the project is explicitly evidence-first.

---

# 27. Sanity Checks

Before trusting results, run basic sanity checks.

### Label permutation

Randomize labels and verify that the classifier loses meaningful predictive performance.

### Feature-only sanity

Inspect whether a single suspicious metadata feature is accidentally driving the classifier.

### Topic-only baseline

Test whether topic information alone produces suspiciously high classification performance.

### Length-only baseline

Test whether essay length alone explains a significant portion of the signal.

### Family leakage check

Verify no family crosses splits.

These tests help identify dataset artifacts.

---

# 28. Metadata Leakage Test

Train an intentionally restricted classifier using only metadata-like variables that should not be available to the detector.

Examples:

* generation model
* source ID
* transformation label
* family ID
* dataset source

If this produces strong classification performance, investigate the dataset before trusting the real detector.

---

# 29. Feature Distribution Analysis

Before classifier training, inspect distributions of major candidate features across categories.

For example:

```text id="6b3j5s"
Feature: Perplexity

Human       █████████████
AI          █████████
Hybrid      ███████████
ESL         ████████████
```

The visualization itself does not establish causality.

It helps identify:

* overlap
* outliers
* dataset artifacts
* potential bias
* feature scale differences

---

# 30. Short-Text Evaluation

Because sentence-level analysis is a core requirement, short text must be explicitly tested.

Test categories may include:

* very short sentences
* medium sentences
* long sentences
* short paragraphs
* full essays

Questions:

* Which features become unstable?
* At what length does perplexity become unreliable?
* At what context size does local anomaly become meaningful?
* When should the system abstain?

---

# 31. Evaluation Artifacts

Experiments should produce reproducible artifacts such as:

```text id="j6o4s7"
experiments/
├── results/
│   ├── metrics.json
│   ├── confusion-matrix.png
│   ├── feature-distributions.png
│   └── predictions.csv
│
└── reports/
    └── EXP-001.md
```

Exact artifact structure may change.

The important requirement is that major conclusions can be traced back to experiment outputs.

---

# 32. Experiment Record

Each significant experiment should document:

```text id="k5c0wq"
Experiment ID:
Question:
Hypothesis:
Dataset version:
Training split:
Validation split:
Test split:
Features:
Model:
Parameters:
Metrics:
Result:
Interpretation:
Decision:
```

Example:

```text id="4x8f3y"
EXP-001

Question:
Does MATTR improve the perplexity baseline?

Hypothesis:
Adding MATTR will improve validation F1 and reduce false positives.

Result:
TBD

Decision:
TBD
```

---

# 33. Statistical Caution

The project may operate with a relatively small dataset.

Therefore:

* avoid over-interpreting tiny metric differences
* report sample sizes
* report uncertainty where practical
* distinguish exploratory observations from robust conclusions
* avoid unnecessary statistical significance claims

A 0.01 F1 improvement on a tiny test set should not automatically be described as meaningful.

---

# 34. Final Evaluation Report

The final evaluation should summarize:

### Overall

* dataset version
* test size
* test composition
* metrics

### Baseline comparison

* trivial baseline
* perplexity baseline
* final model

### Ablation

* feature contribution
* rejected features

### Generalization

* topic holdout
* unseen model
* hybrid

### Bias

* ESL/control results

### Failures

* at least three confident errors
* interpretation

### Limitations

* known weaknesses
* dataset boundaries
* model boundaries
* deployment limitations

---

# 35. Evaluation Decision Rules

A model should not be promoted to the final system merely because it achieves the highest single F1.

Promotion should consider:

1. Validation performance.
2. Generalization.
3. False-positive behavior.
4. Hybrid localization.
5. Evidence quality.
6. Calibration where applicable.
7. ESL bias behavior.
8. Computational cost.
9. Interpretability.

The final model should be the strongest **defensible** system, not necessarily the numerically strongest model under one metric.

---

# 36. What Counts as a Successful Result?

A successful result does not require near-perfect detection.

A strong project outcome could look like:

```text id="z4o3pm"
Perplexity baseline
      ↓
Useful but limited

Multi-feature model
      ↓
Improved validation performance

Hybrid evaluation
      ↓
Partial localization success

Unseen model
      ↓
Performance degradation discovered

ESL audit
      ↓
Some false-positive risk identified

Failure analysis
      ↓
Mechanisms documented
```

This is still a successful engineering/research outcome because it demonstrates understanding of the problem and the detector's boundaries.

---

# 37. Current Evaluation Status

**Phase:** 0 — Project Foundation

**Status:** Evaluation protocol defined; empirical results pending.

### Locked principles

* final test isolation
* family-level splitting
* baseline comparison
* ablation
* hybrid evaluation
* OOD evaluation where feasible
* ESL bias audit
* confident failure analysis
* evidence/abstention evaluation
* metadata leakage checks
* honest reporting

### Pending

* exact dataset sizes
* final metrics table
* exact thresholds
* calibration strategy
* localization metric details
* final OOD configuration
* final acceptance thresholds

These will be determined after dataset construction and feasibility experiments.
