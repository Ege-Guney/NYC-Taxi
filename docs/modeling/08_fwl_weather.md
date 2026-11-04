# 08 · Frisch-Waugh-Lovell: how much does weather change demand?

**Question (proposal):** how much does weather (temperature and weather category) change taxi demand once the normal hour-of-day, day-of-week and month patterns are accounted for?

**Notebook:** `notebooks/08_fwl_weather.ipynb`
**Needs:** 00 (the hourly city table)
**Outputs:** `T17_fwl_effects.csv`, `T18_fwl_check.csv`, F18

## Why FWL

The FWL theorem says that in the regression Y = Xβ + Zγ + e, the β from the full regression equals the slope you get by regressing *the part of Y that Z doesn't explain* on *the part of X that Z doesn't explain*. So we can show the weather effect "after removing the calendar" as a picture (a partial regression plot), and the numbers match the full regression exactly.

**Change from the proposal's wording.** The proposal subtracts the typical demand for each hour, weekday and month in turn. That only equals FWL when the groups are balanced. Ours aren't: months have different lengths, a weekday appears 52 or 53 times, and the split removes different days in each month. With unbalanced groups, one pass of group-by-group subtraction gives different residuals from FWL (checked on synthetic data). The correct version regresses on all the calendar dummies at once. Explain this under "Changes from the proposal" in the report (see [report_plan.md](report_plan.md#changes-from-the-proposal)).

## Data

The `city_hourly` table, **train hours only** (4,727). Demand is summed over all 263 zones.

- **Y** = `y_city` = ln(city pickups). City pickups are never zero, so no +1 is needed.
- **X, version A (continuous):** `temperature_2m`, `precipitation`, `snowfall`. Optional additions: temperature² (a curved effect) and `cloud_cover`.
- **X, version B (weather category, as the proposal says):** dummies for a rain hour and a snow hour, compared with dry hours. For example: snow hour = `snowfall > 0`; rain hour = `precipitation >= 0.1` and not a snow hour. Pick the thresholds once and report them.
- **Z** = `C(hod) + C(dow) + C(month)` plus a constant, built with `patsy.dmatrix(..., return_type="dataframe")`. That's 41 columns. Optional: add `C(wknd_hod)` and `holiday`.

## Steps

1. **Y on Z:** keep the residuals ỹ, the demand the calendar doesn't explain.
2. **Each X on Z:** keep the residuals x̃, the weather that's unusual for that hour, weekday and month.
3. **ỹ on x̃:** the slopes are the weather effects. No constant is needed, because the residuals already have mean zero.
4. **Check (T18):** the full regression Y ~ X + Z must give the same weather coefficients. Report the largest absolute difference. It should be about 1e-12 (synthetic test: 2e-14).
5. **Inference: take it from the full regression with HAC standard errors,** `fit(cov_type="HAC", cov_kwds={"maxlags": 24}, use_t=True)`. Set `maxlags` from F12 in 03; if errors correlate across days, use at least 168.
   - The classic (non-robust) standard errors from step 3 are slightly wrong, because their degrees of freedom ignore the 41 calendar parameters.
   - With statsmodels' default HAC settings, the step-3 and full-regression HAC standard errors happen to match (synthetic test). Report the full regression's anyway, because that's the standard reference.
6. **Effects as % change:** 100 × (exp(b) − 1) per unit, with 95% CI 100 × (exp(b ± 1.96 · SE) − 1). For a step of c units that means something (c = 5 for 5 °C), scale the SE too: 100 × (exp(c · b) − 1), with CI 100 × (exp(c · (b ± 1.96 · SE)) − 1). Put these in T17.
7. **Partial regression plots (F18):** for each weather variable, scatter x̃ against ỹ with the fitted line. `sm.graphics.plot_partregress` does this too, but the manual version matches the steps above.
8. **Raw vs FWL slope (an extra column in T17):** compare the slope from Y ~ X alone with the FWL slope. The difference shows how much the calendar confounds the raw relationship, e.g. warm months are also the months when people walk more (Michael's proposal comment).
9. **Robustness checks:**
   - **all 8,758 hours** instead of train only. FWL here estimates an effect rather than making a forecast, so using every hour is legitimate, and it nearly doubles the weather data (especially snow hours). Just don't feed the result back into choosing the forecasting model
   - HAC with 24 vs 48 vs 168 lags (use the lag length chosen from F12 in 03 as the main one)
   - clustering by date instead of HAC
   - adding `C(wknd_hod)` to Z
   - the zone-panel weather coefficients from M5 in 02, with day-clustered SEs: do they have the same sign and a similar size?

## Reading the results

- Example: a coefficient of −0.02 on precipitation means each extra mm in the hour comes with about 2% fewer recorded pickups, holding the calendar fixed.
- **This is the effect on completed pickups, not on true demand** (proposal review, objection 1). In rainy hours, pickups can hit the number of taxis available, which understates a demand increase. Rain also slows trips and so cuts supply, which can make pickups fall even while demand rises. The link to true demand is unknown, and the estimate is probably biased downward. Say this next to the results.
- Train hours aren't contiguous (the validation and test weeks are removed), so HAC treats the hours either side of a gap as neighbours. That's minor, and clustering by date is the check.

## Pitfalls

- Use **the same Z** in steps 1 and 2 and in the full regression.
- **Don't take p-values from step 3.**
- **Snow is rare:** few train hours have snowfall, so its CI will be wide. Report the number of snow hours.

## Done when

- T17, T18 and F18 are saved.
- Findings gives each weather effect as a % with its 95% CI and HAC standard error, and confirms the FWL check passed.
