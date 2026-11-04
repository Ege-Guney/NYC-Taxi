# 07 · Forecast accuracy on the test weeks

**Question (proposal):** how accurately does the model predict taxi demand across locations, measured by MAE and RMSE?

**Notebook:** `notebooks/07_forecast_accuracy.ipynb`
**Needs:** 06 (the chosen model, target and back-transform)
**Outputs:** `T15_test_accuracy.csv`, `T16_test_by_zone.csv`, F15–F17

## Rules

- **Test weeks are used once, here,** after the model is chosen in 06.
- **Refit the chosen model on train + validation** (281 days), then predict the test weeks. The refit uses more data, including the validation-week holidays.
- **State the forecast horizon** (open decision 1). The default is week-ahead: no feature uses anything more recent than 7 days. Actual weather is used, which assumes a perfect weather forecast, so the reported accuracy is an **upper bound** for a live system.
- **Say that the test weeks are held out *within* the year.** The features look back at most 7 days, but the coefficients are fit on later months too (e.g. Feb 1–14 helps predict Jan 25–31). So test error measures how well the model fills in held-out weeks, which is optimistic for forecasting the future. Step 8 (a date-order split) measures how optimistic. Put this in the report's Methodology section.

## Steps

1. **Overall (T15):** test MAE, RMSE (and WAPE) for the model, `base_lag168` and `base_profile`, plus the skill score 1 − RMSE_model / RMSE_baseline.
2. **By zone (T16):** for the 15 busiest zones, give mean demand, MAE, RMSE and skill. Then report the **share of the 50 zones where the model beats the baseline** (F17: skill per zone, sorted).
3. **By time (F16):** error by hour of day, model vs baseline, and weekday vs weekend. Where does the model miss?
4. **Holidays separately:** compare errors on Memorial Day, Thanksgiving, Christmas and Dec 31 with errors on normal test days. Do the same for the days where the baseline copies a holiday (`holiday_lag7`: Jan 27, Feb 24, Jun 26). Report the skill score with and without all of these days.
5. **F15:** one busy zone's test week (e.g. a Midtown zone or JFK), with actual, model and baseline as hourly lines.
6. **Optional: Diebold-Mariano test.** Is the model's lower error statistically significant?
   - For each test hour, take the loss difference d_t = mean over zones of (error_model² − error_baseline²).
   - Regress d on a constant with HAC standard errors: `sm.OLS(d, np.ones(len(d))).fit(cov_type="HAC", cov_kwds={"maxlags": 168}, use_t=True)`. Loss differences repeat weekly, so use at least 168 lags.
   - A negative, significant constant means the model is more accurate.
7. **Optional: prediction intervals.** Build an 80% interval from the train + validation residual quantiles and check its coverage on test. Dispatch planning cares about the upper end.
8. **Date-order split (required robustness check),** as the proposal described: e.g. train Jan–Aug, validation Sep–Oct, test Nov–Dec, with the month dummies replaced by temperature and daylight. It's the honest "forecast the future" number, and it shows how optimistic the within-year test weeks are. The proposal promised this split, so the report needs it.

## Reading the results

- Put MAE next to mean demand for intuition: "off by X pickups an hour in a zone that averages Y".
- A skill score below 0 means the model is worse than "same as last week". Say so plainly, and point to the zone × hour extension as the next step.
- Big errors on holidays are expected. Each holiday happens once a year, and Memorial Day, Thanksgiving and Christmas fall only in test weeks.

## Pitfalls

- **Don't refit or re-choose after seeing test results.** Label anything done afterwards as exploratory.
- Back-transform exactly as in 06.
- Pooled errors are dominated by the busiest zones. The per-zone results (T16, F17) show the rest.

## Done when

- T15, T16 and F15–F17 are saved.
- Findings gives overall MAE and RMSE vs the baseline, the share of zones beaten, and the worst hours and days.
