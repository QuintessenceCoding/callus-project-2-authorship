# EXP-004 - Feature Extraction Laboratory

## Status

Completed.

## Scope

This is a feature extraction experiment only.

It does not:

- train a classifier
- build API/frontend components
- process the full dataset
- generate AI text
- implement global/local anomaly scoring
- choose production thresholds

## Goal

Convert fixed essay fixtures into quantitative linguistic features at sentence and essay levels.

## Inputs

This experiment uses only local fixed fixtures embedded in `run.py`:

- `fixture-main-essay` (4-sentence essay)
- `fixture-edge-short` (`"Hi"`)

No raw project dataset files are used.

## Methods

- Sentence segmentation and POS tagging: spaCy `en_core_web_sm`
- Perplexity model: `distilgpt2` on CPU
- Perplexity implementation: reuses `calculate_perplexity` from `experiments/EXP-001-perplexity-feasibility/run.py` (same causal-shift logic)
- Essay-level features:
  - sentence length coefficient of variation (CV)
  - MATTR with window size 25 over lowercase alphabetic tokens
  - POS 3-gram entropy (Shannon entropy, base 2)

## Environment

- Python: `3.12.9`
- Torch: `2.13.0+cpu`
- Transformers: `5.15.0`
- spaCy: `3.8.15`
- Device: CPU

## Actual Results

Results file: `results/results.json`

### Fixture: `fixture-main-essay`

- Sentence count: `4`
- Sentence features:
  - S1 token_count=`10`, perplexity=`359.4423828125`
  - S2 token_count=`29`, perplexity=`59.08576202392578`
  - S3 token_count=`17`, perplexity=`392.83367919921875`
  - S4 token_count=`20`, perplexity=`186.2612762451172`
- Essay features:
  - sentence_length_cv=`0.4095582814689554`
  - MATTR=`0.9514285714285714`
  - POS 3-gram entropy=`5.78125`

### Fixture: `fixture-edge-short`

- Sentence count: `1`
- Sentence features:
  - S1 token_count=`1`, perplexity=`null`, status=`insufficient_input`
- Essay features:
  - sentence_length_cv=`null` (reason: insufficient sentences)
  - MATTR=`null` (reason: insufficient tokens for window=25)
  - POS 3-gram entropy=`null` (reason: insufficient POS tags for 3-grams)

## Validation

All configured validations passed for both fixtures:

- sentence count consistency
- non-negative token counts
- finite perplexity for successful runs
- finite CV when enough sentences exist
- MATTR in valid range when available
- finite POS entropy when enough POS 3-grams exist

Global validation result: `true`.

## Reproducibility

Run:

```bash
python experiments/EXP-004-feature-extraction/run.py
```

Output:

- `experiments/EXP-004-feature-extraction/results/results.json`
