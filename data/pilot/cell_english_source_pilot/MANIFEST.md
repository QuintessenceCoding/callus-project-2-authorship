# CELL English Human-Source Pilot Pool

This is a source-diversity pilot pool from the CELL English corpus. These records are human source candidates only. They are not Essay Families, and no AI-generated, AI-polished, or AI-spliced variants have been created.

## Source

- Source dataset/version: CELL Corpus local download, `gs4ppd7sz3-1`
- Source archive: `data/raw/cell/gs4ppd7sz3-1/gs4ppd7sz3-1/English_data.zip`
- Archive inspection basis: ZIP central-directory metadata and selective in-memory content reads
- Archive size: `141,106,116` bytes
- Archive uncompressed size: `137,094,098` bytes
- Archive entries: `11,428`
- File extensions observed: `.txt` only
- Clean non-`All` response files observed: `2,857`
- Tagged non-`All` annotation files observed: `2,857`

The full archive was not extracted. The original ZIP archives were not modified, moved, deleted, or recompressed.

## Archive Structure Notes

Observed English archive path pattern:

```text
term/
  term_course_task_assignment_question/
    term_course_task_assignment_question_clean_markup_txt/
      term_course_task_assignment_question_source-record-id.txt
    term_course_task_assignment_question_clean_markup_txt_tag/
      term_course_task_assignment_question_source-record-id_tagged.txt
```

The `All/` top-level folder contains aggregate duplicate copies of the term-organized files. Files under `*_clean_markup_txt_tag/` are POS-tagged or otherwise annotated derivatives and were not selected.

Filename/path identifiers appear to encode term, course, task, assignment, question, and an anonymized source record identifier. These identifiers are source metadata only. They are not treated as topic labels, demographic labels, model features, or Essay Family identifiers.

## Selection Policy

The first five-record pilot at `data/pilot/cell_english_5_essay_pilot/` was an ingestion validation artifact and used five responses from the same encoded task/question path.

This second pilot instead prioritizes source-path diversity:

- Select clean English response records only.
- Exclude `All/` aggregate duplicates.
- Exclude `_tagged.txt` annotation files.
- Prefer one response per encoded term/course/task/assignment/question path.
- Prefer substantial essay-like responses.
- Do not use demographic metadata as a model feature.
- Do not label these records as Essay Families.

## Candidate Inspection Summary

- Candidate records content-inspected: `16`
- Selected records: `10`
- Excluded inspected records: `6`

## Selected Records

| Selected essay path | Source path in ZIP | Source record/file identifier | Term | Course | Task | Assignment | Question | Approx. words | Selection rationale |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| `data/pilot/cell_english_source_pilot/2018_06_edue350f_t01_a01_q01_s0000719.txt` | `2018_06/2018_06_edue350f_t01_a01_q01/2018_06_edue350f_t01_a01_q01_clean_markup_txt/2018_06_edue350f_t01_a01_q01_s0000719.txt` | `s0000719` | `2018_06` | `edue350f` | `t01` | `a01` | `q01` | 4718 | Clean, non-tagged, non-`All`, substantial response from a distinct encoded source path. |
| `data/pilot/cell_english_source_pilot/2018_09_engle200f_t01_a02_q01_s000056.txt` | `2018_09/2018_09_engle200f_t01_a02_q01/2018_09_engle200f_t01_a02_q01_clean_markup_txt/2018_09_engle200f_t01_a02_q01_s000056.txt` | `s000056` | `2018_09` | `engle200f` | `t01` | `a02` | `q01` | 1306 | Clean, non-tagged, non-`All`, substantial response from a distinct encoded source path. |
| `data/pilot/cell_english_source_pilot/2018_09_gene141f_t01_a01_q01_s0000267.txt` | `2018_09/2018_09_gene141f_t01_a01_q01/2018_09_gene141f_t01_a01_q01_clean_markup_txt/2018_09_gene141f_t01_a01_q01_s0000267.txt` | `s0000267` | `2018_09` | `gene141f` | `t01` | `a01` | `q01` | 1049 | Clean, non-tagged, non-`All`, substantial response from a distinct encoded source path. |
| `data/pilot/cell_english_source_pilot/2019_01_engle102f_t01_a01_q01_s000020.txt` | `2019_01/2019_01_engle102f_t01_a01_q01/2019_01_engle102f_t01_a01_q01_clean_markup_txt/2019_01_engle102f_t01_a01_q01_s000020.txt` | `s000020` | `2019_01` | `engle102f` | `t01` | `a01` | `q01` | 756 | Clean, non-tagged, non-`All`, readable essay response from a distinct encoded source path. |
| `data/pilot/cell_english_source_pilot/2019_06_engle339f_t01_a01_q01_s0000612.txt` | `2019_06/2019_06_engle339f_t01_a01_q01/2019_06_engle339f_t01_a01_q01_clean_markup_txt/2019_06_engle339f_t01_a01_q01_s0000612.txt` | `s0000612` | `2019_06` | `engle339f` | `t01` | `a01` | `q01` | 2996 | Clean, non-tagged, non-`All`, substantial response from a distinct encoded source path. |
| `data/pilot/cell_english_source_pilot/2019_09_engle360f_t01_a02_q02_s0000558.txt` | `2019_09/2019_09_engle360f_t01_a02_q02/2019_09_engle360f_t01_a02_q02_clean_markup_txt/2019_09_engle360f_t01_a02_q02_s0000558.txt` | `s0000558` | `2019_09` | `engle360f` | `t01` | `a02` | `q02` | 2101 | Clean, non-tagged, non-`All`, substantial response from a distinct encoded source path. |
| `data/pilot/cell_english_source_pilot/2019_09_engle360f_t02_a01_q01_s00005.txt` | `2019_09/2019_09_engle360f_t02_a01_q01/2019_09_engle360f_t02_a01_q01_clean_markup_txt/2019_09_engle360f_t02_a01_q01_s00005.txt` | `s00005` | `2019_09` | `engle360f` | `t02` | `a01` | `q01` | 2896 | Clean, non-tagged, non-`All`, substantial response added to improve encoded task diversity. |
| `data/pilot/cell_english_source_pilot/2020_01_edue253f_t01_a01_q01_s0000435.txt` | `2020_01/2020_01_edue253f_t01_a01_q01/2020_01_edue253f_t01_a01_q01_clean_markup_txt/2020_01_edue253f_t01_a01_q01_s0000435.txt` | `s0000435` | `2020_01` | `edue253f` | `t01` | `a01` | `q01` | 2883 | Clean, non-tagged, non-`All`, substantial response from a distinct encoded source path. |
| `data/pilot/cell_english_source_pilot/2020_01_engle102f_t03_a01_q01_s00001013.txt` | `2020_01/2020_01_engle102f_t03_a01_q01/2020_01_engle102f_t03_a01_q01_clean_markup_txt/2020_01_engle102f_t03_a01_q01_s00001013.txt` | `s00001013` | `2020_01` | `engle102f` | `t03` | `a01` | `q01` | 712 | Clean, non-tagged, non-`All`, readable substantial response added to improve encoded task diversity. |
| `data/pilot/cell_english_source_pilot/2020_06_edue219f_t01_a02_q01_s0000272.txt` | `2020_06/2020_06_edue219f_t01_a02_q01/2020_06_edue219f_t01_a02_q01_clean_markup_txt/2020_06_edue219f_t01_a02_q01_s0000272.txt` | `s0000272` | `2020_06` | `edue219f` | `t01` | `a02` | `q01` | 3608 | Clean, non-tagged, non-`All`, substantial response from a distinct encoded source path. |

## Inspected But Not Selected

| Source path in ZIP | Approx. words | Exclusion/filtering reason |
| --- | ---: | --- |
| `2018_09/2018_09_engle101f_t01_a01_q02/2018_09_engle101f_t01_a01_q02_clean_markup_txt/2018_09_engle101f_t01_a01_q02_s0000932.txt` | 397 | Readable response, but shorter than selected records; excluded to prefer more substantial essays for this pilot pool. |
| `2019_09/2019_09_engle320f_t01_a03_q02/2019_09_engle320f_t01_a03_q02_clean_markup_txt/2019_09_engle320f_t01_a03_q02_s0000531.txt` | 3389 | Substantial response, but opening contained sparse structural headings and an empty intro; excluded in favor of cleaner essay-like records for this small pool. |
| `2020_01/2020_01_engle210f_t01_a01_q01/2020_01_engle210f_t01_a01_q01_clean_markup_txt/2020_01_engle210f_t01_a01_q01_s0000183.txt` | 5067 | Substantial response, but appears centered on spoken-language/video discussion analysis and may be transcript-heavy; excluded to keep this small pilot simpler. |
| `2018_09/2018_09_edue365f_t01_a03_q01/2018_09_edue365f_t01_a03_q01_clean_markup_txt/2018_09_edue365f_t01_a03_q01_s0000232.txt` | 6058 | Substantial response, but very long assessment-design report; excluded because the pilot already reached the requested 5-10 record range with more moderate lengths. |
| `2019_09/2019_09_engle300f_t02_a01_q01/2019_09_engle300f_t02_a01_q01_clean_markup_txt/2019_09_engle300f_t02_a01_q01_s0000678.txt` | 7044 | Clean and substantial, but very long; excluded because shorter task-diverse candidates were available within the requested pilot size. |
| `2018_09/2018_09_engle300f_t03_a01_q01/2018_09_engle300f_t03_a01_q01_clean_markup_txt/2018_09_engle300f_t03_a01_q01_s0000676.txt` | 8919 | Clean and substantial, but very long; excluded because shorter task-diverse candidates were available within the requested pilot size. |

## Validation Results

- Selected file count: `10`
- All selected files exist locally: yes
- All selected files are readable: yes
- All selected files are non-empty: yes
- Approximate selected word-count range: `712-4718`
- Duplicate source record IDs: none found
- Duplicate encoded term/course/task/assignment/question keys: none found
- Encoded task identifiers represented: `t01`, `t02`, `t03`
- Tagged or annotation files selected: none
- `All/` aggregate copies selected: none
- AI variants generated: none
- Classifier or feature extraction created: none

## Important Scope Notes

CELL is an undergraduate academic-writing source, not an admissions-specific corpus. These records may be useful for ingestion and source-pool testing, but they do not by themselves satisfy the final target-domain requirement for college admissions essays.

No final dataset size, split, Essay Family structure, topic taxonomy, or AI-generation protocol has been established.
