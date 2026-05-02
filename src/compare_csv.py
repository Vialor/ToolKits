#!/usr/bin/env python

import pandas as pd
from pathlib import Path


# =========================
# 配置区
# =========================
ANSWER_CSV = r"C:\Users\USER\Desktop\a.csv"
PREDICTION_CSV = r"C:\Users\USER\Desktop\b.csv"

ANSWER_COLUMNS = ["src_id", "src_interface", "dst_id", "dst_interface", "source"]
PREDICTION_COLUMNS = ["local_device", "local_interface", "remote_device", "remote_interface", "source"]

OUT_PREFIX = "result"

# =========================
# 脚本逻辑区
# =========================

def read_csv_or_folder(path: str) -> pd.DataFrame:
    path_obj = Path(path)

    if path_obj.is_file():
        return pd.read_csv(path_obj)

    if path_obj.is_dir():
        csv_files = sorted(path_obj.glob("*.csv"))

        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in folder: {path}")

        dfs = []
        for csv_file in csv_files:
            print(f"Reading: {csv_file}")
            dfs.append(pd.read_csv(csv_file))

        return pd.concat(dfs, ignore_index=True)

    raise FileNotFoundError(f"Path not found: {path}")


def normalize_df(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    out = df[columns].copy()
    out = out.fillna("").astype(str).apply(lambda col: col.str.strip())
    return out


def rows_to_set(df: pd.DataFrame) -> set[tuple]:
    return set(map(tuple, df.to_numpy()))


def write_rows(path: str, rows: set[tuple], columns: list[str]) -> None:
    pd.DataFrame(sorted(rows), columns=columns).to_csv(
        path,
        index=False,
        encoding="utf-8-sig",
    )


def main():
    if len(ANSWER_COLUMNS) != len(PREDICTION_COLUMNS):
        raise ValueError("ANSWER_COLUMNS and PREDICTION_COLUMNS must have same length.")

    answer_df = read_csv_or_folder(ANSWER_CSV)
    prediction_df = read_csv_or_folder(PREDICTION_CSV)

    answer = normalize_df(answer_df, ANSWER_COLUMNS)
    prediction = normalize_df(prediction_df, PREDICTION_COLUMNS)

    prediction.columns = ANSWER_COLUMNS

    answer_set = rows_to_set(answer)
    prediction_set = rows_to_set(prediction)

    matched = answer_set & prediction_set
    only_answer = answer_set - prediction_set
    only_prediction = prediction_set - answer_set

    true_positive = len(matched)
    false_negative = len(only_answer)
    false_positive = len(only_prediction)

    precision = true_positive / len(prediction_set) if prediction_set else 0.0
    recall = true_positive / len(answer_set) if answer_set else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall > 0
        else 0.0
    )

    write_rows(f"{OUT_PREFIX}_matched.csv", matched, ANSWER_COLUMNS)
    write_rows(f"{OUT_PREFIX}_only_answer.csv", only_answer, ANSWER_COLUMNS)
    write_rows(f"{OUT_PREFIX}_only_prediction.csv", only_prediction, ANSWER_COLUMNS)

    with open(f"{OUT_PREFIX}_summary.txt", "w", encoding="utf-8") as f:
        f.write("CSV Comparison Report\n")
        f.write("=====================\n\n")
        f.write(f"answer rows:           {len(answer_set)}\n")
        f.write(f"prediction rows:       {len(prediction_set)}\n\n")
        f.write(f"matched rows:          {true_positive}\n")
        f.write(f"only in answer:        {false_negative}\n")
        f.write(f"only in prediction:    {false_positive}\n\n")
        f.write(f"precision:             {precision:.6f}\n")
        f.write(f"recall:                {recall:.6f}\n")
        f.write(f"f1:                    {f1:.6f}\n\n")
        f.write("Definitions:\n")
        f.write("precision = matched / prediction rows\n")
        f.write("recall    = matched / answer rows\n")

    print("Done.")
    print(f"Answer rows:     {len(answer_set)}")
    print(f"Prediction rows: {len(prediction_set)}")
    print(f"Matched rows:    {true_positive}")
    print(f"Precision:       {precision:.6f}")
    print(f"Recall:          {recall:.6f}")
    print(f"F1:              {f1:.6f}")


if __name__ == "__main__":
    main()