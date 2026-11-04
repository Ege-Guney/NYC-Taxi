# 02 · Linear regression: the model ladder

**Question:** which groups of predictors explain zone-hour demand, and how much does each one add?

**Notebook:** `notebooks/02_regression_ladder.ipynb`
**Needs:** 00 · **Feeds:** 03, 04, 06
**Outputs:** `T06_ladder.csv`, `T07_weather_coefs.csv`

## The ladder

Each model adds one block of predictors to the one before. That makes every pair **nested**, which the F-tests in 04 need.

| Model | Adds to the previous model | New params | Total (50 zones) |
|---|---|---|---|
| M0 | Intercept only | 1 | 1 |
| M1 | `C(hod)`: hour of day | 23 | 24 |
| M2 | `C(dow)`: day of week | 6 | 30 |
| M3 | `C(month)` | 11 | 41 |
| M4 | `C(zone)` | 49 | 90 |
| M5 | Weather: `temperature_2m + precipitation + snowfall + snow_depth + cloud_cover + shortwave_radiation + is_day` | 7 | 97 |
| M6 | `C(wknd_hod)`: a separate daily curve for weekends | 23 | 120 |

M0 is the reference for "does the model explain anything at all". M1 vs M0 is the overall F-test of M1.

The target is the one chosen in 03; the default is `y_log`. Fit on **train** rows only.

## Steps

1. **Write the formulas once.** Keep them in one dict at the top of the notebook (`LADDER = {"M1": "y_log ~ C(hod)", ...}`). Notebooks 03, 04 and 06 need the exact same formulas. If copying them gets error-prone, move the dict into a small `notebooks/ladder.py` and import it everywhere.
2. **Fit** each model with `smf.ols(formula, train).fit()`.
   - Check that `int(m.df_model) + 1` matches the table above.
   - Check that the design matrix has full rank: `np.linalg.matrix_rank(m.model.exog) == m.model.exog.shape[1]`.
3. **Refit M5 and M6 with day-clustered standard errors:** `fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(train["date"])[0]}, use_t=True)`. The coefficients stay the same; only the standard errors change. `use_t=True` makes the p-values and F-tests use t and F with (number of days − 1) degrees of freedom. Without it, statsmodels uses normal and χ² distributions on robust fits.
4. **T06:** one row per model with params, R², adjusted R² and the residual sum of squares (RSS, needed in 04).
5. **T07:** the M5 weather coefficients, each with its classic SE, day-clustered SE, p-value from the clustered SE, and % effect.
6. Don't pickle the models. The ladder refits in seconds, and pickles break across library versions. Refit in each notebook that needs them.

## Reading log-model coefficients

- **Dummy:** the effect is 100 × (exp(b) − 1)% compared with the reference level (hour 0, Monday, January, the first zone).
- **Continuous:** 100 × (exp(b) − 1)% per one unit (1 °C, 1 mm, …). For a step that means something, use 100 × (exp(10b) − 1)% per 10 °C.
- With `log(pickups + 1)`, the % applies to pickups + 1. That's close to pickups in busy zones; say so in the report.

## Why clustered standard errors

Weather is the same for all 50 zones in a given hour, and errors in the same day move together: a busy evening is busy everywhere. Classic standard errors treat the 236k rows as independent, which makes them far too small for weather. Clustering by date allows any correlation within a day. The 197 train days give 197 clusters. Expect the clustered standard errors on weather to be several times larger.

Date clusters still assume different days are independent. If the residual autocorrelation in 03 (F12) shows spikes at lags 24 or 168, add a robustness column clustered by ISO week. Train covers about 38 weeks, which is enough for the 7-variable weather block.

## Extensions

Try these after the main ladder, as M7, M8 and so on. Keep one only if it lowers validation error in 06. Each one nests M6, so the F-tests still work **as long as it's fit on exactly the same rows as M6**. patsy silently drops any row with a missing value, so check `m.nobs` is equal for every pair you compare.

| Extension | Formula term | Note |
|---|---|---|
| Holiday | `+ holiday` | Estimated from the 5 train holidays (see [00](00_prepare_data.md#2025-holidays-and-where-they-fall)). The column must be 0, not missing, on other days |
| Curved temperature | `+ I(temperature_2m**2)` | Demand may rise in both cold and heat |
| Zone-specific daily curves | `+ C(zone):C(hod)` | Adds about 1,150 columns, making the design matrix over 2 GB at 236k rows. Fit it with a fixed-effects package, e.g. `pyfixest` with `y_log ~ weather + C(dow) + C(month) + C(wknd_hod) \| zone^hod` (not in `requirements.txt` yet), or demean by zone × hour first (FWL, see [08](08_fwl_weather.md)) |
| Lagged demand | `+ np.log1p(base_lag168)` | Advanced; only if the forecast horizon allows it (open decision 1). Two traps. (1) The lag is missing for Jan 1–7, so those rows drop out. (2) For days 1–7 of every other month, the lag comes from the previous month's test week (`lag_split == "test"`), which leaks test pickups into the fit. If used, restrict **every** compared model to rows where the lag exists and `lag_split != "test"` (this changes the sample, so say so), or drop the extension |
| Rain by hour | `+ precipitation:C(hod)` | Lets the rain effect differ at rush hour |

Count models (Poisson regression) suit pickup counts well, but they're outside the proposal's linear-regression scope. Mention them under limitations.

## Pitfalls

- **Dummy trap with hour × weekend.** `C(hod):weekend` creates 24 columns, and their sum equals the Saturday + Sunday dummies already in `C(dow)`. That's perfect collinearity. statsmodels doesn't raise an error (it uses a pseudo-inverse), so those coefficients come out arbitrary without any warning. Use `C(wknd_hod)` instead. Its reference level 0 covers weekdays and weekend hour 0, which gives exactly 23 columns at full rank. Tested on synthetic data: `C(hod):weekend` has one column more than its rank.
- **Same rows** for every model: rows with missing values are dropped once, in 00, never per model.
- **No same-hour trip summaries** as predictors, because they leak the answer (see [00](00_prepare_data.md#leakage-rules)).
- **R² on the log scale can't be compared** with R² on raw pickups. Compare targets in 06, on validation errors in pickups.
- **Reference levels:** if another baseline reads better, set it explicitly, e.g. `C(hod, Treatment(4))` makes 4 am, the quietest hour, the reference.

## Done when

- T06 and T07 are saved, and the parameter counts match.
- Findings records the R² gained at each step, and the weather coefficients with clustered SEs as % effects.
