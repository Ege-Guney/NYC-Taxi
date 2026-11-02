# Proposal Review: Data Handling Gaps and Required Assumptions

A review of the MMA860 proposal, focused on how the data has to be prepared and modelled. Each section gives the problem and the change we recommend.

## Required assumptions (state these in the report)

1. **Demand means completed pickups.** Unmet demand (people who couldn't find a taxi) is not observed.
2. **No pickups means zero demand.** Zone-hours with no trips are treated as true zeros.
3. **Weather is the same city-wide.** One weather station represents all zones in a given hour.
4. **Weather is known when scheduling.** The model uses actual weather; a live system would have to use a forecast.
5. **Lagged values only use the past.** Lagged demand and rideshare features must only use information available at the time of the forecast.
6. **2025 is representative.** One year of data; congestion pricing (from 2025-01-05) is treated as part of normal conditions, or handled with a dummy.
7. **Zones and calendar effects are stable.** Zone boundaries and calendar effects don't change during the year, apart from the dummies we include.
8. **Daylight saving handling.** The skipped hour (2025-03-09 02:00) is excluded. The repeated hour (2025-11-02 01:00) combines two real hours under one label for both trips and weather.

## Objections

### 1. Pickups measure supply as well as demand
The trip data only records completed trips. When there aren't enough taxis (rain, rush hour, late weekend nights), pickups hit a ceiling set by how many taxis are around, so the people who waited or gave up never appear. This means the model will under-predict the busiest hours, which are the ones that matter for wait times. It also pushes the FWL weather effect towards zero.

**Recommendation:** state this as an assumption. Use the TLC high-volume rideshare (HVFHV) files: they include `request_datetime`, `on_scene_datetime` and `pickup_datetime`, which give request counts and wait times by zone and hour. That is the closest available measure of real demand and of the wait times we want to reduce.

### 2. Drop-offs are ignored
Free taxis appear wherever trips end. A zone with many pickups and few drop-offs runs short of taxis, so the useful scheduling number is pickups minus drop-offs.

**Recommendation:** also count drop-offs by `DOLocationID` for each zone-hour.

### 3. One daily pattern for all zones
Adding hour, weekday, month and zone as separate terms gives every zone the same daily curve. Airports, Midtown and nightlife zones have very different curves, and the zone × hour × weekday combination carries most of the signal. Including that interaction directly needs about 44,000 coefficients.

**Recommendation:** model the top 30–50 zones and group the rest by borough, or group zones by the shape of their daily curve (business, nightlife, airport, residential) and interact the hour with the group. Use `log(pickups + 1)` to handle the many zeros and the heteroskedasticity.

### 4. A date-order split conflicts with month dummies
If later months are held out for testing, they have no fitted month coefficient. With one year of data, each holiday also appears only once.

**Recommendation:** choose one approach and document it: hold out the last week of every month, use rolling-origin evaluation, or replace month dummies with smooth seasonal terms (temperature, daylight).

### 5. Several extra datasets don't fit a zone-hour model
| Dataset | Problem |
|---|---|
| Income by zone | Never changes over time, so zone dummies absorb it completely. Use it only in a model without zone dummies, or interacted with time. |
| Airport passengers | Likely published monthly, so it nearly duplicates the month dummy. |
| Rideshare volume | Moves with the same demand at the same time and isn't known at decision time. Use lagged values only. |
| Daylight / sunrise | Almost fully explained by hour × month. Use `is_day` and check collinearity with F-tests (auxiliary regressions). |
| Events | Each event needs a venue → zone mapping and a time window. Limit to major venues. |
| Weather | The same across the whole city, so effects are estimated from about 8,759 hours, not millions of rows. Use day-clustered or HAC standard errors. |

### 6. The FWL description needs tightening
Subtracting separate averages for hour, weekday and month one after another is not FWL when groups have different sizes (unbalanced data), which ours does.

**Recommendation:** regress demand and each weather variable on all the calendar dummies together (plus a constant), then regress the leftover demand on the leftover weather. Report standard errors from the full regression, not from that last step.

### 7. Cleaning steps not in the proposal
- **Time alignment:** the weather file is on fixed EST all year, so it needs converting to New York clock time. That's done in `scripts/cleaning.ipynb`. Precipitation, rain, snowfall and sunshine also still need shifting back one hour, because Open-Meteo labels them by the end of the hour they cover.
- **Data format:** the proposal names Parquet files, but the team uses a merged CSV. Check that it has 48,722,602 rows.
- **Negative fares:** about 2% of sampled rows. These are usually refunds or corrections. Drop them, but make sure de-duplication doesn't also remove the matching original trip.
- **Congestion pricing:** it started on 2025-01-05, which changes demand right at the start of the sample.

### 8. What collapsing to zone-hour loses
Zone-hour is the right unit for scheduling decisions. To keep most of the detail:
- Store trip features (fare, distance, airport trips, payment type) as sums and counts per zone-hour.
- Keep drop-off counts, and optionally a separate zone-to-zone flow table.
- Use 15-minute bins for the top zones if short peaks matter.

Wait times and unmet demand can't be recovered from yellow-cab data at any level of detail.


