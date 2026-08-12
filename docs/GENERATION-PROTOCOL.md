**# Generation Protocol**

**## 1. Purpose**

This document defines how machine-generated and machine-transformed essay variants will be created for the authorship-analysis dataset.

The protocol exists to prevent generation choices from becoming uncontrolled experimental variables.

No Essay Family should be generated until the generation model and runtime have passed the relevant feasibility experiment.

The protocol is designed for the ₹0 constraint and requires local inference for the core dataset-generation pipeline.

**---**

**## 2. Core Principles**

**### 2.1 Controlled Transformation**
Each variant must differ from its human source in a known and documented way.

**### 2.2 Ground-Truth Boundaries**
For hybrid variants, the exact machine-transformed passage or sentence span must be recorded.

**### 2.3 No Hidden Variables**
Generation model, model version, prompt version, generation parameters, source record, and transformation type must be recorded.

**### 2.4 No Source Leakage**
Generation procedures must not accidentally expose the human source text to variants intended to be independently generated.

**### 2.5 Reproducibility**
A generated artifact should be reproducible as far as the local inference runtime and model permit.

**### 2.6 Quality Before Scale**
A small pilot is generated and reviewed before scaling the dataset.

**---**

**## 3. Variant Definitions**

Each Essay Family may contain four primary variants.

\`\`\`text
Human Original
      │
      ├── AI Generated
      ├── AI Polished
      └── AI Spliced
\`\`\`

**### 3.1 Human Original**

The original human essay is preserved without modification.

It is the source document for the family. The original text must never be overwritten by a generated variant.

**### 3.2 AI Generated**

The AI-generated variant is an independently generated response to the same writing task or assignment context.

The generation model receives the relevant task context and writing requirements, but **\*\*does not receive the human essay itself\*\***.

The purpose is to hold the writing task relatively constant while changing the authorship process.

The generated essay should:

\* satisfy the same task requirements
\* remain within the intended essay domain
\* be a complete response
\* not copy or paraphrase the source essay
\* not intentionally imitate the source author's wording or sentence structure

The exact task context available to the model must be recorded.

If the original task wording cannot be recovered reliably, the generation must not invent a supposedly exact prompt. The reconstructed task context must be explicitly labeled as reconstructed.

**### 3.3 AI Polished**

The AI-polished variant is a hybrid document derived from the human original. Only designated passages are transformed.

The model receives the human text for the purpose of transforming the selected passage while preserving the author's underlying:

\* ideas
\* facts
\* narrative
\* claims
\* chronology
\* intended meaning

The transformation may alter:

\* grammar
\* wording
\* sentence structure
\* transitions
\* lexical choice
\* local fluency

The model must not be instructed to rewrite the entire essay when constructing a partial-polish variant.

The exact transformed spans must be recorded.

Example:

\`\`\`text
Paragraph 1  → Human
Paragraph 2  → AI polished
Paragraph 3  → Human
Paragraph 4  → Human
\`\`\`

The unchanged surrounding text must remain byte-for-byte identical where practical.

**### 3.4 AI Spliced**

The AI-spliced variant is a human essay containing an independently generated machine-written passage.

The inserted passage is generated from the relevant task/narrative context without using the surrounding human passage as a stylistic template.

The original human passage is replaced by the generated passage.

Example:

\`\`\`text
Human paragraph 1
Human paragraph 2
AI-generated paragraph
Human paragraph 4
\`\`\`

The exact replacement span and generated span must be recorded.

The purpose is to create a stronger passage-level discontinuity than ordinary polishing.

**---**

**## 4. Generation Model Policy**

The current generation candidate selected after EXP-003 feasibility testing is:

\* Model: `Qwen/Qwen2.5-0.5B-Instruct`
\* Runtime: Hugging Face Transformers
\* Device: CPU

EXP-003 compared this model against `HuggingFaceTB/SmolLM2-135M-Instruct`.

`Qwen/Qwen2.5-0.5B-Instruct` was selected because it produced a complete, task-aligned sample without obvious repetition or prompt leakage, while the smaller SmolLM2 sample reached the token limit and was judged likely truncated.

This is a current pilot decision, not a claim that Qwen is universally superior. The model may be revisited if later generation quality or dataset experiments expose a problem.

The model used for generation must be recorded by:

\* model name
\* model version/revision where available
\* runtime
\* quantization, if applicable

A larger model must not be selected solely because it is theoretically stronger. Practical generation speed and reproducibility are part of the decision.

**## 5. Generation Runtime**

The core generation pipeline must run locally.

The current pilot runtime is:

\* Hugging Face Transformers
\* CPU inference
\* local model weights

Ollama and llama.cpp remain possible alternatives if later runtime constraints justify a change, but they are not required by the current pipeline.

No paid OpenAI, Anthropic, or proprietary detection API may be a dependency of dataset generation.

**## 6. Prompt Versioning**

Every generated artifact must identify the prompt version used.

Prompts should be stored as versioned project artifacts rather than existing only inside code.

Example:

\`\`\`text
prompts/
├── generation-v1.txt
├── polish-v1.txt
└── splice-v1.txt
\`\`\`

Changing the semantic instructions of a prompt creates a new prompt version.

**---**

**## 7. Current Generation Baseline**

The EXP-003 feasibility run established the following baseline configuration for the initial generation pilot:

\* Model: `Qwen/Qwen2.5-0.5B-Instruct`
\* Runtime: Hugging Face Transformers
\* Device: CPU
\* Maximum new tokens: 420
\* Decoding: deterministic (`do_sample=false`)
\* Repetition penalty: 1.05
\* Seed: 7 where supported
\* Target output: approximately 300–500 words

Observed EXP-003 performance:

\* Generation time: approximately 36.2 seconds
\* Output: 383 tokens / 327 words
\* Output completed before the token limit
\* No prompt leakage detected
\* No obvious repetition detected
\* Basic task-quality checks passed

These values establish a practical pilot baseline. They are not final production settings and may be revised after the generation pilot.

**## 8. Generation Parameters**

Record parameters that can materially affect generation, including where supported:

\* temperature
\* top-p
\* top-k
\* maximum output tokens
\* repetition penalty
\* seed, if supported
\* stop sequences, if used

Parameters must not be changed silently between families.

If a parameter cannot be controlled or reproduced by the selected runtime, that limitation must be documented.

**---**

**## 9. Quality Control**

Every generated variant must pass basic validation before entering the dataset.

**### AI Generated**

Check:

\* non-empty output
\* reasonable length
\* task compliance
\* coherent English
\* no obvious prompt leakage
\* no accidental references to the generation process
\* no obvious copying from the human source
\* output ends at a natural sentence boundary
\* output is not truncated by the generation token limit
\* task-following is checked rather than inferred from length alone

**### AI Polished**

Check:

\* intended passage was actually transformed
\* surrounding text remains unchanged
\* meaning/facts are substantially preserved
\* output is non-empty and coherent
\* transformation boundaries are recorded

**### AI Spliced**

Check:

\* replacement passage exists
\* replacement passage is coherent in isolation
\* surrounding human text remains unchanged
\* replacement boundary is recorded
\* generated passage does not accidentally contain prompt/instruction text

A failed generation is rejected and regenerated according to the documented retry policy. Failed outputs must not silently enter the final dataset.

**---**

**## 10. Ground-Truth Metadata**

Every generated variant must have a manifest entry containing, at minimum:

\`\`\`json
{
  "family\_id": "F001",
  "variant": "ai\_polished",
  "source\_record": "...",
  "model": "...",
  "model\_version": "...",
  "runtime": "...",
  "prompt\_version": "polish-v1",
  "generation\_parameters": {},
  "transformed\_spans": [],
  "dataset\_version": "dataset-v0.1-pilot"
}
\`\`\`

The exact schema will be finalized when the dataset-generation implementation is built.

For \`human\_original\`, generation fields may be null or omitted.

**---**

**## 11. Leakage Prevention**

The following rules are mandatory.

**### AI Generated**

Must not receive the original human essay.

**### AI Spliced**

The generated passage must not be generated by simply asking the model to rewrite the exact human passage unless the experiment explicitly defines that as the transformation.

**### AI Polished**

The model may receive the designated human passage because transformation of that passage is the purpose.

**### Dataset Splits**

All variants belonging to one Essay Family remain in the same train, validation, or test split.

No family may be split across evaluation boundaries.

**### Unseen Model Evaluation**

If an unseen generation-model holdout is used, that model must not contribute generated training/validation examples for the corresponding experiment.

**---**

**## 12. Hybrid Transformation Targets**

The first pilot should use controlled partial transformations rather than transforming entire essays.

The exact proportion will be determined during the pilot, but each hybrid variant must have a known transformation boundary.

The project should test at least:

\* localized AI polishing
\* localized AI splicing

The transformation location should not always be the same paragraph position across families.

**---**

**## 13. Reproducibility and Provenance**

For every generated artifact, retain enough information to answer:

\* Which human source produced this family?
\* Which task context was used?
\* Which model generated the variant?
\* Which runtime was used?
\* Which prompt version was used?
\* Which generation parameters were used?
\* Which passages were transformed?
\* When was it generated?
\* Which dataset version contains it?

The provenance record must be created at generation time rather than reconstructed later.

**---**

**## 14. Pilot Procedure**

The first generation pilot should be deliberately small.

Target:

\`\`\`text
\~5 selected human source essays
        │
        ├── 5 AI-generated
        ├── 5 AI-polished
        └── 5 AI-spliced
\`\`\`

This pilot is intended to validate the generation process, not to train the final detector.

The pilot should measure:

\* generation latency
\* output length
\* failure/retry rate
\* quality
\* transformation fidelity
\* provenance completeness
\* practical local compute requirements

Before generating all pilot variants, one family should be used as a protocol-validation case.

The first family must be reviewed for:

\* generation quality
\* task alignment
\* semantic preservation in the polished variant
\* correctness of spliced boundaries
\* manifest completeness

Only after the first family passes these checks should the remaining pilot families be generated.

Only after the pilot is reviewed should the project scale the number of Essay Families.

**---**

**## 15. What This Protocol Does Not Claim**

This protocol does not claim that:

\* AI-generated text represents every possible LLM writing style
\* AI-polished text represents every real-world editing workflow
\* AI-spliced text perfectly represents authentic human/AI collaboration
\* the resulting dataset represents all college admissions writing
\* generated text is ground truth for universal AI detection

The variants are controlled experimental constructions.

Their purpose is to create measurable, documented conditions under which the detector can be evaluated.

**---**

**## 16. Current Status**

**Status:** Protocol defined; generation candidate selected after EXP-003; controlled pilot pending.

### Locked

\* four variant definitions
\* source leakage rules
\* hybrid transformation boundaries
\* provenance requirements
\* prompt versioning
\* parameter recording
\* quality-control requirements
\* pilot-first generation
\* family-level split isolation
\* ₹0/local generation constraint
\* current generation candidate: `Qwen/Qwen2.5-0.5B-Instruct`
\* current runtime: Hugging Face Transformers on CPU

### Pending

\* exact generation prompt wording
\* final generation parameters for the pilot
\* hybrid transformation percentage
\* retry policy
\* final family count
\* whether a later model/runtime change is justified by pilot results

These decisions should be based on the controlled generation pilot rather than assumptions.
