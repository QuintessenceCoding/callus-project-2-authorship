import kagglehub

persuade_path = kagglehub.dataset_download(
    "julesking/tla-lab-persuade-dataset"
)

aide_path = kagglehub.dataset_download(
    "lburleigh/tla-lab-ai-detection-for-essays-aide-dataset"
)


path = kagglehub.dataset_download(
    "alejopaullier/daigt-external-dataset"
)

print("DAIGT External:", path)
print("PERSUADE:", persuade_path)
print("AIDE:", aide_path)