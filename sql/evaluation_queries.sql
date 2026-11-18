-- Performance by segment (tier shown; swap the GROUP BY column for game_type, worth band, etc.)
SELECT
  tier,
  COUNT(*)                                                    AS trips,
  AVG(predicted_theo)                                         AS avg_predicted,
  AVG(actual_theo)                                            AS avg_actual,
  AVG(ABS(actual_theo - predicted_theo)) / AVG(actual_theo) * 100
                                                              AS normalized_mae_pct,
  (AVG(actual_theo) - AVG(predicted_theo)) / AVG(actual_theo) * 100
                                                              AS bias_pct,
  -- original definition, kept for comparison: explodes when actual_theo is near zero
  AVG((actual_theo - predicted_theo) / NULLIF(actual_theo, 0)) * 100
                                                              AS avg_individual_pct_error
FROM model_eval.next_trip_predictions
GROUP BY tier
ORDER BY avg_predicted DESC;

-- Booking lead-time bins: compute the bin once in a CTE, then group by it
WITH binned AS (
  SELECT *,
    DATEDIFF(day, snapshot_date, checkin_date)            AS lead_days,
    LEAST(FLOOR((DATEDIFF(day, snapshot_date, checkin_date) - 1) / 15), 12)
                                                          AS lead_bin   -- 0 = ≤15 days … 12 = 180+
  FROM model_eval.next_trip_predictions
)
SELECT
  lead_bin,
  CASE WHEN lead_bin = 12 THEN '180+ days'
       ELSE CONCAT(lead_bin * 15, '–', (lead_bin + 1) * 15, ' days') END AS booking_period,
  COUNT(*)                                                         AS trips,
  AVG(ABS(actual_theo - predicted_theo)) / AVG(actual_theo) * 100  AS normalized_mae_pct,
  (AVG(actual_theo) - AVG(predicted_theo)) / AVG(actual_theo) * 100 AS bias_pct
FROM binned
GROUP BY lead_bin
ORDER BY lead_bin;
