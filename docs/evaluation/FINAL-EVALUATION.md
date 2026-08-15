# Final Evaluation Report — Evidence-First Authorship Analysis

## 1. Purpose

This document records the final evaluation of the locked production detector for Callus Project 2.

The goal is to report performance honestly, show the detector's observed failure modes, and distinguish development/validation performance from the final held-out evaluation.

The evaluation is intentionally distribution-specific. It is not a claim of universal AI-authorship detection accuracy.

---

# 2. Production System Evaluated

The evaluated artifact is:

```text
backend/artifacts/authorship_detector.joblib
```

Artifact version:

```text
production-four-feature-logreg-v1
```

Source experiment:

```text
EXP-006
```

Production feature vector:

```text
1. perplexity
2. sentence_length_cv
3. mattr
4. pos_3gram_entropy
```

Model pipeline:

```text
StandardScaler
      ↓
LogisticRegression
```

The detector operates at the **document level**.

The application additionally exposes directly measured sentence-level perplexity observations through the Evidence Inspector. These observations are evidence, not sentence-level authorship predictions.

---

# 3. Development / Validation Reference

The production model was selected in EXP-006.

The pair-aware development/validation split contained:

```text
Training pairs:    160
Validation pairs:   40
```

After feature filtering:

```text
Training rows:     320
Validation rows:    79
```

EXP-006 validation performance:

| Metric | Perplexity-only baseline | Four-feature model |
| --- | ---: | ---: |
| Accuracy | 0.860759 | **0.974684** |
| Precision | 0.795918 | **0.952381** |
| Recall | 0.975000 | **1.000000** |
| F1 | 0.876404 | **0.975610** |
| ROC-AUC | 0.956410 | **0.995513** |

The four-feature model therefore improved substantially over the perplexity-only baseline on this bounded validation split.

These values are **development/validation metrics** and are not used as the final headline performance claim.

---

# 4. Final Held-Out Evaluation

## 4.1 Evaluation Set

The final evaluation was frozen before inference.

The source dataset contained:

```text
Total paired records:       2421
Development pairs:           200
Untouched pairs:            2221
Final held-out pairs:        200
Final held-out essays:       400
```

The development pair IDs were excluded explicitly using the EXP-005 sampling manifest.

The frozen final evaluation manifest is:

```text
data/final_evaluation_manifest.json
```

The dataset SHA-256 is:

```text
3a1ba6c2ba557b83a13022efadb3239185cda05b50a9d31017fcf7967f33bb18
```

Pair semantics:

```text
text        → human/student writing
source_text → AI-generated counterpart
```

Therefore the final evaluation contains:

```text
200 human essays
200 AI-generated essays
```

---

# 5. Final Held-Out Results

The locked production artifact was evaluated without retraining or threshold tuning.

Results:

| Metric | Final held-out |
| --- | ---: |
| Accuracy | **98.49%** |
| Precision | **98.99%** |
| Recall | **98.00%** |
| F1 | **98.49%** |
| ROC-AUC | **99.83%** |
| False-positive rate | **1.01%** |
| False-negative rate | **2.00%** |
| Coverage | **99.50%** |

Input counts:

```text
Total inputs:        400
Classified:          398
Abstained:             2
```

Confusion matrix:

```text
                 Predicted
                Human     AI

Actual Human      196      2

Actual AI           4    196
```

Equivalently:

```text
True negatives:   196
False positives:    2
False negatives:    4
True positives:   196
```

---

# 6. Coverage and Abstention

The production detector classified:

```text
398 / 400 = 99.5%
```

of the final held-out inputs.

Two inputs returned:

```text
insufficient_evidence
```

instead of a forced human/AI classification.

Both abstentions were human essays with only one sentence, making sentence-length coefficient of variation unavailable.

This demonstrates the intended abstention behavior:

> The detector does not invent missing measurements merely to produce a binary verdict.

Coverage should therefore be reported alongside the classification metrics.

---

# 7. Interpretation of Final Performance

The final held-out result shows strong performance on this particular controlled dataset:

```text
98.49% accuracy
98.49% F1
99.83% ROC-AUC
99.5% coverage
```

The result is encouraging, but it must be interpreted within the evaluation conditions.

The model was trained using a bounded DAIGT-derived development sample and evaluated on an untouched subset from the same underlying source distribution.

Therefore the appropriate claim is:

> On the locked 400-essay held-out evaluation set, the production four-feature Logistic Regression achieved 98.49% accuracy and 98.49% F1 at 99.5% coverage.

The project does **not** claim:

> The detector is 98.5% accurate on all AI-generated admissions essays.

---

# 8. False-Positive and False-Negative Behavior

The final held-out confusion matrix contains:

```text
2 human → AI false positives
4 AI → human false negatives
```

This corresponds to:

```text
False-positive rate: 1.01%
False-negative rate: 2.00%
```

The asymmetry is worth reporting because a detector can appear strong on aggregate while still failing in particular writing conditions.

The selected confident failures are documented separately in:

```text
docs/evaluation/CONFIDENT-FAILURES.md
```

---

# 9. Confident Failure Cases

Three representative confident failures were selected from the frozen final evaluation.

## Case 1

```text
Pair: B6A5721D64C1
Actual: AI
Predicted: Human
Model signal: 0.0069
```

This AI example used a numbered list of medical-job competencies and fell strongly inside the human-associated region of the model's feature space.

## Case 2

```text
Pair: F3550CF50ABC
Actual: AI
Predicted: Human
Model signal: 0.1047
```

This AI example used conventional reflective-essay prose and illustrates distribution overlap between machine-generated and human-associated feature profiles.

## Case 3

```text
Pair: B046D31B68F0
Actual: Human
Predicted: AI
Model signal: 0.7536
```

This human essay produced a strong machine-associated signal and contains visible non-native-English characteristics.

The broader interpretation of this third case is addressed by the separate ELL audit.

See:

```text
docs/evaluation/CONFIDENT-FAILURES.md
```

for the complete analyses.

---

# 10. ESL / Non-Native-English Audit

A separate audit evaluated the locked production detector on human essays from the PERSUADE corpus.

The audit used:

```text
701 ELL essays
701 non-ELL essays
1402 total
```

Both groups came from the same:

```text
Text dependent
```

task category.

Audit artifact:

```text
data/esl_audit_manifest.json
```

Results:

| Metric | ELL | Non-ELL |
| --- | ---: | ---: |
| Essays | 701 | 701 |
| Classified | 701 | 700 |
| Abstained | 0 | 1 |
| Coverage | **100.00%** | **99.86%** |
| Flagged as AI | 15 | 17 |
| False-positive rate | **2.14%** | **2.43%** |
| Mean model signal | 0.0370 | 0.0596 |
| Median model signal | 0.00151 | 0.00621 |

Observed difference:

```text
ELL FPR - non-ELL FPR
= -0.29 percentage points
```

Therefore:

> No elevated ELL false-positive rate was observed in this audit sample.

This does **not** establish that the detector is universally free of ESL/non-native-English bias. It is a result for this corpus, sample, and evaluation protocol.

See:

```text
docs/evaluation/ESL-AUDIT.md
```

for the complete audit.

---

# 11. Evidence Inspector Evaluation

The Evidence Inspector was evaluated as an **evidence presentation layer**, not as a sentence-level classifier.

The current production system uses sentence-level perplexity observations because those are directly measured by the validated feature pipeline.

The evidence layer should satisfy the following properties:

- highlighted text corresponds to an actual sentence measurement;
- reported values match backend measurements;
- unavailable measurements remain unavailable;
- no invented sentence-level feature values are displayed;
- highlighted sentences are not labeled as "AI-written";
- document-level feature cards match the API;
- insufficient evidence is distinct from infrastructure failure.

The Evidence Inspector therefore answers:

```text
Where is a measurable local pattern?
Why is that location noteworthy?
```

rather than:

```text
Which sentence is definitely AI-generated?
```

The decision to avoid sentence-level authorship claims follows EXP-007 through EXP-011.

---

# 12. Local Attribution Evaluation

Three groups of experiments tested whether local authorship attribution could be made reliable:

```text
EXP-007 — local anomaly
EXP-008 — window / feature sensitivity
EXP-009 — boundary discontinuity
EXP-011 — leave-one-sentence-out attribution
```

These experiments found some local signal but insufficient reliability for production sentence-level authorship claims.

EXP-011 results:

```text
Top-10% capture: 22.5%
Top-25% capture: 42.5%
```

Decision:

```text
Rejected for production attribution
```

The production system therefore uses direct evidence observations rather than a local AI verdict.

---

# 13. Additional Qualitative Failure

During development, an independently generated Gemini essay was manually tested and classified as human-associated.

It received a model signal of approximately:

```text
0.254
```

This example is **not part of the formal held-out metric**.

It is retained only as an additional qualitative observation showing that AI-generated text outside or beyond the training distribution can overlap the human-associated feature space.

It must not be mixed into the final accuracy calculation.

---

# 14. Limitations

The final evaluation has important boundaries.

## Dataset dependence

The final held-out essays come from the same broad source distribution used to construct the development sample.

This is stronger than reusing the development rows, but it is not equivalent to testing on every admissions domain.

## Generation-model dependence

The final evaluation does not establish universal performance across every generation model.

The external Gemini example illustrates this limitation qualitatively but is not part of the formal held-out metric.

## Hybrid writing

The system was tested experimentally on controlled hybrid writing, but exact sentence-level recovery of AI-inserted passages is not a validated production capability.

## Sentence attribution

The final production detector does not identify individual sentences as definitively AI-generated.

## Calibration

The model's probability-like output is a model score within the development distribution, not calibrated authorship certainty.

## ESL / non-native-English generalization

The separate audit found no elevated ELL false-positive rate in the sampled PERSUADE comparison, but this does not establish universal fairness.

---

# 15. What the Final Evaluation Demonstrates

The completed evaluation supports the following conclusions:

1. The four-feature production classifier strongly outperformed the perplexity-only baseline on the EXP-006 development/validation split.
2. The locked model maintained strong performance on the 400-essay held-out evaluation set.
3. The production detector can abstain when required evidence is unavailable.
4. False positives and false negatives still occur, including confident errors.
5. Local attribution methods were not reliable enough to support sentence-level authorship claims.
6. The Evidence Inspector provides a more defensible way to expose local evidence without claiming unsupported authorship.
7. The matched ELL audit did not show elevated false-positive behavior for ELL essays in the tested sample.
8. The system remains distribution-dependent and should not be described as a universal AI detector.

---

# 16. Evaluation Artifacts

The final submission evaluation artifacts are:

```text
data/final_evaluation_manifest.json
data/final_evaluation/metrics.json
data/final_evaluation/predictions.csv

data/esl_audit_manifest.json
data/esl_audit/metrics.json
data/esl_audit/predictions.csv

docs/evaluation/CONFIDENT-FAILURES.md
docs/evaluation/ESL-AUDIT.md
docs/evaluation/FINAL-EVALUATION.md
```

These artifacts preserve the traceability between:

```text
frozen evaluation set
        ↓
production artifact
        ↓
predictions
        ↓
metrics
        ↓
failure / bias analysis
```

---

# 17. Final Evaluation Conclusion

The final production detector demonstrates strong performance on the locked held-out evaluation set while retaining explicit limitations and failure reporting.

The key final result is:

> **98.49% accuracy, 98.49% F1, and 99.83% ROC-AUC at 99.5% coverage on 400 held-out essays from 200 untouched paired records.**

The result is best understood as evidence that the selected four-feature statistical approach works well on the evaluated distribution—not as proof of universal AI-authorship detection.

The project deliberately prioritizes:

```text
measurable evidence
+
reproducibility
+
abstention
+
failure analysis
+
bias auditing
```

over an unexplained or overstated authorship verdict.
