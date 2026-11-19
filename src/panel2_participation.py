"""Panel 2: Participation breadth among notable AI model developers."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src.data import SOURCE_LINE, exploded_organisations
import src.design as dz


def render(models):
    st.subheader("Panel 2 · Who is in the game, and from where?")
    st.caption("Are more distinct organisations and countries participating in notable AI model development?")

    years = sorted(int(y) for y in models["year"].dropna().unique())
    selected = st.slider("Publication years", min_value=years[0], max_value=years[-1],
                         value=(years[0], years[-1]), key="panel2_years")
    year_axis = list(range(selected[0], selected[1] + 1))

    # Shared alias and multi-credit rules: count every credited partner.
    credits = exploded_organisations(models)
    credits = credits[credits["year"].between(*selected)]
    org_counts = (credits.groupby("year")["organisation"].nunique()
                  .reindex(year_axis, fill_value=0))

    # Country is a comma-separated list for collaborative models. Count each
    # listed country, once per year, without inventing a country-to-partner map.
    selected_models = models[models["year"].between(*selected)].copy()
    country_rows = selected_models[["year", "country"]].copy()
    country_rows["country"] = country_rows["country"].astype(str).str.split(",")
    country_rows = country_rows.explode("country")
    country_rows["country"] = country_rows["country"].str.strip()
    country_rows = country_rows[~country_rows["country"].isin(["", "Not stated", "nan"])]
    country_counts = (country_rows.groupby("year")["country"].nunique()
                      .reindex(year_axis, fill_value=0))

    left, right = st.columns(2)
    left.metric("Distinct credited organisations (selected years)",
                f"{credits['organisation'].nunique():,}")
    right.metric("Countries represented (selected years)",
                 f"{country_rows['country'].nunique():,}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=year_axis, y=org_counts.values, mode="lines+markers",
                             name="Organisations", line=dict(color=dz.PALETTE[0], width=3),
                             hovertemplate="%{x}: %{y} organisations<extra></extra>"))
    fig.update_layout(title="Distinct organisations credited each year",
                      xaxis_title="Publication year", yaxis_title="Unique organisations",
                      yaxis=dict(rangemode="tozero"), xaxis=dict(dtick=1),
                      margin=dict(l=20,r=20,t=55,b=20), height=350)
    st.plotly_chart(fig, use_container_width=True)

    bar = go.Figure(go.Bar(x=year_axis, y=country_counts.values,
                           marker_color=dz.PALETTE[1],
                           hovertemplate="%{x}: %{y} countries<extra></extra>"))
    bar.update_layout(title="Distinct countries represented each year",
                      xaxis_title="Publication year", yaxis_title="Unique countries",
                      yaxis=dict(rangemode="tozero"), xaxis=dict(dtick=1),
                      margin=dict(l=20,r=20,t=55,b=20), height=350)
    st.plotly_chart(bar, use_container_width=True)

    with st.expander("Check the underlying yearly counts"):
        table = pd.DataFrame({"Year": year_axis,
                              "Unique organisations": org_counts.values,
                              "Unique countries": country_counts.values})
        st.dataframe(table, hide_index=True, use_container_width=True)
        st.caption("Organisations count all credited collaborators, after the shared alias folding. "
                   "Countries are split from Epoch's country field and deduplicated by year. "
                   "Country means organisation headquarters, not model-training location.")

    st.caption("Reading the charts: the line counts organisations; the bars count countries. "
               "These are two different chart families, and neither chart measures compute share.")
    st.caption("Interpretation: More participating organisations does not necessarily mean "
               "training compute is less concentrated. Epoch includes only notable models, "
               "and its latest year may be incomplete.")
    st.caption(SOURCE_LINE)
