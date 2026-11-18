# Case study: evaluating a next-visit theo prediction model

*All figures in the public demo are synthetic. This write-up describes the work, not the company's results.*

## Context

The resort's data science team had a model that predicts how much each loyalty member will be worth on their next trip (their theoretical gaming win, or "theo"), built from a range of guest data. That prediction feeds how comps and offers are sized. The team was building a successor model and needed two things: a clear way to show executives how accurate the current model really was, and a way to see where it fell short so the next version could improve on it.

## What I built

1. **Evaluation queries (Databricks SQL)** against the model's scored output table, which holds one row per guest with the prediction, actual theo and error. The queries break performance down by loyalty tier, game type (table vs. slot), predicted-worth band, booking lead time and calendar time.
2. **A metric definition the team could trust.** My first version averaged each trip's percentage error. That made the top tier look thousands of percent wrong even though its aggregate prediction was close to reality. The cause was a handful of trips where a high-value guest barely played, so the error ratio had a tiny denominator. I switched to group-level, dollar-weighted metrics:
   - normalized MAE = mean |error| ÷ mean actual
   - bias = (mean actual − mean predicted) ÷ mean actual
3. **Booking-lead-time bins.** Trips are grouped as ≤15 days, then 15-day windows up to 180+, with an explicit sort key. This shows whether predictions made further ahead are less reliable.
4. **A Databricks dashboard** with two pages, "Categorical Performance" and "Performance Over Time". It was designed so a non-technical executive could read it in a minute, and the team could reopen it after every retrain.

## Impact

- **Gave executives a clear answer on accuracy.** Individual predictions can miss, so a single guest's comp may be off, but across a tier or the whole guest base the errors average out and the model is accurate. That is the level at which the business spends money, so the model was shown to be valuable.
- **Fed the next model.** The breakdowns showed the data science team which segments the current model handled worst, which they used to iterate on the new model.

## What the evaluation surfaced (illustrated with synthetic data)

- **Segment bias that an overall number hides.** A small overall bias can sit on top of an over-predicted entry tier and over-predicted last-minute bookings.
- **Accurate in aggregate, noisy per trip.** Binned by predicted worth, average predicted and average actual line up well. Single-trip misses are still large, so the score works for segment budgeting but not as a precise per-guest number.
- **Table play is harder to predict than slots**, which fits table play's higher trip-to-trip volatility.

## What I'd do differently

- **Agree on metric definitions before writing queries.** Several rounds of confusing output came from not pinning down what "error" meant.
- **Show sample sizes and uncertainty on every cell.** Some tier × lead-time combinations had very few trips. Bootstrap intervals would stop people from over-reading noise.
- **Split "will they play?" from "how much will they play?"** Near-zero trips deserve their own hit-rate metric rather than being folded into a dollar error.
- **Parameterize instead of copying queries.** One parameterized dataset (dimension, model version, date range) would make re-evaluating a retrained model a one-click job.

## Tools

Databricks SQL and dashboards (Azure), Snowflake, Tableau. Public rebuild: Python/NumPy for synthetic data, a static HTML/SVG dashboard, and GitHub Pages.
