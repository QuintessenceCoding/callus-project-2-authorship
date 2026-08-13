Here is the cleaned and properly formatted version of your Markdown file, with all the escaped characters, broken tables, and inconsistent heading tags fixed:

```markdown
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

```text
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

| Category | Description | Purpose |
| --- | --- | --- |
| Human | Original human-authored essays | Human baseline |
| AI | Fully machine-generated essays | Machine baseline |
| Hybrid-Polished | Human essays with selected passages AI-polished | Subtle AI-assistance detection |
| Hybrid-Spliced | Human essays with selected passages replaced by AI-generated text | Local discontinuity detection |
| ESL Control | Human essays produced by non-native English writers | Bias audit |

These categories are analytical labels.

They do not imply that the detector can always distinguish them correctly.

---

# 4. Human Source Data

The project uses a multi-tier dataset strategy rather than requiring a single perfect admissions-essay corpus.

### Tier 1 — Primary Controlled Training / Development Corpus: PERSUADE

PERSUADE is the main human-writing proxy corpus for controlled family construction, feature experiments, classifier development, and hybrid-writing experiments.

The locally inspected training source contains `8,426` unique essays, multiple prompts, discourse annotations, text-dependent and independent tasks, and ELL metadata. The available grade values in this source version include grades 6, 8, 9, 10, and NA.

The inspected PERSUADE writing is predominantly argumentative/source-based student assignment writing. It is therefore **not treated as an admissions-essay corpus**. The project explicitly treats PERSUADE as a training-domain proxy.

### Tier 2 — External Validation: Anthropic Persuasion

The Anthropic Persuasion dataset is reserved for external paired human-vs-model writing validation where useful.

Its role is to test whether selected linguistic signals transfer to a separately collected human/model corpus.

It is not treated as the admissions target domain.

The exact dataset version, source URL, and applicable usage terms are recorded in the source manifest.

### Tier 3 — Target-Domain Evaluation: Consented Admissions Micro-Set

Where feasible, a small set of genuinely college-admissions/personal-statement essays may be obtained through direct author consent.

This is a local target-domain evaluation set, not a representative admissions corpus.

Raw consented essays remain local unless redistribution is explicitly permitted.

### Tier 4 — ESL / Non-Native-English Bias Audit: ELLIPSE

ELLIPSE is reserved for the ESL/non-native-English audit.

It is not automatically treated as an ordinary training category. Its purpose is to measure whether detector features create elevated false-positive rates on English-learner writing.

### Auxiliary Source: CELL

CELL remains an auxiliary undergraduate academic-writing source.

Our inspection showed that the sampled CELL material is primarily academic/assignment writing rather than admissions-style personal writing. It is therefore not the primary family source.

### AIDE

The currently downloaded AIDE training file is **not yet approved as a benchmark source**.

The inspected file contains `1,378` rows with only `3` rows labeled as generated. Its exact role is therefore pending further source/version analysis.

Until resolved, AIDE remains reference material rather than a production training/evaluation dependency.

This multi-tier design makes the domain shift explicit rather than hiding it.

---

# 4A. Current Dataset Architecture

```text
PERSUADE
    ↓
controlled human/student-writing families
    ↓
human / AI-generated / AI-polished / AI-spliced

Anthropic Persuasion
    ↓
external human-vs-model validation

ELLIPSE
    ↓
ESL / non-native-English bias audit

Consented admissions micro-set
    ↓
target-domain local evaluation

CELL
    ↓
auxiliary student-writing source

AIDE
    ↓
reference / pending validation

```

The project does not require all sources to serve the same role.

The key target-domain limitation is explicit: the main controlled corpus is student writing rather than college admissions personal essays. Admissions-domain performance is therefore treated as a domain-shift question.

---

# 5. Source Inclusion Criteria

A human source document may be considered for inclusion when it satisfies the requirements of its intended dataset tier.

General criteria:

* English text
* meaningful prose rather than metadata or boilerplate
* sufficient length for planned feature extraction
* identifiable source provenance
* usage appropriate for the intended project role
* no obvious duplicated content
* no corrupted extraction

Role-specific criteria:

* **PERSUADE:** prefer grade 9/10 where practical and diversify across prompts; retain ELL metadata only for later audit.
* **Anthropic Persuasion:** require identifiable human/model pairing and preserved source labels.
* **Admissions micro-set:** require explicit author consent for local use and any AI transformation.
* **ELLIPSE:** retain only metadata required for the documented bias audit.

The exact minimum word count remains evidence-driven and will be validated during feature experimentation.

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

```text
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

```json
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

The core requirement is:

* ₹0 cost
* local inference
* no paid model/API dependency
* reproducible generation where the runtime permits it
* practical generation time on the available hardware

### Current Pilot Configuration

EXP-003 selected:

* Model: `Qwen/Qwen2.5-0.5B-Instruct`
* Runtime: Hugging Face Transformers
* Device: CPU

Observed baseline:

* approximately 327 generated words
* approximately 36.2 seconds generation time
* natural completion before the token limit
* no obvious prompt leakage
* no obvious repetition

These observations establish the current pilot configuration; they do not claim universal model superiority.

Generation will be piloted on a small number of Essay Families before scaling. Dataset size must be constrained by measured local generation time and quality.

A generation-model or runtime change creates a new dataset version.

---

# 11. AI-Generated Variant

An AI-generated variant is created from the same task or prompt context as its human counterpart where practical.

For PERSUADE family construction:

* the model may receive the assignment/task context
* the model must not receive the original human essay
* the generated essay should be an independent response to the task
* the generated response must not intentionally imitate the source author's wording

For external paired datasets such as Anthropic Persuasion, existing human/model labels are preserved rather than regenerated unnecessarily.

The goal is to reduce task/topic confounding while keeping the authorship process distinct.

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

```text
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

```text
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

```json
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

The project will use a **pilot-first scaling strategy**.

The earlier conceptual target of several hundred documents is not a requirement.

The initial pilot should contain a small number of complete Essay Families sufficient to validate:

* source ingestion
* family construction
* local AI generation
* AI polishing
* AI splicing
* transformation-boundary tracking
* metadata/manifest generation
* leakage checks
* generation runtime
* generation quality checks

A practical initial target is approximately **5 complete families**.

After the pilot, the dataset may be scaled toward approximately **50–60 human source families** if local generation time, source availability, and evaluation coverage justify it.

The final dataset size is therefore evidence-driven rather than fixed.

A smaller, well-controlled dataset is preferable to a larger dataset with:

* poor provenance
* leakage
* weak pairing
* duplicated content
* inadequate metadata
* impractical local generation cost.

---

# 18. Dataset Composition

The intended composition is:

```text
Human Essay Family
  │
  ├── Human Original
  ├── AI-generated
  ├── AI-polished
  └── AI-spliced

Separate:
ESL / non-native-English Control Set

```

The four family variants are the primary experimental documents.

The ESL/control set is not automatically treated as another ordinary training category. Its default role is bias auditing and false-positive analysis.

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

```text
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

```text
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

OOD evaluation must not be created by casually moving individual variants between splits. Family isolation remains mandatory.

The generation model used for the OOD holdout must not appear in the training/validation generation pool for the corresponding experiment.

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

```text
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

```text
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

```text
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

```text
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

The current strategy has known limitations.

### Domain mismatch

PERSUADE and Anthropic Persuasion are not college admissions personal-essay corpora. Primary controlled experiments therefore operate partly outside the target domain.

### Synthetic generation

AI-generated, AI-polished, and AI-spliced variants are controlled experimental constructions, not a complete representation of real student AI use.

### Model coverage

The current local generator is small (`Qwen/Qwen2.5-0.5B-Instruct`); results may not transfer to every LLM.

### ESL coverage

The ESL audit depends on the coverage and quality of the selected control corpus.

### Local compute

Generation and feature extraction are constrained by local CPU resources.

### Admissions evaluation scope

A small consented admissions micro-set, if obtained, can test target-domain transfer but cannot establish population-level admissions performance.

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
* all college admissions personal-writing styles

The primary controlled corpus should be described as **student argumentative writing**, not admissions writing.

The detector's claims must remain bounded by the observed data and by any separate target-domain evaluation.

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

**Phase:** 2 — Dataset Design / Source Strategy

**Status:** Dataset strategy locked at the role level. PERSUADE is the primary controlled proxy corpus; the next execution phase is feature extraction.

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
* ₹0/local generation
* pilot-first dataset scaling
* raw-data separation from GitHub
* explicit domain-shift reporting
* separate dataset roles

### Current decisions

* **PERSUADE** is the primary controlled human/student-writing corpus.
* PERSUADE is explicitly treated as a proxy domain, not admissions writing.
* **Anthropic Persuasion** is reserved for external paired human-vs-model validation where useful.
* **ELLIPSE** is reserved for the ESL/non-native-English bias audit.
* A small **consented admissions micro-set** may be used for target-domain local evaluation if available.
* **CELL** remains an auxiliary undergraduate academic-writing source.
* **AIDE** is not yet approved as a production benchmark because the inspected training file is highly label-skewed and its release role requires further verification.
* `Qwen/Qwen2.5-0.5B-Instruct` with Hugging Face Transformers on CPU is the current local generation configuration.
* Family IDs are the atomic split unit.
* Raw third-party text will not be committed to GitHub unless its usage and redistribution rights explicitly permit it.
* The absence of a large open admissions corpus is no longer an implementation blocker.

### Pending

* exact PERSUADE pilot family selection
* hybrid transformation proportions
* generation prompts/parameters
* Anthropic validation subset
* approved ELLIPSE acquisition/version
* whether a consented admissions micro-set can be obtained
* final dataset size and split proportions
* OOD configuration
* minimum evidence/essay length

The next major workstream is the Feature Extraction Laboratory.

---

# 40. Dataset Pilot

Before constructing the full dataset, the pipeline should be validated on a small pilot.

The pilot should contain approximately **5 complete Essay Families**, subject to source suitability.

Each pilot family should, where feasible, produce:

* human original
* AI-generated variant
* AI-polished variant
* AI-spliced variant

The pilot must validate:

* source ingestion
* family metadata
* local generation
* generation quality control
* transformation-boundary tracking
* manifest creation
* deterministic family-level splitting
* duplicate/leakage checks
* generation runtime

The pilot is not intended to support final model evaluation. Its purpose is to establish whether dataset construction is practical before scaling.

### Current PERSUADE Pilot Status

PERSUADE has been reconstructed from its annotation-level CSV into essay-level text using the correct inclusive discourse offsets.

The selector streams the raw source CSV, preserves source whitespace/newline information where present, and records provenance metadata.

The current selected pool is a proxy-domain pilot of student argumentative writing rather than admissions essays.

### Current CELL Pilot Status

CELL is treated as an auxiliary undergraduate academic-writing source. Its pilot records are not Essay Families.

### Admissions Target-Domain Status

No large reusable admissions corpus is approved as the primary training source.

A small consented admissions micro-set may be added later for target-domain evaluation, but feature extraction and detector development do not depend on it.

---

# 41. GitHub and Raw Data Policy

The repository should contain the **dataset contract, manifests, provenance metadata, processing code, and reproducibility documentation**.

Raw source essays should remain outside Git when:

* redistribution is not explicitly permitted
* the source terms require local/research-only use
* the repository would otherwise redistribute third-party copyrighted text

The `.gitignore` should exclude local raw/processed dataset contents where appropriate.

The repository must never silently contain third-party essays simply because they were downloaded during development.

A dataset version should remain reproducible through its documented source identifiers, processing pipeline, generation configuration, and manifest, subject to the source's redistribution restrictions.

---

# 42. Source Verification Policy

A candidate dataset is not approved merely because:

* it is publicly accessible
* it appears in a search result
* it is hosted on Kaggle or another dataset platform
* another project has used it

Before assigning a source a production role, record:

* dataset name
* official source location
* dataset version where available
* license or documented usage terms
* relevant modification restrictions
* whether redistribution is permitted
* whether commercial use is restricted
* whether the underlying text has separate rights considerations
* intended role in this project

The project does not require identical licensing conditions across every dataset tier.

Sources may be:

* primary controlled training data
* external validation data
* local-only target-domain evaluation data
* bias-audit data
* reference-only data

If a source cannot be used for the intended role with reasonable confidence, it must not be silently promoted into that role.

---

# 43. Dataset Versioning for the Pilot

The first constructed pilot should receive an explicit version identifier, for example:

```text
dataset-v0.1-pilot

```

The pilot version should record:

* approved source composition
* selected family IDs
* transformation protocol
* generation model/configuration
* preprocessing
* split configuration
* known failures
* generation runtime
* known limitations 

Scaling the dataset or changing the generation protocol should produce a new dataset version rather than silently replacing the pilot.

```

```