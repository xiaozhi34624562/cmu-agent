# Project Kestrel Brief

Date: 2026-03-16
Sponsor: Aiko Tanabe, VP Product
Technical lead: Jonas Weber, Senior Data Scientist
Product manager: Elena Vasquez
Classification: Confidential. Do not share outside Cardinal Energy.

## Summary

Project Kestrel is the replacement of the GridLens forecasting engine. The current engine produces one forecast value per time step and recomputes every forecast from scratch in each run. Kestrel produces probabilistic forecasts, updates them incrementally as new readings arrive, and forecasts each feeder directly. Kestrel will ship as the main feature of GridLens 5.0.

## Why now

Three things make the current engine a limit on the business.

1. A full forecast run takes about 11 minutes of the 15 minutes between runs. At the current growth in connected meters, runs will overlap before the end of 2026.
2. Customers with a lot of rooftop solar need to know the range of likely outcomes, not only the expected value. Two prospects chose a competitor in 2025 for this reason.
3. Feeder forecasts are derived today by splitting the substation forecast. That method is poor for feeders with large electric vehicle or solar loads.

## Goals

| Measure | Today | Kestrel target |
|---|---|---|
| Day-ahead system load error (MAPE) | 3.2 percent | 2.5 percent |
| Forecast horizon | 10 days | 14 days |
| Time from a new reading to an updated forecast | Up to 15 minutes | Under 2 minutes |
| Forecast output | Expected value with fixed bounds | Full quantiles from 5 percent to 95 percent |

Kestrel does not change the public forecast endpoint. Quantiles are added as new optional fields, so existing integrations keep working.

## Team

Nine people work on Kestrel: six from Forecasting and Data Science, two from Platform, and one designer. Lila Haddad, Director of Forecasting, is the engineering manager for the project. The Platform engineers work on the incremental update path in the stream pipeline. SRE reviews the design at each milestone but is not part of the project team.

## Milestones

| Date | Milestone |
|---|---|
| 2026-04-30 | Model design review complete |
| 2026-07-31 | Shadow mode: Kestrel runs next to the current engine for all tenants, and its output is not shown to customers |
| 2026-11-03 | Beta begins with 5 design-partner utilities |
| February 2027 | General availability with GridLens 5.0 |

The current engine stays in service for at least 90 days after general availability so that customers can compare the two.

## Budget

The compute budget for Kestrel in 2026 is $1.2 million, most of it for training and for the shadow mode period, when two engines run side by side. Helen Okafor approved the budget in February. Spending is reported to the sponsor each month.

## Risks

- Accuracy on small feeders. Feeders with fewer than 200 meters have noisy load, and the direct feeder model may do worse than the current method. The fallback is to keep the current method below a meter-count threshold.
- Cost. Probabilistic models cost more to run. The team must show by the end of shadow mode that the running cost per meter is no more than 1.3 times the current cost.
- Customer understanding. Operators are used to a single forecast line. Design is testing two ways to show the range with the design partners.

## Communication

Do not describe Kestrel to customers, other than design partners under a confidentiality agreement, before the beta. Sales may say that a new forecasting engine is planned. Questions from customers go to Elena Vasquez. The project channel is `#proj-kestrel`, and the team posts a written update every second Friday.
