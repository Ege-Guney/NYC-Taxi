# 01 · Exploratory analysis

**Goal:** the descriptive figures for the report's Data section, and a first look at the patterns the models have to capture. No models here.

**Notebook:** `notebooks/01_eda.ipynb`
**Reads:** `model_sample.parquet` and `city_hourly.parquet`. Use `model_table.parquet` only for all-zone views.

## Figures and tables

| ID | What to show | Why it matters for the models |
|---|---|---|
| F01 | Mean city pickups by hour of day, weekday vs weekend (two lines) | The daily curve (M1), and how weekends differ (M6) |
| F02 | Daily city pickups over 2025, with validation and test weeks shaded | Seasonality (Michael's summer vs winter comment), holidays, and the split at a glance |
| F03 | Cumulative share of pickups by zone rank, with the top-50 cut marked | Justifies modeling the top 50 |
| F04 | Hour × weekday heatmaps for 3–4 zone types (airport, Midtown, nightlife, residential) | Zones have different daily curves, which motivates the zone × hour extension |
| F05 | Distribution of pickups per zone-hour, raw and `log(pickups + 1)` | Skew and zeros, which motivate the log target |
| F06 | City pickups vs temperature, and vs precipitation (raw scatter) | The raw relationship that FWL (08) corrects for calendar effects |
| T01 | Data summary: raw → clean trips, zones, hours, rows (from `docs/corrections.md`) | The report's data section |
| T02 | Variable dictionary: name, unit, source, role (target / predictor / control / not used) | The report's data section |
| T05 | Weather summary on train hours: mean, SD, min, max, and the share of hours with precipitation > 0 and snowfall > 0 | Shows how little information there is about snow |

**Which rows:** F01, F03–F06 and T05 use **train rows only**, so nothing about the test weeks shapes modeling choices. F03 has to match T03, which ranks zones on train. The one exception is F02, which shows the whole year so the split weeks can be shaded. It's only for context; don't use it to choose features.

## Steps

1. Load both tables and check the sizes against [README.md](README.md#expected-sizes-sanity-checks).
2. Make each figure above. Use `y_city`/`city_pickups` for city-wide views, and the panel for zone views.
3. Count the zero zone-hours in the top 50 and in the other 213 zones. That supports the zone choice.
4. Write 3–6 bullets in Findings: peak hours, weekday vs weekend, the seasonal swing (highest vs lowest month), top-50 share, and how many train hours had rain or snow.

## Tips

- Shading the validation and test weeks in F02 explains the split better than any paragraph.
- In F06 the raw relationship is confounded: warm months and warm hours also differ in calendar demand. Say so in the caption, and point to 08.
- Keep figure titles out of the image. The caption in Word carries the title (see [report_plan.md](report_plan.md#writing-tips)).
