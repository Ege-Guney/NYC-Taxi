# 04 · F-tests: does each block of predictors improve the model?

**Question (proposal):** are the regression models improved by adding pickup location, time-related factors and weather?

**Notebook:** `notebooks/04_f_tests.ipynb`
**Needs:** 02 (the ladder) and 03 (target and standard-error choice)
**Outputs:** `T09_ladder_f_tests.csv`, `T10_drop_block_tests.csv`

## Two kinds of F-test

### 1. Classic nested F-test

This version assumes constant variance and independent errors:

```
F = [(RSS_r − RSS_u) / q] / [RSS_u / (n − k_u)]
```

Here r is the smaller (restricted) model, u the bigger (unrestricted) one, q the number of added parameters and k_u the number of parameters in u. H₀: all the added coefficients are zero.

- Pairwise: `m_big.compare_f_test(m_small)` returns `(F, p, q)`. Equivalently, use `anova_lm(m_small, m_big)`. `compare_f_test` is only valid on fits with the default (non-robust) covariance.
- ⚠ `anova_lm(m0, m1, …, m6)` in a single call uses the **largest** model's error variance in every row, so its F values differ from the pairwise ones (checked on synthetic data). Either is fine to report, but say which. The textbook version is pairwise.

### 2. Robust Wald F-test

This one uses the day-clustered covariance, so it stays valid with the unequal variance and within-day correlation found in 03.

- **Fit with `use_t=True`:** `fit(cov_type="cluster", cov_kwds={"groups": ...}, use_t=True)`. On robust fits, statsmodels otherwise defaults to normal and χ² distributions. `wald_test_terms` would then report χ² statistics (q × F, with no denominator df), which don't match the F values in T09.
- **One block:** build a restriction matrix `R` with one row per tested coefficient and a 1 in that coefficient's column, then call `m.wald_test(R, use_f=True, scalar=True)`. String constraints work too, including dummy names: `"temperature_2m = 0, precipitation = 0"` or `"C(month)[T.2] = 0, ..."`.
- **Every block, each given all the others:** `m.wald_test_terms(skip_single=False, scalar=True)` gives one row per formula **term**. Weather is 7 separate terms, so it comes out as 7 rows. Test the weather block with its own 7-restriction `wald_test`.
- The denominator degrees of freedom are the number of clusters − 1 (196 train days). A block can't test more restrictions than there are clusters, so the zone × hour extension (about 1,150 restrictions) can't get a cluster-robust test. For that block, report the classic F with a caveat, plus the validation RMSE change from 06.

## Steps

1. **Sequential ladder tests (T09):** M0→M1, M1→M2, …, M5→M6. One row per comparison, with columns:
   - block added, q
   - classic F and p
   - robust F and p (fit the bigger model with clustered standard errors and Wald-test the added block)
   - ΔR² = R²_u − R²_r
   - partial R² = (RSS_r − RSS_u) / RSS_r, the share of the remaining unexplained variation that the block explains
2. **Drop-one-block tests on the final model (T10):** test each block (hour, weekday, month, zone, weather, weekend curve) given all the others, on the clustered fit with `use_t=True`. Use `wald_test_terms` for the categorical blocks and one explicit `wald_test` for the 7 weather variables. Unlike the sequential tests, these don't depend on the order of the ladder. Their out-of-sample counterpart is the drop-one-block rows in 06.
3. **The weather block, side by side:** classic F vs robust F. The gap shows how misleading independent-error standard errors are for city-wide variables.
4. **M5 → M6 is a Chow-style test.** It asks whether weekends have a different daily curve. Say that in the report.

## Reading the results

- With n ≈ 236,000, almost every block will be significant (p ≈ 0). **Statistically significant isn't the same as important.** Always report ΔR², partial R² and, from 06, the change in validation RMSE alongside the p-value.
- If the classic test says significant but the robust one doesn't, the evidence came from treating correlated rows as independent. That's most likely for weather.
- Report format: F(q, df) = value, p < .001.

## Pitfalls

- Nested models have to be fit on **identical rows** (built once in 00).
- **Order matters** in the sequential tests. Month enters before weather, so it absorbs the seasonal part of temperature. That's why T10 is also reported.
- Compare only models with the **same target**. An F-test between a log model and a raw model means nothing.

## Done when

- T09 and T10 are saved.
- Findings names the blocks that matter in practice (by partial R²), not just the significant ones, and says whether weather survives the robust test.
