**# Experiment Log — Evidence-First Authorship Analysis**

This document is the chronological record of empirical experiments performed during Project 2.

The purpose is to preserve the reasoning behind methodological decisions.

Experiments should be recorded even when they fail or contradict the original hypothesis.

**---**

**# 1. Experiment Lifecycle**

Every meaningful experiment follows:

\`\`\`text
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
\`\`\`

An experiment is not considered complete until its result and decision are recorded.

**---**

**# 2. Experiment IDs**

Experiments use sequential identifiers:

\`\`\`text
EXP-001
EXP-002
EXP-003
...
\`\`\`

The identifier must remain stable once assigned.

**---**

**# 3. Experiment Status**

Each experiment has one status:

\* **\*\*Planned\*\***
\* **\*\*Running\*\***
\* **\*\*Completed\*\***
\* **\*\*Blocked\*\***
\* **\*\*Abandoned\*\***

**---**

**# 4. Experiment Record Template**

\`\`\`markdown
**# EXP-XXX — Experiment Name**

**## Status**
Planned

**## Question**

What specific question are we trying to answer?

**## Hypothesis**

What do we currently expect to happen?

**## Motivation**

Why does this question matter to the architecture?

**## Dataset**

\- Dataset version:
\- Number of essays:
\- Number of sentences/passages:
\- Relevant categories:
\- Split:

**## Configuration**

\- Model:
\- Features:
\- Parameters:
\- Hardware/runtime:
\- Random seed:

**## Procedure**

Describe exactly what was run.

**## Metrics**

List the metrics that will determine the outcome.

**## Result**

**### Quantitative**

Record actual measurements.

**### Qualitative**

Record important observations.

**## Interpretation**

What do the results mean?

Separate observations from hypotheses.

**## Decision**

\- Accepted
\- Rejected
\- Revised
\- Deferred

Explain why.

**## Follow-up**

What should happen next?
\`\`\`

**---**

**# 5. Phase 1 Experiments**

The first experiments are intentionally small.

The goal is to eliminate technical uncertainty before building the full detector.

**---**

**# EXP-001 — Local Perplexity Feasibility**

**## Status**

Completed

**## Question**

Can we reliably calculate sentence-level perplexity using a locally runnable model on the available hardware?

**## Hypothesis**

A small causal language model should be capable of producing token-level log probabilities locally at a speed acceptable for interactive analysis.

**## Why This Matters**

Perplexity is the initial detection baseline.

If local inference is too slow or unreliable, the architecture needs to change before additional features are built.

**## Variables**

Test at least:

\* very short sentence
\* medium sentence
\* long sentence
\* short paragraph
\* fictional admissions-style paragraph
\* edge cases for empty, whitespace-only, extremely short, and one-usable-prediction inputs

Record:

\* token count
\* inference time
\* tokens/second
\* perplexity
\* whether the output is numerically stable

Memory usage was not measured in this bounded run.

**## Candidate Models**

\`distilgpt2\` was used for this bounded feasibility experiment, as specified for EXP-001.

**## Acceptance Criteria**

The experiment should establish:

1\. Token-level log probabilities can be obtained.
2\. Sentence-level perplexity can be calculated.
3\. Results are deterministic or reproducibly close under the same configuration.
4\. Runtime is practical enough for development.
5\. Memory usage is acceptable.

**## Result**

**### Configuration**

\- Model: \`distilgpt2\`
\- Runtime: Hugging Face Transformers
\- Device: CPU, explicitly selected with \`torch.device("cpu")\`
\- Python: \`3.12.9\`
\- PyTorch: \`2.13.0+cpu\`
\- Transformers: \`5.15.0\`
\- Dependencies: \`torch\`, \`transformers\`
\- Results artifact: \`experiments/EXP-001-perplexity-feasibility/results/results.json\`

**### Quantitative**

Final cached run:

\| Test ID | Tokens | Usable predictions | Perplexity | Inference time (s) | Tokens/s | Status |
\| --- | ---: | ---: | ---: | ---: | ---: | --- |
\| \`A-very-short\` | 5 | 4 | 2589.029541 | 0.157552 | 25.39 | ok |
\| \`B-medium\` | 20 | 19 | 139.890610 | 0.089811 | 211.56 | ok |
\| \`C-long\` | 44 | 43 | 86.941147 | 0.105136 | 409.00 | ok |
\| \`D-paragraph\` | 53 | 52 | 136.837708 | 0.122329 | 425.08 | ok |
\| \`E-admissions-style\` | 88 | 87 | 65.279907 | 0.141792 | 613.57 | ok |

Performance summary:

\- Cached model load time: \`1.152793\` seconds
\- First successful inference time: \`0.157552\` seconds
\- Median successful inference time: \`0.113733\` seconds
\- Median tokens/second: \`310.28\`
\- Total cached experiment runtime: \`1.961918\` seconds

Reproducibility:

\- Repeated input: \`A-very-short\`
\- Perplexities: \`2589.029541015625\`, \`2589.029541015625\`, \`2589.029541015625\`
\- Maximum absolute difference: \`0.0\`
\- Tolerance: \`1e-9\`

Edge cases:

\| Test ID | Tokens | Usable predictions | Status | Result |
\| --- | ---: | ---: | --- | --- |
\| \`EDGE-empty\` | 0 | 0 | insufficient\_input | no perplexity emitted |
\| \`EDGE-whitespace\` | 9 | 8 | insufficient\_input | no perplexity emitted because there is no lexical content |
\| \`EDGE-extremely-short\` | 1 | 0 | insufficient\_input | no perplexity emitted |
\| \`EDGE-one-usable-prediction\` | 2 | 1 | ok | finite perplexity with warning that evidence is unstable |

**### Qualitative**

The first sandboxed run failed because \`torch\` was not installed. A local \`.venv\` was created and only \`torch\` and \`transformers\` were installed.

The first model-loading attempt then failed inside the sandbox because Hugging Face network access was blocked and \`distilgpt2\` was not cached. After approved network access, the model downloaded and ran. A later run loaded from the local cache successfully.

The implementation uses direct token-level logits and the causal language-model shift:

\`\`\`python
shift\_logits = logits[..., :-1, :].contiguous()
shift\_labels = input\_ids[..., 1:].contiguous()
\`\`\`

This scores token \`i\` using the model context up to token \`i-1\`; the first token is excluded.

**## Interpretation**

Observation: \`distilgpt2\` can produce local token-level logits on CPU, and shifted sentence/paragraph perplexity can be calculated with finite results for valid prose inputs.

Observation: repeated evaluation of one input produced exactly identical perplexity in this environment.

Observation: empty, whitespace-only, and one-token inputs require intentional abstention or warnings. A finite value for a two-token input is mathematically computable but not strong evidence.

Interpretation: local perplexity extraction is technically feasible enough to proceed to the next planned feasibility question. This does not validate perplexity as an authorship detector, set thresholds, compare models, or establish minimum evidence requirements.

**## Decision**

\`PROCEED\`

Local sentence-level perplexity using \`distilgpt2\` is feasible as a measurement instrument for later experiments. Continue only after reviewing EXP-001; the appropriate follow-up is EXP-002, which should study perplexity stability by text length.

**---**

**# EXP-002 — Perplexity Stability by Text Length**

**## Status**

Completed

**## Question**

How stable is perplexity when calculated on very short versus longer text?

**## Hypothesis**

Very short sentences will produce noisier and less reliable perplexity measurements than paragraphs.

**## Procedure**

Evaluate four fixed fictional English passages using progressively longer tokenizer-prefixes from the same underlying passage.

Target prefix lengths:

\`\`\`text
10, 20, 30, 50, 75, 100, 150, 200 tokens
\`\`\`

All four passages contained at least 200 tokens, so actual token counts matched the targets in this run.

Record:

\* token count
\* scored-token count
\* mean NLL
\* perplexity
\* runtime
\* repeated short-prefix measurements
\* variation across passages

**## Purpose**

Determine whether the detector requires minimum text lengths before presenting perplexity as meaningful evidence.

**## Result**

**### Configuration**

\- Model: \`distilgpt2\`
\- Runtime: Hugging Face Transformers
\- Device: CPU, explicitly selected with \`torch.device("cpu")\`
\- Python: \`3.12.9\`
\- PyTorch: \`2.13.0+cpu\`
\- Transformers: \`5.15.0\`
\- Target token counts: \`10\`, \`20\`, \`30\`, \`50\`, \`75\`, \`100\`, \`150\`, \`200\`
\- Repeated conditions: \`10\`, \`20\`, and \`30\` token prefixes, repeated three times per passage
\- Results artifact: \`experiments/EXP-002-perplexity-stability/results/results.json\`

**### Quantitative**

Full passage sizes:

\| Passage | Title | Full tokens | Words |
\| --- | --- | ---: | ---: |
\| \`P1\` | community garden reflection | 253 | 220 |
\| \`P2\` | robotics notebook reflection | 248 | 214 |
\| \`P3\` | family translation reflection | 240 | 211 |
\| \`P4\` | school newspaper reflection | 244 | 223 |

Per-passage perplexity by prefix length:

\| Prefix tokens | P1 | P2 | P3 | P4 |
\| ---: | ---: | ---: | ---: | ---: |
\| 10 | 204.868851 | 376.844910 | 693.277893 | 87.928154 |
\| 20 | 97.032600 | 62.586613 | 219.016129 | 106.312996 |
\| 30 | 57.089981 | 64.374504 | 160.746597 | 91.913048 |
\| 50 | 47.302013 | 57.494602 | 121.868866 | 113.127083 |
\| 75 | 55.648594 | 85.635506 | 93.180351 | 140.889938 |
\| 100 | 72.591942 | 69.265503 | 72.477356 | 123.168907 |
\| 150 | 65.631004 | 61.604309 | 71.152733 | 102.863449 |
\| 200 | 62.536346 | 78.042984 | 67.437241 | 87.700996 |

Cross-passage summary:

\| Prefix tokens | Mean PPL | Median PPL | Min | Max | Stdev | CV |
\| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
\| 10 | 340.73 | 290.86 | 87.93 | 693.28 | 263.29 | 0.77 |
\| 20 | 121.24 | 101.67 | 62.59 | 219.02 | 67.85 | 0.56 |
\| 30 | 93.53 | 78.14 | 57.09 | 160.75 | 47.25 | 0.51 |
\| 50 | 84.95 | 85.31 | 47.30 | 121.87 | 37.98 | 0.45 |
\| 75 | 93.84 | 89.41 | 55.65 | 140.89 | 35.31 | 0.38 |
\| 100 | 84.38 | 72.53 | 69.27 | 123.17 | 25.91 | 0.31 |
\| 150 | 75.31 | 68.39 | 61.60 | 102.86 | 18.78 | 0.25 |
\| 200 | 73.93 | 72.74 | 62.54 | 87.70 | 11.23 | 0.15 |

Reproducibility:

\- Repeated condition count: \`12\`
\- Maximum absolute perplexity difference across repeated runs: \`0\`
\- Tolerance: \`1e-9\`
\- All repeated conditions effectively identical: \`true\`

Performance:

\- Model load time: \`1.048615\` seconds
\- Successful inference runs: \`56\`
\- Median successful inference time: \`0.094373\` seconds
\- Median tokens/second: \`308.67\`
\- Total experiment runtime: \`7.692288\` seconds

**### Qualitative**

The implementation reused the EXP-001 causal alignment:

\`\`\`python
shift\_logits = logits[..., :-1, :].contiguous()
shift\_labels = input\_ids[..., 1:].contiguous()
\`\`\`

Short-prefix repetitions were deterministic in this CPU/evaluation setup. The observed variation came from prefix length and passage content, not stochastic inference.

Within-passage trajectories were not universally monotonic. P1, P2, and P3 dropped sharply from their first 10-token prefix, while P4 started with relatively low perplexity and fluctuated before returning close to its initial value at 200 tokens.

**## Interpretation**

Observation: cross-passage perplexity variation was largest at very short prefixes. At 10 tokens, perplexity ranged from \`87.93\` to \`693.28\` with CV \`0.77\`.

Observation: cross-passage variation decreased as prefixes lengthened. At 200 tokens, perplexity ranged from \`62.54\` to \`87.70\` with CV \`0.15\`.

Interpretation: very short prefixes appear sensitive to the specific opening words and early context. Longer prefixes, especially around 150-200 tokens in this small experiment, produced more stable cross-passage measurements.

This does not prove that longer text is better for detection, does not establish a production minimum evidence threshold, and does not imply that lower perplexity means machine authorship.

**## Decision**

\`PROCEED\`

Continue evaluating perplexity as a candidate measurement, but treat very short sentence-level perplexity as potentially unstable evidence.

Candidate range for later validation: approximately \`150-200\` tokens appeared more stable in this run. This is not a locked threshold.

**## Follow-up**

Proceed to the next planned experiment after review. Later evidence-sufficiency work should test this observation against real segmented dataset samples rather than adopting it directly.

**---**

**# EXP-003 — Local Generation Feasibility

## Status

Completed

## Question

Can a small locally runnable instruction-tuned language model generate coherent essay text at practical speed under the ₹0 constraint?

## Motivation

The controlled dataset plan requires local AI generation for AI-polished/spliced variants. This experiment establishes whether local generation is technically practical before using it in later controlled experiments.

## Configuration

- Candidate models: `Qwen2.5-0.5B-Instruct` and `SmolLM2-135M`
- Runtime: local CPU inference
- Input: one controlled essay-generation prompt per model
- Target: short coherent essay sample
- Hardware: local development machine

## Result

`Qwen2.5-0.5B-Instruct` produced a complete coherent sample in approximately 36 seconds and was selected as the current local generation candidate.

`SmolLM2-135M` was faster but hit the configured output limit and ended mid-sentence in the bounded comparison.

## Interpretation

Local generation is technically feasible under the ₹0 constraint. The selected model is a generation candidate for controlled experiments; this does not establish that it represents all machine-generated prose or that it should be treated as the final generation model without later validation.

## Decision

`PROCEED`

Use `Qwen2.5-0.5B-Instruct` as the current local generation candidate for controlled generation experiments.

---

# EXP-004 — Feature Extraction Laboratory

## Status

Completed

## Question

Can one essay be converted reliably into the quantitative features required by the planned detector?

## Configuration

- Perplexity: validated EXP-001 `distilgpt2` implementation
- Sentence segmentation/POS: spaCy `en_core_web_sm`
- MATTR window: `25` tokens
- Runtime: CPU

## Procedure

For the main fixture, extract per-sentence token count and perplexity, then calculate essay-level sentence-length CV, MATTR, and POS 3-gram entropy.

Also run a very short edge-case input and abstain when a feature does not have enough evidence.

## Result

Main fixture:

- Sentence count: `4`
- Sentence perplexities: `359.442383`, `59.085762`, `392.833679`, `186.261276`
- Sentence-length CV: `0.409558`
- MATTR: `0.951429`
- POS 3-gram entropy: `5.781250`

Edge-case fixture:

- One-token input produced no perplexity.
- Sentence-length CV was unavailable because there were insufficient sentences.
- MATTR was unavailable because there were insufficient tokens for the 25-token window.
- POS 3-gram entropy was unavailable because there were insufficient POS tags for 3-grams.

## Interpretation

The requested feature measurements are technically implementable and can explicitly report insufficient evidence. The experiment validates extraction, not predictive usefulness.

## Decision

`PROCEED`

Reuse the validated feature implementations in later experiments.

---

# EXP-005 — Feature Distribution Sanity Check

## Status

Completed

## Question

Do the EXP-004 candidate features produce measurable paired human-vs-AI distributions on DAIGT External data without training a classifier or setting thresholds?

## Dataset

- Source: `data/raw/daigt_external/daigt_external_dataset.csv`
- Total scanned rows: `2421`
- Usable paired rows: `2421`
- Selected paired rows: `200`
- Pair semantics: `text` = human/student writing; `source_text` = AI-generated text
- Sampling seed: `20260813`
- Raw CSV SHA-256 before and after: `3a1ba6c2ba557b83a13022efadb3239185cda05b50a9d31017fcf7967f33bb18`

## Result

| Feature | Human median | AI median | Paired median diff | Cohen's d |
| --- | ---: | ---: | ---: | ---: |
| perplexity | 98.196951 | 42.932217 | -53.462189 | -1.184548 |
| sentence-length CV | 0.489799 | 0.297963 | -0.211034 | -1.604178 |
| MATTR | 0.850048 | 0.905364 | 0.056470 | 1.929558 |
| POS 3-gram entropy | 7.249802 | 6.665574 | -0.609158 | -1.675681 |

One human sample lacked sentence-length CV. No outliers were removed.

## Interpretation

All four candidate features showed measurable paired differences in this bounded DAIGT sample. This establishes candidate signal worth testing, but not production thresholds or target-domain generalization.

## Decision

`PROCEED TO BASELINE MODELING`

---

# EXP-006 — Baseline Classification

## Status

Completed

## Question

Does the four-feature model improve classification over a perplexity-only baseline on unseen paired DAIGT data?

## Dataset / Split

- Source: 200 paired records from EXP-005
- Pair-level split: `160` training pairs / `40` validation pairs
- Training rows: `320`
- Validation rows: `79` after one missing-feature row was removed
- Seed: `20260814`
- Human and AI members of each pair remained in the same split

## Models

### Perplexity-only baseline

Logistic Regression using standardized perplexity.

### Four-feature model

Logistic Regression using standardized:

- perplexity
- sentence-length CV
- MATTR
- POS 3-gram entropy

## Result

| Metric | Perplexity only | Four features |
| --- | ---: | ---: |
| Accuracy | 0.860759 | **0.974684** |
| Precision | 0.795918 | **0.952381** |
| Recall | 0.975000 | **1.000000** |
| F1 | 0.876404 | **0.975610** |
| ROC-AUC | 0.956410 | **0.995513** |

F1 improvement: `+0.099205`, approximately `+9.9` percentage points.

Standardized coefficients:

- perplexity: `-2.767575`
- sentence-length CV: `-1.318850`
- MATTR: `+2.271050`
- POS 3-gram entropy: `-1.938117`

## Interpretation

Perplexity alone is already a strong baseline. The four-feature model substantially improved validation performance on this controlled, pair-aware DAIGT split.

This is a bounded dataset result and does not establish admissions-domain performance.

## Validation

- Train/validation pair sets were disjoint.
- Both classes were present in both splits.
- No raw datasets were modified.

## Decision

`PROCEED`

Use the four-feature Logistic Regression as the primary global detection baseline.

---

# EXP-007 — Hybrid Local-Anomaly Feasibility

## Status

Completed

## Question

Can a known two-sentence AI passage inserted into an otherwise human essay become locally anomalous relative to the rest of that hybrid?

## Dataset

- Raw source: `data/raw/daigt_external/daigt_external_dataset.csv`
- Exact first 20 pair results from EXP-005
- Successful hybrids: `20`
- Ground-truth inserted AI sentences: `40`
- Raw CSV unchanged

## Method

For each pair:

1. Segment human and AI text using the EXP-004 spaCy pipeline.
2. Select two contiguous AI sentences.
3. Insert them into the human essay at a sentence boundary.
4. Calculate per-sentence perplexity, length, local MATTR, and local POS 3-gram entropy.
5. Compute leave-one-out robust z-scores within each hybrid.
6. Average absolute available z-scores into an experimental anomaly ranking.

## Result

| Capture band | Rate | Count |
| --- | ---: | ---: |
| Top 50% | 55.0% | 22 / 40 |
| Top 25% | 15.0% | 6 / 40 |
| Top 10% | 2.5% | 1 / 40 |

Median anomaly:

- Inserted AI: `0.977125`
- Human: `0.869977`
- Difference: `+0.107147`

## Interpretation

The local anomaly score is computable and sometimes ranks inserted AI sentences highly, but human outliers frequently dominate. It is therefore not sufficiently reliable as a standalone localization mechanism.

## Decision

`PROCEED WITH REVISION`

Revise the local-evidence formulation rather than promoting the current anomaly score.

---

# EXP-008 — Local Window & Feature Contribution Sensitivity

## Status

Completed

## Question

Can changing local context size or restricting the contributing feature set materially improve EXP-007's local anomaly signal?

## Configuration

Same 20 hybrids / 40 ground-truth AI sentences from EXP-007.

Windows: `1`, `3`, `5`, `7` sentences.

Feature configurations:

- perplexity only
- sentence length only
- MATTR only
- POS 3-gram entropy only
- all four

Total configurations: `20`.

## Result

| Window / Feature set | AI − human median anomaly | Top-25% | Top-10% |
| --- | ---: | ---: | ---: |
| 1 / all features | -0.054192 | 22.5% | 7.5% |
| 3 / all features | 0.106537 | 27.5% | 2.5% |
| 5 / all features | 0.113813 | 20.0% | 10.0% |
| 7 / all features | 0.072074 | 22.5% | 7.5% |
| 7 / POS entropy only | 0.413327 | 42.1% | 15.8% |

Additional observations:

- Sentence length alone showed essentially no median separation.
- The apparent 1-sentence MATTR result had incomplete coverage because of the 25-token MATTR requirement.
- No window consistently rescued the all-feature anomaly score.

## Interpretation

Changing window size does not consistently solve the local anomaly problem. POS entropy showed the strongest individual local signal in one larger-window setting, but not enough to justify a standalone production detector.

## Decision

`REVISE LOCAL EVIDENCE FORMULATION`

Do not lock a local anomaly score based on this sensitivity sweep.

---

# EXP-009 — Boundary Discontinuity Feasibility

## Status

Completed

## Question

Can abrupt feature changes across adjacent sentence boundaries localize a known inserted AI passage better than within-document anomaly scoring?

## Dataset

The exact same 20 synthetic hybrids from EXP-007 were reused, producing `40` target boundaries.

Target boundaries were the two boundaries surrounding the inserted AI block:

- human → AI
- AI → human

## Method

For each adjacent sentence boundary, measure:

- raw perplexity change
- log-perplexity change
- sentence-length change
- MATTR change
- POS 3-gram entropy change

Normalize each boundary feature with a within-hybrid robust z-score and calculate an experimental combined boundary score.

## Result

- Target boundaries: `40`
- Top 50% capture: `60.0%`
- Top 25% capture: `32.5%`
- Top 10% capture: `25.0%`
- Target-boundary median minus human-internal-boundary median: `+0.048926`

## Interpretation

Boundary discontinuity contains some localization signal, but separation from ordinary human→human boundaries is small. Individual human boundaries can still rank above the true insertion boundaries.

The experiment therefore does not justify replacing the rejected local anomaly score with a production boundary score.

## Decision

`PROCEED TO EVIDENCE SUFFICIENCY / FINAL LOCAL-EVIDENCE DESIGN`

Treat boundary discontinuity as an experimental supporting signal only, not a standalone detector.

---

# EXP-010 — Evidence Sufficiency & Empirical Abstention

## Status

Completed

## Question

When does the global classifier have enough evidence to make a useful claim, and when should it abstain?

## Objective

The earlier EXP-010 diagnostic only measured feature availability. It did not justify numeric abstention thresholds, so it was replaced by this empirical reproduction and binning experiment.

## Configuration

- Source: EXP-005 paired feature data + EXP-006 baseline protocol
- Model: four-feature Logistic Regression
- Features:
  - perplexity
  - sentence-length CV
  - MATTR
  - POS 3-gram entropy
- Pair split: `160` train / `40` validation
- Validation rows: `79`
- Seed: `20260814`
- Standardization fitted on training data only

## Reproduction Check

The EXP-006 model was recreated before any abstention analysis.

Reproduced metrics matched the saved EXP-006 metrics exactly:

| Metric | Reproduced |
| --- | ---: |
| Accuracy | 0.974684 |
| Precision | 0.952381 |
| Recall | 1.000000 |
| F1 | 0.975610 |
| ROC-AUC | 0.995513 |

All metric deltas were `0.0`.

## Text-Length Analysis

The validation set did not contain sufficiently short examples to empirically establish a minimum text-length threshold.

Observed bins:

| Word-count bin | Samples | Accuracy | F1 |
| --- | ---: | ---: | ---: |
| 81–100 | 1 | 1.000000 | 1.000000 |
| 101–150 | 8 | 1.000000 | 1.000000 |
| 151–200 | 9 | 1.000000 | 1.000000 |
| 201+ | 61 | 0.967213 | 0.960000 |

The absence of shorter validation samples means this experiment cannot defensibly derive a cutoff such as `40 words`.

EXP-002 nevertheless showed that short prefixes are substantially less stable for perplexity measurement: cross-passage CV was `0.77` at 10 tokens versus `0.15` at 200 tokens. This is evidence for caution with short inputs, not a validated classifier threshold.

## Confidence-Margin Analysis

Confidence margin is:

```text
abs(P(AI) - 0.5)
```

The validation distribution was heavily concentrated at high margins.

- `0.00–0.05`: `1` sample, accuracy `0.0`
- `0.35–0.40`: `6` samples, accuracy `0.833333`
- `0.40–0.45`: `9` samples, accuracy `1.0`
- `0.45–0.50`: `57` samples, accuracy `1.0`

The single near-boundary example was a human sample with `P(AI)=0.51885` and was misclassified. The sample is useful as a qualitative example of uncertainty, but there are not enough near-boundary cases to validate a numeric confidence dead-zone.

## Interpretation

This experiment supports an abstention *architecture* but does not support a statistically validated numeric threshold.

The defensible production behavior is therefore:

1. **Hard insufficiency:** abstain when required feature measurements cannot be computed reliably.
2. **Soft uncertainty:** expose classifier uncertainty near the decision boundary without claiming that an exact numeric dead-zone has been empirically validated.
3. **No forced verdict:** missing or contradictory evidence should not be converted into a confident AI/human claim.

## Decision

`PROCEED TO IMPLEMENTATION WITH CONSERVATIVE ABSTENTION`

Do not lock an arbitrary minimum word-count threshold or confidence-margin threshold from this bounded validation set.

## Follow-up

Close the feasibility experiment loop and begin the production detection pipeline. Further experiments such as OOD/topic generalization, unseen-model evaluation, ESL bias auditing, and failure analysis should be performed after a working detector exists and should be treated as refinement/evaluation rather than prerequisites for implementation.

---

# 6. Experiment Promotion Rules**

An experimental finding may influence the production system when:

1\. The experiment is reproducible.
2\. The result is recorded.
3\. The interpretation is supported by the result.
4\. The change does not compromise test-set integrity.
5\. The resulting decision is documented.

A feature should not be promoted simply because it produces the highest score on one run.

**---**

**# 7. Rejected Hypotheses**

Rejected ideas remain documented.

Example:

\`\`\`markdown
**## EXP-XXX**

Hypothesis:
POS entropy improves classification.

Result:
No meaningful improvement and increased ESL false positives.

Decision:
Rejected.

Reason:
The feature did not provide sufficient value relative to its
computational and bias cost.
\`\`\`

This is useful engineering evidence.

**---**

**# 8. Experiment Naming Convention**

Use:

\`\`\`text
EXP-XXX-short-description
\`\`\`

Examples:

\`\`\`text
EXP-001-perplexity-feasibility
EXP-002-perplexity-length-stability
EXP-007-local-baseline-stability
EXP-011-feature-ablation
\`\`\`

Experiment outputs should use the same identifier.

**---**

**# 9. Experiment Reproducibility**

Every experiment should record enough information to rerun it.

At minimum:

\* experiment ID
\* code version / commit
\* dataset version
\* model
\* model version
\* feature configuration
\* parameters
\* random seed where applicable
\* hardware
\* runtime
\* result artifacts

**---**

**# 10. Experiment Artifacts**

A possible structure:

\`\`\`text
experiments/
├── EXP-001-perplexity-feasibility/
│   ├── README.md
│   ├── config.json
│   ├── results.json
│   └── output/
│
├── EXP-002-perplexity-length-stability/
│   ├── README.md
│   ├── config.json
│   └── output/
│
└── ...
\`\`\`

The exact structure may change.

Experiments should remain separable from production application code.

**---**

**# 11. Current Experiment Queue

| ID | Experiment | Status |
| --- | --- | --- |
| EXP-001 | Local perplexity feasibility | Completed |
| EXP-002 | Perplexity stability by text length | Completed |
| EXP-003 | Local generation feasibility | Completed |
| EXP-004 | Feature extraction laboratory | Completed |
| EXP-005 | Feature distribution sanity check | Completed |
| EXP-006 | Baseline classification | Completed |
| EXP-007 | Hybrid local-anomaly feasibility | Completed |
| EXP-008 | Local window & feature sensitivity | Completed |
| EXP-009 | Boundary discontinuity feasibility | Completed |
| EXP-010 | Evidence sufficiency & empirical abstention | Completed |
| EXP-011 | Logistic Regression vs Random Forest | Planned |
| EXP-012 | Feature ablation | Planned |
| EXP-013 | Hybrid detection | Planned |
| EXP-014 | Global vs local signal | Planned |
| EXP-015 | Topic generalization | Planned |
| EXP-016 | Unseen model generalization | Planned |
| EXP-017 | ESL bias audit | Planned |
| EXP-018 | Confident failure analysis | Planned |

The order may change based on feasibility results.

---

# 12. Current Status

**Phase:** 1 — Research & Feasibility

**Status:** EXP-001 through EXP-010 completed.

Current evidence supports:

- local perplexity extraction is technically feasible;
- very short prefixes produce less stable perplexity measurements than longer prefixes;
- the four candidate features show measurable paired signal on the controlled DAIGT sample;
- the four-feature Logistic Regression baseline substantially outperformed the perplexity-only baseline on the bounded pair-aware validation split;
- the initial within-document local anomaly score is not reliable enough to serve as the primary localization mechanism;
- local window and feature sensitivity did not consistently rescue the anomaly score;
- boundary discontinuity shows some signal but does not provide sufficiently strong separation for a standalone production local detector;
- feature measurement failures should result in abstention rather than fabricated values;
- the bounded validation data do not justify a universal numeric minimum-word or confidence dead-zone threshold.

The research phase is now complete for the purposes of beginning implementation.

> **Next: build the production detection pipeline using the four-feature Logistic Regression as the primary global signal, with conservative insufficient-evidence handling.**

Further experiments should be treated as post-implementation evaluation/refinement rather than prerequisites for the first working detector.
