# 00 · Prepare the modeling data

**Goal:** build the two tables every later notebook reads, once, so all models use the same rows.

**Notebook:** `notebooks/00_prepare_data.ipynb`
**Reads:** `data/processed/model_table.parquet` (from `scripts/04_build_model_table.py`)
**Writes:** `data/processed/model_sample.parquet` (top zones, all hours), `data/processed/city_hourly.parquet` (one row per hour), `outputs/tables/T03_top_zones.csv`, `outputs/tables/T04_split_summary.csv`

## Input

`model_table.parquet` has 2,303,617 rows (263 zones × 8,759 hours) with these columns:

- `zone`, `hour`, `pickups` (the target), `dropoffs`
- trip summaries: `fare_sum`, `fare_n`, `distance_sum`, `distance_n`, `duration_min_sum`, `airport_trips`, `card_trips`, `flex_fare_trips`
- weather: `temperature_2m`, `precipitation`, `snowfall`, `snow_depth`, `is_day`, `cloud_cover`, `shortwave_radiation`. The precipitation columns change if step 1 was run with `--precip rain` or `--precip both`. Check the names.

Weather units come from the raw Open-Meteo header. Check them there; the defaults are °C, mm, cm (snowfall), m (snow depth), % and W/m².

## Steps

1. **Load and check.** Confirm the row count, and that weather is missing only at 2025-12-31 23:00. Drop that hour.
2. **Calendar columns.** The DuckDB function for each is in brackets.

   | Column | Meaning | DuckDB |
   |---|---|---|
   | `date` | Calendar date (cluster variable) | `hour::DATE` |
   | `hod` | Hour of day, 0–23 | `hour(hour)` |
   | `dow` | Day of week, 1 = Monday … 7 = Sunday | `isodow(hour)` |
   | `month` | 1–12 | `month(hour)` |
   | `weekend` | 1 if Saturday or Sunday | `isodow(hour) >= 6` |
   | `dom`, `days_in_month` | Day of month, and month length | `day(hour)`, `day(last_day(hour))` |
   | `wknd_hod` | `hod` on weekends, 0 on weekdays. Used for the weekend daily curve in M6 (see [02](02_regression_ladder.md#pitfalls)) | `CASE WHEN isodow(hour) >= 6 THEN hour(hour) ELSE 0 END` |
   | `holiday` | Optional: 1 on the holidays listed below, otherwise **0** | Left join on `date`, then `coalesce(..., 0)`. A null here would make patsy silently drop every non-holiday row |
   | `holiday_lag7` | 1 on the day 7 days after a holiday, so the baseline copies a holiday | Same join, shifted 7 days, also `coalesce(..., 0)` |

3. **Split label** `split`: `'test'` if `dom > days_in_month - 7`, `'val'` if `dom > days_in_month - 14`, otherwise `'train'`.
4. **Pick the zones.** Rank zones by total pickups in **train rows only** and keep the top 50. Save each zone's train pickups and cumulative share to `T03_top_zones.csv`, and write the share covered in Findings.
   - Optional: add zone and borough names from the TLC taxi zone lookup table (CSV, on the TLC trip record page under "Taxi Zone Maps and Lookup Tables"). Save it in `data/`. Report tables read better as "132 JFK Airport" than as "132".
5. **Targets.** `y_log = ln(pickups + 1)`, and `y_sqrt = sqrt(pickups)` for the comparison in 03.
6. **Baseline** `base_lag168`: pickups in the same zone at the same clock time 7 days earlier. Self-join on `hour - INTERVAL 7 DAY` **before** filtering by split, because a test row's lag is in a validation week.
   - It's missing for the first week of January and for 2025-03-16 02:00 (Mar 9 02:00 doesn't exist). All of those are train rows, so every validation and test row should have a baseline. Assert it.
   - Also store `lag_split`, the split of the hour the lag comes from. For days 1–7 of Feb–Dec (about 39% of train rows), the lag comes from the previous month's **test** week. That's fine for the baseline, which isn't fitted. But it means the lag can't be used as a training feature without leaking test pickups into the fit (see the lagged-demand extension in [02](02_regression_ladder.md#extensions)).
   - Optional second baseline `base_profile`: the mean train pickups for the same zone × weekday × hour. It's a lookup table, and hard to beat.
7. **City hourly table** for 05 and 08: sum `pickups` over **all 263 zones** per hour into `city_pickups`, add `y_city = ln(city_pickups)` (never zero, so no +1), and keep weather, the calendar columns and `split`. That gives 8,758 rows.
8. **Checks** (asserts): sizes match the table in [README.md](README.md#expected-sizes-sanity-checks), there are no nulls in weather, every validation and test row has a baseline, and each zone appears in every hour. Save the per-split counts as `T04_split_summary.csv`.
9. **Write** both tables with DuckDB `COPY (...) TO '...' (FORMAT parquet)`. That doesn't need `pyarrow`.

## 2025 holidays and where they fall

| Holiday | Date | Day | Split |
|---|---|---|---|
| New Year's Day | Jan 1 | Wed | train |
| MLK Day | Jan 20 | Mon | val |
| Presidents Day | Feb 17 | Mon | val |
| Memorial Day | May 26 | Mon | **test** |
| Juneteenth | Jun 19 | Thu | val |
| Independence Day | Jul 4 | Fri | train |
| Labor Day | Sep 1 | Mon | train |
| Columbus Day | Oct 13 | Mon | train |
| Veterans Day | Nov 11 | Tue | train |
| Thanksgiving | Nov 27 | Thu | **test** |
| Christmas | Dec 25 | Thu | **test** |

Memorial Day, Thanksgiving and Christmas appear only in test weeks. A single `holiday` dummy would be estimated from the 5 train holidays and applied to them, so expect large test errors on those days. Report them separately in 07. Dec 31 (New Year's Eve) is also a test day.

The baseline is also wrong **7 days after** each holiday, because it copies the holiday. Those days are Oct 20 and Nov 18 (validation), and Jan 27, Feb 24 and Jun 26 (test). They hurt the baseline but not the regression, so 06 and 07 report skill with and without them (`holiday_lag7`).

Congestion pricing started on 2025-01-05, so Jan 1–4 (all train) come before it. A dummy is optional. Those days overlap with the New Year holiday, so the two effects can't be separated.

## Leakage rules

- **Same-hour trip summaries** (`dropoffs`, `fare_sum`, `distance_sum`, `airport_trips`, …) are only known after the hour ends. Never use them as predictors. Use them for EDA, or lagged.
- **Zone ranking, holiday effects and any scaling** use train rows only.
- **Lagged demand** must respect the forecast horizon (open decision 1). With a week-ahead horizon, nothing more recent than 7 days is allowed, so `base_lag168` is fine and a 24-hour lag is not.

## Done when

- Both Parquet files are written and every assert passes.
- `T03` and `T04` are saved.
- Findings records the share of pickups the top 50 zones cover, and the row counts per split.
