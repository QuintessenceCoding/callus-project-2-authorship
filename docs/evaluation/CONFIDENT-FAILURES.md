# Confident Failure Analysis — Final Held-Out Evaluation

## 1. Purpose

The Callus brief requires the detector to report three essays that it gets confidently wrong and explain why those failures matter.

This document records three failures selected from the **locked final held-out evaluation set**.

The cases were selected to cover both directions of error:

- machine-associated text classified as human-associated;
- human text classified as machine-associated.

The purpose is not to invent a post-hoc explanation for each error. The report separates:

1. what the detector measured;
2. what prediction it made;
3. what is observed in the text;
4. what we infer may have contributed to the failure;
5. what limitation the case demonstrates.

---

# 2. Final Evaluation Context

The failures come from:

```text
Evaluation: final-heldout-evaluation-v1
Final pairs: 200
Final essays: 400
Model: production-four-feature-logreg-v1
Source experiment: EXP-006
```

Final held-out performance:

```text
Accuracy:             98.49%
Precision:            98.99%
Recall:               98.00%
F1:                   98.49%
ROC-AUC:              99.83%
Coverage:             99.50%
False-positive rate:   1.01%
False-negative rate:   2.00%
```

Confusion matrix:

```text
                 Predicted
                Human     AI

Actual Human      196      2

Actual AI           4    196
```

The three cases below are drawn from those six misclassified inputs.

---

# 3. Failure Case 1 — AI Text Classified as Human

## Pair

```text
B6A5721D64C1
```

## Expected

```text
AI / machine-associated
```

## Predicted

```text
Human / human-associated
```

## Model Signal

```text
AI-associated signal: 0.00689067499
```

This was a **high-confidence false negative**.

---

## 3.1 Measured Features

```text
Perplexity:             92.7572
Sentence-length CV:      0.7458
MATTR:                   0.8614
POS 3-gram entropy:      6.2261
Word count:                 132
```

The four-feature vector therefore produced a strongly human-associated model output despite the source being the AI side of the controlled pair.

---

## 3.2 Text Characteristics

The AI text is structured as a numbered list of medical-job talking points rather than a conventional continuous essay.

Examples include:

```text
1. Advanced medical knowledge and expertise gained from studying
   and/or working in the medical field

2. Ability to work calmly and reliably in emergency and
   high-pressure situations

3. Ability to identify potential problems quickly and devise
   appropriate solutions
```

The text is highly templated and consists largely of short competency statements.

---

## 3.3 Observed Failure

The production detector classified this machine-generated text as human-associated with a model signal of approximately `0.0069`.

This is not a borderline error.

It is a strong model decision in the wrong direction.

---

## 3.4 Likely Limitation

A plausible explanation is that the text's list-like structure and varied item lengths produced a feature profile that overlaps with human-associated examples in the development distribution.

The available evidence does **not** establish that list structure itself caused the failure.

The defensible observation is:

> This AI-generated example falls inside a human-associated region of the four-feature distribution learned by the production classifier.

---

## 3.5 What This Failure Demonstrates

This case demonstrates that:

- high-confidence AI false negatives remain possible;
- a compact statistical feature model can fail when machine-generated text has an unusual structure;
- model confidence does not guarantee correct authorship classification;
- the detector is distribution-dependent.

---

# 4. Failure Case 2 — AI Text Classified as Human

## Pair

```text
F3550CF50ABC
```

## Expected

```text
AI / machine-associated
```

## Predicted

```text
Human / human-associated
```

## Model Signal

```text
AI-associated signal: 0.10472096836
```

This was another **confident false negative**.

---

## 4.1 Measured Features

```text
Perplexity:             55.0513
Sentence-length CV:      0.5005
MATTR:                   0.8296
POS 3-gram entropy:      6.7235
Word count:                 316
```

---

## 4.2 Text Characteristics

The AI text is a conventional reflective essay about the factors that shape character.

Its structure includes familiar essay patterns:

```text
general claim
→ explanation
→ friendship example
→ family example
→ discussion of social influence
```

The language is coherent, conventional, and topic-appropriate rather than obviously templated or list-based.

---

## 4.3 Observed Failure

Despite being the AI-generated counterpart, the document received a strong human-associated prediction.

The model signal was approximately `0.105`.

---

## 4.4 Likely Limitation

This case is consistent with a **distribution-overlap limitation**.

The document's measured features fall into a region that the classifier associates more strongly with human writing in its training distribution.

This does not mean the prose is "actually human-like" in every linguistic sense. It means the four measured features did not provide enough evidence to move the document into the machine-associated region learned by the model.

---

## 4.5 What This Failure Demonstrates

This case demonstrates that:

- conventional AI prose can overlap the human feature distribution;
- generation-model or generation-style shifts can cause false negatives;
- the detector should not be presented as a universal AI detector;
- strong validation performance does not eliminate out-of-distribution failures.

This limitation is also consistent with the external Gemini-generated essay tested separately during development, which was likewise classified as human-associated.

That Gemini example is **not part of the formal held-out metric** and is therefore treated only as an additional qualitative observation.

---

# 5. Failure Case 3 — Human Text Classified as AI

## Pair

```text
B046D31B68F0
```

## Expected

```text
Human / human-associated
```

## Predicted

```text
AI / machine-associated
```

## Model Signal

```text
AI-associated signal: 0.7536140213
```

This is a **strong false positive**.

---

## 5.1 Measured Features

```text
Perplexity:             70.6395
Sentence-length CV:      0.8188
MATTR:                   0.9069
POS 3-gram entropy:      6.2166
Word count:                  94
```

---

## 5.2 Text Characteristics

The essay is a short student-style response about community service and littering.

It contains several visible non-native-English characteristics, including grammatical and lexical errors.

For example:

> "If you don't like to leaving in a place were there is lots of people that litter..."

Other wording also contains:

- non-standard verb forms;
- article/preposition errors;
- spelling errors;
- awkward sentence construction.

---

## 5.3 Observed Failure

The detector classified this human essay as machine-associated with a model signal of approximately `0.754`.

Unlike the first two cases, this is a false positive rather than a false negative.

---

## 5.4 ESL / Non-Native-English Interpretation

This case is relevant to the project's ESL bias concern because the text visibly exhibits non-native-English characteristics.

However, this individual failure **does not prove ESL bias**.

The separate balanced PERSUADE audit produced:

```text
ELL false-positive rate:      2.14%
non-ELL false-positive rate:  2.43%
```

Therefore, the broader audit did not show elevated false-positive behavior for ELL essays in that sample.

The correct interpretation is:

> This is an informative individual false positive with non-native-English characteristics, but the group-level audit did not show elevated ELL false-positive behavior.

---

## 5.5 What This Failure Demonstrates

This case demonstrates that:

- human writing can strongly resemble the machine-associated region of the learned feature space;
- a single false positive should not automatically be attributed to one demographic characteristic;
- individual failure analysis and group-level fairness analysis answer different questions;
- the detector's evidence should be presented as statistical association, not as proof of AI authorship.

---

# 6. Secondary Misclassifications

The final held-out evaluation contained two additional false negatives that were much closer to the decision boundary:

```text
7D0CE6E00B68
AI → Human
Model signal: 0.472

9F1230B269C1
AI → Human
Model signal: 0.484
```

These are not included in the primary three because their signals are near the decision boundary and therefore provide less informative examples of confident error.

---

# 7. Abstentions

The final held-out set also contained two abstentions:

```text
D8934CA35801
E362F08345FE
```

Both were human essays with insufficient sentence-level evidence for the required feature vector.

The important point is that these were returned as:

```text
insufficient_evidence
```

rather than being forced into a human/AI classification.

This is treated as intended abstention behavior, not a model misclassification.

---

# 8. Cross-Case Findings

These three failures illustrate three different limitations:

### 8.1 Machine text can resemble human text

Cases `B6A5721D64C1` and `F3550CF50ABC` show that AI-generated text can fall inside the human-associated feature region.

### 8.2 Human text can resemble machine-associated text

Case `B046D31B68F0` shows the reverse failure.

### 8.3 Confidence does not equal correctness

All three selected failures have model outputs that are substantially away from the decision boundary.

This is why the project intentionally avoids presenting the model score as calibrated authorship certainty.

---

# 9. What We Learn From These Failures

The failures reinforce several locked project decisions:

```text
1. No universal AI-detection claim.
2. No sentence-level authorship claim.
3. No raw probability presented as factual authorship probability.
4. Distribution and generation-model dependence must be acknowledged.
5. Human false positives require explicit bias analysis.
6. Abstention is preferable when required evidence is unavailable.
```

The detector therefore remains an **evidence-oriented document classifier**, not an authorship oracle.

---

# 10. Reproducibility

The failures come from the frozen final evaluation set:

```text
Evaluation:
final-heldout-evaluation-v1

Final pairs:
200

Final essays:
400

Model:
production-four-feature-logreg-v1

Source:
EXP-006
```

The final prediction artifact is:

```text
data/final_evaluation/predictions.csv
```

The final metrics artifact is:

```text
data/final_evaluation/metrics.json
```

The dataset is identified by the SHA-256 recorded in:

```text
data/final_evaluation_manifest.json
```

---

# 11. Final Takeaway

The detector achieved strong performance on the final held-out evaluation, but the errors are informative.

The three selected failures show that:

> strong aggregate performance does not eliminate distributional false negatives or false positives.

That is a central limitation of statistical AI detection and a reason the project emphasizes measurable evidence, explicit uncertainty, and honest failure reporting rather than a single unexplained AI percentage.
