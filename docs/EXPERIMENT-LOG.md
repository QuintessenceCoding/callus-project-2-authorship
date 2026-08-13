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

Planned

## Question

Can a small locally runnable instruction-tuned language model generate coherent essay text at practical speed under the ₹0 constraint?

## Hypothesis

A sufficiently small open-weight instruction-tuned model should be capable of generating coherent short essay samples locally on consumer hardware, but model size, runtime overhead, and generation speed may create practical trade-offs.

## Motivation

The dataset requires locally generated AI, polished, and spliced variants. Before constructing any Essay Families, we need to establish that local generation is technically practical and reproducible under the project's ₹0 constraint.

This experiment evaluates generation feasibility only. It does not evaluate AI-detection accuracy and does not authorize full dataset generation.

## Dataset / Inputs

- Dataset version: N/A
- Input source: Controlled generation prompt
- Number of inputs: One shared task prompt per candidate model
- Categories: N/A
- Split: N/A
- Reason: This is a local runtime feasibility experiment, not a dataset evaluation.

## Configuration

- Candidate models: Two small locally runnable instruction-tuned open-weight models
- Runtime: Free local inference runtime
- Device: CPU unless the environment requires otherwise
- Target output: approximately 300–500 words
- Generation parameters: recorded after implementation
- Random seed: recorded where supported

The models must be practical to download and run in the available environment. This bounded experiment should not select a 7B+ model.

## Procedure

1. Select two small candidate instruction-tuned models that satisfy the ₹0/local constraint.
2. Run the same controlled essay-generation task with each model.
3. Generate one short sample per model.
4. Record actual model loading and generation measurements.
5. Inspect the generated outputs for basic quality and prompt leakage.
6. Compare practical speed, output length, and quality.
7. Recommend whether local generation should proceed to the pilot.

Generated samples are experiment artifacts only and must not become the actual project dataset.

## Metrics

Record:

- model name/version
- runtime
- model size where available
- model load time
- generation time
- output token count
- tokens/second where measurable
- successful/failed generation
- basic quality observations
- prompt leakage or malformed-output observations

## Result

**TBD**

### Quantitative

Record actual measurements after execution.

### Qualitative

Record actual observations from the generated samples.

## Interpretation

Separate measured observations from hypotheses.

The experiment must not claim that the selected model is suitable for AI detection merely because it generates coherent text. It only establishes whether the model/runtime combination is practical for controlled dataset generation.

## Decision

**TBD**

Allowed outcomes:

- `PROCEED`
- `PROCEED WITH SMALLER MODEL`
- `BLOCKED`

Explain the decision using the observed generation success, speed, and output quality.

## Follow-up

If feasible, finalize the generation model/runtime and move to the controlled generation pilot and prompt-versioning work. Do not construct the full dataset directly from this experiment.

---

# EXP-004 — Sentence Segmentation Feasibility**

**## Question**

Can \`spaCy\` reliably segment admissions-style essays into usable sentences?

**## Hypothesis**

A standard English spaCy pipeline will provide sufficiently reliable sentence boundaries for the target domain.

**## Procedure**

Test against essays containing:

\* abbreviations
\* quotations
\* punctuation-heavy sentences
\* dialogue
\* unusual formatting
\* short fragments

Record obvious segmentation errors.

**## Purpose**

Sentence boundaries affect every downstream feature.

**## Result**

**\*\*TBD\*\***

**## Decision**

**\*\*TBD\*\***

**---**

**# EXP-005 — Feature Distribution Sanity Check**

**## Status**

Completed

**## Question**

Do the EXP-004 candidate features produce measurable paired human-vs-AI distributions on DAIGT External data without training a classifier or setting thresholds?

**## Dataset**

- Dataset: DAIGT External local CSV
- Source path: `data/raw/daigt_external/daigt_external_dataset.csv`
- Total scanned rows: `2421`
- Usable paired rows: `2421`
- Selected paired rows: `200`
- Pair semantics: `text` = human/student writing; `source_text` = AI-generated text from the same CSV row
- Raw CSV SHA-256 before and after run: `3a1ba6c2ba557b83a13022efadb3239185cda05b50a9d31017fcf7967f33bb18`

**## Configuration**

- Random seed: `20260813`
- Sample target: `200` paired records
- Perplexity model: `distilgpt2`
- Runtime: Hugging Face Transformers on CPU
- Sentence/POS pipeline: spaCy `en_core_web_sm`
- Feature source: EXP-004 feature implementations reused for `sentence_length_cv`, `mattr`, lexical tokenization, and `pos_3gram_entropy`; perplexity reused from EXP-001 through EXP-004.
- Document perplexity summary: median of valid sentence perplexities
- Results artifact: `experiments/EXP-005-feature-distribution/results/results.json`

**## Procedure**

1. Scan the DAIGT External CSV for rows with both `text` and `source_text`.
2. Select a deterministic sample of 200 usable rows using seed `20260813`.
3. Preserve each row as a human/AI pair from the same source row.
4. Extract the four candidate features for each side of each pair.
5. Summarize class distributions and paired AI-minus-human differences.
6. Validate sample size, uniqueness, pair preservation, feature availability, summary consistency, and raw dataset integrity.

No classifier, thresholds, anomaly scoring, or feature promotion/rejection decisions were performed.

**## Metrics**

For each feature and class:

- valid count
- missing/abstained count
- mean
- median
- standard deviation
- IQR
- min
- max

For human-vs-AI comparison:

- class medians
- AI-minus-human median difference
- paired AI-minus-human differences where both values are valid
- Cohen's d where valid
- range and IQR overlap ratios

**## Result**

**### Quantitative**

Class distribution summary:

| Feature | Class | Valid | Missing | Mean | Median | Stdev | IQR | Min | Max |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| perplexity | human | 200 | 0 | 118.607749 | 98.196951 | 87.340346 | 56.245147 | 33.789711 | 799.672791 |
| perplexity | AI | 200 | 0 | 44.676744 | 42.932217 | 12.743399 | 14.562595 | 20.824144 | 120.996506 |
| sentence_length_cv | human | 199 | 1 | 0.527162 | 0.489799 | 0.179204 | 0.194288 | 0.153779 | 1.188102 |
| sentence_length_cv | AI | 200 | 0 | 0.300048 | 0.297963 | 0.089636 | 0.124705 | 0.053878 | 0.624626 |
| MATTR | human | 200 | 0 | 0.845757 | 0.850048 | 0.034253 | 0.043237 | 0.713290 | 0.916962 |
| MATTR | AI | 200 | 0 | 0.903339 | 0.905364 | 0.024655 | 0.029848 | 0.811667 | 0.947191 |
| POS 3-gram entropy | human | 200 | 0 | 7.236224 | 7.249802 | 0.393334 | 0.550990 | 6.267128 | 8.025335 |
| POS 3-gram entropy | AI | 200 | 0 | 6.631243 | 6.665574 | 0.325549 | 0.450480 | 5.821791 | 7.396942 |

Human-vs-AI summary:

| Feature | Human median | AI median | Median diff, AI - human | Paired valid | Paired missing | Paired median diff | Cohen's d, AI - human | Range overlap | IQR overlap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| perplexity | 98.196951 | 42.932217 | -55.264734 | 200 | 0 | -53.462189 | -1.184548 | 0.111969 | 0.000000 |
| sentence_length_cv | 0.489799 | 0.297963 | -0.191836 | 199 | 1 | -0.211034 | -1.604178 | 0.415126 | 0.000000 |
| MATTR | 0.850048 | 0.905364 | 0.055316 | 200 | 0 | 0.056470 | 1.929558 | 0.450171 | 0.000000 |
| POS 3-gram entropy | 7.249802 | 6.665574 | -0.584228 | 200 | 0 | -0.609158 | -1.675681 | 0.512726 | 0.000000 |

Paired direction counts:

| Feature | AI > human | AI < human | AI = human |
| --- | ---: | ---: | ---: |
| perplexity | 12 | 188 | 0 |
| sentence_length_cv | 18 | 181 | 0 |
| MATTR | 190 | 10 | 0 |
| POS 3-gram entropy | 14 | 186 | 0 |

Runtime: `683.744290` seconds.

**### Qualitative**

All four features produced measurable paired distributions. One human row abstained for `sentence_length_cv` because at least two sentences are required for CV. No outliers were removed.

The observed class medians differed for all four features in this sample. The IQR overlap ratio was `0.0` for all four features, while min-max ranges overlapped for all four features. These observations are limited to this DAIGT External paired sample and do not establish thresholds, classifier performance, target-domain generalization, or final feature inclusion.

**## Validation**

All configured validation checks passed:

- expected sample size reached
- selected row indices and IDs are unique
- pair results match selected source row indices and IDs
- pair count equals selected count
- raw dataset checksum unchanged
- finite feature values when present
- MATTR values remain in `[0, 1]`
- distribution summary counts match pair-level feature availability

**## Decision**

`PROCEED TO BASELINE MODELING`

The distribution sanity check is complete and supports running a bounded baseline/modeling experiment next. EXP-005 does not promote or reject any feature by itself.

**## Follow-up**

Run a paired-data baseline experiment with explicit train/validation separation, beginning with a perplexity-only baseline and then the four-feature set. Threshold/model decisions should be made only inside the development split protocol and not on final test data.

**---**

**# EXP-006 — Feature Distribution Sanity Check**

**## Question**

Do candidate features produce sensible distributions across the available categories?

**## Hypothesis**

Some candidate features will show separation between human and machine-generated text, but significant overlap will remain.

**## Procedure**

Plot and summarize feature distributions across:

\* human
\* AI
\* hybrid
\* ESL/control where available

Inspect:

\* overlap
\* outliers
\* suspiciously perfect separation
\* length effects

**## Important Constraint**

A feature that perfectly separates the categories should be treated as suspicious rather than immediately celebrated.

Perfect separation may indicate:

\* metadata leakage
\* source artifacts
\* topic confounding
\* generation artifacts

**## Result**

**\*\*TBD\*\***

**## Decision**

**\*\*TBD\*\***

**---**

**# EXP-007 — Perplexity Baseline**

**## Question**

How well does perplexity alone classify the available data?

**## Hypothesis**

Perplexity should provide meaningful signal but will not reliably distinguish all human and machine-generated examples.

**## Procedure**

Train/select a threshold using training/validation data.

Evaluate on the appropriate held-out set.

Record:

\* accuracy
\* precision
\* recall
\* F1
\* FPR
\* FNR

**## Result**

**\*\*TBD\*\***

**## Decision**

**\*\*TBD\*\***

**---**

**# EXP-008 — Local Baseline Stability**

**## Question**

Can a local stylistic baseline be estimated reliably using robust statistics?

**## Hypothesis**

Median/MAD with leave-one-out exclusion will be more stable than mean/std when local outliers are present.

**## Comparison**

Compare:

**### Method A**

Mean + standard deviation

**### Method B**

Median + MAD

**### Method C**

Leave-one-out median + MAD

**### Method D**

Leave-one-out local-window median + MAD

**## Test Conditions**

Include:

\* normal human essays
\* AI-spliced essays
\* AI-polished essays
\* very short essays
\* essays with few sentences

**## Metrics**

Record:

\* baseline stability
\* anomaly-score stability
\* zero/near-zero MAD frequency
\* ability to identify known transformed passages

**## Result**

**\*\*TBD\*\***

**## Decision**

**\*\*TBD\*\***

**---**

**# EXP-009 — Local Window Size**

**## Question**

What local context size provides the most stable and useful anomaly measurement?

**## Candidate Windows**

\`\`\`text
±2 sentences
±3 sentences
±4 sentences
paragraph-level
whole-document
\`\`\`

**## Hypothesis**

A local window should better capture stylistic discontinuities than a whole-document baseline while remaining sufficiently large for stable statistics.

**## Result**

**\*\*TBD\*\***

**## Decision**

**\*\*TBD\*\***

**---**

**# EXP-010 — Evidence Sufficiency Thresholds**

**## Question**

At what text/context sizes do the detector's measurements become too unstable to support a strong interpretation?

**## Candidate Inputs**

Vary:

\* sentence length
\* passage length
\* number of neighboring sentences
\* number of available baseline observations

Record:

\* feature stability
\* anomaly stability
\* perplexity stability
\* classification confidence

**## Goal**

Define conditions under which the system should return:

\`\`\`text
Insufficient Evidence
\`\`\`

rather than forcing a classification.

**## Result**

**\*\*TBD\*\***

**## Decision**

**\*\*TBD\*\***

**---**

**# EXP-011 — Logistic Regression vs Random Forest**

**## Question**

Does a nonlinear classifier provide meaningful value over a transparent linear classifier?

**## Candidates**

**### Logistic Regression**

Advantages:

\* interpretable
\* fast
\* simple
\* easy to calibrate

**### Random Forest**

Advantages:

\* nonlinear relationships
\* minimal distribution assumptions
\* potentially stronger performance

**## Comparison**

Evaluate using the same:

\* dataset
\* features
\* split
\* evaluation metrics

**## Decision Criteria**

Consider:

\* F1
\* precision
\* recall
\* FPR
\* calibration
\* OOD performance
\* computational cost
\* interpretability

**## Result**

**\*\*TBD\*\***

**## Decision**

**\*\*TBD\*\***

**---**

**# EXP-012 — Feature Ablation**

**## Question**

Which candidate feature groups provide incremental value?

**## Baseline**

Perplexity only.

**## Progression**

\`\`\`text
Perplexity
    ↓
\+ Rhythm
    ↓
\+ Lexical
    ↓
\+ Syntax
    ↓
\+ Repetition
    ↓
\+ Local consistency
\`\`\`

**## Goal**

Determine which feature groups:

\* improve performance
\* add redundancy
\* hurt generalization
\* increase bias
\* increase computational cost without sufficient benefit

**## Result**

**\*\*TBD\*\***

**## Decision**

**\*\*TBD\*\***

**---**

**# EXP-013 — Hybrid Detection**

**## Question**

Can the detector identify localized machine-associated writing inside otherwise human essays?

**## Test Cases**

**### AI Polishing**

Selected human passages modified by a local model.

**### AI Splicing**

Selected passages replaced with newly generated text.

**## Metrics**

Evaluate:

\* document-level classification
\* sentence-level classification
\* localization precision
\* localization recall
\* passage overlap
\* false-positive spillover

**## Result**

**\*\*TBD\*\***

**## Decision**

**\*\*TBD\*\***

**---**

**# EXP-014 — Global vs Local Signal**

**## Question**

Does combining machine association with local stylistic anomaly improve interpretation of hybrid writing?

**## Compare**

**### Global only**

\`\`\`text
S\_global
\`\`\`

**### Local only**

\`\`\`text
S\_local
\`\`\`

**### Combined**

\`\`\`text
S\_global + S\_local
\`\`\`

**## Important**

The combination method should not be assumed beforehand.

Candidate methods may include:

\* rule-based interpretation
\* classifier input
\* calibrated combination
\* evidence matrix

The simplest defensible method should be preferred.

**## Result**

**\*\*TBD\*\***

**## Decision**

**\*\*TBD\*\***

**---**

**# EXP-015 — Topic Generalization**

**## Question**

Does the detector generalize to an unseen topic cluster?

**## Procedure**

Hold out a topic cluster from training.

Evaluate on that topic only.

**## Result**

**\*\*TBD\*\***

**## Decision**

**\*\*TBD\*\***

**---**

**# EXP-016 — Unseen Model Generalization**

**## Question**

Does the detector generalize to a generation model that was not present during training?

**## Procedure**

Train using available model families except one.

Evaluate on the held-out generation model.

**## Interpretation**

A performance drop should be documented rather than automatically treated as an implementation failure.

**## Result**

**\*\*TBD\*\***

**## Decision**

**\*\*TBD\*\***

**---**

**# EXP-017 — ESL Bias Audit**

**## Question**

Does the detector produce a disproportionately high false-positive rate on the ESL/non-native-English control set?

**## Compare**

\* general human test set
\* ESL/control set

Metrics:

\* FPR
\* machine-association score
\* evidence strength
\* feature distributions

**## Result**

**\*\*TBD\*\***

**## Decision**

**\*\*TBD\*\***

**---**

**# EXP-018 — Confident Failure Analysis**

**## Question**

What causes the detector's strongest incorrect predictions?

**## Procedure**

Select at least three confident failures.

For each:

1\. inspect text
2\. inspect feature vector
3\. inspect global signal
4\. inspect local signal
5\. inspect evidence sufficiency
6\. identify likely failure mechanism
7\. determine whether mitigation is justified

**## Result**

**\*\*TBD\*\***

**## Decision**

**\*\*TBD\*\***

**---**

**# 6. Experiment Promotion Rules**

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
| EXP-004 | Sentence segmentation feasibility | Planned |
| EXP-005 | Candidate feature extraction | Planned |
| EXP-006 | Feature distribution sanity check | Planned |
| EXP-007 | Perplexity baseline | Planned |
| EXP-008 | Local baseline stability | Planned |
| EXP-009 | Local window size | Planned |
| EXP-010 | Evidence sufficiency thresholds | Planned |
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

**Status:** EXP-001 and EXP-002 completed. Human-source inspection and the generation protocol have been established.

The next experiment to execute is:

> **EXP-003 — Local Generation Feasibility**

EXP-003 will determine whether local instruction-tuned generation is practical under the ₹0 constraint before any Essay Families are constructed.

No production detection architecture should depend on a specific generation model or runtime until the relevant feasibility experiment has been completed.
