import pandas as pd

ORIGINAL_DATASET_PATH = "data/dataset.csv"
FILL_DATASET_PATH = "data/filled_dataset.csv"
SUBMISSION_PATH = "data/submission.csv"
SEPARATOR = "||"

def generate_solution(filled_path: str, output_path: str):
    print("Initializing submission conversion...")
    original = pd.read_csv(ORIGINAL_DATASET_PATH)
    filled = pd.read_csv(filled_path)

    feature_cols = [c for c in original.columns if c != "datetime"]

    rows = []
    for col in feature_cols:
        was_missing = original[col].isna()

        for idx in original.index[was_missing]:
            dt = original.loc[idx, "datetime"]
            uid = f"{dt}{SEPARATOR}{col}"
            val = filled.loc[idx, col]
            rows.append({"id": uid, "value": val})

    solution = pd.DataFrame(rows, columns=["id", "value"])
    solution = solution.sort_values("id").reset_index(drop=True)
    solution.to_csv(output_path, index=False)
    print(f"Submission saved -> {output_path} ({len(solution)} entries mapped)")

if __name__ == "__main__":
    generate_solution(FILL_DATASET_PATH, SUBMISSION_PATH)
