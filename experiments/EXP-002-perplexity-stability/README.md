# EXP-002 - Perplexity Stability by Text Length

## Status

Completed.

## Question

How stable is perplexity when calculated on very short versus longer text prefixes from the same underlying passages?

## Hypothesis

Very short inputs may produce noisier and less reliable perplexity measurements than longer passage-level inputs.

This experiment does not assume the hypothesis is true; it records how `distilgpt2` perplexity behaved on the fixed test passages.

## Model

- Model identifier: `distilgpt2`
- Source: Hugging Face Transformers
- Execution device: CPU
- Role: token-probability instrument only, not a detector or authorship judge

## Environment

Measured environment:

- OS/platform: Windows 11, AMD64
- Python: `3.12.9`
- PyTorch: `2.13.0+cpu`
- Transformers: `5.15.0`
- Device explicitly selected in code: `torch.device("cpu")`

The model was loaded from the local Hugging Face cache. No model weights are stored in the experiment directory.

## Method

The experiment uses four fixed, fictional English passages. For each passage, the tokenizer encodes the full text once, then evaluates tokenizer-prefixes targeting:

```text
10, 20, 30, 50, 75, 100, 150, 200 tokens
```

All four passages contained at least 200 tokens, so the actual prefix token counts matched the targets in this run. Each prefix is the first `N` tokenizer tokens from the same underlying passage; the experiment does not compare unrelated short and long texts.

Shorter conditions at 10, 20, and 30 tokens were repeated three times per passage. Longer conditions were run once per passage.

## Token Alignment

The perplexity calculation reuses the EXP-001 causal alignment:

```text
input_ids:
[t1, t2, t3, t4]

shift_logits:
prediction for t2
prediction for t3
prediction for t4

shift_labels:
[t2, t3, t4]
```

The first token is excluded because it has no preceding-token prediction inside the supplied sequence.

```python
shift_logits = logits[..., :-1, :].contiguous()
shift_labels = input_ids[..., 1:].contiguous()
```

Perplexity is calculated as `exp(mean NLL)` from token-level cross entropy over the shifted logits and labels.

## Test Passages

| Passage | Title | Full tokens | Words |
| --- | --- | ---: | ---: |
| `P1` | community garden reflection | 253 | 220 |
| `P2` | robotics notebook reflection | 248 | 214 |
| `P3` | family translation reflection | 240 | 211 |
| `P4` | school newspaper reflection | 244 | 223 |

## Results

Machine-readable results are stored in `results/results.json`.

### Per-Passage Perplexity

| Prefix tokens | P1 | P2 | P3 | P4 |
| ---: | ---: | ---: | ---: | ---: |
| 10 | 204.868851 | 376.844910 | 693.277893 | 87.928154 |
| 20 | 97.032600 | 62.586613 | 219.016129 | 106.312996 |
| 30 | 57.089981 | 64.374504 | 160.746597 | 91.913048 |
| 50 | 47.302013 | 57.494602 | 121.868866 | 113.127083 |
| 75 | 55.648594 | 85.635506 | 93.180351 | 140.889938 |
| 100 | 72.591942 | 69.265503 | 72.477356 | 123.168907 |
| 150 | 65.631004 | 61.604309 | 71.152733 | 102.863449 |
| 200 | 62.536346 | 78.042984 | 67.437241 | 87.700996 |

### Cross-Passage Summary

| Prefix tokens | Mean PPL | Median PPL | Min | Max | Stdev | CV | Mean NLL mean | Mean NLL stdev |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10 | 340.73 | 290.86 | 87.93 | 693.28 | 263.29 | 0.77 | 5.57 | 0.88 |
| 20 | 121.24 | 101.67 | 62.59 | 219.02 | 67.85 | 0.56 | 4.69 | 0.52 |
| 30 | 93.53 | 78.14 | 57.09 | 160.75 | 47.25 | 0.51 | 4.45 | 0.46 |
| 50 | 84.95 | 85.31 | 47.30 | 121.87 | 37.98 | 0.45 | 4.36 | 0.48 |
| 75 | 93.84 | 89.41 | 55.65 | 140.89 | 35.31 | 0.38 | 4.49 | 0.38 |
| 100 | 84.38 | 72.53 | 69.27 | 123.17 | 25.91 | 0.31 | 4.40 | 0.27 |
| 150 | 75.31 | 68.39 | 61.60 | 102.86 | 18.78 | 0.25 | 4.30 | 0.23 |
| 200 | 73.93 | 72.74 | 62.54 | 87.70 | 11.23 | 0.15 | 4.29 | 0.15 |

Observation: cross-passage perplexity variation was highest for the shortest prefixes and lower for the longest prefixes. The coefficient of variation decreased from `0.77` at 10 tokens to `0.15` at 200 tokens.

## Reproducibility

The 10, 20, and 30 token conditions were repeated three times for each passage, for 12 repeated conditions.

- Max absolute perplexity difference across repeated runs: `0`
- Tolerance: `1e-9`
- All repeated conditions effectively identical: `true`

Observation: repeated measurements were deterministic in this CPU/evaluation setup. The variation observed across prefix lengths is therefore not caused by stochastic inference.

## Performance

- Model load time: `1.048615` seconds
- Successful inference runs: `56`
- Median successful inference time: `0.094373` seconds
- Median tokens/second: `308.67`
- Total experiment runtime: `7.692288` seconds

## Interpretation

Observation: the shortest prefixes produced the largest cross-passage spread. At 10 tokens, perplexity ranged from `87.93` to `693.28`; at 200 tokens, it ranged from `62.54` to `87.70`.

Observation: within-passage trajectories were not universally monotonic. P1, P2, and P3 dropped sharply from their first 10-token prefix, while P4 started with relatively low perplexity and fluctuated before returning close to its initial value at 200 tokens.

Interpretation: very short prefixes appear sensitive to the specific opening words and early context. Longer prefixes, especially around 150-200 tokens in this small experiment, produced lower cross-passage variation. This suggests that passage-level perplexity is likely more stable than very short sentence-level perplexity.

This does not prove that longer text is better for detection, does not establish a production threshold, and does not show that lower perplexity means machine authorship.

## Candidate Evidence Range

The observed data supports a tentative candidate range of approximately 150-200 tokens for more stable perplexity measurement in later experiments.

This is not a production minimum evidence threshold. It is only a candidate range to test further with more passages, real dataset samples, sentence/passsage segmentation, and downstream evaluation.

## Decision

`PROCEED`

Proceed to the next planned feasibility experiment after review. EXP-002 supports continuing to evaluate perplexity, while treating very short sentence-level measurements as potentially unstable evidence.

## Limitations

- Only four fixed fictional passages were tested.
- All passages were reflective/admissions-style, but they are not a real dataset.
- Prefixes were token-count based, not sentence-boundary based.
- No classification experiment was performed.
- No production threshold was selected.
- Memory usage was not measured.
- The experiment used only `distilgpt2`; no model comparison was performed.

