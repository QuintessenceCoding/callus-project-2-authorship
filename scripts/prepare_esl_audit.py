from __future__ import annotations

import json
import random
from pathlib import Path

import pandas as pd


DATASET = Path(
    "data/raw/persuade/persuade2_train_srctexts.csv"
)

OUTPUT = Path(
    "data/esl_audit_manifest.json"
)

SEED = 20260815


def main() -> None:
    df = pd.read_csv(
        DATASET,
        low_memory=False,
    )

    # Collapse discourse rows to one record per essay.
    essays = (
        df[
            [
                "essay_id_comp",
                "ell_status",
                "task",
            ]
        ]
        .drop_duplicates("essay_id_comp")
        .copy()
    )

    essays = essays[
        essays["ell_status"].isin(["Yes", "No"])
    ].copy()

    ell = essays[
        essays["ell_status"] == "Yes"
    ]

    non_ell = essays[
        essays["ell_status"] == "No"
    ]

    if len(ell) < 1:
        raise RuntimeError(
            "No ELL essays found."
        )

    sample_size = len(ell)

    if len(non_ell) < sample_size:
        raise RuntimeError(
            "Not enough non-ELL essays for a balanced audit."
        )

    rng = random.Random(SEED)

    ell_ids = sorted(
        ell["essay_id_comp"].astype(str)
    )

    non_ell_ids = sorted(
        non_ell["essay_id_comp"].astype(str)
    )

    sampled_non_ell = sorted(
        rng.sample(
            non_ell_ids,
            sample_size,
        )
    )

    manifest = {
        "audit_name": "esl-non-native-english-audit-v1",
        "created_at": "2026-08-15",
        "dataset": str(DATASET),
        "seed": SEED,
        "task": "Text dependent",
        "ell_count": len(ell_ids),
        "non_ell_count": len(sampled_non_ell),
        "total_essays": (
            len(ell_ids)
            + len(sampled_non_ell)
        ),
        "ell_ids": ell_ids,
        "non_ell_ids": sampled_non_ell,
    }

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT.write_text(
        json.dumps(
            manifest,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "ELL essays": len(ell_ids),
                "non-ELL essays": len(sampled_non_ell),
                "total": (
                    len(ell_ids)
                    + len(sampled_non_ell)
                ),
                "seed": SEED,
                "output": str(OUTPUT),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()