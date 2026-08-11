# EXP-001 — Local Perplexity Feasibility

## Status

Completed.

## Question

Can we reliably calculate sentence-level perplexity using a locally runnable causal language model on the available development environment?

## Hypothesis

A small causal language model should be capable of producing token-level log probabilities locally with sufficiently correct numerical behavior and practical runtime for later experiments.

## Model

- Model identifier: `distilgpt2`
- Source: Hugging Face Transformers
- Execution device: CPU
- Role: token-probability instrument only, not a detector or judge

## Environment

Final measured environment:

- OS/platform: Windows 11, AMD64
- Python: `3.12.9`
- PyTorch: `2.13.0+cpu`
- Transformers: `5.15.0`
- Device explicitly selected in code: `torch.device("cpu")`

The model was downloaded into the normal local Hugging Face cache, outside the repository. No model weights are stored in the experiment directory.

## Method

The experiment loads `distilgpt2` with `AutoModelForCausalLM` and `AutoTokenizer`, sets `tokenizer.pad_token = tokenizer.eos_token` if needed, moves the model to CPU, and runs it in evaluation mode under `torch.inference_mode()`.

Perplexity is calculated directly from logits, not through a black-box helper:

1. Tokenize one input at a time.
2. Run the causal language model to obtain logits.
3. Shift logits and labels so each token is scored from its preceding context.
4. Calculate token-level negative log likelihood with `F.cross_entropy(..., reduction="none")`.
5. Average token NLL.
6. Exponentiate mean NLL to produce perplexity.

## Token Alignment

The experiment uses the required causal alignment:

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

The first token is excluded because it has no preceding-token prediction inside the supplied sequence. The implementation uses:

```python
shift_logits = logits[..., :-1, :].contiguous()
shift_labels = input_ids[..., 1:].contiguous()
```

## Test Inputs

The fixed non-private inputs are embedded in `run.py`:

- `A-very-short`: short sentence
- `B-medium`: normal multi-clause sentence
- `C-long`: longer sentence
- `D-paragraph`: short multi-sentence paragraph
- `E-admissions-style`: fictional admissions-style paragraph written for this experiment

Additional edge cases:

- `EDGE-empty`
- `EDGE-whitespace`
- `EDGE-extremely-short`
- `EDGE-one-usable-prediction`

## Results

Observation: valid prose inputs produced finite perplexity values using CPU-only inference and shifted token-level logits.

| Test ID | Tokens | Usable predictions | Perplexity | Inference time (s) | Tokens/s | Status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `A-very-short` | 5 | 4 | 2589.029541 | 0.157552 | 25.39 | ok |
| `B-medium` | 20 | 19 | 139.890610 | 0.089811 | 211.56 | ok |
| `C-long` | 44 | 43 | 86.941147 | 0.105136 | 409.00 | ok |
| `D-paragraph` | 53 | 52 | 136.837708 | 0.122329 | 425.08 | ok |
| `E-admissions-style` | 88 | 87 | 65.279907 | 0.141792 | 613.57 | ok |

Machine-readable measurements are stored in `results/results.json`.

## Reproducibility

Observation: `A-very-short` was run three times in the same process with the same model and CPU configuration.

- Perplexities: `2589.029541015625`, `2589.029541015625`, `2589.029541015625`
- Maximum absolute difference: `0.0`
- Tolerance: `1e-9`
- Result: exactly identical within the recorded tolerance

Interpretation: with `model.eval()`, CPU execution, and `torch.inference_mode()`, the measured perplexity is deterministic for this input in this environment.

## Edge Cases

Observation: edge cases were handled intentionally rather than allowed to produce silent `NaN` or `inf` success results.

| Test ID | Tokens | Usable predictions | Perplexity | Status | Note |
| --- | ---: | ---: | ---: | --- | --- |
| `EDGE-empty` | 0 | 0 | null | insufficient_input | no usable prediction tokens |
| `EDGE-whitespace` | 9 | 8 | null | insufficient_input | whitespace tokens exist, but no lexical content |
| `EDGE-extremely-short` | 1 | 0 | null | insufficient_input | first token has no preceding-token prediction |
| `EDGE-one-usable-prediction` | 2 | 1 | 76679.726562 | ok | finite but warned as unstable evidence |

Interpretation: finite perplexity can still be weak evidence when only one prediction token is available. Evidence sufficiency must remain separate from numerical computability.

## Performance

Final cached run:

- Model load time: `1.152793` seconds
- First successful inference time: `0.157552` seconds
- Median successful inference time: `0.113733` seconds
- Median tokens/second: `310.28`
- Total experiment runtime: `1.961918` seconds

During the first full run, downloading/loading the uncached model took `23.826917` seconds. The final cached run is the more relevant local repeat-execution measurement.

## Interpretation

Observation: `distilgpt2` exposes token-level logits locally, runs on CPU, and supports correct causal-shift perplexity calculation for sentence and paragraph inputs.

Interpretation: this is enough evidence to proceed with local perplexity as a feasible measurement instrument for later experiments. It does not validate perplexity as a detector, establish a threshold, determine minimum evidence requirements, or prove usefulness for admissions-essay classification.

The very short and one-prediction-token results also support the project principle that numerical output alone is not sufficient evidence.

## Decision

`PROCEED`

Proceed to the next planned feasibility question after review. Local sentence/passage perplexity calculation with `distilgpt2` is technically feasible in this environment.

## Limitations

- This experiment used fixed synthetic/non-private strings, not a dataset.
- It did not test classification accuracy.
- It did not compare models.
- It did not establish evidence thresholds.
- It did not evaluate sentence-length stability beyond the small edge-case checks.
- It did not measure memory usage.
- The installed dependencies and downloaded Hugging Face model cache are local environment artifacts, not repository artifacts.
