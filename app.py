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
    "**Question.** Counted by the number of notable models released each "
    "year, the field appears to be widening. Counted by the share of training "
    "compute those models represent, it appears to be narrowing. The two "
    "measures are drawn from the same records, and the panels below present "
    "them side by side rather than resolving the tension."
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
# from src.panel4_disclosure import render as panel4
#
# panel1(models)
# st.divider()
# panel2(models)
# st.divider()
# panel3(models)
# st.divider()
# panel4(models)

st.info("Panels are being added. See README.md for who owns what.")

st.divider()

st.subheader("Reading the two measures together")
st.write(
    "Neither measure is incorrect, but they answer different questions. A "
    "regulator assessing barriers to entry is concerned with the compute "
    "figure, since access to frontier-scale training capacity is what a new "
    "entrant must secure. A regulator counting how many firms are active in "
    "the market is better served by the model count. The layout above places "
    "the two adjacent so that neither is read as the finding on its own."
)

with st.expander("Limitations of the underlying data"):
    st.markdown(
        "**Sample selection.** Epoch's inclusion criteria are notability "
        "based: a model enters the dataset by being state of the art, highly "
        "cited, or historically significant. Concentration measured across "
        "this sample therefore describes the set of models already judged "
        "notable, and cannot be read as concentration across all model "
        "development."
    )
    st.markdown(
        "**Organisational boundaries.** Google appears under five separate "
        "strings in the source file, and Meta, Microsoft and Salesforce under "
        "several each. These have been consolidated to parent entities on the "
        "basis that DeepMind has operated within Google since 2014 and merged "
        "with Google Brain in 2023. The choice is consequential: "
        "consolidated, Google leads on model count; left as published, OpenAI "
        "does. An analyst treating subsidiaries as independent competitors "
        "would reach a less concentrated picture."
    )
    st.markdown(
        f"**Attribution of jointly credited models.** {MULTI_CREDIT_MODELS} "
        f"of {total:,} models list more than one organisation. Training "
        f"compute cannot be apportioned between collaborators without "
        f"imposing an arbitrary division, so it is attributed in full to the "
        f"organisation Epoch lists first. Inspection of the collaboration "
        f"records shows the industry partner is ordinarily listed ahead of "
        f"academic partners, which biases the compute measure toward the "
        f"concentration this app sets out to test."
    )
    st.markdown(
        f"**Incomplete disclosure.** Training compute is absent for "
        f"{total - disclosed:,} of {total:,} models, so compute shares are "
        f"calculated over the reporting subset rather than the full sample. "
        f"Where a figure is present it is frequently Epoch's own estimate, "
        f"derived from hardware counts or from parameter and token "
        f"arithmetic, rather than a value disclosed by the developer."
    )
    st.markdown(
        "**Geographic attribution.** Country records the headquarters of the "
        "organisation, not the location of the training run or of the "
        "research staff."
    )

st.caption(SOURCE_LINE)