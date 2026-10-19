"""Shared loading and cleaning for every panel.

All four panels import from here so that they count the same way. Do not read
the CSV directly in a panel file: the start-year filter and the organisation
rules live here, and a panel that bypasses them will contradict the others on
screen.
"""
from pathlib import Path

import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "data"
SNAPSHOT = DATA / "notable_ai_models_2026-10-18.csv"

SNAPSHOT_DATE = "18 October 2026"
SOURCE_LINE = ("Source: Notable AI Models, Epoch AI, CC BY 4.0. "
               f"Snapshot taken {SNAPSHOT_DATE}.")

# Before 2017 there are too few models in a year for a proportion to carry
# meaning, so the app starts with the transformer era.
START_YEAR = 2017

# DeepMind has sat inside Google since 2014 and merged with Google Brain in
# 2023, so the five Google strings describe work in one corporate group over
# the period measured here. Folding them changes the ranking: Google's
# variants total 117 models against OpenAI's 76, so unfolded the data would
# show OpenAI in front. The app states the rule on screen.
ORGANISATION_ALIASES = {
    "Google DeepMind": "Google",
    "Google Research": "Google",
    "Google Brain": "Google",
    "DeepMind": "Google",
    "Meta AI": "Meta",
    "Facebook AI Research": "Meta",
    "Facebook AI": "Meta",
    "Facebook": "Meta",
    "Microsoft Research": "Microsoft",
    "Salesforce Research": "Salesforce",
}

# 230 of the 788 models from 2017 onwards credit more than one organisation.
MULTI_CREDIT_MODELS = 230


def canonical(name):
    """Fold a published organisation string onto its parent entity."""
    name = str(name).strip()
    if name in ORGANISATION_ALIASES:
        return ORGANISATION_ALIASES[name]
    return name


@st.cache_data
def load_models():
    """One row per model, with the shared derived columns added."""
    frame = pd.read_csv(SNAPSHOT, low_memory=False)
    frame["publication_date"] = pd.to_datetime(frame["Publication date"],
                                               errors="coerce")
    frame["year"] = frame["publication_date"].dt.year
    frame = frame[frame["year"] >= START_YEAR].copy()

    # One organisation per model: the first credited, after aliasing. Training
    # compute cannot be divided between partners without inventing a split
    # rule, so panels measuring compute use this column.
    leads = []
    for value in frame["Organization"]:
        leads.append(canonical(str(value).split(",")[0]))
    frame["organisation"] = leads

    frame["compute_flop"] = pd.to_numeric(frame["Training compute (FLOP)"],
                                          errors="coerce")
    frame["has_compute"] = frame["compute_flop"].notna()
    frame["is_frontier"] = frame["Frontier model"].notna()
    frame["sector"] = frame["Organization categorization"].fillna("Not stated")
    frame["country"] = frame["Country (of organization)"].fillna("Not stated")
    frame["confidence"] = frame["Confidence"].fillna("Not stated")

    frame = frame.sort_values(["year", "organisation"]).reset_index(drop=True)
    validate(frame)
    return frame


def validate(frame):
    """Stop the load if the data breaks something the panels assume."""
    required = ["Model", "organisation", "year", "has_compute", "is_frontier",
                "sector", "country", "confidence", "compute_flop"]
    for column in required:
        if column not in frame.columns:
            raise ValueError(f"Missing column: {column}")

    if len(frame) < 500:
        raise ValueError("Expected at least 500 models from 2017 onwards")

    if frame["year"].min() < START_YEAR:
        raise ValueError(f"A row predates the start year {START_YEAR}")

    if frame["organisation"].str.contains(",").any():
        raise ValueError("Organisation must be a single name, not a list")

    if frame["organisation"].str.strip().eq("").any():
        raise ValueError("Every model must carry an organisation")

    present = frame.loc[frame["has_compute"], "compute_flop"]
    if (present <= 0).any():
        raise ValueError("Training compute must be positive where present")


@st.cache_data
def exploded_organisations(frame):
    """One row per organisation credited on a model.

    In collaborations the industry partner is usually listed first, so taking
    only the lead would strip academic partners out of a participation count.
    A panel measuring how many organisations are in the game should call this;
    one measuring compute should not, since compute cannot be split.
    """
    rows = []
    for i in frame.index:
        for name in str(frame.loc[i, "Organization"]).split(","):
            name = canonical(name)
            if name and name.lower() != "nan":
                rows.append({"Model": frame.loc[i, "Model"],
                             "organisation": name,
                             "year": frame.loc[i, "year"],
                             "country": frame.loc[i, "country"]})
    return pd.DataFrame(rows).drop_duplicates(["Model", "organisation"])
