# Data Corrections

Every column and row cut from the raw data, with the reason. The raw files in `data/` are never modified. The cleaning scripts write new files to `data/processed/`.

| Script | Input | Output |
|---|---|---|
| `scripts/01_clean_weather.py` | `data/weather.csv` | `data/processed/weather_hourly.parquet` |
| `scripts/02_clean_taxi.py` | `data/taxi.csv` | `data/processed/taxi_clean.parquet`, `data/processed/taxi_cleaning_report.csv` |

---

## Weather

### Columns removed

| Column | Why |
|---|---|
| `apparent_temperature` | Near-duplicate of `temperature_2m` (it's temperature adjusted for wind and humidity). Keeping both causes collinearity, so we keep the simpler measured temperature. |
| `sunshine_duration` | Mostly repeats `is_day` and the season (0 at night, high in summer daytime). `shortwave_radiation` and `cloud_cover` measure brightness more directly. |
| `rain` (by default) | Already included in `precipitation`, which is rain plus snow measured as water. **Option:** if `precipitation` turns out to be collinear with `snowfall`, run `python scripts/01_clean_weather.py --precip rain` to keep `rain` instead of `precipitation`, so rain and snow stay separate. `--precip both` keeps both. |

**Columns kept:** `time`, `temperature_2m`, `precipitation`, `snowfall`, `snow_depth`, `is_day`, `cloud_cover`, `shortwave_radiation`.

### Time corrections

| Correction | Why | Effect on rows |
|---|---|---|
| Converted times from fixed UTC−5 to New York clock time | Open-Meteo returned fixed EST (UTC−5) all year even though we requested `timezone=America/New_York`: the header shows a single offset of −18000 s, both DST days have 24 rows, and daylight hours don't jump at the DST changes. Without the fix, weather is one hour behind the trips from Mar 9 to Nov 2. | Summer rows move forward one hour. 2025-03-09 02:00 disappears (that hour doesn't exist on the clock), so no data is lost. |
| Merged the two 2025-11-02 01:00 rows | When the clocks fall back, two real hours share the 01:00 label. The trip data counts both under one label, so the weather does the same: `precipitation`, `rain` and `snowfall` are summed; `temperature_2m`, `snow_depth`, `cloud_cover` and `shortwave_radiation` are averaged; `is_day` takes the max. | **1 row removed** by merging (8,760 → 8,759 hours). |
| Shifted `precipitation`, `rain`, `snowfall` and `shortwave_radiation` back one hour | Open-Meteo labels these by the end of the hour they cover (e.g. 06:00 = 05:00–06:00). The shift aligns them with the pickup hour. Check: on 2025-06-21, sunlight now first appears in the 05:00 hour, matching the 05:25 sunrise. | **2025-12-31 23:00 is missing** for these columns, because its value would be in the 2026-01-01 00:00 row, which isn't in the file. Left missing, not imputed. |

`temperature_2m`, `snow_depth`, `is_day` and `cloud_cover` are instantaneous readings and are not shifted.

No other gaps: the raw file has all 8,760 hours of 2025 and no missing values.

---

## Taxi

**Raw rows:** 48,722,602 (matches the TLC total for 2025).
**Kept:** 46,579,523 (95.6%). **Removed:** 2,143,079 (4.4%).

### Columns removed

| Column | Why |
|---|---|
| `store_and_fwd_flag` | Only records whether the meter had a connection when the trip ended. Nothing to do with demand. |
| `VendorID` | The meter/technology provider, not a property of the rider, place or time. |
| `mta_tax` | Flat $0.50 tax on almost every trip, so no useful variation. |
| `improvement_surcharge` | Flat $1.00 fee on almost every trip, so no useful variation. |
| `extra` | Rush-hour and overnight surcharges set by time of day, so it repeats the hour information. |
| `tolls_amount` | Depends on the route, known only after the trip. Not a demand driver. |
| `tip_amount` | Paid after the trip; describes payment, not demand. Also only recorded for card payments. |
| `total_amount` | The sum of the fare and fee columns, so no new information. |
| `congestion_surcharge` | Flat fee for trips in Manhattan south of 96th St, so it's set by zone and is covered by zone dummies. |
| `cbd_congestion_fee` | Congestion-pricing fee for the Manhattan central business district (from 2025-01-05), set by zone and date, so covered by zone and date dummies. |
| `passenger_count` | Demand is measured in trips, not people, and the dispatch decision is about taxis. It's also blank in many late-2025 rows. |

**Columns kept:** `tpep_pickup_datetime` and `PULocationID` (the demand count), `DOLocationID` (drop-off counts), `tpep_dropoff_datetime`, `trip_distance`, `fare_amount` and `payment_type` (cleaning checks, and possible summary features), `RatecodeID` (see below) and `Airport_fee` (identifies airport pickups).

### Rows removed

A row is removed by the **first** rule it fails, in the order below, so the "Removed" column adds up to the total. "Flagged" counts each rule on its own; the rules overlap, so a row can be flagged by more than one.

| # | Rule | Condition | Flagged | Removed | % of raw | Why |
|---|---|---|---|---|---|---|
| 1 | Pickup outside 2025 | pickup missing, before 2025-01-01 or from 2026-01-01 on | 29 | 29 | 0.00% | Wrong timestamps (meter clock errors). |
| 2 | Unknown pickup zone | `PULocationID` missing or not 1–263 (264 = unknown, 265 = outside NYC) | 103,043 | 103,043 | 0.21% | We can't assign the pickup to a zone. |
| 3 | Non-trip payment | `payment_type` 3 (no charge) or 6 (voided); or 4 (dispute) **unless** distance > 0 and fare ≥ 0 | 866,279 | 861,351 | 1.77% | No-charge and voided rows aren't normal paid trips. Disputes with a real distance and a non-negative fare are real rides and are kept (decision 2). The other dispute rows are mostly reversal copies of a ride already in the data. Breakdown of all rows with each code: no charge 308,147 rows / 305,378 removed; dispute 1,094,213 / 555,973; voided 0 / 0. |
| 4 | Negative fare | `fare_amount < 0`, **except** `payment_type = 0` (Flex Fare) with distance > 0 | 992,398 | 377,601 | 0.78% | Refunds and corrections. About 89% of negative cash and dispute rows have a positive "twin" (same vendor, pickup, dropoff and zones), so they're copies of a trip already counted. Flex Fare rows with a real distance are kept (decision 1). |
| 5 | Dropoff before pickup | dropoff missing or earlier than pickup | 2,235 | 2,218 | 0.00% | Impossible timestamps. |
| 6 | Impossible duration | exactly 0 seconds, or longer than 6 hours | 558,985 | 552,522 | 1.13% | A 0-second trip isn't a real ride. Trips over 6 hours are meter errors, usually meters left running for about 24 hours. |
| 7 | Zero distance (cancellations) | `trip_distance` missing or ≤ 0, **unless** the trip lasted ≥ 1 minute and the fare is > 0 | 579,771 | 234,584 | 0.48% | Under a minute or with no fare, a zero-distance trip is most likely a cancellation, which we don't count as demand. Longer paid ones are real rides where the meter didn't record miles (decision 3). |
| 8 | Extreme distance | `trip_distance` > 100 miles | 2,870 | 2,539 | 0.01% | Beyond any realistic NYC taxi trip; odometer errors. |
| 9 | Impossible speed | distance ÷ duration > 80 mph | 13,700 | 9,192 | 0.02% | Physically impossible in NYC, so distance or time is wrong. |
| 10 | Exact duplicate | identical on all 20 original columns (the first copy is kept) | 1 | 0 | 0.00% | The same trip recorded twice. The only duplicate found was already removed by an earlier rule. |
| | **Total** | | | **2,143,079** | **4.40%** | |

The thresholds (6 hours, 100 miles, 80 mph) are constants at the top of `scripts/02_clean_taxi.py`. Full counts are in `data/processed/taxi_cleaning_report.csv` after each run.

### RatecodeID

`RatecodeID` is the fare type: 1 = standard metered, 2 = JFK flat fare, 3 = Newark, 4 = Nassau/Westchester, 5 = negotiated, 6 = group ride, 99 = unknown.

- **Kept the column.** It doesn't affect whether a pickup happened, but it marks airport flat-fare and out-of-city trips, which could be useful features.
- **Recoded 99 to missing (NULL)** because 99 means "unknown". Treating it as a number would be wrong.
- **No rows removed** because of it. The column is blank in many late-2025 rows; those trips are still real pickups and are kept.

### Kept on purpose

- **`payment_type = 0` (Flex Fare, a fixed upfront price):** these rows often have a blank `passenger_count` and `RatecodeID` but are real trips, so they're kept unless another rule removes them. 10,698,069 are in the cleaned data.
- **Flex Fare trips with a negative fare and a real distance:** kept as real pickups. Their `fare_amount` is set to **missing (NULL)** in the output, because the negative value isn't a real price and we don't impute it. 1,855,532 rows. Fare sums and averages leave these rows out.
- **Zero-distance trips lasting ≥ 1 minute with a positive fare:** kept as real pickups. Their `trip_distance` is set to **missing (NULL)** in the output, because the real distance wasn't recorded and we don't impute it. 808,375 rows. Distance sums and averages leave these rows out.
- **Unknown drop-off zones** (`DOLocationID` 264/265): kept, because the pickup is still valid demand.
- **Zero fares** (`fare_amount = 0`): not removed; only negative fares are.

### Decisions

Since demand = pickup count, removing real trips lowers demand, and it does so unevenly across the year and across zones. The aim is to keep as many real trips as possible, without imputing values and without counting any trip twice.

1. **Decided: keep Flex Fare trips with a real distance, even if the fare is negative.** The first version of the rules removed 2,047,089 Flex Fare rows for a negative fare. About 90% have a positive distance, and only 8 of 1.86M have a positive twin, so they're standalone trips, not refunds. They were also uneven across months (about 85k in January rising to 347k in November, 35 in December), so removing them distorted the monthly pattern. Their fare is set to missing (see "Kept on purpose").
2. **Decided: keep disputed fares with a real distance.** A dispute means the passenger contested the fare, so the ride usually happened. Only dispute rows with distance > 0 **and** fare ≥ 0 are kept (531,711 in the cleaned data). Negative dispute rows stay removed, because 89% of them are reversal copies of a ride already counted, and keeping them would double-count.
3. **Decided: keep zero-distance trips that lasted at least 1 minute and have a positive fare; remove the rest as cancellations.** The first version removed every zero-distance trip (1,042,959). Now 234,584 are removed as cancellations and 808,375 are kept. Evidence that many zero-distance trips are real rides:
   - Of the 1,085,897 zero-distance trips that pass the payment, fare and duration rules, 814,272 last at least 1 minute with a positive fare, and 651,638 last at least 5 minutes with a fare of at least $10. The median is 13 minutes and $18.74.
   - Many are fares that don't use the odometer: 138,323 negotiated fares (`RatecodeID` 5, median $58.60) and 26,778 JFK flat fares (`RatecodeID` 2, exactly $70).
   - Removal isn't random. Vendor 2's trips have twice the zero-distance rate of vendor 1's (3.2% vs 1.6%), which points to equipment. Some zones lose a large share of their trips, e.g. zone 145 (17%), 226 (8%) and 65 (8%).
   - Distance isn't needed to count demand, so keeping these rows wouldn't require imputing anything: the distance could be set to missing.

   Trips under 1 minute or without a positive fare are treated as cancellations: the passenger never rode, so they aren't demand.

Fare sign alternative (not used): the commented-out code in `scripts/02_clean_taxi.py` keeps **all** negative-fare rows and flips the sign. It would double-count the reversal copies, so it shouldn't be used as is.
