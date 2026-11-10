"""Load the raw files into a persistent DuckDB database: energy.duckdb"""
import duckdb

con = duckdb.connect("energy.duckdb")

# DuckDB reads CSV and Parquet directly - no schema needed up front
con.sql("CREATE OR REPLACE TABLE buildings AS FROM 'data/buildings.csv'")
con.sql("CREATE OR REPLACE TABLE readings AS FROM 'data/readings.parquet'")

# A clean view: drop missing / negative readings, add power in kW
con.sql("""
    CREATE OR REPLACE VIEW readings_clean AS
    SELECT r.*, b.building_type,
           r.kwh * 4 AS kw              -- 15-min energy -> average power
    FROM readings r
    JOIN buildings b USING (building_id)
    WHERE r.kwh IS NOT NULL AND r.kwh >= 0
""")

print(con.sql("SELECT count(*) AS readings, count(DISTINCT meter_id) AS meters, "
              "min(ts) AS first, max(ts) AS last FROM readings"))
