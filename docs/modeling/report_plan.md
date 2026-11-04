# Report plan (Word document)

The final deliverable is a Word report built from the figures and tables the notebooks save. This page sets out the outline, the full list of figures and tables, and how to keep the report in step with the code.

## Workflow

1. **Notebooks save every figure and table** under its register ID (see below): figures to `outputs/figures/` as 300 dpi PNG, sized for a 6.5-inch text column, and tables to `outputs/tables/` as CSV.
2. **The Word file lives in the team's shared drive** (OneDrive, Teams or Google Drive) so everyone can edit and comment at once. Git can't merge Word files. Keep only this plan in git (open decision 8).
3. **Captions and numbering:** insert each figure with Insert → Caption (auto-numbered "Figure 1", "Table 1") and refer to it with a cross-reference. Register IDs like F07 are working names; the report numbers figures in the order they appear.
4. **Headline numbers** come from each notebook's Findings cell. Optionally, collect them in `outputs/tables/key_numbers.csv` (name, value, notebook) so the text can be checked against the latest run.
5. **Final check before submitting:** rerun every notebook from a fresh kernel, replace every figure in Word, and recheck the key numbers.

## Outline

The outline mirrors the proposal, so a marker can tick off each technique.

1. **Executive summary** (half a page): objective, data, the best model's test accuracy against the baseline, the size of the weather effects, and one dispatch recommendation.
2. **Objective and business question** (from the proposal).
3. **Data**
   1. Sources: TLC yellow taxi trips for 2025 (48,722,602 trips) and Open-Meteo hourly weather.
   2. Cleaning: a summary of `docs/corrections.md`, with 46,579,523 trips kept (95.6%), the daylight-saving alignment, and T01.
   3. The modeling table: zone × hour, the top 50 zones, the variables (T02, T03).
   4. Assumptions: the 8 listed in `docs/proposal_review.md`.
   5. Changes from the proposal (table below).
4. **Exploratory analysis:** F01–F06, T05.
5. **Methodology:** the split (T04, and the shading in F02), the target, the baseline, the standard-error choices, and why the top 50 zones. Say that the test weeks are held out within the year, which is optimistic for forecasting, and point to the date-order check in 6.6.
6. **Results**, one subsection per proposal technique:
   1. Linear regression ladder (T06, T07)
   2. Heteroskedasticity and residual plots (F07–F12, T08)
   3. F-tests (T09, T10)
   4. Collinearity (T11–T13, F13)
   5. Model comparison (T14, F14)
   6. Forecast accuracy (T15, T16, F15–F17)
   7. FWL weather effect (T17, T18, F18)
7. **Discussion**
   - What it means for dispatch: when and where to add taxis, and how to adjust for rain and temperature.
   - Limitations: completed pickups aren't the same as demand; actual weather vs a forecast; one year of data; yellow cabs only (green cabs as future work); one daily curve shared by all zones in the basic ladder.
   - Next steps.
8. **Conclusion**

**Appendices:** A, the full M5/M6 coefficient table with clustered SEs. B, the cleaning rules (table from `docs/corrections.md`). C, the variable dictionary. D, reproducibility: the repository, the order to run the scripts, and library versions.

## Changes from the proposal

Explain these in section 3.5. Rows marked "to confirm" are what `docs/proposal_review.md` recommends; the team hasn't confirmed them yet.

| The proposal said | We did | Why |
|---|---|---|
| Split by date order: earlier records train, later records test | Last 7 days of each month = test, 7 days before = validation. The date-order split is kept as a robustness check (07, step 8) | Month dummies need every month in train (proposal review §4) |
| FWL by subtracting the typical demand for each hour, weekday and month | Regress on all the calendar dummies together | Subtracting group by group isn't FWL with unequal group sizes (proposal review §6; [08](08_fwl_weather.md#why-fwl)) |
| Parquet files | A merged CSV with the same 48,722,602 rows | The team's download; the row count matches the TLC total |
| Clean missing locations, duplicates and bad timestamps | 10 documented rules, 4.4% of rows removed | `docs/corrections.md` |
| Daylight: sunrise and sunset times | `is_day` and `shortwave_radiation` | Already in the weather file |
| Holidays and long weekends | A holiday dummy (if adopted; open decision 4) | |
| Income by zone | Not used (to confirm) | Constant within each zone, so the zone dummies absorb it |
| Rideshare volume | Not used, or lagged only (to confirm) | Same-hour volume isn't known at dispatch time |
| Airport passenger volume | Not used (to confirm) | Published monthly, so it nearly duplicates the month dummies |
| Local events | Not used (to confirm) | Each event needs a venue → zone mapping and a time window |

## Figure and table register

| ID | Content | Notebook | Report section |
|---|---|---|---|
| T01 | Data summary: raw → clean trips, zones, hours | 01 | 3.2 |
| T02 | Variable dictionary | 01 | 3.3 / App. C |
| T03 | Top 50 zones with pickup share | 00 | 3.3 |
| T04 | Split summary: days, hours, rows | 00 | 5 |
| T05 | Weather summary statistics (train) | 01 | 4 |
| F01 | Hourly profile, weekday vs weekend | 01 | 4 |
| F02 | Daily pickups over 2025, split weeks shaded | 01 | 4 / 5 |
| F03 | Zone concentration curve | 01 | 4 |
| F04 | Hour × weekday heatmaps by zone type | 01 | 4 |
| F05 | Pickups distribution, raw vs log | 01 | 4 |
| F06 | Raw demand vs temperature and precipitation | 01 | 4 |
| T06 | Model ladder: params, R², adjusted R² | 02 | 6.1 |
| T07 | M5 weather coefficients, classic vs clustered SE | 02 | 6.1 |
| F07 | Residuals vs fitted: raw, square root, log | 03 | 6.2 |
| F08 | Residual SD by fitted decile | 03 | 6.2 |
| F09 | QQ plots | 03 | 6.2 |
| F10 | Actual vs predicted (validation) | 03 | 6.2 |
| F11 | Residuals by hour of day and by zone | 03 | 6.2 |
| F12 | Residual autocorrelation | 03 | 6.2 |
| T08 | Breusch-Pagan and simplified White tests | 03 | 6.2 |
| T09 | Sequential F-tests, classic and robust | 04 | 6.3 |
| T10 | Drop-one-block robust tests | 04 | 6.3 |
| T11 | Weather correlation matrix | 05 | 6.4 |
| F13 | Weather correlation heatmap | 05 | 6.4 |
| T12 | Joint vs individual tests | 05 | 6.4 |
| T13 | Auxiliary regressions: R², F, partial F | 05 | 6.4 |
| T14 | Model comparison: fit and validation errors | 06 | 6.5 |
| F14 | Validation RMSE by model | 06 | 6.5 |
| T15 | Test accuracy: model vs baselines | 07 | 6.6 |
| T16 | Test accuracy for the busiest zones | 07 | 6.6 |
| F15 | One zone's test week: actual vs model vs baseline | 07 | 6.6 |
| F16 | Test error by hour of day | 07 | 6.6 |
| F17 | Skill vs baseline per zone | 07 | 6.6 |
| T17 | FWL weather effects (% change, HAC SE, 95% CI, raw slope) | 08 | 6.7 |
| T18 | FWL check: step-3 vs full-regression coefficients | 08 | 6.7 |
| F18 | Partial regression plots | 08 | 6.7 |

The body of the report doesn't need all of these. Choose the strongest and move the rest to an appendix.

## Writing tips

- Each result names its **model, sample** (train, validation or test) **and standard-error type**.
- Test results: "F(7, 196) = 12.4, p < .001". Effects come with a 95% CI.
- Keep tables in the body short. The full statsmodels output belongs in an appendix, if anywhere.
- Before each result, explain the technique in one or two plain sentences. The marker wants to see that you know why it's being used.
- Figures: put the title in the caption, label axes with units, and keep colours the same throughout (actual = black, model = blue, baseline = grey).
- Check the course's page limit and rubric before drafting.
