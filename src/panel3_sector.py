"""
Panel 3: Academia versus industry
Sub-question: Who is building these models, and how has that shifted over time?

Owner: Eva

This panel has two charts:
  Chart 3A - 100% stacked column: share of notable models by developer type, per year
             (Visual Vocabulary family: PART-TO-WHOLE)
  Chart 3B - Horizontal bar: top 10 organisations by number of notable models
             (Visual Vocabulary family: RANKING)

How it plugs into the app:
  app.py calls  render(models)  with the shared table from src/data.py.
  Group rules followed: data comes from data.py (start year, organisation
  aliases), colours come from design.py, widget keys start with "panel3_".

How to make the processed CSV files (for the data package):
  python -m src.panel3_sector
  -> writes data/processed/panel3_sector_share.csv
  -> writes data/processed/panel3_top_orgs.csv
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data import SOURCE_LINE, START_YEAR, canonical
import src.design as dz

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
DATE_COL = "Publication date"
CATEGORY_COL = "Organization categorization"
ORG_COL = "Organization"      # full credit list; names folded with data.canonical()

# Shared Okabe-Ito palette from design.py (colour-blind safe)
SECTOR_COLOURS = {
    "Industry": dz.PALETTE[0],                         # blue
    "Academia": dz.PALETTE[1],                         # orange
    "Industry–academia collaboration": dz.PALETTE[2],  # green
    "Other": dz.REST,                                  # grey
}
SECTOR_ORDER = list(SECTOR_COLOURS.keys())


# ---------------------------------------------------------------------------
# Step 1: the grouping rule (write this rule in the data dictionary too)
# ---------------------------------------------------------------------------
def sector_group(value):
    """Turn the raw 'Organization categorization' text into one of 4 groups.

    Rule:
      only Industry                    -> Industry
      only Academia                    -> Academia
      both Industry and Academia       -> Industry–academia collaboration
      anything else, or blank          -> Other
    """
    if pd.isna(value) or str(value).strip() == "":
        return "Other"
    parts = {p.strip() for p in str(value).split(",") if p.strip()}
    if "Industry" in parts and "Academia" in parts:
        return "Industry–academia collaboration"
    if parts == {"Industry"}:
        return "Industry"
    if parts == {"Academia"}:
        return "Academia"
    return "Other"


def prepare(df):
    """Add a 'year' and 'sector' column, keep START_YEAR onwards.

    data.load_models() already adds 'year' and applies the start year;
    this repeats it only so the file also works on the raw CSV.
    """
    out = df.copy()
    if "year" not in out.columns:
        out["year"] = pd.to_datetime(out[DATE_COL], errors="coerce").dt.year
    out = out.dropna(subset=["year"])
    out["year"] = out["year"].astype(int)
    out = out[out["year"] >= START_YEAR]
    out["sector"] = out[CATEGORY_COL].apply(sector_group)
    return out


# ---------------------------------------------------------------------------
# Step 2: the two summary tables (these become the processed CSV files)
# ---------------------------------------------------------------------------
def sector_share_table(prepared):
    """Chart 3A table: one row per year per sector, with count and % share."""
    counts = (prepared.groupby(["year", "sector"]).size()
              .reset_index(name="models"))
    totals = prepared.groupby("year").size().rename("year_total")
    counts = counts.join(totals, on="year")
    counts["share_pct"] = (counts["models"] / counts["year_total"] * 100).round(1)
    return counts.sort_values(["year", "sector"]).reset_index(drop=True)


def top_orgs_table(prepared, n=10):
    """Chart 3B table: top n organisations by number of notable models.

    A model built by several organisations counts once for each of them.
    Each organisation is coloured by the sector most of its models fall in.
    """
    rows = prepared[[ORG_COL, "sector"]].dropna(subset=[ORG_COL]).copy()
    rows["model_id"] = rows.index
    rows["org"] = rows[ORG_COL].astype(str).str.split(",")
    rows = rows.explode("org")
    rows["org"] = rows["org"].map(canonical)
    rows = rows[rows["org"] != ""]
    # e.g. "Google,Google Brain" becomes Google twice: count that model once
    rows = rows.drop_duplicates(subset=["model_id", "org"])

    counts = rows.groupby("org").size().rename("models")
    main_sector = rows.groupby("org")["sector"].agg(lambda s: s.mode().iloc[0])
    table = pd.concat([counts, main_sector.rename("main_sector")], axis=1)
    table = table.reset_index().sort_values(["models", "org"], ascending=[False, True])
    return table.head(n).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Step 3: draw the panel in the app
# ---------------------------------------------------------------------------
def sector_share_in(prepared, year, sector):
    """% of one year's notable models that fall in one sector."""
    year_rows = prepared[prepared["year"] == year]
    if year_rows.empty:
        return None
    return round((year_rows["sector"] == sector).mean() * 100, 1)


KPI_CSS = """
<style>
.p3-kpis {display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 12px; margin: 4px 0 6px 0;}
.p3-card {border: 1px solid rgba(128,128,128,0.35); border-radius: 10px;
          padding: 12px 14px; height: 118px; box-sizing: border-box;
          display: flex; flex-direction: column; justify-content: space-between;
          overflow: hidden;}
.p3-label {font-size: 0.85rem; opacity: 0.75; line-height: 1.2;}
.p3-value {font-size: 1.45rem; font-weight: 600; line-height: 1.15;
           overflow-wrap: anywhere;}
.p3-sub {font-size: 0.78rem; opacity: 0.7; line-height: 1.2;}
@media (max-width: 900px) {.p3-kpis {grid-template-columns: repeat(2, minmax(0, 1fr));}}
</style>
"""


def render_cards(cards):
    """Draw equal-sized cards: (label, value, small line underneath)."""
    from html import escape
    items = "".join(
        f'<div class="p3-card"><div class="p3-label">{escape(label)}</div>'
        f'<div class="p3-value">{escape(value)}</div>'
        f'<div class="p3-sub">{escape(sub)}</div></div>'
        for label, value, sub in cards
    )
    st.markdown(KPI_CSS + f'<div class="p3-kpis">{items}</div>', unsafe_allow_html=True)


def render_kpis(in_years, year_range, max_year):
    """Four small cards summarising the selected years.

    Uses every developer type (the tick-box filter doesn't change these),
    so the shares always describe all notable models in those years.
    """
    if in_years.empty:
        st.info("No models in the selected years, so there's nothing to summarise.")
        return

    first, last = year_range
    last_label = f"{last}*" if last == max_year else str(last)
    ind_first = sector_share_in(in_years, first, "Industry")
    ind_last = sector_share_in(in_years, last, "Industry")
    aca_first = sector_share_in(in_years, first, "Academia")
    aca_last = sector_share_in(in_years, last, "Academia")

    def change(a, b):
        if a is None or b is None or first == last:
            return "No earlier year selected"
        arrow = "↑" if b > a else ("↓" if b < a else "→")
        return f"{arrow} {b - a:+.1f} pts since {first}"

    def pct(v):
        return "–" if v is None else f"{v:.1f}%"

    top = top_orgs_table(in_years, n=1)
    top_org = top["org"].iloc[0] if not top.empty else "None"
    top_share = (top["models"].iloc[0] / len(in_years) * 100) if not top.empty else 0

    cards = [
        ("Notable models", f"{len(in_years):,}", f"Released {first}–{last}"),
        (f"Industry share, {last_label}", pct(ind_last), change(ind_first, ind_last)),
        (f"Academia share, {last_label}", pct(aca_last), change(aca_first, aca_last)),
        ("Top organisation", top_org, f"Involved in {top_share:.0f}% of models"),
    ]
    render_cards(cards)

    note = (f"Cards cover {first}–{last}. Shares are % of that year's notable models; "
            "'pts' means percentage points.")
    if last == max_year:
        note += f" *{max_year} is a partial year."
    st.caption(note)


def render(df):
    st.subheader("Academia versus industry")
    st.markdown("**Who is building notable AI models, and how has that shifted over time?**")

    prepared = prepare(df)
    if prepared.empty:
        st.info("No models are available to show for this panel.")
        return

    # --- Interaction: year range + sector filter -------------------------
    min_year, max_year = int(prepared["year"].min()), int(prepared["year"].max())
    latest = pd.to_datetime(df[DATE_COL], errors="coerce").max().strftime("%d %b %Y")
    col1, col2 = st.columns(2)
    with col1:
        year_range = st.slider("Years to show", min_year, max_year,
                               (min_year, max_year), key="panel3_years")
    with col2:
        sectors = st.multiselect("Developer types", SECTOR_ORDER,
                                 default=SECTOR_ORDER, key="panel3_sectors")

    in_years = prepared[prepared["year"].between(*year_range)]

    # ---------------- KPI cards (follow the year slider) -----------------
    render_kpis(in_years, year_range, max_year)

    # ---------------- Chart 3A: 100% stacked column ----------------------
    share = sector_share_table(in_years)
    share = share[share["sector"].isin(sectors)]

    st.subheader(f"Share of notable AI models by developer type, {year_range[0]}–{year_range[1]}")
    if share.empty:
        st.info("No models match these filters. Try widening the year range "
                "or selecting more developer types.")
    else:
        fig = px.bar(
            share, x="year", y="share_pct", color="sector",
            category_orders={"sector": SECTOR_ORDER},
            color_discrete_map=SECTOR_COLOURS,
            text=share["share_pct"].map(lambda v: f"{v:.0f}%" if v >= 8 else ""),
            labels={"year": "Year of release",
                    "share_pct": "Share of that year's notable models (%)",
                    "sector": "Developer type"},
        )
        fig.update_traces(textposition="inside", insidetextanchor="middle")
        fig.update_layout(barmode="stack", yaxis_range=[0, 112],
                          xaxis=dict(dtick=1), legend_title_text="Developer type",
                          height=450, margin=dict(t=30))
        # Total number of models above each column (n = baseline)
        totals = share.groupby("year")["year_total"].first()
        for year, n in totals.items():
            fig.add_annotation(x=year, y=104, text=f"n={n}", showarrow=False,
                               font=dict(size=11))
        st.plotly_chart(fig, width="stretch")

        # Every value as a small table, so small segments are readable without hovering
        table = (share.pivot(index="sector", columns="year", values="share_pct")
                 .reindex([s for s in SECTOR_ORDER if s in sectors]).fillna(0))
        table.loc["Number of models (n)"] = share.groupby("year")["year_total"].first()
        table.columns = [str(c) for c in table.columns]
        table.index.name = "Share of models (%)"
        st.dataframe(table.style.format(lambda v: f"{v:.0f}" if v == int(v) else f"{v:.1f}"),
                     width="stretch")

        st.caption(
            f"{max_year} is a partial year (latest model in the data: {latest}). "
            "Each column is 100% of the notable models released that year; "
            "n above each column is the number of models that year. "
            "Developer type comes from Epoch AI's 'Organization categorization'. "
            "Models listing both industry and academia count as a collaboration. "
            "If some types are unticked, the remaining shares add up to less than 100%."
        )

    # ---------------- Chart 3B: ranked horizontal bar --------------------
    top = top_orgs_table(in_years[in_years["sector"].isin(sectors)])

    st.subheader(f"Top 10 organisations by number of notable models, {year_range[0]}–{year_range[1]}")
    if top.empty:
        st.info("No organisations match these filters. Try widening the year range "
                "or selecting more developer types.")
    else:
        fig2 = px.bar(
            top, x="models", y="org", orientation="h", color="main_sector",
            category_orders={"org": top["org"].tolist(), "main_sector": SECTOR_ORDER},
            color_discrete_map=SECTOR_COLOURS, text="models",
            labels={"models": "Number of notable models",
                    "org": "Organisation", "main_sector": "Main developer type"},
        )
        fig2.update_traces(textposition="outside")
        fig2.update_layout(height=420, margin=dict(t=30),
                           xaxis_range=[0, top["models"].max() * 1.15])
        st.plotly_chart(fig2, width="stretch")
        st.caption(
            "Count of notable models per organisation in the selected years. "
            "A model built by several organisations counts once for each. "
            "Name variants are merged using the group's rule in data.py "
            "(e.g. Google includes DeepMind, Google Brain and Google Research). "
            "Colour shows the developer type most of that organisation's models fall in."
        )

    st.markdown(
        "**What this panel can't show:** it shows *what kind* of organisation builds "
        "notable models, not *how many* organisations there are (see Panel 2), and "
        "Epoch AI's list is not a complete record of every model released."
    )
    st.caption(SOURCE_LINE)


# ---------------------------------------------------------------------------
# Run this file directly to write the processed CSVs
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Run from the repo folder:  python -m src.panel3_sector
    from src.data import DATA, SNAPSHOT, load_models

    out_dir = DATA / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)

    prepared = prepare(load_models())
    sector_share_table(prepared).to_csv(out_dir / "panel3_sector_share.csv", index=False)
    top_orgs_table(prepared).to_csv(out_dir / "panel3_top_orgs.csv", index=False)
    print(f"Wrote panel3 tables from {SNAPSHOT.name} to {out_dir}")
