# ESL / Non-Native-English Audit

## 1. Purpose

This audit evaluates whether the production detector disproportionately flags human essays written by English language learners (ELL) compared with a matched human comparison group.

The Callus brief explicitly identifies non-native-English writing as a potential false-positive risk. The audit therefore measures the observed behavior of the locked production detector rather than assuming that such a bias is present or absent.

This audit is a bias evaluation, not a training or model-tuning experiment.

---

## 2. Dataset

The audit uses the locally available PERSUADE corpus:

```text
data/raw/persuade/persuade2_train_srctexts.csv
```

The source file contains discourse-level records, so multiple rows can belong to the same essay.

The audit therefore first collapses the corpus to one record per:

```text
essay_id_comp
```

Only essays with an explicit:

```text
ell_status = Yes
```

or:

```text
ell_status = No
```

were eligible.

Essays with missing or blank ELL status were excluded.

The eligible essay-level population was:

```text
ELL:      701 essays
non-ELL: 6928 essays
```

The audit uses a balanced sample of:

```text
701 ELL essays
701 non-ELL essays
------------------
1402 essays total
```

A fixed random seed was used:

```text
20260815
```

The audit manifest is:

```text
data/esl_audit_manifest.json
```

---

## 3. Task Distribution

Both groups in the audit are:

```text
Text dependent
```

Therefore no task-category balancing adjustment was required for this audit.

---

## 4. Production Model

The audit uses the exact locked production artifact:

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

No retraining, feature modification, threshold tuning, or calibration was performed for this audit.

The same production feature extractor and abstention behavior were used for both groups.

---

## 5. Audit Metrics

For each group we record:

- sample count
- classified count
- abstained count
- coverage
- essays flagged as machine-associated
- false-positive rate
- model-signal mean
- model-signal median
- model-signal 10th percentile
- model-signal 90th percentile

Because all audit inputs are human essays, a classification as `ai_associated` is a false positive for purposes of this group comparison.

---

## 6. Results

### 6.1 Group-Level Results

| Metric | ELL | Non-ELL |
| --- | ---: | ---: |
| Essays | 701 | 701 |
| Classified | 701 | 700 |
| Abstained | 0 | 1 |
| Coverage | 100.00% | 99.86% |
| Flagged as AI | 15 | 17 |
| False-positive rate | **2.14%** | **2.43%** |
| Mean model signal | 0.0370 | 0.0596 |
| Median model signal | 0.00151 | 0.00621 |
| Model signal P10 | 1.35e-07 | 4.25e-05 |
| Model signal P90 | 0.0875 | 0.1818 |

The observed false-positive-rate difference is:

```text
ELL FPR - non-ELL FPR
= 2.14% - 2.43%
= -0.29 percentage points
```

In this balanced audit sample, the ELL group was not flagged at a higher rate than the non-ELL comparison group.

---

## 7. Interpretation

### Observed Result

The production detector produced:

```text
ELL false-positive rate:     2.14%
non-ELL false-positive rate: 2.43%
```

The ELL group therefore had a slightly lower observed false-positive rate in this audit.

Coverage was also effectively the same:

```text
ELL:     100.00%
non-ELL: 99.86%
```

### What This Supports

Within this particular PERSUADE sample and audit protocol:

> We did not observe elevated false-positive behavior for ELL essays relative to the matched non-ELL comparison group.

### What This Does Not Support

The audit does not prove that the detector is universally unbiased against non-native-English writers.

It is limited by:

- one corpus
- one ELL annotation scheme
- one balanced sample
- one production detector
- one evaluation protocol
- the distribution represented by PERSUADE

The result should therefore be reported as an observed audit outcome, not a universal guarantee.

---

## 8. Relationship to Individual Failure Cases

One final held-out evaluation failure, pair `B046D31B68F0`, was a human essay that received a machine-associated classification with model signal `0.7536`.

The essay contains visible non-native-English characteristics.

However, that single failure should not be presented as proof of ELL bias.

The broader audit produced:

```text
ELL FPR:     2.14%
non-ELL FPR: 2.43%
```

Therefore the appropriate interpretation is:

> The individual case is a useful qualitative false-positive example with non-native-English characteristics, but the balanced group-level audit did not show elevated false-positive behavior for ELL writers.

This distinction is important because an individual failure and a systematic group-level bias are not the same claim.

---

## 9. Limitations

This audit does not test:

- every non-native-English background
- every proficiency level
- every essay domain
- every admissions context
- every language model or generation model
- long-term behavior across different datasets

It also does not establish causal mechanisms for any observed feature differences.

A larger and more diverse evaluation would be required before making broader fairness claims.

---

## 10. Reproducibility

Audit configuration:

```text
Audit:       esl-non-native-english-audit-v1
Seed:        20260815
ELL essays:  701
non-ELL:     701
Total:       1402
Model:       production-four-feature-logreg-v1
Source:      EXP-006
```

Artifacts:

```text
data/esl_audit_manifest.json
data/esl_audit/predictions.csv
data/esl_audit/metrics.json
```

The audit was run using the same production detector used by the application.

---

## 11. Conclusion

The audit did not find evidence of elevated false-positive behavior for ELL essays in this balanced PERSUADE sample.

The observed rates were:

```text
ELL:      2.14%
non-ELL:  2.43%
```

The result should be presented as:

> **No elevated ELL false-positive rate observed in this audit sample.**

It should not be expanded into a universal claim that the detector has no ESL/non-native-English bias.
