# 05 · Collinearity with F-tests (no VIF)

> **Rule: the professor doesn't allow VIF.** Don't report VIF, and don't report 1 / (1 − R²) from an auxiliary regression either, because that *is* the VIF. Use the F-test approaches below.

**Question:** do some predictors carry nearly the same information, making their individual coefficients unreliable?

**Notebook:** `notebooks/05_collinearity.ipynb`
**Needs:** 00 (the hourly city table); 02 for step 2
**Outputs:** F13, `T11_weather_corr.csv`, `T12_joint_vs_individual.csv`, `T13_auxiliary_regressions.csv`

## Where to look

The calendar dummies within each block can't be collinear with each other; the only exact trap is the one described in [02](02_regression_ladder.md#pitfalls). The suspects are the weather variables, both among themselves and against the calendar:

| Pair or group | Why it's suspect |
|---|---|
| `is_day` ↔ `shortwave_radiation` | Radiation is 0 whenever `is_day` = 0 |
| `cloud_cover` ↔ `shortwave_radiation` | Clouds block sunlight |
| `precipitation` ↔ `snowfall` | Precipitation includes snow as water, so in snow hours the two move together |
| `snowfall` ↔ `snow_depth` | Depth builds up from snowfall |
| `temperature_2m`, `is_day`, `shortwave_radiation` ↔ hour × month | All follow the daily and seasonal cycle |

## Use one row per hour

Weather doesn't vary by zone, and every zone appears in every hour, so zone dummies explain nothing about a weather variable beyond its overall mean. An auxiliary regression on `city_hourly` train rows (4,727) gives the same answer as on the 236k-row panel, and it's much faster.

## Steps

1. **Correlation matrix** (T11, heatmap F13) of the weather variables on train hours. It only shows pairs, so it misses overlaps among three or more variables.
2. **Joint vs individual tests (T12).** In the day-clustered M5 from 02, for each suspect pair report:
   - each variable's own p-value (t-test)
   - the joint Wald F-test that both are zero (see [04](04_f_tests.md#2-robust-wald-f-test))

   The classic sign of collinearity: the joint test rejects, but neither individual test does. The pair matters together, but the data can't split the credit between them.
3. **Auxiliary regressions (T13).** This is the F-test stage of Farrar-Glauber. For each weather variable X_j:
   1. X_j ~ calendar (`C(hod) + C(dow) + C(month)`) → R²_cal
   2. X_j ~ calendar + the other weather variables → R²_full, with its overall F-test
   3. **Partial F** (model a vs model b, `compare_f_test`): does the other weather still predict X_j once the calendar is accounted for?

   Report R²_cal, R²_full, the overall F and p, and the partial F and p. With 4,727 hours the F-tests always reject, so judge the size from R²: **R²_full above about 0.8 is serious.**
4. **Coefficient stability** (optional but persuasive): refit M5 dropping one variable from each suspect pair, and show how the partner's coefficient and standard error change. Big swings or sign flips are collinearity in action.
5. **Perfect collinearity check:** for every ladder model, `np.linalg.matrix_rank(m.model.exog) == m.model.exog.shape[1]`. statsmodels doesn't stop on perfect collinearity (it uses a pseudo-inverse), so check explicitly.
6. **Optional: the Farrar-Glauber χ² test** for whether any collinearity is present: χ² = −[n − 1 − (2k + 5) / 6] · ln|R|, where |R| is the determinant of the correlation matrix of the k weather variables, with df = k(k − 1) / 2. It will reject with n = 4,727; include it only if the course covered it. The condition number printed by `summary()` is another diagnostic. Check with the professor before using it.

## What to do with the results

- **For prediction (02, 06, 07):** collinearity doesn't hurt predictions, only the individual coefficients. Keep a variable if it lowers validation error.
- **For interpretation (M5 coefficients, 08 FWL):** drop or combine the weaker variable of a collinear pair. For example, keep `shortwave_radiation` and drop `is_day`. If `precipitation` and `snowfall` collide, rerun step 1 with `--precip rain` so rain and snow are kept separately (see `docs/corrections.md`), then rerun steps 4 and 00.
- **Count the train hours with snowfall > 0.** A snow coefficient estimated from a few dozen hours is fragile, collinear or not.

## Done when

- T11–T13 and F13 are saved.
- Findings lists the collinear pairs (if any), what was dropped or kept, and the precipitation decision (open decision 3).
