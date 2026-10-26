"""Panel 1 — share of training compute.

The question is whether leading model development is concentrating in fewer
organisations. Counting models answers it one way and this panel weighs each
model by the training compute behind it, which is the measure a competition
analyst would want, since compute is the scarce input.

Two charts.
The first stacks each year's disclosed compute by lead organisation,
so the reader can see how much a named handful holds and who that handful is.
The second turns the same shares into the Herfindahl-Hirschman index,
the screen the ACCC uses for market concentration, and draws it twice:
once weighted by compute and once giving every model one vote.
The gap between the two lines is the disagreement that makes the group's
question arguable.

Every figure here is a share of the compute Epoch has a figure for, because
compute cannot be shared out among models that do not disclose it. Panel 4
measures how large that gap is.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.data import SOURCE_LINE
import src.design as dz


OTHER = "All other organisations"

# The ACCC's Merger Assessment Guidelines (June 2025, paragraph 1.24) treat
# a market with an HHI above 2,000 as highly concentrated, giving five firms
# of 20 percent each as the example. It is drawn as a reference, not a
# verdict: the index here is computed over a notability-filtered sample of
# models, not over a defined market.
ACCC_HHI_LINE = 2000

# A bar segment is hatched when more than half of its compute rests
# on figures Epoch grades speculative, following the shared rule that
# estimated numbers are drawn differently from reported ones.
SPECULATIVE_HATCH_THRESHOLD = 0.5

# Segments at least this wide carry the organisation's name inside them,
# so the chart can be read without the legend or with colour removed.
LABEL_MIN_SHARE = 15

COMPUTE_COLOUR = dz.PALETTE[0]
COUNT_COLOUR = dz.PALETTE[1]


def compute_shares_by_year(models):
    """One row per organisation per year: its share of that year's compute.

    Only models with a training compute figure take part,
    and the share is of the total those models add up to.
    Each row also carries the number of models behind the slice,
    the largest of them, and how much of the slice rests on figures
    Epoch grades speculative.
    """
    disclosed = models[models["has_compute"]]

    rows = []
    for year, in_year in disclosed.groupby("year"):
        year_total = in_year["compute_flop"].sum()
        for organisation, slice_ in in_year.groupby("organisation"):
            flop = slice_["compute_flop"].sum()
            largest = slice_.loc[slice_["compute_flop"].idxmax()]
            speculative = slice_.loc[slice_["confidence"] == "Speculative",
                                     "compute_flop"].sum()
            rows.append({
                "year": int(year),
                "organisation": organisation,
                "flop": flop,
                "share": 100 * flop / year_total,
                "models": len(slice_),
                "largest_model": largest["Model"],
                "largest_share_of_slice": largest["compute_flop"] / flop,
                "speculative_share": speculative / flop,
            })
    return pd.DataFrame(rows)


def rank_organisations(shares):
    """Organisations ordered by their mean share across the years shown.

    Ranking on total compute would hand the whole list to the last two years,
    because compute grows by orders of magnitude and the latest runs dwarf
    everything before them.
    Averaging the annual shares gives every year an equal say,
    so an organisation that led in 2019 counts as much as one that led in 2025.
    """
    table = shares.pivot_table(index="organisation", columns="year",
                               values="share", aggfunc="sum", fill_value=0)
    return table.mean(axis=1).sort_values(ascending=False)


def concentration_by_year(models, exclude_speculative=False):
    """The Herfindahl-Hirschman index of each year's compute, two ways.

    HHI is the sum of squared percentage shares: 10,000 if one organisation
    holds everything, close to 0 if many hold a little. It is computed twice
    on the same set of models, once with each model weighted by its compute
    and once with each model counting as one, so the only thing that differs
    between the two lines is the weighting.
    The equivalent number of equal-sized organisations,
    10,000 / HHI, is carried along as a plainer reading of the same number.
    """
    frame = models[models["has_compute"]]
    if exclude_speculative:
        frame = frame[frame["confidence"] != "Speculative"]

    rows = []
    for year, in_year in frame.groupby("year"):
        by_org = in_year.groupby("organisation")["compute_flop"].agg(
            ["sum", "size"])
        compute_share = 100 * by_org["sum"] / by_org["sum"].sum()
        count_share = 100 * by_org["size"] / by_org["size"].sum()
        hhi_compute = (compute_share ** 2).sum()
        hhi_count = (count_share ** 2).sum()
        rows.append({
            "year": int(year),
            "models": len(in_year),
            "organisations": len(by_org),
            "hhi_compute": round(hhi_compute),
            "hhi_count": round(hhi_count),
            "equivalent_compute": round(10000 / hhi_compute, 1),
            "equivalent_count": round(10000 / hhi_count, 1),
            "top4_compute": round(compute_share.nlargest(4).sum(), 1),
            "top4_count": round(count_share.nlargest(4).sum(), 1),
        })
    return pd.DataFrame(rows)


def _share_chart(shares, named, years, published, per_year):
    """Stacked bars: each year's disclosed compute by lead organisation.

    An organisation with no compute figure in a year is drawn as nothing,
    which looks the same as a zero share. The hover text separates the two:
    it reports how many models the organisation published that year
    without a figure, so an empty bar reads as missing rather than as absent.
    """
    figure = go.Figure()

    for i, organisation in enumerate(named):
        own = shares[shares["organisation"] == organisation].set_index("year")
        values, labels, hover, hatch = [], [], [], []
        for year in years:
            count = int(published.get((year, organisation), 0))
            if year in own.index:
                row = own.loc[year]
                values.append(row["share"])
                labels.append(organisation if row["share"] >= LABEL_MIN_SHARE
                              else "")
                text = (f"<b>{organisation}</b>: {row['share']:.0f}% of the "
                        f"year's disclosed compute<br>{int(row['models'])} of "
                        f"its {count} models carry a figure; largest "
                        f"{row['largest_model']}")
                if row["speculative_share"] > SPECULATIVE_HATCH_THRESHOLD:
                    text += (f"<br><i>{100 * row['speculative_share']:.0f}% "
                             f"of this rests on speculative figures</i>")
                    hatch.append("/")
                else:
                    hatch.append("")
            else:
                values.append(0)
                labels.append("")
                hatch.append("")
                if count:
                    text = (f"<b>{organisation}</b>: no compute figure for "
                            f"any of its {count} models this year")
                else:
                    text = f"<b>{organisation}</b>: no notable model this year"
            hover.append(text)
        figure.add_trace(go.Bar(
            x=years, y=values, name=organisation,
            text=labels, textposition="inside", insidetextanchor="middle",
            textangle=0, textfont=dict(color="white", size=11),
            marker=dict(
                color=dz.hue(i),
                pattern=dict(shape=hatch, fillmode="overlay",
                             fgcolor="rgba(255,255,255,0.65)", solidity=0.3),
            ),
            customdata=hover,
            hovertemplate="%{customdata}<extra></extra>",
        ))

    rest = shares[~shares["organisation"].isin(named)]
    pooled = rest.groupby("year").agg(share=("share", "sum"),
                                      organisations=("organisation", "size"),
                                      models=("models", "sum"))
    pooled = pooled.reindex(years).fillna(0)
    figure.add_trace(go.Bar(
        x=years, y=pooled["share"], name=OTHER,
        marker_color=dz.REST,
        customdata=pooled[["organisations", "models"]].astype(int),
        hovertemplate=(
            f"<b>{OTHER}</b>: %{{y:.0f}}% of the year's disclosed compute"
            "<br>%{customdata[0]} organisations, %{customdata[1]} models"
            "<extra></extra>"
        ),
    ))

    # The number this panel asks for sits above each bar:
    # how much of that year's compute the named handful holds between them.
    named_share = (shares[shares["organisation"].isin(named)]
                   .groupby("year")["share"].sum().reindex(years).fillna(0))
    for year in years:
        figure.add_annotation(
            x=year, y=100, text=f"{named_share[year]:.0f}%",
            showarrow=False, yshift=12,
            font=dict(size=12, color=dz.INK),
        )

    # Each bar's denominator sits under its year, so the reader can see how
    # many models the share is a share of and how many are left out.
    ticktext = []
    for year in years:
        row = per_year.loc[year]
        ticktext.append(
            f"{year}<br><span style='font-size:10px;color:{dz.FAINT}'>"
            f"{int(row['with_figure'])} of {int(row['total'])} models</span>")

    figure.update_layout(
        barmode="stack",
        height=460,
        margin=dict(l=70, r=20, t=50, b=70),
        xaxis=dict(title="Year of publication, and models with a compute "
                         "figure out of all models published",
                   tickmode="array", tickvals=years, ticktext=ticktext,
                   showgrid=False, showline=True,
                   linecolor="rgba(128,128,128,0.4)"),
        yaxis=dict(title="Share of that year's disclosed compute",
                   range=[0, 110], dtick=25, ticksuffix="%",
                   gridcolor="rgba(128,128,128,0.18)", zeroline=False),
        legend=dict(orientation="h", y=1.14, x=0, traceorder="normal"),
        hovermode="x unified",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
    )
    return figure, named_share


def _hhi_chart(index):
    """Two lines of the same index: compute-weighted and one-model-one-vote."""
    figure = go.Figure()

    for field, equivalent, label, colour in [
        ("hhi_compute", "equivalent_compute",
         "Weighted by training compute", COMPUTE_COLOUR),
        ("hhi_count", "equivalent_count",
         "One model, one vote", COUNT_COLOUR),
    ]:
        figure.add_trace(go.Scatter(
            x=index["year"], y=index[field], name=label,
            mode="lines+markers",
            line=dict(color=colour, width=2.4, dash=dz.SOLID),
            marker=dict(size=7),
            customdata=index[[equivalent, "models", "organisations"]],
            hovertemplate=(
                f"{label}: HHI %{{y:,.0f}}, like %{{customdata[0]}} "
                "equal-sized organisations"
                + ("<br>%{customdata[1]} models from %{customdata[2]} "
                   "organisations" if field == "hhi_compute" else "")
                + "<extra></extra>"
            ),
        ))

    figure.add_hline(
        y=ACCC_HHI_LINE, line_dash="dash", line_color="#5a5a52",
        line_width=1.2,
        annotation_text=f"{ACCC_HHI_LINE:,}: above this the ACCC's 2025 "
                        f"merger guidelines call a market highly concentrated",
        annotation_position="top left", annotation_font_size=11,
    )

    # The last value of each line is labelled so the current gap can be read
    # without hovering.
    latest = index.iloc[-1]
    for field, colour in [("hhi_compute", COMPUTE_COLOUR),
                          ("hhi_count", COUNT_COLOUR)]:
        figure.add_annotation(
            x=latest["year"], y=latest[field],
            text=f"{latest[field]:,.0f}", showarrow=False,
            xanchor="left", xshift=10,
            font=dict(size=12, color=colour),
            bgcolor="rgba(255,255,255,0.85)", borderpad=2,
        )

    figure.update_layout(
        height=400,
        margin=dict(l=70, r=70, t=40, b=60),
        xaxis=dict(title="Year of publication", dtick=1, showgrid=False,
                   showline=True, linecolor="rgba(128,128,128,0.4)"),
        yaxis=dict(title="Herfindahl-Hirschman index (0 to 10,000)",
                   range=[0, 10500], dtick=2000, tickformat=",",
                   gridcolor="rgba(128,128,128,0.18)", zeroline=False),
        legend=dict(orientation="h", y=1.12, x=0),
        hovermode="x unified",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
    )
    return figure


def _join(names):
    """'A, B and C' for a list of names."""
    names = list(names)
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


def render(models):
    st.subheader("Who holds the compute")
    st.caption(
        "Of the training compute behind each year's models, how much sits "
        "with a handful of organisations, and is that handful getting smaller?"
    )

    shares = compute_shares_by_year(models)
    years = sorted(shares["year"].unique())
    ranking = rank_organisations(shares)

    handful = st.slider(
        "Organisations to name",
        min_value=3, max_value=8, value=4, step=1,
        key="panel1_handful",
        help="The organisations with the highest average annual share "
             "of disclosed compute across the years shown. "
             "Everyone else is pooled into the grey segment.",
    )
    named = list(ranking.index[:handful])

    disclosed = int(models["has_compute"].sum())
    st.write(
        f"Naming {_join(named)}. Shares are of the compute behind the "
        f"{disclosed:,} models that carry a figure; hatched segments rest "
        f"mainly on figures Epoch grades speculative."
    )

    published = models.groupby(["year", "organisation"]).size()
    per_year = models.groupby("year").agg(total=("Model", "size"),
                                          with_figure=("has_compute", "sum"))
    figure, named_share = _share_chart(shares, named, years, published,
                                       per_year)
    st.plotly_chart(figure, width="stretch")

    # Everything in the captions is computed, so it stays true if the snapshot
    # or the slider changes. Observation and interpretation are kept in
    # separate sentences.
    leaders = (shares.sort_values("share", ascending=False)
               .drop_duplicates("year").set_index("year")["organisation"])
    led = leaders.value_counts()
    led_items = list(led.items())
    led_text = (f"{led_items[0][0]} had the largest share in "
                f"{led_items[0][1]} of the {len(years)} years, "
                + _join(f"{org} in {n}" for org, n in led_items[1:]))
    lowest_year = int(named_share.idxmin())
    latest_year = int(years[-1])
    largest_run = (shares.assign(
        run=shares["share"] * shares["largest_share_of_slice"])
        .groupby("year")["run"].max())
    st.caption(
        f"**The chart shows.** The {handful} named organisations hold "
        f"{named_share[latest_year]:.0f}% of {latest_year}'s disclosed "
        f"compute, and never less than {named_share[lowest_year]:.0f}% "
        f"({lowest_year}) across the {len(years)} years. {led_text}. The "
        f"largest single run is {largest_run.mean():.0f}% of a year's "
        f"compute on average and {largest_run.max():.0f}% in "
        f"{int(largest_run.idxmax())}."
    )

    # The named organisation-year with the most models and no figure at all
    # is the clearest case of missing being drawn as zero.
    gaps = []
    for organisation in named:
        for year in years:
            count = int(published.get((year, organisation), 0))
            has_slice = ((shares["organisation"] == organisation)
                         & (shares["year"] == year)).any()
            if count and not has_slice:
                gaps.append((count, organisation, year))
    gap_text = ""
    if gaps:
        count, organisation, year = max(gaps)
        gap_text = (f" {organisation} published {count} notable models in "
                    f"{year} and has no segment in that bar.")
    st.caption(
        f"**This suggests.** Each year's shares are decided by a few very "
        f"large runs rather than many medium ones, so one disclosure can move "
        f"a bar a long way. An organisation with no segment in a year has no "
        f"compute figure that year, not no models.{gap_text}"
    )

    with st.expander("How to read this, and what it cannot settle"):
        st.markdown(
            "**Why a share of the year rather than FLOP.** Total disclosed "
            "compute grew by orders of magnitude over the window, so the "
            "absolute figures would show nothing but the most recent year. A "
            "share asks the question the regulator asks: of what was spent "
            "that year, how much did a few organisations spend?"
        )
        st.markdown(
            "**Why these organisations are named.** The slider picks the "
            "organisations with the highest *average annual* share. Ranking "
            "on total compute instead would hand the whole list to the two "
            "latest years, because the newest runs dwarf everything before "
            "them. The fixed list means a year's leader is not always among "
            "the named, which is why the number above a bar can be lower "
            "than that year's top-four share in the index below."
        )
        frontier = models[models["is_frontier"]]
        hidden = (frontier[~frontier["has_compute"]]
                  .groupby("year")["organisation"].agg(["size", "unique"]))
        if not hidden.empty:
            worst_year = int(hidden["size"].idxmax())
            worst = hidden.loc[worst_year]
            frontier_that_year = int((frontier["year"] == worst_year).sum())
            st.markdown(
                f"**A year can look more open because the leaders went "
                f"quiet.** Every share is a share of the compute that has a "
                f"figure. When the largest laboratories stop publishing one, "
                f"their runs leave the denominator and the remaining field "
                f"looks more evenly spread than it is. {worst_year} is the "
                f"clearest case: {int(worst['size'])} of its "
                f"{frontier_that_year} frontier models carry no figure, from "
                f"{_join(sorted(worst['unique']))}. Panel 4 measures that "
                f"gap directly."
            )
        st.markdown(
            "**Compute goes to the first-listed organisation.** Where a model "
            "credits several organisations, the whole figure is assigned to "
            "the lead, and in collaborations the industry partner is usually "
            "listed first. That pushes every bar toward the named "
            "organisations and away from the grey segment."
        )
        st.markdown(
            "**What the hatching marks.** A named segment is hatched when "
            "more than half of its compute rests on figures Epoch grades "
            "speculative, which is usually one very large run estimated from "
            "hardware reports rather than disclosed. The grey segment pools "
            "many organisations and is never hatched. The control under the "
            "index below removes speculative figures altogether."
        )
        st.markdown(
            f"**The last bar is a partial year.** {latest_year} runs to the "
            f"snapshot date, and Epoch's own estimates for recent models "
            f"arrive with a lag, so that bar will change as the file is "
            f"updated."
        )

    st.markdown("###### The same shares as a concentration index")
    st.caption(
        "The Herfindahl-Hirschman index of each year's compute, weighted two "
        "ways on the same models. The gap between the lines is the "
        "disagreement at the centre of the question."
    )

    exclude_speculative = st.checkbox(
        "Exclude figures Epoch grades speculative",
        value=False,
        key="panel1_exclude_speculative",
        help="Several of the largest recent runs carry speculative figures. "
             "Removing them tests whether the compute-weighted line depends "
             "on numbers nobody has confirmed.",
    )

    index = concentration_by_year(models, exclude_speculative)
    scope = ("confident and likely figures only" if exclude_speculative
             else "all figures, whatever their grade")
    st.write(f"Computed over {int(index['models'].sum()):,} models, {scope}.")

    st.plotly_chart(_hhi_chart(index), width="stretch")

    above_compute = int((index["hhi_compute"] >= ACCC_HHI_LINE).sum())
    above_count = int((index["hhi_count"] >= ACCC_HHI_LINE).sum())
    latest = index.iloc[-1]
    first = index.iloc[0]
    st.caption(
        f"**The chart shows.** Weighted by compute, the index is above "
        f"{ACCC_HHI_LINE:,} in {above_compute} of {len(index)} years; "
        f"counting models, in {above_count}. In {int(latest['year'])} it is "
        f"{latest['hhi_compute']:,.0f} by compute, like "
        f"{latest['equivalent_compute']} equal-sized organisations, against "
        f"{latest['hhi_count']:,.0f} by count, like "
        f"{latest['equivalent_count']}. It started at "
        f"{first['hhi_compute']:,.0f} in {int(first['year'])} and has no "
        f"steady direction since."
    )
    st.caption(
        "**This suggests.** By this measure the field has been concentrated "
        "for the whole window rather than becoming so, and the answer to the "
        "group's question turns on what each model is weighted by, not on "
        "which years are in view."
    )

    with st.expander("How to read the index, and what it cannot settle"):
        st.markdown(
            "**What the number means.** The index is the sum of each "
            "organisation's squared percentage share: 10,000 if one "
            "organisation held everything, 2,500 if four held a quarter each, "
            "and so on down. Dividing 10,000 by the index gives the number of "
            "equal-sized organisations that would produce the same value, "
            "which is the figure shown on hover."
        )
        st.markdown(
            f"**Why the {ACCC_HHI_LINE:,} line is a reference and not a "
            f"finding.** The ACCC's merger assessment guidelines (June 2025, "
            f"paragraph 1.24) apply that threshold to a defined market with "
            f"measured sales. This index is computed over a sample of "
            f"models Epoch judged notable, assigned to lead organisations, "
            f"using compute as the quantity. It describes the shape of the "
            f"sample; it does not establish a market or market power."
        )
        st.markdown(
            "**Why both lines use the same models.** The one-model-one-vote "
            "line could be computed over every model in the year, but then "
            "the gap between the lines would mix two things: the weighting, "
            "and the fact that disclosed models are a biased subset. Holding "
            "the models fixed means the gap is weighting alone. Panels 2 and "
            "3 count the full set."
        )
        st.markdown(
            "**What the speculative control shows.** Ticking it removes the "
            "runs Epoch is least sure about, several of which are the "
            "largest in their year. If the compute line stays above the "
            "reference after they go, the concentration reading does not "
            "rest on those estimates. If it falls, it partly does."
        )

    st.caption(SOURCE_LINE)


if __name__ == "__main__":
    # Prints the two tables the charts draw, so any number on screen can be
    # traced back to a row here. Run from the repository root:
    #     python -m src.panel1_compute
    from src.data import load_models

    frame = load_models()
    pd.set_option("display.width", 160)
    print("Share of each year's disclosed compute, by lead organisation")
    print(compute_shares_by_year(frame).round(3).to_string(index=False))

    print("\nConcentration index by year")
    print(concentration_by_year(frame).to_string(index=False))