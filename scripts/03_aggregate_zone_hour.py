"""Step 3 of 4: group cleaned taxi trips into one row per (pickup zone, hour).

Usage:
    python scripts/03_aggregate_zone_hour.py

Run after step 2 (02_clean_taxi.py). Reads data/processed/taxi_clean.parquet.
Writes data/processed/zone_hour.parquet: every zone (1-263) x every 2025 NYC clock hour,
zero-filled, so a zone-hour with no trips is a row with pickups = 0 (a real zero, not missing).

Columns:
    zone, hour             pickup zone (PULocationID) and hour (NYC clock time)
    pickups                trips picked up in this zone in this hour (the demand target)
    dropoffs               trips dropped off in this zone in this hour (by dropoff time)
    fare_sum, fare_n       sum of fares and number of trips with a known fare
    distance_sum, distance_n
    duration_min_sum       total trip minutes
    airport_trips          pickups charged the airport fee (JFK/LGA)
    card_trips             pickups paid by credit card (payment_type 1)
    flex_fare_trips        pickups with a fixed upfront price (payment_type 0)

Other trip features are stored as sums and counts, not averages, so they can be re-aggregated later
(zone -> borough, hour -> day). Compute averages afterwards, e.g. fare_sum / fare_n; they're undefined
when the count is 0. These summaries are only known after the hour ends, so use them for exploration
or as lagged features, never as same-hour predictors (that leaks the answer).
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
TRIPS = ROOT / "data" / "processed" / "taxi_clean.parquet"
OUT = ROOT / "data" / "processed" / "zone_hour.parquet"

ZONES = 263  # TLC taxi zones 1-263 (264/265 = unknown/outside NYC, removed in step 2)
SKIPPED_HOUR = "2025-03-09 02:00"  # spring-forward hour doesn't exist on NYC clocks


def main():
    con = duckdb.connect()
    con.execute(f"""
        COPY (
            WITH grid AS (
                SELECT z.zone, g.hour
                FROM range(1, {ZONES + 1}) z(zone),
                     (SELECT unnest(generate_series(TIMESTAMP '2025-01-01', TIMESTAMP '2025-12-31 23:00',
                                                    INTERVAL 1 HOUR)) AS hour) g
                WHERE g.hour <> TIMESTAMP '{SKIPPED_HOUR}'
            ),
            pu AS (
                SELECT PULocationID AS zone, date_trunc('hour', tpep_pickup_datetime) AS hour,
                       count(*)                                    AS pickups,
                       sum(fare_amount)                            AS fare_sum,
                       count(fare_amount)                          AS fare_n,
                       sum(trip_distance)                          AS distance_sum,
                       count(trip_distance)                        AS distance_n,
                       sum(date_diff('second', tpep_pickup_datetime, tpep_dropoff_datetime)) / 60.0
                                                                   AS duration_min_sum,
                       count(*) FILTER (Airport_fee > 0)           AS airport_trips,
                       count(*) FILTER (payment_type = 1)          AS card_trips,
                       count(*) FILTER (payment_type = 0)          AS flex_fare_trips
                FROM '{TRIPS.as_posix()}'
                GROUP BY ALL
            ),
            dof AS (
                SELECT DOLocationID AS zone, date_trunc('hour', tpep_dropoff_datetime) AS hour, count(*) AS dropoffs
                FROM '{TRIPS.as_posix()}'
                GROUP BY ALL
            )
            -- Zero-fill: no trips means 0 pickups and 0 for every sum and count.
            SELECT grid.zone, grid.hour,
                   coalesce(pickups, 0) AS pickups,
                   coalesce(dropoffs, 0) AS dropoffs,
                   coalesce(fare_sum, 0) AS fare_sum,           coalesce(fare_n, 0) AS fare_n,
                   coalesce(distance_sum, 0) AS distance_sum,   coalesce(distance_n, 0) AS distance_n,
                   coalesce(duration_min_sum, 0) AS duration_min_sum,
                   coalesce(airport_trips, 0) AS airport_trips,
                   coalesce(card_trips, 0) AS card_trips,
                   coalesce(flex_fare_trips, 0) AS flex_fare_trips
            FROM grid
            LEFT JOIN pu USING (zone, hour)
            LEFT JOIN dof USING (zone, hour)
            ORDER BY grid.zone, grid.hour
        ) TO '{OUT.as_posix()}' (FORMAT parquet)
    """)
    n, pickups, dropoffs = con.execute(f"SELECT count(*), sum(pickups), sum(dropoffs) FROM '{OUT.as_posix()}'").fetchall()[0]
    print(f"{n:,} zone-hours, {pickups:,} pickups, {dropoffs:,} dropoffs")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
