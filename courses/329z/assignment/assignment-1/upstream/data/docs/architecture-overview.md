# GridLens Architecture Overview

Date: 2026-01-30
Authors: Dmitri Volkov (Platform) and Grace Nwosu (Site Reliability Engineering)
Audience: New engineers, Customer Success, anyone who needs to know how the system fits together

## 1. What the system does

GridLens takes measurements from meters and sensors on a utility's distribution grid, stores them, and turns them into forecasts, outage alerts, and loss reports. At the date of this document the system receives data from 1.4 million connected meters belonging to 61 utilities. The peak rate is about 9,200 messages per second, which occurs at the top of each quarter hour when many third-party meters report at once.

This overview follows a reading from the device to the screen. It names each service and says which team owns it. It ends with the operational facts that engineers most often need: regions, recovery targets, retention, and how we deploy.

## 2. Two ways in

Data enters GridLens by one of two paths.

**The device path.** Cardinal devices, the Meridian M4 and through it the Pulse S2, connect to the device broker over MQTT with TLS. The protocol is defined in the EmberOS 3 Firmware Specification. The broker is a cluster of six nodes per region. It authenticates each device by its certificate and passes messages to the `ingest-gateway` service.

**The API path.** Customer systems and third-party meters send readings over HTTPS to the Ingestion API, which is defined in the GridLens Ingestion API Specification. Requests arrive at `api-edge`, which checks the token and the rate limit and then hands the batch to `ingest-gateway`.

From `ingest-gateway` onward, the two paths are the same.

## 3. The pipeline

**ingest-gateway** (Platform). Decodes messages from both paths into a common internal record, attaches the tenant and the meter identifier, and appends the record to the event log. It is written in Go. It holds no state and scales by adding instances.

**The event log** (SRE). A partitioned, replicated log that every later stage reads from. Records are partitioned by tenant and meter so that readings from one meter stay in order. The event log keeps records for 72 hours. That window is what allows us to replay data after a fault in a later stage, and it sets the upper limit on how long a downstream outage can last without loss of data.

**stream-validator** (Platform). Reads the event log and checks each record: the timestamp is plausible, the values are in range for the meter's rating, and the record is not a duplicate. Records that fail are written to a quarantine topic and appear in the customer's data quality report. Valid records continue.

**tsdb-writer** (Platform). Writes valid readings to the time-series store and maintains the rollups. Katya Petrova leads this area.

**The time-series store** (Platform, operated by SRE). Holds raw readings and rollups. Raw readings are retained for 13 months. Rollups at 15 minutes are retained for 7 years, which meets the record-keeping rules of most of our customers' regulators. Each tenant's data is encrypted with a key that belongs to that tenant.

**forecast-engine** (Forecasting and Data Science). Runs the load forecasting models. It is written in Python. It reads rollups and weather data, and writes forecasts back to the store. A full forecast run for all tenants starts every 15 minutes. Project Kestrel will replace this service.

**outage-detector** (Forecasting and Data Science). Watches last-gasp messages, silent meters, and sensor events, and groups them into outage events by feeder.

**api-edge** (Platform). Serves the public API and the internal API that the applications use.

**notify** (Apps). Sends webhooks, email, and push notifications.

**The applications** (Apps). The GridLens web application and the FieldKit mobile application are written in TypeScript.

## 4. Regions and tenancy

GridLens runs in three cloud regions.

| Region | Location | Role |
|---|---|---|
| us-west | Oregon | Primary for customers in North America |
| us-east | Virginia | Disaster recovery for us-west |
| eu-west | Frankfurt | Customers in the European Union. Data does not leave the region. |

The system is multi-tenant. Every record carries a tenant identifier from `ingest-gateway` onward, and every query is scoped to a tenant by `api-edge`. Engineers cannot query customer data without an access grant that is logged and that expires after 8 hours.

## 5. Recovery targets

The recovery point objective is 15 minutes: after a regional failure, we may lose at most the last 15 minutes of data that had not yet been copied to the recovery region. In practice devices buffer data locally and resend it, so the loss for Cardinal devices is usually zero.

The recovery time objective is 4 hours: service in the recovery region must be available within that time. SRE rehearses a regional failover twice a year, in March and in September. The eu-west region recovers within the region, across availability zones, because its data may not be copied outside the European Union.

The time-series store is backed up every night. Backups are kept for 35 days and a restore is tested every month.

## 6. Reliability

SRE tracks uptime for each service against internal objectives that are tighter than the figure we promise customers, which is published in the GridLens Product FAQ. The internal objective for `api-edge` and `ingest-gateway` is 99.99 percent per month. When a service has used up its error budget for the month, its team stops feature deploys to that service until the month ends or until the reliability work agreed with SRE is done.

Each service has a dashboard, alerts that link to runbooks, and an entry in the service catalog that names the owning rotation. The On-Call and Incident Process describes what happens when an alert fires.

## 7. How we deploy

All services are built and deployed by the continuous delivery pipeline. A change is merged after review by one engineer from the owning team and after the automated tests pass.

A deploy goes first to a canary that takes 5 percent of traffic for 30 minutes. The pipeline compares the canary's error rate and latency with the rest of the fleet. If they are worse, it rolls the canary back without human action. If they are not, the deploy continues to the whole region, and then to the next region.

There is a deploy freeze every Friday after 14:00 Pacific until Monday morning, and during the winter closure. An emergency fix during a freeze needs approval from the engineering manager on call.

To roll back a service, run the pipeline's rollback job for that service. It redeploys the previous release and takes about six minutes. Database schema changes are written so that the previous release still works with the new schema, which makes a rollback safe.

Firmware is not deployed by this pipeline. Over-the-air updates follow the staged rollout in the firmware specification.

## 8. Languages and tools

- Go for ingestion and API services.
- Python for forecasting and analytics.
- TypeScript for the web and mobile applications.
- C for device firmware.
- Infrastructure is described as code and reviewed like any other change.

## 9. Known limits and planned work

- The quarter-hour peak makes `ingest-gateway` scale up and down sharply. Platform plans to smooth it with per-tenant admission control in the second half of 2026.
- A full forecast run takes about 11 minutes of the 15 minutes available. Project Kestrel changes the design so that forecasts update incrementally.
- The event log retention was raised from 48 hours to 72 hours in November 2025 after an incident in which a fault in `tsdb-writer` went unnoticed over a weekend.
- API version 1 is still served by a compatibility layer in `api-edge`. It will be removed after the version 1 shutdown date given in the API specification.

## 10. Where to learn more

- Device protocol: EmberOS 3 Firmware Specification.
- Public interface: GridLens Ingestion API Specification.
- Incidents and rotations: On-Call and Incident Process.
- Product behavior and commercial terms: GridLens Product FAQ.
- Service catalog and runbooks: the Engineering space on Perch.
