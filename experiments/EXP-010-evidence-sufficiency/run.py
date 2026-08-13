from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[2]

EXP005_RESULTS = (
    ROOT
    / "experiments"
    / "EXP-005-feature-distribution"
    / "results"
    / "results.json"
)

EXP006_RESULTS = (
    ROOT
    / "experiments"
    / "EXP-006-baseline-classification"
    / "results"
    / "results.json"
)

RAW_DAIGT = (
    ROOT
    / "data"
    / "raw"
    / "daigt_external"
    / "daigt_external_dataset.csv"
)

OUT = (
    ROOT
    / "experiments"
    / "EXP-010-evidence-sufficiency"
    / "results"
    / "results.json"
)

SEED = 20260814

FEATURES = [
    "perplexity",
    "sentence_length_cv",
    "mattr",
    "pos_3gram_entropy",
]

# Word-count bins used only for this diagnostic experiment.
WORD_BINS = [
    (0, 20),
    (21, 40),
    (41, 60),
    (61, 80),
    (81, 100),
    (101, 150),
    (151, 200),
    (201, float("inf")),
]

# Confidence margin = abs(P(AI) - 0.5)
MARGIN_BINS = [
    (0.00, 0.05),
    (0.05, 0.10),
    (0.10, 0.15),
    (0.15, 0.20),
    (0.20, 0.25),
    (0.25, 0.30),
    (0.30, 0.35),
    (0.35, 0.40),
    (0.40, 0.45),
    (0.45, 0.50),
]


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def finite(value) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def extract_pair_rows(exp005: dict) -> pd.DataFrame:
    pair_results = exp005.get("pair_results")

    if not isinstance(pair_results, list) or not pair_results:
        raise ValueError("EXP-005 pair_results missing or empty.")

    rows = []

    for pair in pair_results:
        pair_id = str(pair["id"])

        for label, role in [(0, "human"), (1, "ai")]:
            feature_block = (
                pair.get(role, {})
                .get("features", {})
            )

            row = {
                "pair_id": pair_id,
                "label": label,
            }

            for feature in FEATURES:
                entry = feature_block.get(feature)

                if not isinstance(entry, dict):
                    row[feature] = None
                else:
                    row[feature] = entry.get("value")

            rows.append(row)

    return pd.DataFrame(rows)


def load_raw_texts() -> pd.DataFrame:
    if not RAW_DAIGT.exists():
        raise FileNotFoundError(
            f"Missing DAIGT dataset: {RAW_DAIGT}"
        )

    df = pd.read_csv(
        RAW_DAIGT,
        usecols=["id", "text", "source_text"],
    )

    df["id"] = df["id"].astype(str)

    if df["id"].duplicated().any():
        raise ValueError("Raw DAIGT dataset contains duplicate IDs.")

    return df


def word_count(text: str) -> int:
    # Deliberately use whitespace-separated words.
    # This is a diagnostic binning variable, not a model feature.
    return len(str(text).split())


def build_model(features: list[str]) -> Pipeline:
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


def metric_block(
    y_true,
    y_pred,
    y_prob,
) -> dict:
    result = {
        "count": int(len(y_true)),
        "accuracy": float(
            accuracy_score(y_true, y_pred)
        ),
        "precision": float(
            precision_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        ),
        "recall": float(
            recall_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        ),
        "f1": float(
            f1_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        ),
    }

    # ROC-AUC requires both classes to be present.
    if len(set(y_true)) == 2:
        result["roc_auc"] = float(
            roc_auc_score(y_true, y_prob)
        )
    else:
        result["roc_auc"] = None

    return result


def assign_word_bin(value: int) -> str:
    for low, high in WORD_BINS:
        if low <= value <= high:
            if math.isinf(high):
                return f"{low}+"
            return f"{low}-{int(high)}"

    raise ValueError(
        f"Could not assign word count {value}"
    )


def assign_margin_bin(value: float) -> str:
    for index, (low, high) in enumerate(MARGIN_BINS):
        is_last = index == len(MARGIN_BINS) - 1

        if is_last:
            if low <= value <= high:
                return f"{low:.2f}-{high:.2f}"

        elif low <= value < high:
            return f"{low:.2f}-{high:.2f}"

    raise ValueError(
        f"Could not assign confidence margin {value}"
    )


def evaluate_bins(
    df: pd.DataFrame,
    column: str,
    bin_column_name: str,
) -> list[dict]:
    results = []

    for bin_label in df[bin_column_name].dropna().unique():
        subset = df[
            df[bin_column_name] == bin_label
        ].copy()

        y_true = subset["label"]
        y_pred = subset["prediction"]
        y_prob = subset["ai_probability"]

        item = {
            "bin": bin_label,
            "sample_count": int(len(subset)),
            "human_count": int(
                (subset["label"] == 0).sum()
            ),
            "ai_count": int(
                (subset["label"] == 1).sum()
            ),
        }

        item.update(
            metric_block(
                y_true,
                y_pred,
                y_prob,
            )
        )

        results.append(item)

    def sort_key(item):
        label = item["bin"]

        if bin_column_name == "word_bin":
            if label.endswith("+"):
                return float(label[:-1])
            return float(label.split("-")[0])

        return float(label.split("-")[0])

    results.sort(key=sort_key)

    return results


def main() -> None:
    exp005 = load_json(EXP005_RESULTS)
    exp006 = load_json(EXP006_RESULTS)

    features_df = extract_pair_rows(exp005)
    raw_df = load_raw_texts()

    # ---------------------------------------------------------
    # Recreate EXP-006 pair-level split exactly
    # ---------------------------------------------------------

    complete = features_df.dropna(
        subset=FEATURES
    ).copy()

    pair_ids = (
        complete["pair_id"]
        .drop_duplicates()
        .tolist()
    )

    train_pairs, validation_pairs = train_test_split(
        pair_ids,
        test_size=0.20,
        random_state=SEED,
    )

    train_pairs = set(train_pairs)
    validation_pairs = set(validation_pairs)

    train_df = complete[
        complete["pair_id"].isin(train_pairs)
    ].copy()

    validation_df = complete[
        complete["pair_id"].isin(validation_pairs)
    ].copy()

    # Critical leakage checks.
    assert train_pairs.isdisjoint(
        validation_pairs
    )

    assert set(train_df["label"]) == {0, 1}
    assert set(validation_df["label"]) == {0, 1}

    # ---------------------------------------------------------
    # Train exact EXP-006 four-feature model
    # ---------------------------------------------------------

    model = build_model(FEATURES)

    model.fit(
        train_df[FEATURES],
        train_df["label"],
    )

    validation_predictions = model.predict(
        validation_df[FEATURES]
    )

    validation_probabilities = (
        model.predict_proba(
            validation_df[FEATURES]
        )[:, 1]
    )

    validation_df = validation_df.copy()

    validation_df["prediction"] = (
        validation_predictions
    )

    validation_df["ai_probability"] = (
        validation_probabilities
    )

    validation_df["confidence_margin"] = (
        validation_df["ai_probability"]
        .sub(0.5)
        .abs()
    )

    # ---------------------------------------------------------
    # Join raw text for word-count analysis
    # ---------------------------------------------------------

    text_lookup = raw_df.set_index("id")

    def get_text(row):
        record = text_lookup.loc[row["pair_id"]]

        if row["label"] == 0:
            return record["text"]

        return record["source_text"]

    validation_df["text"] = validation_df.apply(
        get_text,
        axis=1,
    )

    validation_df["word_count"] = (
        validation_df["text"]
        .astype(str)
        .map(word_count)
    )

    validation_df["word_bin"] = (
        validation_df["word_count"]
        .map(assign_word_bin)
    )

    validation_df["margin_bin"] = (
        validation_df["confidence_margin"]
        .map(assign_margin_bin)
    )

    # ---------------------------------------------------------
    # Reproduction of aggregate EXP-006 result
    # ---------------------------------------------------------

    reproduced_metrics = metric_block(
        validation_df["label"],
        validation_df["prediction"],
        validation_df["ai_probability"],
    )

    saved_metrics = (
        exp006["models"]["all_features"]["metrics"]
    )

    metric_deltas = {}

    for name in (
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
    ):
        metric_deltas[name] = (
            reproduced_metrics[name]
            - saved_metrics[name]
        )

    # Tight tolerance because this should reproduce the
    # same deterministic model/split.
    reproduction_matches = all(
        abs(value) <= 1e-12
        for value in metric_deltas.values()
    )

    # ---------------------------------------------------------
    # Word-length bins
    # ---------------------------------------------------------

    word_bins = evaluate_bins(
        validation_df,
        "word_count",
        "word_bin",
    )

    # ---------------------------------------------------------
    # Confidence-margin bins
    # ---------------------------------------------------------

    margin_bins = evaluate_bins(
        validation_df,
        "confidence_margin",
        "margin_bin",
    )

    # ---------------------------------------------------------
    # Save row-level validation diagnostics
    # ---------------------------------------------------------

    row_predictions = []

    for _, row in validation_df.sort_values(
        ["pair_id", "label"]
    ).iterrows():
        row_predictions.append(
            {
                "pair_id": row["pair_id"],
                "label": int(row["label"]),
                "word_count": int(row["word_count"]),
                "word_bin": row["word_bin"],
                "ai_probability": float(
                    row["ai_probability"]
                ),
                "confidence_margin": float(
                    row["confidence_margin"]
                ),
                "margin_bin": row["margin_bin"],
                "prediction": int(
                    row["prediction"]
                ),
                "correct": bool(
                    row["prediction"]
                    == row["label"]
                ),
            }
        )

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    validation = {
        "pair_split_disjoint": (
            train_pairs.isdisjoint(
                validation_pairs
            )
        ),
        "both_classes_in_train": (
            set(train_df["label"]) == {0, 1}
        ),
        "both_classes_in_validation": (
            set(validation_df["label"]) == {0, 1}
        ),
        "reproduced_exp006_metrics": (
            reproduction_matches
        ),
        "validation_row_count_matches_exp006": (
            len(validation_df)
            == exp006["validation_row_count"]
        ),
        "raw_dataset_rows_joined": (
            len(validation_df)
            == len(
                validation_df[
                    validation_df["word_count"].notna()
                ]
            )
        ),
    }

    validation["all_passed"] = all(
        validation.values()
    )

    # ---------------------------------------------------------
    # Output
    # ---------------------------------------------------------

    output = {
        "experiment_id": "EXP-010",
        "name": (
            "Evidence Sufficiency & Empirical Abstention"
        ),
        "status": "Completed",
        "purpose": (
            "Measure how validation performance changes "
            "with text length and classifier confidence "
            "margin, using the deterministic EXP-006 "
            "four-feature baseline."
        ),
        "source_experiments": {
            "EXP-005": str(EXP005_RESULTS),
            "EXP-006": str(EXP006_RESULTS),
        },
        "model": {
            "type": "LogisticRegression",
            "features": FEATURES,
            "seed": SEED,
            "standardization": (
                "StandardScaler fitted on training data only"
            ),
        },
        "split": {
            "train_pair_count": len(train_pairs),
            "validation_pair_count": len(
                validation_pairs
            ),
            "train_row_count": len(train_df),
            "validation_row_count": len(
                validation_df
            ),
        },
        "reproduction": {
            "saved_exp006_metrics": saved_metrics,
            "reproduced_metrics": reproduced_metrics,
            "metric_deltas": metric_deltas,
            "matches_saved_exp006": (
                reproduction_matches
            ),
        },
        "word_length_analysis": {
            "bin_definition": (
                "Whitespace-separated word counts"
            ),
            "bins": WORD_BINS,
            "results": word_bins,
        },
        "confidence_margin_analysis": {
            "definition": (
                "abs(P(AI) - 0.5)"
            ),
            "bins": MARGIN_BINS,
            "results": margin_bins,
        },
        "row_level_validation_predictions": (
            row_predictions
        ),
        "interpretation_guardrail": (
            "This experiment estimates whether empirical "
            "abstention regions are justified on the same "
            "bounded validation split used by EXP-006. "
            "It does not establish universal thresholds."
        ),
        "validation": validation,
    }

    OUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUT.write_text(
        json.dumps(
            output,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "experiment_id": "EXP-010",
                "validation": validation,
                "reproduced_metrics": reproduced_metrics,
                "word_bin_count": len(word_bins),
                "margin_bin_count": len(
                    margin_bins
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()