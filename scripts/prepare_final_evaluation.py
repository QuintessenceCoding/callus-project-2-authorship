from __future__ import annotations

import csv
import hashlib
import json
import random
from pathlib import Path

DATASET_PATH = Path("data/raw/daigt_external/daigt_external_dataset.csv")
EXP005_PATH = Path(
    "experiments/EXP-005-feature-distribution/results/results.json"
)
OUTPUT_PATH = Path("data/final_evaluation_manifest.json")

FINAL_PAIR_COUNT = 200
SEED = 20260815


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    with EXP005_PATH.open("r", encoding="utf-8") as handle:
        exp005 = json.load(handle)

    development_ids = set(
        exp005["sampling"]["selected_row_ids"]
    )

    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle))

    all_ids = [row["id"] for row in rows]

    untouched_ids = [
        row_id
        for row_id in all_ids
        if row_id not in development_ids
    ]

    if len(untouched_ids) < FINAL_PAIR_COUNT:
        raise RuntimeError(
            f"Only {len(untouched_ids)} untouched pairs are available; "
            f"need {FINAL_PAIR_COUNT}."
        )

    rng = random.Random(SEED)

    final_ids = sorted(
        rng.sample(
            untouched_ids,
            FINAL_PAIR_COUNT,
        )
    )

    assert not development_ids.intersection(final_ids)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest = {
        "evaluation_name": "final-heldout-evaluation-v1",
        "created_at": "2026-08-15",
        "dataset_path": str(DATASET_PATH),
        "dataset_sha256": sha256_file(DATASET_PATH),
        "total_dataset_pairs": len(all_ids),
        "development_pair_count": len(development_ids),
        "untouched_pair_count": len(untouched_ids),
        "final_pair_count": len(final_ids),
        "final_text_count": FINAL_PAIR_COUNT * 2,
        "seed": SEED,
        "pair_preservation": True,
        "development_ids_excluded": True,
        "selected_pair_ids": final_ids,
    }

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            manifest,
            handle,
            indent=2,
        )

    print(json.dumps({
        "total_dataset_pairs": len(all_ids),
        "development_pairs": len(development_ids),
        "untouched_pairs": len(untouched_ids),
        "final_pairs": len(final_ids),
        "final_texts": FINAL_PAIR_COUNT * 2,
        "seed": SEED,
        "dataset_sha256": manifest["dataset_sha256"],
        "output": str(OUTPUT_PATH),
    }, indent=2))


if __name__ == "__main__":
    main()