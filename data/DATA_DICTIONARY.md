# Data dictionary

## 1. Raw data: `data/notable_ai_models_2026-10-18.csv`

| Field | Value |
|---|---|
| Source | Epoch AI, Notable AI Models |
| URL | https://epoch.ai/data/ai-models |
| Licence | CC BY 4.0 |
| Primary key | `Model` |
| Time coverage | 1950 to 2026 (1,078 models) |
| Latest observation | 30 September 2026 (snapshot downloaded 18 October 2026) |
| Transform | None. Kept exactly as downloaded |

Columns used by the app (the other 37 are not used; definitions at https://epoch.ai/data/ai-models-documentation):

| Column | Meaning | Units |
|---|---|---|
| `Model` | Model name | Text |
| `Organization` | Organisation(s) that built it, comma-separated | Text |
| `Publication date` | Release date | Date (YYYY-MM-DD) |
| `Organization categorization` | Type of each organisation, e.g. `Industry`, `Academia`, `Industry,Academia` | Text |
| `Country (of organization)` | Organisation's headquarters country | Text |
| `Training compute (FLOP)` | Compute used to train the model | FLOP |
| `Confidence` | Epoch's confidence in the compute figure | `Confident`, `Likely`, `Speculative`, `Unknown` |
| `Frontier model` | Top 5 by compute when released | `True` or blank |
| `Open model weights?` | Weights can be downloaded | `Yes` / `No` |
| `Model accessibility` | How the model is released | Text |

## 2. Processed file the app reads: `data/processed/models_clean.csv`

| Field | Value |
|---|---|
| Source | Raw data (section 1) |
| Primary key | `Model` |
| Time coverage | 2017 to 2026 (788 models; 2026 is a partial year) |
| Latest observation | 30 September 2026 |
| Transform | Made by `clean_models()` in `src/data.py`. Rebuild with `python -m src.build_processed`. Keep models from 2017 onwards. Take the first listed organisation and merge name variants (e.g. DeepMind, Google Brain and Google Research become Google). Convert compute to a number and flag whether it exists. Fill blank sector, country and confidence with `Not stated` |

All 47 source columns are kept, plus these added columns:

| Added column | Meaning | Units |
|---|---|---|
| `year` | Publication year | Year |
| `organisation` | Lead organisation after merging names | Text |
| `compute_flop` | Training compute | FLOP |
| `has_compute` | A compute figure exists | True / False |
| `is_frontier` | Frontier model | True / False |
| `sector`, `country`, `confidence` | Copies of the raw columns with blanks as `Not stated` | Text |

## 3. `data/processed/panel3_sector_share.csv`

| Field | Value |
|---|---|
| Source | Processed file (section 2) |
| Primary key | `year` + `sector` |
| Time coverage | 2017 to 2026 |
| Latest observation | 30 September 2026 |
| Transform | Group each model into Industry, Academia, Industry–academia collaboration (lists both) or Other. Count per year, then divide by that year's total. Rebuild with `python -m src.panel3_sector` |

| Column | Meaning | Units |
|---|---|---|
| `year` | Publication year | Year |
| `sector` | Developer type | Text |
| `models` | Models of that type that year | Count |
| `year_total` | All models that year | Count |
| `share_pct` | `models` ÷ `year_total` × 100 | Percent |

## 4. `data/processed/panel3_top_orgs.csv`

| Field | Value |
|---|---|
| Source | Processed file (section 2) |
| Primary key | `org` |
| Time coverage | 2017 to 2026 combined |
| Latest observation | 30 September 2026 |
| Transform | Split jointly built models so each organisation is credited once, merge name variants, count models per organisation and keep the top 10. Rebuild with `python -m src.panel3_sector` |

| Column | Meaning | Units |
|---|---|---|
| `org` | Organisation | Text |
| `models` | Models the organisation is credited on | Count |
| `main_sector` | Sector most of its models fall in | Text |
