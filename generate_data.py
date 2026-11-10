"""Generate a realistic IoT smart-meter dataset and save it as Parquet.

200 meters in 20 buildings, one reading every 15 minutes (96 per day)
for 30 days = 576,000 readings. A few real-world problems are planted
in the data so we have something to find later.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import duckdb

rng = np.random.default_rng(42)
DAYS, METERS_PER_BUILDING = 30, 10

# --- 1. Buildings ---------------------------------------------------------
types = ["office", "laboratory", "warehouse", "retail", "data_center"]
buildings = pd.DataFrame({
    "building_id": [f"B{i:02d}" for i in range(1, 21)],
    "building_type": [types[i % 5] for i in range(20)],
    "floor_area_m2": rng.integers(2_000, 15_000, 20),
})

# --- 2. Timestamps: every 15 minutes -------------------------------------
ts = pd.date_range("2026-10-01", periods=DAYS * 96, freq="15min")
hour = ts.hour.to_numpy() + ts.minute.to_numpy() / 60
weekday = ts.day_of_week.to_numpy() < 5

def load_profile(btype):
    """Typical kW per meter for each building type."""
    work = (hour >= 8) & (hour < 18) & weekday
    if btype == "office":      return np.where(work, 22, 4)
    if btype == "laboratory":  return np.where(work, 30, 14)
    if btype == "warehouse":   return np.where((hour >= 6) & (hour < 22), 12, 3)
    if btype == "retail":      return np.where((hour >= 9) & (hour < 21), 18, 3)
    return np.full(len(ts), 40.0)  # data_center runs flat out 24/7

frames = []
for b in buildings.itertuples():
    base_kw = load_profile(b.building_type) * (b.floor_area_m2 / 8_000)
    for m in range(1, METERS_PER_BUILDING + 1):
        kw = base_kw * rng.uniform(0.8, 1.2) + rng.normal(0, 0.6, len(ts))
        frames.append(pd.DataFrame({
            "meter_id": f"{b.building_id}-M{m:02d}",
            "building_id": b.building_id,
            "ts": ts,
            "kwh": np.clip(kw, 0.1, None) / 4,  # 15 min of energy = kW / 4
            "voltage": rng.normal(230, 2, len(ts)).round(1),
        }))
df = pd.concat(frames, ignore_index=True)

# --- 3. Plant real-world problems ----------------------------------------
day = (df.ts - df.ts.min()).dt.days
hr = df.ts.dt.hour
# a) B07: HVAC left running at night from 15 Oct
night = (hr < 6) | (hr >= 20)
df.loc[(df.building_id == "B07") & (day >= 14) & night, "kwh"] *= 3.5
# b) B12-M03: meter stuck - reports the same value for 5 days
stuck = (df.meter_id == "B12-M03") & day.between(9, 13)
df.loc[stuck, "kwh"] = 1.25
# c) B03-M07: equipment fault causes short demand spikes
spikes = df.index[df.meter_id == "B03-M07"][::400]
df.loc[spikes, "kwh"] *= 8
# d) B16: failing chiller, consumption creeps up 2% per day
b16 = df.building_id == "B16"
df.loc[b16, "kwh"] *= 1 + 0.02 * day[b16]
# e) data-quality issues: negative readings, missing values, voltage sag
df.loc[df.sample(40, random_state=1).index, "kwh"] = -1.0
df.loc[df.sample(60, random_state=2).index, "kwh"] = np.nan
df.loc[(df.meter_id == "B18-M02") & (day == 20), "voltage"] = 196.0
df["kwh"] = df.kwh.round(3)

# --- 4. Save with DuckDB: it can query pandas DataFrames directly ---------
Path("data").mkdir(exist_ok=True)
duckdb.sql("COPY buildings TO 'data/buildings.csv' (HEADER)")
duckdb.sql("COPY (SELECT * FROM df ORDER BY ts, meter_id) "
           "TO 'data/readings.parquet' (FORMAT parquet, COMPRESSION zstd)")
print(f"Wrote {len(df):,} readings from {df.meter_id.nunique()} meters")
