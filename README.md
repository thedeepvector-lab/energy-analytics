# AI-Powered Engineering Analytics with DuckDB + Claude Skills

Companion project for the 15-minute YouTube course.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run it
```bash
python generate_data.py            # 576,000 smart-meter readings -> data/readings.parquet
python build_database.py           # loads everything into energy.duckdb
python .claude/skills/duckdb-engineering-analytics/scripts/analyze_energy.py -f queries.sql
python scale_test.py               # optional: 28.8 million rows
```

## Ask Claude
Open this folder in VS Code, start Claude Code (`claude` in the terminal, or the
Claude Code extension) and ask:

> Analyze the electricity consumption data. Identify the top five buildings with
> abnormal energy consumption and explain possible reasons.

Claude finds the skill in `.claude/skills/duckdb-engineering-analytics/`, reads
`SKILL.md`, and runs `scripts/analyze_energy.py` to execute DuckDB SQL. You can
also invoke it directly with `/duckdb-engineering-analytics`.

## Project layout
```
energy-analytics/
├── generate_data.py        # IoT data generator (with planted problems)
├── build_database.py       # creates energy.duckdb
├── queries.sql             # the five engineering questions
├── scale_test.py           # 28.8M-row performance demo
├── data/                   # buildings.csv, readings.parquet
└── .claude/skills/duckdb-engineering-analytics/
    ├── SKILL.md
    ├── references/
    │   ├── duckdb-sql.md
    │   └── engineering-metrics.md
    └── scripts/
        └── analyze_energy.py
```

## Problems planted in the data (spoilers!)
| Building | Problem |
|---|---|
| B07 | Night-time load 3x higher from 15 Oct (HVAC schedule) |
| B16 | Consumption creeps up 2% per day (failing chiller) |
| B03 | Meter B03-M07 shows short 8x spikes (equipment fault) |
| B12 | Meter B12-M03 stuck at 1.25 kWh for 5 days |
| B18 | Meter B18-M02 voltage sag to 196 V on 21 Oct |
| all | 60 missing and 40 negative readings |
# energy-analytics
