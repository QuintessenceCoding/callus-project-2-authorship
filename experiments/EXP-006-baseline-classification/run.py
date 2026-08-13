from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "experiments"
    / "EXP-005-feature-distribution"
    / "results"
    / "results.json"
)

OUT_DIR = ROOT / "experiments" / "EXP-006-baseline-classification"
RESULTS = OUT_DIR / "results" / "results.json"

FEATURES = [
    "perplexity",
    "sentence_length_cv",
    "mattr",
    "pos_3gram_entropy",
]

SEED = 20260814


def load_feature_rows() -> pd.DataFrame:
    with INPUT.open("r", encoding="utf-8") as f:
        data = json.load(f)

    pair_results = data["pair_results"]

    rows: list[dict] = []

    for pair in pair_results:
        pair_id = str(pair["id"])

        for label, role in [(0, "human"), (1, "ai")]:
            feature_block = pair[role]["features"]

            row = {
                "pair_id": pair_id,
                "label": label,
            }

            for feature in FEATURES:
                row[feature] = feature_block[feature]["value"]

            rows.append(row)

    df = pd.DataFrame(rows)

    return df


def metrics(y_true, y_pred, y_prob) -> dict:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(
            precision_score(y_true, y_pred, zero_division=0)
        ),
        "recall": float(
            recall_score(y_true, y_pred, zero_division=0)
        ),
        "f1": float(
            f1_score(y_true, y_pred, zero_division=0)
        ),
        "roc_auc": float(
            roc_auc_score(y_true, y_prob)
        ),
        "confusion_matrix": confusion_matrix(
            y_true, y_pred
        ).tolist(),
    }


def make_model(features: list[str]) -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(
                    random_state=SEED,
                    max_iter=1000,
                ),
            ),
        ]
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "results").mkdir(parents=True, exist_ok=True)

    df = load_feature_rows()

    # Drop only rows where one of the required features is unavailable.
    before = len(df)

    df = df.dropna(subset=FEATURES).copy()

    dropped_rows = before - len(df)

    # Split by pair ID so human and AI versions of a pair
    # always remain in the same split.
    pair_ids = df["pair_id"].drop_duplicates().tolist()

    train_pairs, val_pairs = train_test_split(
        pair_ids,
        test_size=0.20,
        random_state=SEED,
    )

    train_pairs = set(train_pairs)
    val_pairs = set(val_pairs)

    train_df = df[df["pair_id"].isin(train_pairs)].copy()
    val_df = df[df["pair_id"].isin(val_pairs)].copy()

    # Safety checks.
    assert train_pairs.isdisjoint(val_pairs)

    assert set(train_df["label"]) == {0, 1}
    assert set(val_df["label"]) == {0, 1}

    # -----------------------------
    # Model A: perplexity only
    # -----------------------------
    model_ppl = make_model(["perplexity"])

    model_ppl.fit(
        train_df[["perplexity"]],
        train_df["label"],
    )

    pred_ppl = model_ppl.predict(
        val_df[["perplexity"]]
    )

    prob_ppl = model_ppl.predict_proba(
        val_df[["perplexity"]]
    )[:, 1]

    # -----------------------------
    # Model B: all four features
    # -----------------------------
    model_all = make_model(FEATURES)

    model_all.fit(
        train_df[FEATURES],
        train_df["label"],
    )

    pred_all = model_all.predict(
        val_df[FEATURES]
    )

    prob_all = model_all.predict_proba(
        val_df[FEATURES]
    )[:, 1]

    # Coefficients are on standardized features.
    classifier = model_all.named_steps["classifier"]

    results = {
        "experiment_id": "EXP-006",
        "name": "Baseline Classification",
        "seed": SEED,
        "source_experiment": "EXP-005",
        "feature_definition_source": "EXP-004",
        "input_pair_count": len(pair_ids),
        "rows_before_feature_filter": before,
        "rows_dropped_for_missing_features": dropped_rows,
        "train_pair_count": len(train_pairs),
        "validation_pair_count": len(val_pairs),
        "train_row_count": len(train_df),
        "validation_row_count": len(val_df),
        "models": {
            "perplexity_only": {
                "features": ["perplexity"],
                "metrics": metrics(
                    val_df["label"],
                    pred_ppl,
                    prob_ppl,
                ),
            },
            "all_features": {
                "features": FEATURES,
                "metrics": metrics(
                    val_df["label"],
                    pred_all,
                    prob_all,
                ),
                "standardized_coefficients": {
                    feature: float(coef)
                    for feature, coef in zip(
                        FEATURES,
                        classifier.coef_[0],
                    )
                },
            },
        },
        "delta_f1": float(
            f1_score(
                val_df["label"],
                pred_all,
                zero_division=0,
            )
            - f1_score(
                val_df["label"],
                pred_ppl,
                zero_division=0,
            )
        ),
        "validation": {
            "pair_disjoint": train_pairs.isdisjoint(val_pairs),
            "both_classes_in_train": set(train_df["label"]) == {0, 1},
            "both_classes_in_validation": set(val_df["label"]) == {0, 1},
        },
    }

    RESULTS.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()