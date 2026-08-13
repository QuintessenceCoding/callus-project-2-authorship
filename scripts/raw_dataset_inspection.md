# Raw Dataset Inspection (Local Files Only)

## Scope and Guardrails
- Inspected only local raw files.
- No raw dataset files were modified.
- No processed datasets were created.
- No training or text generation was performed.
- PERSUADE CSV was processed in streaming mode (row-by-row), not loaded wholesale.

## Files
- AIDE essays: `D:\Code\callushackathon\project2\callus-project-2-authorship\data\raw\aide\AIDE_train_essays.csv`
- AIDE prompts: `D:\Code\callushackathon\project2\callus-project-2-authorship\data\raw\aide\train_prompts.csv`
- AIDE instructions docx: `D:\Code\callushackathon\project2\callus-project-2-authorship\data\raw\aide\Instructions to recreate AI Generated Text Dataset.docx` (exists: True)
- PERSUADE source rows: `D:\Code\callushackathon\project2\callus-project-2-authorship\data\raw\persuade\persuade2_train_srctexts.csv`
- PERSUADE annotation scheme pdf: `D:\Code\callushackathon\project2\callus-project-2-authorship\data\raw\persuade\PERSUADE corpus_ annotation scheme - binary.pdf` (exists: True)

## AIDE Inspection
- Row count: 1,378
- Columns: ['id', 'prompt_id', 'text', 'generated']
- Inferred data types:
  - id: string
  - prompt_id: int
  - text: string
  - generated: int
- `generated` unique values / counts:
  - '0': 1375
  - '1': 3
- Unique prompt IDs (2): ['0', '1']
- Text length (characters): min=1,356, median=2,985.50, max=8,436
- First 2 records (safe preview):
  - Record 1:
    - id: 0059830c
    - prompt_id: 0
    - generated: 0
    - text_preview: Cars. Cars have been around since they became famous in the 1900s, when Henry Ford created and built the first ModelT. Cars have played a major role in our every day lives since then. But now, people are starting to question if limiting car...
  - Record 2:
    - id: 005db917
    - prompt_id: 0
    - generated: 0
    - text_preview: Transportation is a large necessity in most countries worldwide. With no doubt, cars, buses, and other means of transportation make going from place to place easier and faster. However there's always a negative pollution. Although mobile tr...
- Prompt joinability with train_prompts.csv: True

## PERSUADE Inspection
- Total row count: 84,440
- Column names (25): ['essay_id_comp', 'discourse_id', 'discourse_start', 'discourse_end', 'discourse_type', 'predictionstring', 'discourse_text', 'discourse_effectiveness', 'discourse_type_num', 'hierarchical_id', 'hierarchical_text', 'hierarchical_label', 'prompt_name', 'assignment', 'gender', 'grade_level', 'ell_status', 'race_ethnicity', 'economically_disadvantaged', 'student_disability_status', 'source_text_1', 'source_text_2', 'source_text_3', 'source_text_4', 'task']
- Unique `essay_id_comp` count: 8,426
- Unique `prompt_name` count: 8
- `grade_level` values/counts:
- '10': 42932
- '9': 19894
- '8': 7816
- 'NA': 7381
- '6': 6417
- `ell_status` values/counts:
- 'No': 70459
- '': 7530
- 'Yes': 5725
- ' ': 726
- `task` values/counts:
- 'Text dependent': 77059
- 'Independent': 7381
- Approximate essay length distribution (chars, reconstructed using min(discourse_start) and max(discourse_end) per essay):
  - min=158, median=1,973.50, p90=3,321, p95=3,832, max=7,939
- Number of discourse types: 8
- Discourse type counts:
- 'Claim': 24118
- 'Evidence': 23830
- 'Unannotated': 11205
- 'Position': 8239
- 'Concluding Statement': 7118
- 'Lead': 4823
- 'Counterclaim': 2963
- 'Rebuttal': 2144
- Multiple rows per essay present: True (8,338 / 8,426 essays have >1 row)
- Sample essay discourse-to-text mapping:
  - sample essay_id_comp: 423A1CA112E2
  - discourse rows found for sample: 11
  - row text aligns with reconstructed span: 11/11 rows
  - reconstructed essay preview (safe):
    - Phones  Modern humans today are always on their phone. They are always on their phone more than 5 hours a day no stop .All they do is text back and forward and just have group Chats on social media. They even do it while driving. They are some really bad consequences when stuff happens when it comes to a phone. Some certain areas in the United States ban phones from class rooms just because of it. When people have phones, they know about certain apps that they have .Apps like Facebook Twitter In...
  - first discourse rows (ordered by span):
    - [0, 7) type='Unannotated' discourse_id=1622627660525 text=Phones
    - [8, 229) type='Lead' discourse_id=1622627660524 text=Modern humans today are always on their phone. They are always on their phone more than 5 hours a day no stop .All they ...
    - [230, 312) type='Position' discourse_id=1622627653021 text=They are some really bad consequences when stuff happens when it comes to a phone.
    - [313, 400) type='Evidence' discourse_id=1622627671020 text=Some certain areas in the United States ban phones from class rooms just because of it.
    - [401, 756) type='Evidence' discourse_id=1622627696365 text=When people have phones, they know about certain apps that they have .Apps like Facebook Twitter Instagram and Snapchat....
    - [757, 884) type='Claim' discourse_id=1622627759780 text=Driving is one of the way how to get around. People always be on their phones while doing it. Which can cause serious Pr...
    - [885, 1147) type='Evidence' discourse_id=1622627780655 text=That's why there's a thing that's called no texting while driving. That's a really important thing to remember. Some peo...
    - [1148, 1528) type='Evidence' discourse_id=1622627811787 text=Sometimes on the news there is either an accident or a suicide. It might involve someone not looking where they're going...
    - [1529, 1597) type='Claim' discourse_id=1622627585180 text=Phones are fine to use and it's also the best way to come over help.
    - [1598, 1885) type='Evidence' discourse_id=1622627895668 text=If you go through a problem and you can't find help you ,always have a phone there with you. Even though phones are used...
    - [1886, 2021) type='Concluding Statement' discourse_id=1622627628524 text=The news always updated when people do something stupid around that involves their phones. The safest way is the best wa...

## Stop Condition
Inspection completed. No additional processing was performed.
