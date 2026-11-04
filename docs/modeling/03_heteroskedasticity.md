# 03 · Heteroskedasticity and residual plots

**Question:** do prediction errors grow or shrink with the level of demand? And so: which target (raw, square root, log) and which standard errors should the rest of the analysis use?

From the proposal: compare actual pickups with the model's predictions, and use residual plots to see whether the errors vary at different levels of demand.

**Notebook:** `notebooks/03_heteroskedasticity.ipynb`
**Needs:** 02 · **Feeds:** 04, 06. Do this before the F-tests, because it decides which standard errors they can trust.
**Outputs:** F07–F12, `T08_het_tests.csv`

## Steps

1. **Fit the fullest ladder model (M6) on train three times:** on `pickups`, on `y_sqrt` and on `y_log`.
2. **Plots for each target.** Use a random 20,000-row subsample (`SEED`) for scatter plots, and all rows for statistics.

   | ID | Plot | What to look for |
   |---|---|---|
   | F07 | Residuals vs fitted, one panel per target | A funnel shape means heteroskedasticity. On raw pickups, count the negative fitted values |
   | F08 | Residual SD by fitted-value decile, one panel per target | A rising line means errors grow with demand; a falling line, the reverse |
   | F09 | QQ plot of residuals: `sm.qqplot(resid, line="s")` | An S-shape or bent tails mean heavy tails or skew |
   | F10 | Actual vs predicted pickups on **validation**, back-transformed to pickups, with a 45° line | The comparison the proposal promised |
   | F11 | Residuals by hour of day and by zone (boxplots) | Systematic misses. That's misspecification rather than heteroskedasticity, but these plots show both |
   | F12 | Autocorrelation of the hourly mean residual (`sm.graphics.tsa.plot_acf`, up to lag 200) | Lags 1–23 (within a day) justify clustering by date. Spikes at 24 and 168 mean errors are correlated **across** days, which date clusters ignore. If you see them, add ISO-week clustering as a check, and use HAC with at least 168 lags for the city series |

3. **Tests (T08), for each target:**
   - **Breusch-Pagan:** `het_breuschpagan(m.resid, m.model.exog)` returns the LM statistic, its p-value, an F statistic and its p-value. H₀: constant error variance. By default statsmodels uses the robust (Koenker) version.
   - **Simplified White test:** regress the squared residuals on the fitted values and their squares, then F-test the slopes. The full White test (`het_white`) needs every square and cross-product of the 120 columns, which is too many.
4. **List the 10 largest residuals** with zone, date and hour. Expect holidays, storms and events. That table is useful in the report.
5. **Decide** the standard-error type (date, plus ISO week if F12 calls for it), the HAC lag length, and a **provisional** target. Write them into the open-decisions table in [README.md](README.md#decisions-still-open). The final target is chosen in 06 on validation error. F10 uses the back-transforms described in [06](06_model_comparison.md#steps).

## Reading the results

- With 236k rows, Breusch-Pagan rejects even for tiny departures. Judge the size of the problem from the plots, and report the test as support.
- What to expect:
  - **Raw:** the spread grows with demand (the classic funnel), and the model predicts negative pickups at low demand.
  - **Log:** the reverse. Low-demand zone-hours are the noisiest, because `log(0 + 1) = 0` is a floor.
  - **Square root:** somewhere in between. It's the standard variance-stabilizing transform for counts.
  - None of the three will have constant variance.
- **Heteroskedasticity doesn't bias OLS coefficients.** It makes the classic standard errors, t-tests and F-tests wrong. The fix is robust standard errors, not a different model. Changing the target is about fit and sensible predictions (no negative pickups).
- **Clustered by date beats HC3 here.** HC3 only fixes unequal variance. Clustering by date also handles correlation within a day (F12, lags 1–23), but not across days.

## Pitfalls

- Each target has its own residual scale, so compare plot **shapes**, not axis values.
- Weighted least squares (weights = 1 / residual variance by fitted decile) is an option, but it changes the estimates. Only try it if the team wants to, and compare it on validation in 06.
- Train hours have gaps where the validation and test weeks were removed. The autocorrelation in F12 treats the hours either side of a gap as neighbours. That's fine for a diagnostic; note it in the caption.

## Done when

- F07–F12 and T08 are saved.
- The standard-error type, HAC lags and provisional target are written into the README with a one-line reason.
