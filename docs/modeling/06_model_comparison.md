# 06 · Comparing models

**Question (proposal):** which combination of predictors predicts hourly zone demand most accurately on data the model hasn't seen?

**Notebook:** `notebooks/06_model_comparison.ipynb`
**Needs:** 02 (ladder) and 03 (target) · **Feeds:** 07
**Outputs:** `T14_model_comparison.csv`, F14

## The comparison table (T14)

One row per model, with the baselines included as reference rows.

| Column | Computed on | Note |
|---|---|---|
| Params | Train | `int(m.df_model) + 1` |
| R², adjusted R² | Train | Only comparable between models with the same target |
| AIC, BIC | Train | Lower is better. Same target only |
| **Validation MAE, RMSE** | Validation weeks, in pickups | **Main selection criterion** |
| Validation WAPE (optional) | Validation | Σ\|error\| / Σ pickups. A % error that works with zeros, unlike MAPE |
| Skill vs baseline | Validation | 1 − RMSE_model / RMSE_baseline. Above 0 means the model beats the baseline |

Rows:

- the `base_lag168` baseline, and the `base_profile` baseline (optional)
- M1–M6, and any extensions from [02](02_regression_ladder.md#extensions)
- **drop-one-block rows:** M6 without hour, without weekday, without month, without zone, without weather, and without the weekend curve. The ladder adds zone 4th, so the M1–M3 errors mostly reflect the missing zone effects. These rows show each block's own contribution out of sample (the proposal's "combinations"; the in-sample version is T10 in 04)
- the best model refit on the other targets (raw, square root)

**This is where the target is finally chosen** (03 only makes a provisional pick). If it changes, rerun 04.

## Steps

1. **Fit** each model on train (same rows), and predict the validation rows.
2. **Back-transform** predictions to pickups:
   - **Log target:** the naive `np.expm1(ŷ)` predicts a median-like value and under-predicts the mean. The smearing correction (Duan) is `np.exp(ŷ) * S - 1`, where `S` is the mean of `np.exp(train_resid)`.
     - Compute `S` **by fitted-value decile** on train, not as one number. 03 expects the error variance to differ with demand, and a single factor would over-inflate the busy zone-hours that dominate RMSE.
     - Try both versions and say which you keep. `expm1` targets the median, so it tends to win on MAE; smearing targets the mean, so it tends to win on RMSE.
   - **Square-root target:** `np.clip(ŷ, 0, None)**2 + s2`, where `s2` is the mean squared train residual, also by fitted-value decile.
   - **Raw target:** clip negative predictions to 0.
3. **Errors:** compute MAE and RMSE (and optionally WAPE) on validation, pooled over all zone-hours.
4. **F14:** validation RMSE per model as a line or bar chart, with the baseline drawn as a horizontal line.
5. **Choose** the model with the lowest validation RMSE. If two are within about 1%, prefer the simpler one (fewer parameters). Write the choice and the reason in Findings and in the README.

## Reading the results

- In-sample R² always rises as parameters are added; validation error doesn't. That's why validation is the honest test.
- AIC and BIC penalize parameters (BIC more heavily). They're a useful check on parsimony, but for prediction the validation error decides.
- RMSE weighs large errors heavily (busy zones and peak hours), while MAE is the typical error. Report both, and select on RMSE. The proposal names it, and peak errors matter most for dispatch.
- The baseline captures each zone's own daily and weekly shape. The additive ladder forces one shared daily curve on every zone. **Don't be surprised if the baseline wins** until the zone × hour extension is added. That's a finding, not a failure.

## Pitfalls

- **Never choose using the test weeks.**
- R², AIC and BIC can't be compared across raw vs log targets. Compare targets only on validation errors in pickups. RMSE in pickups naturally favours the raw target, because OLS on raw pickups minimizes exactly that squared error. Weigh that against its negative predictions and the residual problems found in 03.
- Use the **same validation rows** for every model, baselines included. Notebook 00 checks that every validation row has a baseline.
- **Holidays don't affect every model equally.** Validation weeks include MLK Day, Presidents Day and Juneteenth. They also include Oct 20 and Nov 18, where the baseline copies a holiday from 7 days earlier (`holiday_lag7`). Holidays hurt the baseline more than the regression, and a holiday dummy helps the regression further. Report skill **with and without** the `holiday` and `holiday_lag7` days.

## Done when

- T14 and F14 are saved.
- The chosen model, target and back-transform are written down with a reason.
