"""Build data/processed/models_clean.csv from the source CSV.

Run from the repo folder:
    python -m src.build_processed

It reads the Epoch AI snapshot, applies clean_models() from src/data.py
(start year 2017, organisation name merging, derived columns) and writes the
processed file the app reads. Running it again on the same source produces
an identical file.
"""
import pandas as pd

from src.data import PROCESSED, SNAPSHOT, clean_models


def main():
    source = pd.read_csv(SNAPSHOT, low_memory=False)
    models = clean_models(source)
    PROCESSED.parent.mkdir(parents=True, exist_ok=True)
    models.to_csv(PROCESSED, index=False)
    print(f"Wrote {len(models)} models from {SNAPSHOT.name} to {PROCESSED}")


if __name__ == "__main__":
    main()
