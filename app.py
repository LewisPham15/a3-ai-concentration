"""Is the development of leading AI models concentrating in fewer organisations?

Four panels, one per group member. Each lives in its own module and exposes a
single render(models) function, so nobody edits this file after setup.
"""
import streamlit as st

from src.data import (MULTI_CREDIT_MODELS, SNAPSHOT_DATE, SOURCE_LINE,
                      START_YEAR, load_models)

st.set_page_config(page_title="AI model concentration", layout="wide")

models = load_models()

st.title("Is the development of leading AI models "
         "concentrating in fewer organisations?")
st.write(
    "**Question.** Are the most capable AI models coming from a shrinking set "
    "of organisations, or is the field opening up? The same dataset supports "
    "both readings, and which one you reach depends on whether you count "
    "models or the compute behind them."
)
st.caption(
    "Audience: a competition policy analyst at the ACCC, deciding whether AI "
    "model development warrants closer competition monitoring."
)
st.caption(f"Data as at {SNAPSHOT_DATE}. Models published from {START_YEAR}.")

total = len(models)
organisations = models["organisation"].nunique()
countries = models["country"].nunique()
disclosed = int(models["has_compute"].sum())

first, second, third, fourth = st.columns(4)
first.metric("Notable models", f"{total:,}")
second.metric("Lead organisations", f"{organisations:,}")
third.metric("Countries", f"{countries:,}")
fourth.metric("Disclosing compute", f"{100 * disclosed / total:.0f}%")

st.divider()

# --- panels, uncommented as each owner pushes their module ------------------
# from src.panel1_compute import render as panel1
# from src.panel2_participation import render as panel2
# from src.panel3_sector import render as panel3
from src.panel4_disclosure import render as panel4

# panel1(models)
# st.divider()
# panel2(models)
# st.divider()
# panel3(models)
# st.divider()
panel4(models)

st.info("Panels 1 to 3 are still being added. See README.md for who owns what.")

st.divider()

st.subheader("What the answer depends on")
st.write(
    "Counted by the number of notable models released each year, the field is "
    "opening up. Counted by the share of training compute behind them, it is "
    "consolidating. Both counts come from the same file, which is what makes "
    "this question arguable rather than settled."
)

with st.expander("What this app cannot show"):
    st.markdown(
        "**Selection.** Epoch includes a model when it is state of the art, "
        "highly cited, or historically significant. Concentration measured on "
        "a notability-filtered sample is not concentration across the whole "
        "field."
    )
    st.markdown(
        f"**Organisation identity.** The Google, Meta, Microsoft and "
        f"Salesforce name variants are folded onto one parent each. That "
        f"raises measured concentration: unfolded, the data would put OpenAI "
        f"in front on model count. The opposite rule gives a different answer."
    )
    st.markdown(
        f"**Joint credits.** {MULTI_CREDIT_MODELS} of {total:,} models credit "
        f"more than one organisation, and in collaborations the industry "
        f"partner is usually listed first. Compute cannot be divided between "
        f"partners without inventing a split rule, so compute is assigned to "
        f"the lead organisation. This overstates how much the leads hold."
    )
    st.markdown(
        f"**Missing compute.** {total - disclosed:,} of {total:,} models carry "
        f"no training compute figure, so every compute share here is computed "
        f"over the subset that does. Where a figure is present it is often "
        f"Epoch's own estimate from hardware or parameter counts rather than a "
        f"number the developer published."
    )
    st.markdown(
        "**Geography.** Country is where the organisation is headquartered, "
        "not where the training ran."
    )

st.caption(SOURCE_LINE)
