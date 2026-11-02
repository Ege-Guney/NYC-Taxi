"""Step 4 of 4: join hourly weather onto the zone-hour demand table.

Usage:
    python scripts/04_build_model_table.py

Run after steps 1 (01_clean_weather.py) and 3 (03_aggregate_zone_hour.py).
Reads  data/processed/zone_hour.parquet and data/processed/weather_hourly.parquet.
Writes data/processed/model_table.parquet: one row per (zone, hour) with demand and that hour's weather.

Weather is city-wide, so every zone gets the same weather in a given hour. Weather effects are
therefore estimated from ~8,759 distinct hours, not millions of rows: use day-clustered or HAC
standard errors. Whichever precipitation columns step 1 kept (--precip) are carried through.
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
ZONE_HOUR = ROOT / "data" / "processed" / "zone_hour.parquet"
WEATHER = ROOT / "data" / "processed" / "weather_hourly.parquet"
OUT = ROOT / "data" / "processed" / "model_table.parquet"


def main():
    con = duckdb.connect()
    con.execute(f"CREATE VIEW zh AS SELECT * FROM '{ZONE_HOUR.as_posix()}'")
    con.execute(f"CREATE VIEW wx AS SELECT * FROM '{WEATHER.as_posix()}'")

    unmatched = con.execute("SELECT count(DISTINCT hour) FROM zh ANTI JOIN wx ON zh.hour = wx.time").fetchall()[0][0]
    assert unmatched == 0, f"{unmatched} zone-hour hours have no weather row; re-run step 1"

    con.execute(f"""
        COPY (
            SELECT zh.*, wx.* EXCLUDE (time)
            FROM zh JOIN wx ON zh.hour = wx.time
            ORDER BY zh.zone, zh.hour
        ) TO '{OUT.as_posix()}' (FORMAT parquet)
    """)
    n, cols = con.execute(f"SELECT count(*), (SELECT count(*) FROM (DESCRIBE SELECT * FROM '{OUT.as_posix()}')) "
                          f"FROM '{OUT.as_posix()}'").fetchall()[0]
    rows_in = con.execute("SELECT count(*) FROM zh").fetchall()[0][0]
    assert n == rows_in, f"join changed the row count: {rows_in:,} -> {n:,}"
    print(f"{n:,} rows, {cols} columns")
    # 2025-12-31 23:00 has no value for the shifted weather columns (see docs/corrections.md).
    print("weather columns with missing values (expected: the shifted columns, last hour only):")
    print(con.execute(f"SUMMARIZE SELECT * FROM '{OUT.as_posix()}'").df()
             .query("null_percentage > 0")[["column_name", "null_percentage"]].to_string(index=False))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
