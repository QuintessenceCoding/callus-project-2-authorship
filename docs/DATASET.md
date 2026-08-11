# Dataset Design & Data Governance

## 1. Purpose

This document defines how data for Project 2 will be sourced, transformed, organized, split, validated, and documented.

The dataset is part of the detection system rather than a disposable implementation detail.

The goal is to construct a dataset that allows us to evaluate whether the detector learns writing characteristics rather than:

* topic
* source identity
* prompt wording
* dataset artifacts
* generation-model fingerprints
* essay-family relationships

The dataset must also support explicit investigation of:

* hybrid writing
* unseen generation models
* topic shifts
* ESL/non-native-English false positives

---

# 2. Dataset Principles

## 2.1 Provenance First

Every source document must have traceable provenance.

For each source, record:

* source name
* source URL or identifier
* original dataset/archive
* collection date where relevant
* license or usage terms
* intended use
* transformation performed
* whether redistribution is permitted

A document with unclear provenance should not silently enter the final dataset.

---

## 2.2 Family-Based Organization

The primary unit of organization is the **Essay Family**, not the individual document.

An Essay Family contains a human source essay and any controlled variants derived from it.

Conceptually:

```text id="8cxg9r"
Essay Family
│
├── Human Original
│
├── AI Generated
│
├── AI Polished
│
└── AI Spliced
```

The family relationship must be preserved in metadata even after documents are transformed.

---

## 2.3 Experimental Control

Where practical, AI-generated variants should preserve the underlying:

* prompt/topic
* narrative constraints
* intended subject
* core facts

This allows the classifier to focus more strongly on writing characteristics.

The goal is not to make AI and human text identical.

The goal is to reduce obvious topic-level confounding.

---

## 2.4 No Dataset Leakage

Related documents must never be split across train, validation, and test sets.

The atomic split unit is the **Essay Family**.

---

# 3. Dataset Categories

The planned dataset contains five primary categories.

| Category        | Description                                                       | Purpose                        |
| --------------- | ----------------------------------------------------------------- | ------------------------------ |
| Human           | Original human-authored essays                                    | Human baseline                 |
| AI              | Fully machine-generated essays                                    | Machine baseline               |
| Hybrid-Polished | Human essays with selected passages AI-polished                   | Subtle AI-assistance detection |
| Hybrid-Spliced  | Human essays with selected passages replaced by AI-generated text | Local discontinuity detection  |
| ESL Control     | Human essays produced by non-native English writers               | Bias audit                     |

These categories are analytical labels.

They do not imply that the detector can always distinguish them correctly.

---

# 4. Human Source Data

Human essays form the foundation of the dataset.

Preferred sources should be:

* relevant to college/admissions-style writing
* legally usable for the project's intended purpose
* sufficiently documented
* diverse in topic
* sufficiently long for feature extraction
* written in English

Potential source types include:

* public admissions essay archives
* research datasets containing student writing
* public educational writing collections
* other datasets with appropriate usage rights

No source will be considered approved solely because it is publicly accessible.

Licensing and usage terms must be verified.

---

# 5. Source Inclusion Criteria

A human essay may be considered for inclusion when it satisfies the project's requirements.

Candidate criteria:

* English text
* meaningful prose rather than metadata or boilerplate
* sufficient length for analysis
* primarily narrative/reflection-oriented
* identifiable source provenance
* permitted usage
* no obvious duplicated content
* no corrupted extraction

The exact minimum word count will be determined through feasibility experiments.

---

# 6. Source Exclusion Criteria

Potential exclusions include:

* extremely short responses
* duplicated essays
* corrupted text
* non-English text for the primary dataset
* essays with unclear provenance
* text with insufficient usable content
* content whose usage rights cannot be established
* documents dominated by quotations or externally sourced text

Exclusion decisions should be recorded where they materially affect dataset composition.

---

# 7. Essay Family Schema

Each family should have a stable identifier.

Example:

```text id="3b0y8m"
family_id: FAM-0001

source:
  type: human
  source_id: ...
  provenance: ...

variants:
  human: ...
  ai_generated: ...
  ai_polished: ...
  ai_spliced: ...
```

The family ID must remain stable throughout preprocessing and splitting.

---

# 8. Document Metadata

Every document should have metadata sufficient for later analysis.

Conceptual schema:

```json id="5od2ka"
{
  "document_id": "DOC-0001",
  "family_id": "FAM-0001",
  "category": "human",
  "source_id": "SOURCE-01",
  "topic_id": "TOPIC-07",
  "generation_model": null,
  "transformation": null,
  "word_count": 742,
  "language": "en",
  "split": "train"
}
```

Additional fields may be added as the dataset develops.

---

# 9. Generation Metadata

AI-generated documents must record:

* generation model
* model version where available
* generation runtime
* generation configuration
* prompt/template identifier
* generation date
* temperature or sampling settings where applicable
* source family
* transformation type

The exact prompt text should be preserved when redistribution and privacy constraints permit.

Otherwise, store a prompt/template identifier and document the generation procedure separately.

---

# 10. AI Generation Strategy

The project uses AI generation to create controlled experimental variants.

The core requirement is local, reproducible generation.

Potential local model families may include small quantized instruction-tuned models that can run on consumer hardware.

The exact generation models remain pending feasibility testing.

---

# 11. AI-Generated Variant

An AI-generated variant should be created from the same underlying prompt/topic or narrative constraints as its human counterpart where practical.

Conceptually:

```text id="7k0k90"
Human source
     │
     ├── original essay
     │
     └── controlled prompt/context
               │
               ▼
          Local model
               │
               ▼
        AI-generated essay
```

The goal is to reduce topic confounding.

The generated essay should be stored independently while maintaining its family relationship.

---

# 12. Hybrid-Polished Variant

The hybrid-polished category represents human text that has been modified by an AI system.

The transformation protocol should specify:

* which passage(s) were selected
* approximate proportion of the essay transformed
* whether meaning was preserved
* model used
* transformation prompt/template
* generation settings

Example:

```text id="n6n8fp"
Human essay
│
├── Human paragraph
├── Human paragraph
├── AI-polished paragraph  ← transformed
├── Human paragraph
└── Human paragraph
```

The original human text must remain available for comparison.

---

# 13. Hybrid-Spliced Variant

The hybrid-spliced category represents human essays containing newly generated machine-written passages.

Example:

```text id="i9rj3q"
Human paragraph
Human paragraph
AI-generated paragraph
Human paragraph
Human paragraph
```

The metadata must identify:

* inserted passage boundaries
* source family
* generation model
* generation procedure

This allows evaluation of whether the local anomaly signal identifies discontinuities.

---

# 14. Hybrid Transformation Metadata

Hybrid variants should record transformation locations.

Conceptual structure:

```json id="h0i2so"
{
  "transformation": "polished",
  "segments": [
    {
      "start": 412,
      "end": 893,
      "type": "ai_modified"
    }
  ]
}
```

The exact schema may change.

The important requirement is that ground-truth transformation boundaries remain available for evaluation.

---

# 15. ESL Control Set

The project will include an ESL/non-native-English control set where legally and ethically appropriate data is available.

The purpose is not to label a person's writing ability.

The purpose is to test whether detector features create elevated false-positive rates under a documented control condition.

Metadata should avoid unnecessary personal information.

Only information required for the bias experiment should be retained.

---

# 16. ESL Evaluation Principle

The project should not assume:

> ESL writing has lower lexical diversity.

Instead, that is treated as a hypothesis to test.

Potential measurements include:

* false-positive rate
* machine-association distribution
* evidence-strength distribution
* feature-level differences
* local-anomaly behavior

If elevated false positives are observed, the result must be documented.

---

# 17. Dataset Size

The initial conceptual target is approximately several hundred essays/families.

However, dataset size is not a fixed requirement.

The final size depends on:

* legally usable human data
* generation time
* local compute
* model availability
* family diversity
* topic diversity
* evaluation requirements

A smaller, well-controlled dataset is preferable to a larger dataset with:

* poor provenance
* leakage
* weak pairing
* duplicated content
* inadequate metadata

---

# 18. Dataset Composition

The intended composition is approximately:

```text id="h5qfpg"
Human
  │
  ├── AI-generated
  ├── AI-polished
  └── AI-spliced

Plus:

ESL / non-native-English control
```

Exact proportions will be finalized after source and generation feasibility is established.

The dataset should not be artificially balanced if doing so would create unrealistic sampling or reduce important evaluation coverage.

---

# 19. Topic Distribution

Topic distribution must be tracked.

Potential topic metadata may include broad clusters such as:

* family
* education
* failure
* leadership
* community
* identity
* extracurricular activity
* personal growth
* challenge
* achievement

These categories are illustrative.

The actual topic taxonomy should be derived from the available data rather than imposed arbitrarily.

---

# 20. Topic Leakage Prevention

Topic information must not become a proxy for the label.

For example, this dataset design is dangerous:

```text id="4k4p6w"
Human:
  sports
  family
  volunteering

AI:
  technology
  leadership
  academics
```

The classifier could learn topic vocabulary instead of writing characteristics.

Paired families and topic-aware splitting should reduce this risk.

---

# 21. Family-Level Splitting

The split process must operate on family IDs.

Example:

```text id="t3a7q1"
TRAIN
├── FAM-001
├── FAM-002
└── FAM-003

VALIDATION
├── FAM-004
└── FAM-005

TEST
├── FAM-006
└── FAM-007
```

All variants of `FAM-001` remain in TRAIN.

No variant may appear in another split.

---

# 22. Split Strategy

The target split will be approximately:

* training: 70–80%
* validation: 10–15%
* test: 10–20%

Exact percentages are less important than maintaining:

* family isolation
* category coverage
* topic diversity
* model diversity
* sufficient evaluation size

The final split should be generated deterministically and recorded.

---

# 23. Out-of-Distribution Splits

Where dataset size permits, separate OOD evaluation sets should be maintained.

### Unseen Topic

A topic cluster absent from training.

### Unseen Generation Model

A generation model absent from training.

### Hybrid

A transformation type or composition that was not fully represented during training.

The exact OOD design depends on available data.

---

# 24. Dataset Leakage Checks

Before training, automated checks should verify:

### Family leakage

No family appears in multiple splits.

### Duplicate text

Exact duplicates do not cross splits.

### Near duplicates

Highly similar documents are investigated.

### Prompt leakage

Generation prompts or metadata do not accidentally encode labels.

### Metadata leakage

Fields such as:

```text
generation_model = GPT-X
```

must never become model features unless intentionally part of an experiment.

### Transformation markers

Ground-truth metadata must remain outside the feature matrix used for classification.

---

# 25. Text Normalization

Raw text should be preserved.

A separate normalized representation may be created for feature extraction.

Potential normalization includes:

* Unicode normalization
* whitespace normalization
* consistent line endings
* removal of extraction artifacts

Normalization must not:

* rewrite prose
* correct grammar
* alter punctuation unnecessarily
* remove stylistic characteristics being measured

Both original and normalized representations should be traceable.

---

# 26. Sentence and Passage Ground Truth

For hybrid documents, transformation boundaries should be mapped to:

* character offsets
* sentence IDs
* passage IDs

Example:

```text id="9g7wq2"
Essay
│
├── Sentence 1 — human
├── Sentence 2 — human
├── Sentence 3 — AI-modified
├── Sentence 4 — AI-modified
└── Sentence 5 — human
```

This allows sentence-level detection to be evaluated against known transformation regions.

---

# 27. Generation Reproducibility

AI-generation scripts should be deterministic where the selected model/runtime allows it.

Record:

* model
* prompt
* parameters
* seed where supported
* runtime
* timestamp
* source family

If exact deterministic reproduction is impossible, the generation configuration must still be documented.

---

# 28. Generation Quality Control

Generated essays should not be accepted blindly.

Potential checks include:

* minimum length
* successful generation
* no obvious prompt leakage
* no meta-commentary
* no generation artifacts
* no accidental copying of the source essay
* reasonable coherence

Rejected generations should be recorded rather than silently replaced.

---

# 29. Source Data Privacy

The dataset should not retain unnecessary personal information.

Potentially sensitive metadata should be removed or minimized unless required for a documented experiment.

The runtime application should not require persistent storage of user-submitted essays.

---

# 30. Data Versioning

Dataset changes must produce a new dataset version.

Example:

```text id="6p3n5v"
dataset-v0.1
dataset-v0.2
dataset-v1.0
```

A dataset version should identify:

* source composition
* transformation protocol
* split configuration
* preprocessing
* generation models
* known limitations

Model evaluation results must reference the dataset version used.

---

# 31. Data Manifest

A machine-readable manifest should eventually contain one row per document.

Conceptual columns:

```text id="c5b4fq"
document_id
family_id
category
source_id
topic_id
language
word_count
generation_model
transformation_type
transformation_regions
split
dataset_version
```

The manifest is the authoritative mapping between documents and metadata.

---

# 32. Feature Matrix Boundary

Dataset metadata and ML features must remain separate.

Example:

```text id="krx0k8"
Metadata
────────────────────
family_id
source_id
topic_id
category
generation_model
split
transformation_type

             ↓

       Feature extraction

             ↓

ML Feature Matrix
────────────────────
perplexity
sentence_length
MATTR
POS_entropy
...
```

Fields such as `category`, `generation_model`, or `transformation_type` must never accidentally enter the classifier feature matrix.

---

# 33. Training Data

The training set may contain:

* human documents
* AI documents
* selected hybrid documents depending on the experiment

The training composition must be explicitly recorded for each experiment.

Different experiments may intentionally use different training configurations.

---

# 34. Validation Data

Validation data is used for development decisions such as:

* feature selection
* classifier comparison
* threshold selection
* calibration
* evidence-sufficiency thresholds

Validation data must remain separate from final test evaluation.

---

# 35. Test Data

The final test set is reserved for evaluation.

It must not be repeatedly inspected and used to guide model changes.

Once the methodology is locked, the final test set should be evaluated and reported.

---

# 36. Dataset Limitations

The dataset is expected to have limitations.

Potential limitations include:

* limited number of source essays
* limited model families
* synthetic AI generation
* imperfect human/AI pairing
* topic imbalance
* limited ESL data
* domain-specific writing
* licensing constraints
* local model generation quality
* inability to reproduce some external model behavior

These limitations must be reported in the final evaluation.

---

# 37. What the Dataset Does Not Represent

Unless explicitly added and documented, the dataset does not claim to represent:

* all college applicants
* all English-language writers
* all geographic regions
* all socioeconomic backgrounds
* all educational systems
* all LLM families
* all prompting strategies
* all editing workflows
* adversarially optimized AI text

The detector's claims must remain bounded by the observed data.

---

# 38. Dataset Acceptance Checklist

Before a dataset version is used for model training, verify:

### Provenance

* [ ] Every source has documented provenance.
* [ ] Usage rights have been reviewed.
* [ ] Source identifiers are preserved.

### Structure

* [ ] Every document has a family ID.
* [ ] Every document has a unique document ID.
* [ ] Categories are recorded.
* [ ] Transformation metadata exists where applicable.

### Leakage

* [ ] No family crosses splits.
* [ ] Exact duplicates are checked.
* [ ] Near duplicates are investigated.
* [ ] Metadata is excluded from ML features.

### Generation

* [ ] Model identity is recorded.
* [ ] Generation configuration is recorded.
* [ ] Hybrid transformation regions are recorded.
* [ ] Failed generations are tracked.

### Evaluation

* [ ] Test set is isolated.
* [ ] OOD configuration is documented.
* [ ] ESL/control data is separately identifiable.

---

# 39. Current Dataset Status

**Phase:** 0 — Project Foundation

**Status:** Dataset contract defined; actual sources and generation models pending verification.

### Accepted principles

* Essay-family organization
* family-level splitting
* provenance tracking
* metadata/feature separation
* hybrid-writing representation
* leakage checks
* explicit dataset versioning
* documented generation configuration
* bias-control evaluation
* test-set isolation

### Pending

* approved human datasets
* exact dataset size
* exact topic taxonomy
* local generation model(s)
* generation prompts
* generation parameters
* ESL dataset
* final split proportions
* OOD configuration
* minimum essay length

These should be resolved through source verification and Phase 1 feasibility work rather than assumed in advance.
