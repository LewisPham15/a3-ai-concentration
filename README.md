# Is the development of leading AI models concentrating in fewer organisations?

**Question.** Are the most capable AI models coming from a shrinking set of
organisations, or is the field opening up?

**Persona.** A competition policy analyst at the ACCC, deciding whether AI
model development warrants closer competition monitoring.

**User stories.**

- As a competition analyst, I want to see how much of each year's training
  compute sits with a handful of laboratories, so that I can judge whether
  frontier capability is consolidating. *(Panel 1: move the "handful" slider
  to change how many organisations count as the handful.)*
- As a competition analyst, I want to count how many distinct organisations
  and countries publish a notable model each year, so that I can tell a
  widening field from a narrowing one. *(Panel 2: move the year slider to
  change the window.)*
- As a competition analyst, I want to know how much of the field still
  reports its training compute, so that I can tell how far the concentration
  figures can be trusted. *(Panel 4: switch between share and count, and
  raise the minimum-models threshold on the organisation ranking.)*

## Data

Epoch AI, *Notable AI Models*, CC BY 4.0. Snapshot taken 18 October 2026 and
committed as `data/notable_ai_models_2026-10-18.csv`. Epoch updates the live
file roughly weekly, so everyone works from this copy and our figures match.

1,078 rows in the file; 788 published from 2017 onwards.

## Decisions applied in `src/data.py`

**Start year 2017.** Before that there are too few models in a year for a
proportion to carry meaning.

**Organisation aliases.** The Google, Meta, Microsoft and Salesforce name
variants fold onto one parent each. This matters: Google's five strings
(Google, Google DeepMind, DeepMind, Google Research, Google Brain) total 117
models against OpenAI's 76, so the rule reverses the ranking. The app states
it on screen.

**Joint credits.** 230 of the 788 models credit more than one organisation,
and in collaborations the industry partner is usually listed first. Panels
measuring compute use `organisation`, the lead credit, because compute cannot
be split between partners without inventing a split rule. Panels measuring
participation call `exploded_organisations()` and count every partner.


## Panels

| Panel | File | Owner |
|---|---|---|
| 1 · Share of compute | `src/panel1_compute.py` | Tahreema Rahman Zariyat |
| 2 · Who is in the game, and from where | `src/panel2_participation.py` | Mohit Sehrawat |
| 3 · Academia versus industry | `src/panel3_sector.py` | Eva Shrestha |
| 4 · How much is still observable | `src/panel4_disclosure.py` | Ngoc Gia Phong Pham |

Each panel is one function, `render(models)`:

```python
import streamlit as st
import plotly.express as px

from src.data import SOURCE_LINE
import src.design as dz


def render(models):
    st.subheader("Your heading")
    st.caption("The sub-question this panel answers")

    choice = st.selectbox("...", options, key="panelN_choice")
    # build and draw your chart
    st.plotly_chart(fig, width="stretch")

    st.caption(SOURCE_LINE)
```

Three rules so the panels stay consistent. Take your data from `src/data.py`,
never read the CSV yourself. Prefix every widget key with your panel number,
or two panels will collide. Import colours from `src/design.py` rather than
choosing your own, so the palette survives a colour vision deficiency check.

When your panel runs, uncomment its two lines in `app.py`.

## Running it

```
pip install -r requirements.txt
streamlit run app.py
```

The app reads `data/processed/models_clean.csv`. To rebuild it from the
source CSV (for example after changing a rule in `src/data.py`), run:

```
python -m src.build_processed
```

Python 3.11.


## Data and AI disclosure statement

**Data:** The app uses Epoch AI's *Notable AI Models* dataset
(https://epoch.ai/data/ai-models), licensed CC BY 4.0. We downloaded one
snapshot on 18 October 2026 and kept it unchanged in `data/`. How it was
processed is described in `data/DATA_DICTIONARY.md`.

**AI use:** AI tools were used to help understand the assignment steps and review, debug and improve the code. Each use is listed in `AI_PROVENANCE.md`.
