"""Scale test: 10,000 meters x 96 readings/day x 30 days = 28.8 million rows.
Generated entirely inside DuckDB with SQL - no Python loops."""
import time
import duckdb

con = duckdb.connect()

t = time.perf_counter()
con.sql("""
    COPY (
        SELECT 'M' || lpad(m::VARCHAR, 5, '0')           AS meter_id,
               'B' || lpad((m // 50)::VARCHAR, 3, '0')    AS building_id,
               TIMESTAMP '2026-10-01' + INTERVAL (i * 15) MINUTE AS ts,
               round(1 + random() * 4, 3)                 AS kwh
        FROM range(10000) r(m), range(96 * 30) s(i)
    ) TO 'data/scale_readings.parquet' (FORMAT parquet)
""")
print(f"Generated 28.8M rows in {time.perf_counter() - t:.1f}s")

t = time.perf_counter()
print(con.sql("""
    SELECT building_id, round(sum(kwh) / 1000, 1) AS mwh
    FROM 'data/scale_readings.parquet'
    GROUP BY ALL ORDER BY mwh DESC LIMIT 3
"""))
print(f"Aggregated 28.8M rows in {time.perf_counter() - t:.2f}s")
