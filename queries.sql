-- Q1: Which building consumes the most electricity?
SELECT building_id, building_type,
       round(sum(kwh) / 1000, 1) AS total_mwh
FROM readings_clean
GROUP BY ALL
ORDER BY total_mwh DESC
LIMIT 5;

-- Q2: What is the daily energy consumption trend?
SELECT ts::DATE AS day,
       round(sum(kwh) / 1000, 1) AS mwh
FROM readings_clean
GROUP BY day
ORDER BY day;

-- Q3: What is the peak demand?
SELECT time_bucket(INTERVAL 15 MINUTE, ts) AS interval_start,
       round(sum(kw)) AS site_kw
FROM readings_clean
GROUP BY interval_start
ORDER BY site_kw DESC, interval_start
LIMIT 3;

-- Q4: Which buildings consume electricity after working hours?
SELECT building_id, building_type,
       round(100 * sum(kwh) FILTER (WHERE hour(ts) NOT BETWEEN 8 AND 17)
             / sum(kwh), 1) AS after_hours_pct
FROM readings_clean
WHERE building_type IN ('office', 'laboratory')
GROUP BY ALL
ORDER BY after_hours_pct DESC
LIMIT 5;

-- Q5: Which meters have abnormal consumption?
WITH stats AS (
    SELECT *,
           avg(kwh)    OVER w AS mean_kwh,
           stddev(kwh) OVER w AS sd_kwh
    FROM readings_clean
    WINDOW w AS (PARTITION BY meter_id, hour(ts))
)
SELECT meter_id, count(*) AS anomalies,
       round(max(kwh / mean_kwh), 1) AS worst_x_normal
FROM stats
WHERE kwh > mean_kwh + 4 * sd_kwh   -- 4-sigma spike
  AND kwh > 2 * mean_kwh             -- and at least 2x normal
GROUP BY meter_id
ORDER BY anomalies DESC, meter_id
LIMIT 5;
