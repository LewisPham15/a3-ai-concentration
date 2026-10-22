"""Panel 4 — how much of the field is still measurable.

The other panels measure concentration using training compute. This one asks
how much of the field that measure can still reach. Each year's models are
split by what is known about their compute: a figure Epoch records as
confident, one it records as likely or speculative, or no figure at all. The
bands make the shrinking measurable fraction visible as an area rather than
leaving the reader to infer it from the space above a line. A second chart
then asks which organisations account for the decline.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.data import SOURCE_LINE
import src.design as dz


BANDS = [
    ("confident", "Figure Epoch records as confident", "#8f2d05"),
    ("likely", "Figure recorded as likely", "#e8590c"),
    ("speculative", "Figure recorded as speculative", "#fb9a4b"),
    ("none", "No figure at all", "rgba(140,140,132,0.22)"),
]
LABEL_COLOUR = "#8f2d05"

# The ranking below looks only at the period in which disclosure fell, so it
# describes current practice rather than averaging it with the years before
# the decline began.
RANKING_SINCE = 2022
BELOW, ABOVE = "#8f2d05", "#fb9a4b"


def disclosure_by_year(models, first_half_only=False):
    """Split each year's models by what is known about their training compute.

    Setting first_half_only keeps models published January to June. Every year
    in the window has then had at least six months for Epoch to work on it, so
    a trend that survives the filter cannot be explained by the most recent
    models simply not having been estimated yet.
    """
    frame = models
    if first_half_only:
        frame = models[models["publication_date"].dt.month <= 6]

    years = sorted(frame["year"].dropna().unique())

    rows = []
    for year in years:
        in_year = frame[frame["year"] == year]
        total = len(in_year)
        if total == 0:
            continue

        has = in_year["has_compute"]
        with_figure = int(has.sum())
        confident = int((has & (in_year["confidence"] == "Confident")).sum())
        likely = int((has & (in_year["confidence"] == "Likely")).sum())
        # Anything else with a figure is pooled here, so no model can fall
        # between the bands if Epoch adds a grade we have not seen.
        speculative = with_figure - confident - likely
        none = total - with_figure

        row = {"year": int(year), "total": total, "confident": confident,
               "likely": likely, "speculative": speculative, "none": none}
        for key in ["confident", "likely", "speculative"]:
            row["share_" + key] = round(100 * row[key] / total, 1)
        # Closing the stack on the last band rather than rounding it
        # independently keeps every year summing to exactly 100.
        row["share_none"] = round(
            100 - row["share_confident"] - row["share_likely"]
            - row["share_speculative"], 1)
        rows.append(row)

    return pd.DataFrame(rows)


def disclosure_by_organisation(models, minimum_models, since=RANKING_SINCE):
    """Share of each organisation's recent models that carry a compute figure.

    Organisations below the model threshold are dropped rather than plotted,
    because a laboratory with two models can only score 0, 50 or 100 per cent
    and would rank above or below the rest on nothing but sample size.
    """
    recent = models[models["year"] >= since]

    grouped = recent.groupby("organisation").agg(
        models=("Model", "size"),
        with_figure=("has_compute", "sum"),
    )
    grouped = grouped[grouped["models"] >= minimum_models].copy()
    grouped["share"] = (100 * grouped["with_figure"] / grouped["models"]).round(1)
    grouped = grouped.sort_values("share").reset_index()

    overall = round(100 * recent["has_compute"].sum() / len(recent), 1)
    return grouped, overall, len(recent)


def render(models):
    st.subheader("How much of the field is still measurable")
    st.caption(
        "Of the models published each year, how many carry a training compute "
        "figure, and how much of that is a disclosure rather than an estimate?"
    )

    left, right = st.columns([2, 3])
    with left:
        measure = st.radio(
            "Plot as",
            ["Share of that year's models", "Number of models"],
            key="panel4_measure",
        )
    with right:
        first_half = st.checkbox(
            "Only models published January to June",
            value=False,
            key="panel4_first_half",
            help="Gives every year in the window at least six months of "
                 "estimation time, so recency of publication cannot explain "
                 "a falling trend on its own.",
        )

    counts = disclosure_by_year(models, first_half_only=first_half)

    scope = "January to June only" if first_half else "all months"
    st.write(f"Showing {measure.lower()}, {scope}.")

    as_share = measure.startswith("Share")
    prefix = "share_" if as_share else ""
    axis_title = ("Percent of models published that year" if as_share
                  else "Models published that year")

    figure = go.Figure()
    for key, label, colour in BANDS:
        field = prefix + key
        if as_share:
            template = "%{y:.1f}%% " + label + "<extra></extra>"
        else:
            template = "%{y:.0f} models, " + label + "<extra></extra>"
        figure.add_trace(go.Scatter(
            x=counts["year"], y=counts[field], name=label,
            mode="lines", stackgroup="disclosure",
            line=dict(width=1.1, color="rgba(255,255,255,0.8)"),
            fillcolor=colour,
            hovertemplate=template,
        ))

    # The confident band is what the argument rests on, so its upper edge
    # carries a value at the first year, the peak and the latest year. These
    # are annotations rather than text marks so they can sit on a backing
    # panel and stay legible over any band beneath them.
    marked_years = [int(counts["year"].iloc[0]),
                    int(counts.loc[counts["share_confident"].idxmax(), "year"]),
                    int(counts["year"].iloc[-1])]
    seen = []
    for year in marked_years:
        if year in seen:
            continue
        seen.append(year)
        row = counts[counts["year"] == year].iloc[0]
        value = row[prefix + "confident"]
        text = f"{value:.0f}%" if as_share else f"{value:.0f}"
        if year == marked_years[-1]:
            anchor, shift = "right", -6
        elif year == marked_years[0]:
            anchor, shift = "left", 6
        else:
            anchor, shift = "center", 0
        figure.add_annotation(
            x=year, y=value, text=text, showarrow=False,
            xanchor=anchor, xshift=shift, yshift=14,
            font=dict(color=LABEL_COLOUR, size=12),
            bgcolor="rgba(255,252,248,0.9)",
            bordercolor="rgba(143,45,5,0.4)", borderwidth=1, borderpad=3,
        )

    figure.update_layout(
        height=420,
        margin=dict(l=10, r=30, t=40, b=10),
        xaxis=dict(title="Year of publication", dtick=1, showgrid=False,
                   showline=True, linecolor="rgba(128,128,128,0.4)"),
        yaxis=dict(title=axis_title, rangemode="tozero",
                   gridcolor="rgba(128,128,128,0.18)", zeroline=False),
        legend=dict(orientation="h", y=1.14, x=0, traceorder="normal"),
        hovermode="x unified",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
    )
    st.plotly_chart(figure, width="stretch")

    peak = counts.loc[counts["share_confident"].idxmax()]
    latest = counts.iloc[-1]
    st.caption(
        f"The confident band was widest in {int(peak['year'])}, covering "
        f"{peak['share_confident']:.0f}% of that year's models. By "
        f"{int(latest['year'])} it had fallen to "
        f"{latest['share_confident']:.0f}%, or {int(latest['confident'])} "
        f"models out of {int(latest['total'])}. The grey band is what nobody "
        f"has a figure for: {latest['share_none']:.0f}% of the most recent "
        f"year."
    )

    with st.expander("How to read this, and what it cannot settle"):
        first = counts.iloc[0]
        st.markdown(
            f"**Why a share rather than a count.** The number of models "
            f"published each year has grown, from {int(first['total'])} in "
            f"{int(first['year'])} to {int(latest['total'])} in "
            f"{int(latest['year'])}. A count of models without a figure would "
            f"therefore rise even if laboratories had not changed their "
            f"behaviour. Switching the control to *Number of models* shows "
            f"the difference: measured in counts the confident band peaks "
            f"later and holds up longer, because the denominator is growing "
            f"underneath it. Only the share separates a change in disclosure "
            f"practice from a change in publication volume."
        )
        st.markdown(
            "**What the confidence grade means.** The grade is Epoch's "
            "assessment of the figure it recorded, not the laboratory's. "
            "*Likely* or *Speculative* ordinarily marks a figure derived from "
            "hardware counts or from parameter and token arithmetic. Treating "
            "those as equivalent to a published number would overstate how "
            "much of the field is observed, which is why they are banded "
            "separately here rather than pooled."
        )
        st.markdown(
            "**An explanation this panel cannot rule out.** Epoch estimates "
            "compute itself where a developer has not published it, and that "
            "work takes time, so recent models may lack a figure because "
            "nobody has produced one yet rather than because the developer "
            "withheld it. The January to June control is a partial test: it "
            "restricts every year to models that have had at least six months "
            "of estimation time. A decline that survives the filter is harder "
            "to attribute to processing lag, though it does not eliminate the "
            "possibility, since older models have had years rather than "
            "months."
        )

    st.markdown("###### Which organisations stopped publishing")
    st.caption(
        f"Share of each organisation's models since {RANKING_SINCE} that "
        f"carry a training compute figure, at any confidence grade."
    )

    threshold = st.slider(
        "Minimum models published since " + str(RANKING_SINCE),
        min_value=4, max_value=20, value=10, step=1,
        key="panel4_min_models",
        help="Raising the threshold removes laboratories whose share rests "
             "on a handful of models.",
    )

    ranked, overall, in_period = disclosure_by_organisation(models, threshold)
    st.write(f"{len(ranked)} organisations clear the threshold.")

    if ranked.empty:
        st.info("No organisation published that many models in the period.")
    else:
        colours = []
        for value in ranked["share"]:
            colours.append(BELOW if value < overall else ABOVE)

        labels = []
        for i in ranked.index:
            labels.append(f"{ranked.loc[i, 'share']:.0f}%  "
                          f"({int(ranked.loc[i, 'with_figure'])}"
                          f"/{int(ranked.loc[i, 'models'])})")

        bars = go.Figure(go.Bar(
            x=ranked["share"], y=ranked["organisation"], orientation="h",
            marker_color=colours, text=labels, textposition="outside",
            cliponaxis=False,
            textfont=dict(size=11),
            customdata=ranked["models"],
            hovertemplate="%{y}: %{x:.1f}% of %{customdata} models"
                          "<extra></extra>",
        ))
        bars.add_vline(
            x=overall, line_dash="dash", line_color="#5a5a52", line_width=1.2,
            annotation_text=f"all organisations, {overall:.0f}%",
            annotation_position="top", annotation_font_size=11,
        )
        bars.update_layout(
            height=max(320, 26 * len(ranked)),
            margin=dict(l=10, r=120, t=46, b=10),
            xaxis=dict(title="Percent of that organisation's models with a "
                             "compute figure",
                       range=[0, 118], showgrid=True,
                       gridcolor="rgba(128,128,128,0.18)"),
            yaxis=dict(title=None),
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(size=13),
        )
        st.plotly_chart(bars, width="stretch")

        lowest = ranked.iloc[0]
        st.caption(
            f"Darker bars fall below the {overall:.0f}% average across all "
            f"{in_period:,} models published since {RANKING_SINCE}. The "
            f"lowest is {lowest['organisation']} at "
            f"{lowest['share']:.0f}%, {int(lowest['with_figure'])} of "
            f"{int(lowest['models'])} models. A laboratory can sit low here "
            f"either by withholding figures or by publishing models Epoch has "
            f"not yet estimated; the two cannot be separated from this column "
            f"alone."
        )

        # The ranking does not sort by size or by country, so the question is
        # what it does sort by. Model access turns out to track it closely.
        recent = models[models["year"] >= RANKING_SINCE].copy()
        recent["access"] = recent["Open model weights?"].fillna("Not stated")
        by_access = recent.groupby("access")["has_compute"].agg(["size", "sum"])
        if "Yes" in by_access.index and "No" in by_access.index:
            open_share = (100 * by_access.loc["Yes", "sum"]
                          / by_access.loc["Yes", "size"])
            closed_share = (100 * by_access.loc["No", "sum"]
                            / by_access.loc["No", "size"])
            st.caption(
                f"The order tracks how a model is released more closely than "
                f"it tracks size or country. Since {RANKING_SINCE}, models "
                f"published with open weights carry a compute figure "
                f"{open_share:.0f}% of the time "
                f"({int(by_access.loc['Yes', 'sum'])} of "
                f"{int(by_access.loc['Yes', 'size'])}); models that are not "
                f"released that way, {closed_share:.0f}% "
                f"({int(by_access.loc['No', 'sum'])} of "
                f"{int(by_access.loc['No', 'size'])}). The gap in the chart "
                f"above is therefore not spread evenly across the field. It "
                f"sits with the laboratories that sell access to a model "
                f"rather than publish it, which is the part of the field a "
                f"competition regulator has least visibility into."
            )

    st.caption(SOURCE_LINE)
