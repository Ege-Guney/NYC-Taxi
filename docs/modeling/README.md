# Modeling plan

This folder plans the modeling phase. There's one guide per technique in the proposal, plus a plan for the Word report. **Nothing here has been run yet.** Each guide has a matching notebook skeleton in `notebooks/`, with the same steps as headings and empty code cells.

## What we're answering

From the proposal: predict hourly taxi pickups by zone, across the day, the week and the year, so a dispatcher knows how many taxis to send. That splits into two questions:

1. **Forecasting:** how accurately can a linear regression predict zone-hour pickups, and does it beat a simple "same hour last week" rule?
2. **Explanation:** how much does weather change demand once the normal hour, weekday and month pattern is removed (FWL)?

## Order of work

| # | Notebook | Guide | Proposal technique |
|---|---|---|---|
| 00 | `notebooks/00_prepare_data.ipynb` | [00_prepare_data.md](00_prepare_data.md) | Setup: split, zones, baseline |
| 01 | `notebooks/01_eda.ipynb` | [01_eda.md](01_eda.md) | Description for the report |
| 02 | `notebooks/02_regression_ladder.ipynb` | [02_regression_ladder.md](02_regression_ladder.md) | Linear regression |
| 03 | `notebooks/03_heteroskedasticity.ipynb` | [03_heteroskedasticity.md](03_heteroskedasticity.md) | Heteroskedasticity and residual plots |
| 04 | `notebooks/04_f_tests.ipynb` | [04_f_tests.md](04_f_tests.md) | F-test |
| 05 | `notebooks/05_collinearity.ipynb` | [05_collinearity.md](05_collinearity.md) | Collinearity |
| 06 | `notebooks/06_model_comparison.ipynb` | [06_model_comparison.md](06_model_comparison.md) | Comparing models |
| 07 | `notebooks/07_forecast_accuracy.ipynb` | [07_forecast_accuracy.md](07_forecast_accuracy.md) | Forecast accuracy |
| 08 | `notebooks/08_fwl_weather.ipynb` | [08_fwl_weather.md](08_fwl_weather.md) | Frisch-Waugh-Lovell |
| | Word report | [report_plan.md](report_plan.md) | All of the above |

What depends on what:

```
00 prepare data
 ├─ 01 EDA
 ├─ 02 regression ladder
 │   └─ 03 heteroskedasticity     (picks the target and the standard-error type)
 │       ├─ 04 F-tests
 │       └─ 06 model comparison
 │           └─ 07 forecast accuracy
 ├─ 05 collinearity               (hourly city table; step 2 also needs M5 from 02)
 └─ 08 FWL weather effect         (uses the hourly city table)
```

Once 00 is done, three people can work in parallel: one on 01, 05 and 08, one on 02 → 03 → 04, and one on 06 → 07 after 03.

`scripts/05_statistical_tests.ipynb` holds the original handover notes. These guides build on them and split the work into one notebook per technique. See open decision 6.

## Decisions already made

These come from the handover notes in `scripts/05_statistical_tests.ipynb` and from `docs/proposal_review.md`. Change one only if you write down why.

| Decision | Choice | Why |
|---|---|---|
| Unit | One row per zone × NYC clock hour | The dispatch decision is per zone and hour |
| Zones | Top 50 by **training** pickups. FWL uses the city total of all 263 | The top 60 carry about 90% of pickups; small zones are mostly zeros |
| Target | `log(pickups + 1)` (03 also checks raw and square root) | Count variance grows with the mean |
| Split | Within every month: last 7 days = test, 7 days before = validation, rest = train | Every month stays in train, so month dummies work (proposal review §4) |
| Baseline | Same zone, same clock hour, 7 days earlier | Simple rule the model has to beat |
| Standard errors | Clustered by date for the zone panel; HAC for the hourly city series. Always fit with `use_t=True` | Weather is city-wide, and errors within a day are correlated. Date clusters don't cover correlation **across** days, so if F12 (03) shows spikes at lags 24 and 168, also report SEs clustered by ISO week, and set the HAC lag length from F12 (24 by default, check 168) |
| Collinearity | F-tests and auxiliary regressions. **No VIF** | The professor doesn't allow VIF |
| Missing weather | Drop 2025-12-31 23:00 | The end-of-hour shift leaves it blank (`docs/corrections.md`) |

## Decisions still open

Write the choice and the reason here when made.

| # | Question | Options | Decide in | Choice |
|---|---|---|---|---|
| 1 | Forecast horizon | **Week-ahead** (matches the baseline; nothing newer than 7 days) or day-ahead (allows yesterday's demand as a feature) | Before 02 | |
| 2 | Target | `log(pickups + 1)`, `sqrt(pickups)`, raw | Provisional in 03; final in 06 (on validation error). Rerun 04 if it changes | |
| 3 | Precipitation columns | `precipitation` (default) or `rain` + `snowfall` (`01_clean_weather.py --precip rain`) | 05 | |
| 4 | Extensions | Holiday dummy, temperature², zone × hour curves, lagged demand | 02 / 06 | |
| 5 | Zones | Top 30, 50 or 60; optionally group the rest by borough | 00 | |
| 6 | Old notebook | Keep `scripts/05_statistical_tests.ipynb` or retire it in favour of `notebooks/` | Team | |
| 7 | Green cabs | Out of scope (future work) or a second run (Michael's proposal comment) | Team | |
| 8 | Where the Word file lives | Shared drive (recommended) or git | Team | |

## Conventions for every notebook

- **Inputs:** read only files in `data/processed/`, never the raw CSVs. Load Parquet with DuckDB (pandas needs `pyarrow` for Parquet, which some machines don't have).
- **Same rows:** every model in a comparison or a nested F-test is fit on exactly the same rows. Notebook 00 builds the sample once, and nobody drops rows later.
- **Test weeks are scored once,** in 07, after the model is chosen. They're never used for fitting, choosing or tuning.
- **Every reported number names its model, sample and standard-error type,** e.g. "M5, train, day-clustered SE".
- **Figures and tables** are saved under their register ID from [report_plan.md](report_plan.md): `outputs/figures/F07_resid_vs_fitted.png`, `outputs/tables/T06_ladder.csv`. `outputs/` isn't in git, so rerun the notebook to recreate them.
- **Random sampling** (e.g. plot subsamples) uses `SEED = 42`.
- **Findings cell:** each notebook ends with 3–6 bullets holding the numbers the report needs.
- **Before committing:** Restart & Run All. `nbstripout` strips the outputs.

## Expected sizes (sanity checks)

| Set | Days | Hours | Rows (50 zones) |
|---|---|---|---|
| Train | 197 | 4,727 | 236,350 |
| Validation | 84 | 2,016 | 100,800 |
| Test | 84 | 2,015 | 100,750 |
| **Total** | **365** | **8,758** | **437,900** |

Train has 4,727 hours rather than 197 × 24 = 4,728, because 2025-03-09 02:00 doesn't exist on the clock. Test has 2,015 because 2025-12-31 23:00 is dropped (no weather).

Parameter counts with 50 zones (intercept included): M0 = 1, M1 = 24, M2 = 30, M3 = 41, M4 = 90, M5 = 97, M6 = 120.

## Done when

- Every notebook runs top to bottom from a fresh kernel.
- Every figure and table in the register exists in `outputs/`.
- The open-decisions table is filled in.
- The report draft follows [report_plan.md](report_plan.md).
