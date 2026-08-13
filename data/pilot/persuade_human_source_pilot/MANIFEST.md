# PERSUADE Human-Source Pilot Manifest

## Dataset Provenance
- source dataset/version: PERSUADE 2.0 train source rows (local raw file)
- source archive/file: D:\Code\callushackathon\project2\callus-project-2-authorship\data\raw\persuade\persuade2_train_srctexts.csv
- source columns observed: ['essay_id_comp', 'discourse_id', 'discourse_start', 'discourse_end', 'discourse_type', 'predictionstring', 'discourse_text', 'discourse_effectiveness', 'discourse_type_num', 'hierarchical_id', 'hierarchical_text', 'hierarchical_label', 'prompt_name', 'assignment', 'gender', 'grade_level', 'ell_status', 'race_ethnicity', 'economically_disadvantaged', 'student_disability_status', 'source_text_1', 'source_text_2', 'source_text_3', 'source_text_4', 'task']

## Selection Policy
- Target count: approximately 8 essays
- Preference: grade_level 9/10
- Preference: substantial essays roughly 500-1500 words where possible
- Preference: prompt diversity
- No duplicate essay IDs
- Demographic fields (race, gender, economic status, disability status, etc.) are not used as model features
- ell_status retained only as metadata for later bias analysis
- No AI variants generated

## Reconstruction Finding
- The source rows include meaningful embedded whitespace in `discourse_text`, including paragraph line breaks for selected essays.
- `discourse_start` and `discourse_end` are used as inclusive character offsets; selected source rows are contiguous under that interpretation.
- Reconstruction preserves the `discourse_text` characters at their source offsets and uses spaces only for any offset gaps whose original characters are not available in this CSV.

## Selected Essays
### 1. 3CB7F7FC1F29
- essay_id_comp: 3CB7F7FC1F29
- prompt_name: "A Cowboy Who Rode the Waves"
- grade_level: 6
- task: Text dependent
- ell_status: No
- word count: 684
- source row count for essay: 25
- discourse row ordering key: discourse_start ascending
- discourse type set: ['Claim', 'Concluding Statement', 'Evidence', 'Lead', 'Position', 'Unannotated']
- discourse_id preview (first 12 in order): 1619801686224, 1619801693961, 1619801693960, 1619801701689, 1619801701688, 1619801710129, 1619801725453, 1619801725452, 1619801734488, 1619801750832, 1619801750831, 1619801766504
- selected file: selected/3CB7F7FC1F29.txt
- selection rationale: within preferred word range, unique essay_id_comp

### 2. D40D5A13E1AB
- essay_id_comp: D40D5A13E1AB
- prompt_name: Car-free cities
- grade_level: 10
- task: Text dependent
- ell_status: No
- word count: 669
- source row count for essay: 27
- discourse row ordering key: discourse_start ascending
- discourse type set: ['Claim', 'Concluding Statement', 'Evidence', 'Position', 'Unannotated']
- discourse_id preview (first 12 in order): 1622572449486, 1622572449485, 1622572457112, 1622572457111, 1622572462759, 1622572469720, 1622572474846, 1622572480143, 1622572480142, 1622572492624, 1622572492623, 1622572506668
- selected file: selected/D40D5A13E1AB.txt
- selection rationale: preferred grade 9/10, within preferred word range, unique essay_id_comp

### 3. D9B5F55E6705
- essay_id_comp: D9B5F55E6705
- prompt_name: Does the electoral college work?
- grade_level: 9
- task: Text dependent
- ell_status: No
- word count: 819
- source row count for essay: 30
- discourse row ordering key: discourse_start ascending
- discourse type set: ['Claim', 'Concluding Statement', 'Counterclaim', 'Evidence', 'Lead', 'Position', 'Rebuttal', 'Unannotated']
- discourse_id preview (first 12 in order): 1615300689783, 1615300699229, 1615300996646, 1615301007270, 1615301013485, 1615300794549, 1615300813344, 1615300813343, 1615300827591, 1615300844245, 1615300892877, 1615301065284
- selected file: selected/D9B5F55E6705.txt
- selection rationale: preferred grade 9/10, within preferred word range, unique essay_id_comp

### 4. AFB2995F886F
- essay_id_comp: AFB2995F886F
- prompt_name: Driverless cars
- grade_level: 10
- task: Text dependent
- ell_status: No
- word count: 757
- source row count for essay: 27
- discourse row ordering key: discourse_start ascending
- discourse type set: ['Claim', 'Concluding Statement', 'Counterclaim', 'Evidence', 'Position', 'Unannotated']
- discourse_id preview (first 12 in order): 1620997926049, 1620997952873, 1620997952872, 1620997962265, 1620997962264, 1620997969841, 1620997969840, 1620998047823, 1620998047822, 1620998091301, 1620998091300, 1620998162681
- selected file: selected/AFB2995F886F.txt
- selection rationale: preferred grade 9/10, within preferred word range, unique essay_id_comp

### 5. FB6A513EBFC6
- essay_id_comp: FB6A513EBFC6
- prompt_name: Exploring Venus
- grade_level: 10
- task: Text dependent
- ell_status: No
- word count: 752
- source row count for essay: 18
- discourse row ordering key: discourse_start ascending
- discourse type set: ['Claim', 'Concluding Statement', 'Counterclaim', 'Evidence', 'Lead', 'Position', 'Rebuttal', 'Unannotated']
- discourse_id preview (first 12 in order): 1616438247905, 1616438275220, 1616437932118, 1616437932117, 1616438077225, 1616438156552, 1616438156551, 1616437938072, 1616438053318, 1616438026551, 1616438035669, 1616438046529
- selected file: selected/FB6A513EBFC6.txt
- selection rationale: preferred grade 9/10, within preferred word range, unique essay_id_comp

### 6. 64EED50CD664
- essay_id_comp: 64EED50CD664
- prompt_name: Facial action coding system
- grade_level: 10
- task: Text dependent
- ell_status: No
- word count: 775
- source row count for essay: 22
- discourse row ordering key: discourse_start ascending
- discourse type set: ['Claim', 'Concluding Statement', 'Counterclaim', 'Evidence', 'Lead', 'Position', 'Rebuttal', 'Unannotated']
- discourse_id preview (first 12 in order): 1619699232832, 1619699225797, 1619699216047, 1619699216046, 1619699202167, 1619699208617, 1619699208616, 1619699310987, 1619699258051, 1619699274839, 1619699285278, 1619699249235
- selected file: selected/64EED50CD664.txt
- selection rationale: preferred grade 9/10, within preferred word range, unique essay_id_comp

### 7. C2E33FCEC470
- essay_id_comp: C2E33FCEC470
- prompt_name: Phones and driving
- grade_level: NA
- task: Independent
- ell_status: (missing)
- word count: 762
- source row count for essay: 24
- discourse row ordering key: discourse_start ascending
- discourse type set: ['Claim', 'Concluding Statement', 'Evidence', 'Position', 'Unannotated']
- discourse_id preview (first 12 in order): 1622559195537, 1622559195536, 1622559205703, 1622559205702, 1622559241506, 1622559241505, 1622559249215, 1622559249214, 1622559255492, 1622559255491, 1622559262211, 1622559262210
- selected file: selected/C2E33FCEC470.txt
- selection rationale: within preferred word range, unique essay_id_comp

### 8. 8E7A630DDB1B
- essay_id_comp: 8E7A630DDB1B
- prompt_name: The Face on Mars
- grade_level: 8
- task: Text dependent
- ell_status: No
- word count: 721
- source row count for essay: 21
- discourse row ordering key: discourse_start ascending
- discourse type set: ['Claim', 'Concluding Statement', 'Counterclaim', 'Evidence', 'Lead', 'Position', 'Rebuttal', 'Unannotated']
- discourse_id preview (first 12 in order): 1617737452227, 1617737452226, 1617737474419, 1617737474418, 1617737485563, 1617737500412, 1617737525701, 1617737532642, 1617737441914, 1617737544398, 1617737559893, 1617737571026
- selected file: selected/8E7A630DDB1B.txt
- selection rationale: within preferred word range, unique essay_id_comp
