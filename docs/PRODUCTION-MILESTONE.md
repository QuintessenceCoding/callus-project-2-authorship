# Production Milestone — Detector + Backend + Frontend

## Status

Completed — first end-to-end production prototype.

## Scope

The detector has moved from experiments into a runnable application consisting of:

```text
Frontend (Vite + React + TypeScript)
        ↓
POST /api/analyze
        ↓
FastAPI backend
        ↓
Production detector
        ↓
Four-feature extraction
        ↓
StandardScaler + Logistic Regression
        ↓
Structured evidence response
```

## Production Detection Method

The production feature vector is fixed to the four features validated during Phase 1:

1. Perplexity
2. Sentence-length coefficient of variation
3. MATTR
4. POS 3-gram entropy

The production extractor reuses the validated EXP-001 / EXP-004 implementations rather than introducing new feature mathematics.

The classifier is the four-feature Logistic Regression baseline from EXP-006, with StandardScaler preprocessing.

The persisted model artifact is:

```text
backend/artifacts/authorship_detector.joblib
```

and its metadata is:

```text
backend/artifacts/authorship_detector.metadata.json
```

## API

The backend exposes:

```text
POST /api/analyze
```

Request:

```json
{
  "text": "essay text..."
}
```

The response contains:

- evidence state
- classification label when available
- model signal when classification is possible
- four feature measurements
- feature availability and reasons
- text statistics
- model metadata

## Evidence-First Behavior

The detector does not fabricate missing feature values.

A classification is produced only when the complete four-feature vector required by the trained Logistic Regression model is available.

Otherwise the system returns:

```text
insufficient_evidence
```

This behavior is deliberate and follows the evidence-sufficiency conclusions from EXP-010.

The model probability is exposed as a **model signal for machine association**, not as calibrated authorship certainty.

## Robustness Fix — Long Single-Sentence Input

During integration testing, an 867-word PERSUADE essay was treated by spaCy as a single sentence containing 1,134 language-model tokens.

`distilgpt2` supports a 1,024-token context, so the initial implementation attempted to score an oversized sentence and returned HTTP 500.

The production extractor was updated to detect the language-model context limit before calling the perplexity function.

When a sentence exceeds the supported context, perplexity is marked unavailable with:

```text
sentence_exceeds_language_model_context
```

The detector then returns:

```text
insufficient_evidence
```

instead of crashing or silently truncating the user's text.

This preserves the validated perplexity definition and follows the project's evidence-first rule: when a measurement cannot be computed reliably using the validated method, abstain rather than invent a workaround.

## Integration Verification

The following states have been verified through the running application:

### AI-associated case

A controlled AI-generated essay produced:

```text
state: classified
label: ai_associated
model signal: 0.960
features: 4 / 4 available
```

### Human-associated case

A human-written PERSUADE essay produced:

```text
state: classified
label: human_associated
model signal: 0.056
features: 4 / 4 available
```

### Insufficient evidence — short input

For:

```text
I like school.
```

the detector returned:

```text
state: insufficient_evidence
```

because sentence-length CV and MATTR were unavailable.

### Insufficient evidence — oversized sentence

An 867-word single-sentence input exceeded the language-model context.

The application now returns:

```text
state: insufficient_evidence
```

without an HTTP 500.

## Validation

Backend tests:

```text
10 passed
```

The known EXP-006 validation-row inference reproduced the saved model output to floating-point precision.

No experiment files from EXP-001 through EXP-010 were modified as part of the production milestone.

## Frontend

The frontend is implemented as a focused editorial-brutalist research interface.

Design principles:

- warm paper-like background
- near-black typography
- strong borders
- restrained vermilion accent
- large editorial headings
- technical/monospace labels
- no generic AI-dashboard styling
- no fake percentage bars
- no LLM-generated explanations

The UI presents:

- essay input
- analysis state
- feature evidence
- text statistics
- methodology explanation
- insufficient-evidence handling
- human-associated and AI-associated results

The raw classifier output is presented as a model signal rather than as a literal probability of authorship.

## Known Limitations

- The strongest validation result comes from the controlled DAIGT External dataset and should not be presented as admissions-domain accuracy.
- Local anomaly and boundary-discontinuity methods from EXP-007 through EXP-009 were not promoted to production because their localization performance was insufficiently reliable.
- The system does not claim to prove authorship or prove that AI was used.
- Sentence-level AI attribution is not currently implemented as a definitive production claim.
- No universal numeric confidence or text-length threshold was established by EXP-010.

## Next Phase

The next work is integration hardening, final evaluation, demo preparation, and full codebase/viva understanding.
