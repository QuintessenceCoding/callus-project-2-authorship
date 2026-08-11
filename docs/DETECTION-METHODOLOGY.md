# Detection Methodology — Evidence-First Authorship Analysis

## 1. Purpose

This document defines the proposed statistical and machine-learning methodology for detecting measurable characteristics associated with machine-generated text in college admissions essays.

It serves three purposes:

1. Define the analytical concepts used by the system.
2. Separate established assumptions from experimental hypotheses.
3. Provide implementation guidance once feasibility experiments validate the approach.

The methodology is intentionally experiment-driven.

A candidate feature, model, threshold, or statistical formulation must not become part of the final system solely because it appears theoretically plausible.

---

# 2. Methodological Position

The system does not attempt to determine authorship with certainty.

Instead, it estimates whether text exhibits characteristics that are statistically associated with machine-generated writing within the project's training and evaluation distributions.

The system also measures whether individual passages deviate from the surrounding writing.

Therefore, the detector produces evidence along two separate dimensions:

```text id="f7w9qn"
                Passage
                   │
          ┌────────┴────────┐
          ▼                 ▼
 Machine Association   Stylistic Anomaly
    "Does this            "Does this
     resemble             differ from
     machine text?"       its context?"
```

Neither signal alone constitutes proof of AI authorship.

---

# 3. Core Analytical Questions

The methodology attempts to answer four questions.

### Q1 — Machine Association

Does this passage exhibit measurable characteristics that resemble machine-generated examples?

### Q2 — Stylistic Consistency

Does this passage behave similarly to the surrounding writing?

### Q3 — Evidence Sufficiency

Is there enough reliable text and context to support an interpretation?

### Q4 — Generalization

Does the detector continue to behave reasonably when the topic, generation model, or writing style changes?

The final system should expose these distinctions rather than collapse them into a single unexplained percentage.

---

# 4. Analytical Units

The system operates at multiple granularities.

## 4.1 Document

The complete submitted essay.

Used for:

* overall assessment
* essay-level feature distributions
* contextual baselines
* aggregate evidence

---

## 4.2 Sentence

The smallest primary analytical unit.

Used for:

* sentence-level features
* local anomaly analysis
* highlighting
* fine-grained evidence

Very short sentences may not contain enough information for reliable analysis.

---

## 4.3 Passage

A group of adjacent sentences.

Used for:

* more stable feature estimation
* local stylistic comparison
* hybrid-writing detection
* stronger evidence when individual sentences are too short

Passages may correspond to paragraphs or dynamically constructed sentence windows.

The exact passage construction strategy remains experimental.

---

# 5. Methodology Pipeline

The proposed analytical pipeline is:

```text id="wjh7uo"
Raw Essay
    │
    ▼
Normalization
    │
    ▼
Sentence / Passage Segmentation
    │
    ▼
Feature Extraction
    │
    ├──────────────────────────────┐
    ▼                              ▼
Machine Association          Stylistic Anomaly
Features                     Features
    │                              │
    ▼                              ▼
Global Classifier             Robust Local Analysis
    │                              │
    └──────────────┬───────────────┘
                   ▼
           Evidence Sufficiency
                   │
                   ▼
          Decision / Abstention
                   │
                   ▼
           Evidence Aggregation
                   │
                   ▼
                UI Result
```

---

# 6. Feature Laboratory

The project will initially maintain a broad candidate feature pool.

Features are organized into categories.

The purpose of the laboratory is to experimentally determine:

* which features contain useful signal
* which features are redundant
* which features improve generalization
* which features introduce undesirable bias
* which features are computationally practical

No candidate feature is guaranteed to reach the final model.

---

# 7. Predictability Features

## 7.1 Perplexity

Perplexity measures how predictable a sequence is according to a language model.

For tokens with log probabilities:

[
PPL = \exp\left(-\frac{1}{N}\sum_{i=1}^{N}\log P(x_i|x_{<i})\right)
]

Lower perplexity indicates that the language model considers the text more predictable.

Perplexity is useful as a candidate signal because generated text can exhibit different predictability distributions from human text.

However:

> **Low perplexity does not imply AI authorship.**

Human writing can also be highly predictable, especially when formal, edited, or produced by experienced writers.

This is particularly relevant to ESL/non-native-English bias.

---

## 7.2 Sentence-Level Perplexity

Perplexity should initially be calculated at sentence or passage level rather than only for the complete document.

This enables:

* localized highlighting
* local comparison
* passage-level anomaly detection

The language model used for this calculation must be locally runnable.

Candidate models will be evaluated during Phase 1.

---

## 7.3 Perplexity Variation

In addition to absolute perplexity, the system may calculate:

* mean perplexity
* median perplexity
* variance
* coefficient of variation
* neighboring-sentence changes

These features attempt to capture whether predictability is relatively uniform or varies throughout the essay.

---

# 8. Rhythm and Pacing Features

Human writing often varies sentence structure and pacing.

Candidate features include:

## 8.1 Sentence Length

Measured using:

* tokens
* words
* characters where useful

---

## 8.2 Sentence Length Coefficient of Variation

Instead of using raw variance:

[
CV = \frac{\sigma}{\mu}
]

This normalizes variation relative to the average sentence length.

The feature may be calculated:

* across a passage
* across the document
* within local windows

depending on experimental results.

---

## 8.3 Punctuation Distribution

Potential measurements include:

* commas per sentence
* semicolons
* colons
* dashes
* parentheses
* quotation marks
* terminal punctuation

The goal is not to assume that a particular punctuation pattern is inherently AI-like.

Instead, punctuation features are candidate indicators of stylistic regularity.

---

# 9. Lexical Features

## 9.1 MATTR

Type-Token Ratio (TTR) is strongly affected by document length.

Therefore, the initial candidate metric is:

**Moving-Average Type-Token Ratio (MATTR).**

MATTR calculates lexical diversity over fixed-size moving windows and averages the resulting values.

This reduces the direct dependence of lexical diversity on total essay length.

---

## 9.2 Rare-Word Proportion

Potentially measure the proportion of words outside a reference frequency list.

This feature must be handled carefully because:

* frequency lists vary
* vocabulary depends on topic
* domain-specific terminology can appear rare
* ESL writing may be affected differently

Therefore, this feature will require validation before being retained.

---

## 9.3 Repetition

Potential measurements include:

* repeated words
* repeated n-grams
* repeated phrase structures
* distance between repeated constructions

Repetition should be measured relative to an appropriate baseline rather than automatically treated as evidence of machine generation.

---

# 10. Structural and Syntactic Features

## 10.1 POS N-Gram Entropy

Part-of-speech sequences can be represented as n-grams.

For example:

```text id="3l5xg4"
DET → ADJ → NOUN → VERB
```

The distribution of POS n-grams can be measured using entropy:

[
H(X) = -\sum_i p(x_i)\log p(x_i)
]

Lower entropy may indicate more repetitive structural patterns.

However, entropy alone is not interpreted as an AI score.

It is a candidate feature whose usefulness must be experimentally established.

---

## 10.2 Dependency Statistics

Potential features include:

* dependency tree depth
* number of dependency relations
* clause-related measurements
* structural variation between sentences

These are candidate features.

They will only be retained if they provide measurable value without creating unnecessary computational or bias costs.

---

# 11. Local Consistency Features

This is a major component of the methodology.

Traditional detection asks:

> Does this text look machine-generated?

Our system additionally asks:

> Does this passage look unusually different from the writing around it?

This is particularly relevant to:

* AI polishing
* AI-assisted rewriting
* AI-spliced passages

---

# 12. Stylistic Anomaly Score

Let an essay consist of analytical units:

[
E = (s_1, s_2, ..., s_n)
]

Each unit has a feature vector:

[
x_i \in \mathbb{R}^k
]

For the target unit (s_i), construct a reference distribution using surrounding or remaining observations.

The initial candidate approach is robust statistics.

---

# 13. Robust Baseline

Ordinary mean and standard deviation are vulnerable to outliers.

That is particularly problematic because the outlier may be the exact passage we are attempting to identify.

Therefore, the initial approach is:

* median
* Median Absolute Deviation (MAD)

For a feature (j):

[
MAD_j = median(|x_j - median(x_j)|)
]

A robust standardized deviation may be represented as:

[
z_{robust} =
\frac{0.6745(x - median(x))}
{MAD + \epsilon}
]

The constant and exact formulation are subject to validation.

The system must handle the case where MAD is zero or extremely small.

---

# 14. Leave-One-Out Baseline

When evaluating a target sentence or passage, that unit should not substantially influence the baseline against which it is evaluated.

For target (s_i):

[
B_i = E \setminus {s_i}
]

The baseline statistics are therefore calculated without the target observation where sufficient data exists.

Conceptually:

```text id="qfd3z6"
Essay units:

S1 S2 S3 S4 S5 S6 S7 S8

Target:
          S4

Baseline:
S1 S2 S3    S5 S6 S7 S8
```

This reduces self-contamination.

---

# 15. Local Windows

A full-document baseline may hide local discontinuities.

Therefore, local windows are a candidate approach.

For target sentence (s_i), a local neighborhood might include:

[
W_i = {s_{i-m}, ..., s_{i-1}, s_{i+1}, ..., s_{i+m}}
]

where (m) is experimentally determined.

Potential values may include:

* 2 neighboring sentences
* 3 neighboring sentences
* paragraph-level neighbors
* adaptive windows

The window size must be large enough to produce stable statistics without becoming equivalent to the entire essay.

---

# 16. Local Anomaly Aggregation

For each feature, calculate a robust standardized deviation.

A candidate aggregate anomaly score is:

[
S_{local}(s_i)
==============

\sqrt{
\sum_{j=1}^{k}
w_j z_{i,j}^{2}
}
]

where:

* (z_{i,j}) is the robust standardized deviation
* (w_j) is an optional feature weight

However, this exact aggregation is **not locked**.

Alternatives include:

* mean absolute standardized deviation
* maximum standardized deviation
* robust multivariate distance
* learned anomaly scoring
* feature-specific aggregation

The simplest stable method should be preferred unless experimentation justifies greater complexity.

---

# 17. Machine Association Score

The global detector learns a relationship between feature vectors and training labels.

Conceptually:

[
S_{global}(x) =
P(machine \mid x)
]

when the chosen classifier provides a calibrated probability interpretation.

However, a raw classifier probability must not automatically be described as a statistically valid confidence interval.

Probability calibration will be investigated separately.

The final UI terminology may therefore use:

* machine association
* evidence strength
* uncertain

rather than presenting uncalibrated probabilities as objective truth.

---

# 18. Classifier Candidates

The initial candidate classifiers are:

### Logistic Regression

Advantages:

* simple
* fast
* interpretable
* works well with normalized numerical features
* suitable as a transparent baseline

### Random Forest

Advantages:

* handles nonlinear relationships
* minimal assumptions about feature distributions
* useful for comparing against a linear baseline
* provides feature importance mechanisms

Additional models may be tested if justified.

The final classifier will be selected based on:

* held-out performance
* generalization
* calibration
* computational cost
* interpretability
* hybrid performance
* bias behavior

---

# 19. Baselines

The project will establish progressively stronger baselines.

## Baseline 0 — Always Human

Predict the majority class.

Purpose:

* sanity check
* establish a trivial lower bound

---

## Baseline 1 — Perplexity Threshold

Use a simple threshold on perplexity.

Purpose:

* measure the standalone value of predictability
* establish whether the feature-engineered detector adds value

---

## Model 2 — Multi-Feature Classifier

Combine validated linguistic features.

Purpose:

* determine whether multiple signals provide useful incremental information

---

# 20. Ablation Study

The feature laboratory will use controlled ablation.

Example progression:

```text id="h5v94x"
Baseline
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

Each configuration should be evaluated on the same validation protocol.

The purpose is to determine:

* which features improve discrimination
* which features are redundant
* which features hurt generalization
* which features disproportionately affect bias
* which features improve hybrid detection

A feature may be retained even without a large overall F1 improvement if it provides meaningful value in another required dimension.

---

# 21. Hybrid Writing Methodology

Hybrid writing is a first-class evaluation case.

The project will distinguish at least:

### AI Polishing

Human text remains intact in meaning and structure while selected passages are substantially edited by a local language model.

Expected challenge:

> The machine-associated signal may be subtle.

---

### AI Splicing

One or more passages are replaced with newly generated text while the surrounding essay remains human-written.

Expected challenge:

> The inserted passage may create a local statistical discontinuity.

---

### Potential Additional Case

If time permits:

**Human-edited AI**

AI-generated text is subsequently substantially edited by a human.

This tests whether the detector can survive partial removal of machine-associated characteristics.

This case is optional and should not compromise the core experiments.

---

# 22. Global + Local Interpretation

The system maintains two distinct signals.

```text id="s5c0uy"
                Stylistic Anomaly
                      HIGH
                        │
                        │
       Human-style      │      Local machine-
       shift            │      associated anomaly
                        │
────────────────────────┼────────────────────────
                        │
       Consistent       │      Consistently
       human-like       │      machine-associated
                        │
                        │
                      LOW
                        │
                  Machine Association
```

The quadrants are interpretive aids, not ground-truth labels.

For example:

### Low Global + Low Local

Consistent with human-writing distribution and internally consistent.

### High Global + Low Local

Machine-associated characteristics appear relatively consistently.

### High Global + High Local

Machine-associated characteristics coincide with a localized stylistic anomaly.

### Low Global + High Local

A stylistic shift exists, but evidence for machine association is weak.

This should generally produce uncertainty rather than a machine attribution.

---

# 23. Evidence Sufficiency

Evidence sufficiency determines whether an analytical result should be surfaced strongly.

Potential requirements include:

### Text quantity

Enough tokens to calculate stable language-model statistics.

### Context quantity

Enough neighboring observations to establish a local baseline.

### Feature availability

Required features must be computable.

### Statistical stability

Variance/MAD must not be degenerate.

### Signal agreement

If major signals strongly conflict, the system should reduce evidence strength or abstain.

The exact thresholds are experimental.

---

# 24. Uncertainty and Abstention

The detector should be capable of declining to make a strong classification.

Potential states:

```text id="1v7xoe"
HIGH EVIDENCE
    ↓
Strong interpretation

MODERATE EVIDENCE
    ↓
Qualified interpretation

LOW / CONFLICTING EVIDENCE
    ↓
Uncertain

INSUFFICIENT EVIDENCE
    ↓
No meaningful classification
```

The system should not convert uncertainty into an arbitrary percentage.

---

# 25. Calibration

Classifier probabilities and user-facing confidence are separate concepts.

A value returned by:

```text id="3x3h5q"
classifier.predict_proba()
```

should not automatically be called:

> "87% probability this was written by AI."

If calibration is needed, candidate methods may include:

* Platt scaling
* isotonic regression

Calibration must be evaluated on held-out validation data.

If calibrated probabilities do not provide meaningful value, the UI may instead expose categorical evidence strength.

---

# 26. Feature Contribution and Evidence

Evidence should be generated from measurable model inputs.

For a linear classifier, contribution may be estimated from:

[
contribution_j = w_j x_j
]

after appropriate preprocessing.

For nonlinear models, alternatives may include:

* permutation-based feature importance
* controlled feature perturbation
* model-specific attribution methods

The project should avoid introducing a complex explanation system unless necessary.

The simplest explanation method that faithfully represents the model should be preferred.

---

# 27. Dataset Relationship to Methodology

The detector's methodology is only meaningful relative to its training distribution.

Therefore, every evaluation must record:

* dataset source
* essay family
* human/AI/hybrid category
* generation model where applicable
* topic
* split
* transformation type
* word count

This allows later investigation of unexpected behavior.

---

# 28. Generalization Experiments

The detector will be evaluated under controlled distribution shifts.

## Topic Shift

Train on one set of topic clusters and evaluate on a held-out topic cluster.

Question:

> Does the detector depend on topic-specific vocabulary?

---

## Model Shift

Train without examples from a particular generation model.

Evaluate against that unseen model.

Question:

> Has the classifier learned machine-associated characteristics or simply learned the fingerprint of known models?

---

## Hybrid Shift

Train on pure human/AI data and evaluate on human-AI hybrid data.

Question:

> Can the detector identify partial machine assistance?

---

# 29. Bias Evaluation

ESL/non-native-English writing is treated as a specific audit condition.

The experiment asks:

> Do features used by the detector produce elevated false positives on the control group?

Possible metrics include:

* false-positive rate
* evidence-strength distribution
* average machine-association score
* feature distributions

The goal is not to assume bias exists.

The goal is to measure whether it exists in this system.

---

# 30. Failure Analysis

The project must intentionally inspect confident errors.

For each failure:

```text id="p7v8c1"
Input
  ↓
Prediction
  ↓
Feature values
  ↓
Global signal
  ↓
Local signal
  ↓
Evidence sufficiency
  ↓
Failure interpretation
```

Potential failure categories:

* polished human prose
* ESL/non-native-English writing
* unusual human style
* human-edited AI
* unseen generation model
* topic shift
* short passage
* contradictory feature signals

The analysis should distinguish:

> **What the detector did**

from:

> **Why we believe it failed.**

The latter is a hypothesis unless experimentally verified.

---

# 31. Evaluation Metrics

Primary metrics may include:

* accuracy
* precision
* recall
* F1

However, accuracy alone is insufficient.

Additional analysis should consider:

* false-positive rate
* false-negative rate
* precision at high-confidence decisions
* coverage under abstention
* calibration if probabilities are exposed
* hybrid detection performance
* OOD performance
* ESL false-positive behavior

---

# 32. Coverage vs Accuracy

If the system supports abstention, evaluation should measure the relationship between:

> how often the system makes a strong claim

and:

> how often those claims are correct.

For example:

```text id="n8h2dy"
All inputs
    │
    ├── Strong decision
    ├── Uncertain
    └── Insufficient evidence
```

A useful evaluation question becomes:

> When the system chooses to make a strong claim, how reliable is that claim?

This is preferable to forcing every input into a binary category.

---

# 33. Experimental Reproducibility

Every experiment should record:

* experiment identifier
* date
* dataset version
* feature configuration
* model configuration
* preprocessing configuration
* random seed where applicable
* metrics
* output artifacts
* interpretation
* resulting decision

Example:

```text id="zj4y6a"
EXP-004

Question:
Does adding MATTR improve the perplexity baseline?

Dataset:
dataset-v1

Baseline:
Perplexity threshold

Variant:
Perplexity + MATTR

Result:
TBD

Decision:
TBD
```

---

# 34. Hypothesis → Experiment → Result → Decision

This is the central experimental workflow.

```text id="h6c3y8"
HYPOTHESIS
    ↓
EXPERIMENT
    ↓
RESULT
    ↓
INTERPRETATION
    ↓
DECISION
```

A result should not be rewritten after the fact to match the desired conclusion.

If an experiment contradicts the original hypothesis, the hypothesis is updated.

---

# 35. Methodology Status Labels

Methodology documentation should distinguish:

### Accepted

Supported by project evidence or an explicit architectural decision.

### Proposed

Current preferred approach but not yet experimentally validated.

### Experimental

Being actively tested.

### Rejected

Tested and intentionally not used.

### Deferred

Potentially useful but outside the current scope/time budget.

This prevents assumptions from being mistaken for established facts.

---

# 36. Current Proposed Feature Matrix

| Category             | Feature                        | Status                  |
| -------------------- | ------------------------------ | ----------------------- |
| Predictability       | Mean perplexity                | Proposed baseline       |
| Predictability       | Perplexity variation           | Experimental            |
| Rhythm               | Sentence length                | Experimental            |
| Rhythm               | Sentence length CV             | Experimental            |
| Rhythm               | Punctuation distribution       | Experimental            |
| Lexical              | MATTR                          | Experimental            |
| Lexical              | Rare-word proportion           | Experimental            |
| Repetition           | Repeated n-grams               | Experimental            |
| Syntax               | POS n-gram entropy             | Experimental            |
| Syntax               | Dependency statistics          | Experimental            |
| Local consistency    | Essay-relative deviation       | Proposed                |
| Local consistency    | Local-window deviation         | Experimental            |
| Local consistency    | Leave-one-out robust deviation | Proposed                |
| Advanced probability | Perturbation curvature         | Deferred / Experimental |

No row marked Experimental or Proposed is guaranteed to enter the final detector.

---

# 37. Methodology Constraints

The final implementation must not:

* use a chat model as the final judge
* generate an explanation through an LLM after classification
* present uncalibrated classifier probabilities as factual authorship probabilities
* use test data for feature/threshold tuning
* split variants from the same essay family across train/test
* silently discard failures
* claim universal detection capability
* hide dataset limitations

---

# 38. Phase 1 Feasibility Questions

Before production implementation, the following must be tested.

### Perplexity

* Which local model is practical?
* How fast is inference?
* Is sentence-level token probability extraction reliable?
* How does performance change with sentence length?

### Features

* Are candidate features stable?
* Are they computationally practical?
* Do they contain useful signal?

### Local anomaly

* Does LOO Median/MAD remain stable?
* What minimum number of observations is required?
* Do local windows outperform whole-document baselines?
* How should zero/near-zero MAD be handled?

### Classifier

* Does Logistic Regression beat the perplexity baseline?
* Does Random Forest add meaningful nonlinear value?
* Are probabilities calibrated enough to expose?

### Evidence

* How much text is required for a strong assessment?
* When should the system abstain?
* Which feature contributions can be explained faithfully?

---

# 39. Current Methodology Status

**Phase:** 0 — Project Foundation

**Status:** Conceptually defined; experimental validation pending.

### Locked principles

* Evidence-first analysis
* Machine association and stylistic anomaly remain separate
* Perplexity serves as a baseline, not a final verdict
* Candidate features require empirical validation
* Robust local statistics are preferred over naive mean/std baselines
* Leave-one-out analysis is preferred where sufficient context exists
* Short or unstable inputs must be allowed to abstain
* Hybrid writing is a first-class evaluation condition
* Final test data remains untouched during model development
* Failure and bias analysis are required deliverables

### Pending

* exact language model
* final feature set
* final classifier
* anomaly formulation
* minimum evidence thresholds
* local window size
* calibration strategy
* decision thresholds
* final evidence-attribution mechanism

The next technical step is **Phase 1 feasibility experimentation**.
