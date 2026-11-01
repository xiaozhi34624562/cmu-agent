# GridLens Ingestion API Specification

Document number: API-SPEC-002
Version: 2.1
Date: 2026-02-20
Owner: Platform team (Dmitri Volkov, Director of Platform Engineering)
Author: Arjun Mehta, Staff Engineer
Status: Approved. Describes API version 2.1, which ships with GridLens 4.8.

## 1. Scope

This specification defines the HTTP interface through which customers and integrators send data to GridLens and read data from it. Typical clients are a utility's meter data management system, its SCADA historian, and third-party meters that are not Cardinal devices.

Cardinal devices do not use this interface. They connect to the device broker with the protocol defined in the EmberOS 3 Firmware Specification (FW-SPEC-003). Both paths feed the same pipeline, which is described in the GridLens Architecture Overview.

## 2. Conventions

2.1 The base address is `https://api.gridlens.cardinal-energy.example/v2`. Customers in the European Union use `https://api.eu.gridlens.cardinal-energy.example/v2`, and their data stays in the EU region.

2.2 Requests and responses are JSON encoded in UTF-8. Clients must send `Content-Type: application/json`.

2.3 Timestamps are ISO 8601 strings in UTC, for example `2026-02-20T17:45:00Z`. A timestamp without a time zone is rejected.

2.4 Energy is in kilowatt-hours, power in kilowatts, voltage in volts, and current in amperes. Values are JSON numbers, not strings.

2.5 Meter identifiers are strings of up to 64 characters chosen by the customer. They must be unique within the customer's tenant.

## 3. Authentication

3.1 The API uses OAuth 2.0 with the client credentials grant. A customer administrator creates a client identifier and secret in the GridLens web application under Settings, Integrations.

3.2 The client exchanges its credentials for an access token at `/v2/oauth/token`. Access tokens expire after 60 minutes. There are no refresh tokens. The client requests a new token when the old one is close to expiry.

3.3 Every other request carries the token in the `Authorization: Bearer` header.

3.4 Each client has one or more scopes: `readings:write`, `readings:read`, `meters:write`, `meters:read`, `forecasts:read`, and `webhooks:manage`.

3.5 A client secret can be rotated at any time. The old secret stays valid for 24 hours after rotation so that clients can be updated without an outage.

## 4. Limits

4.1 Each client may make up to 600 requests per minute. A request over the limit receives status 429 with a `Retry-After` header that gives the number of seconds to wait.

4.2 A single request to write readings may carry up to 5,000 readings. The request body may not exceed 2 MB.

4.3 List responses are paginated. The default page size is 200 and the maximum is 1,000. The response includes a `next_cursor` value when more results exist. Cursors expire after 15 minutes.

4.4 Enterprise customers may ask for higher limits through their Customer Success Manager. Changes are made per tenant by the Platform on-call engineer.

## 5. Writing readings

5.1 `POST /v2/readings` accepts a batch of readings. Each reading has a `meter_id`, a `timestamp`, and one or more measurement fields: `kwh_delivered`, `kwh_received`, `kw`, `kvar`, `voltage`, `current`.

5.2 The request is accepted as a whole or rejected as a whole. If any reading is invalid, the response has status 422 and lists the index and the reason for each invalid reading, and nothing is stored.

5.3 A client should send an `Idempotency-Key` header with a unique value for each batch. If a request with the same key arrives again, the API returns the original response and does not store the readings a second time. Idempotency keys are remembered for 24 hours.

5.4 A reading for a meter and timestamp that already exists replaces the stored reading. The replaced value is kept in the audit history for 90 days.

5.5 Readings with a timestamp more than 10 minutes in the future are rejected. Readings may be backfilled up to 13 months into the past, which matches the retention period for raw readings.

5.6 A successful write returns status 202. The readings are queryable within 90 seconds at the 95th percentile. Forecasts that use them are refreshed on the next forecast run.

## 6. Meters

6.1 `PUT /v2/meters/{meter_id}` creates or updates a meter record. The fields are the service point, the feeder, the phase, the geographic coordinates, the rate class, and free-form tags.

6.2 `GET /v2/meters/{meter_id}` returns the record and the time of the last reading.

6.3 `GET /v2/meters` lists meters, with filters for feeder, tag, and last-reading age.

6.4 `DELETE /v2/meters/{meter_id}` retires a meter. Its readings are kept for the normal retention period and the identifier cannot be reused for 30 days.

## 7. Reading data

7.1 `GET /v2/readings` returns readings for one meter or for a feeder over a time range. The `resolution` parameter selects raw readings or rollups of 15 minutes, 1 hour, or 1 day.

7.2 `GET /v2/forecasts` returns the current load forecast for a feeder, a substation, or the whole system. Each forecast point has a timestamp, an expected value, and lower and upper bounds.

7.3 `GET /v2/outages` returns open and recent outage events detected by the Outage Detection module.

7.4 A query may cover at most 31 days of raw readings per request. Rollup queries may cover up to 2 years per request.

## 8. Webhooks

8.1 A client with the `webhooks:manage` scope can register a webhook with `POST /v2/webhooks`, giving a destination address and a list of event types: `outage.opened`, `outage.closed`, `forecast.updated`, `meter.silent`, and `ingest.rejected`.

8.2 GridLens delivers each event as an HTTP POST with a JSON body. The `X-GridLens-Signature` header carries an HMAC-SHA256 of the body, computed with the webhook's secret. The receiver must verify the signature.

8.3 The receiver must answer with a 2xx status within 10 seconds. Otherwise GridLens retries the delivery up to 5 times with exponential backoff over a period of 30 minutes. After the last failure the event is marked undelivered and can be fetched from `GET /v2/webhooks/{id}/undelivered` for 7 days.

8.4 A webhook that fails every delivery for 24 hours is disabled, and the customer administrators are notified by email.

## 9. Errors

9.1 Errors use standard HTTP status codes. The body is a JSON object with `code`, `message`, and `request_id`.

| Status | Code | Meaning |
|---|---|---|
| 400 | `bad_request` | The request could not be parsed. |
| 401 | `unauthenticated` | The token is missing, expired, or invalid. |
| 403 | `forbidden` | The token lacks the required scope. |
| 404 | `not_found` | The meter or resource does not exist. |
| 409 | `conflict` | The identifier was retired within the last 30 days. |
| 413 | `too_large` | The body exceeds 2 MB or the batch exceeds 5,000 readings. |
| 422 | `invalid_reading` | One or more readings failed validation. |
| 429 | `rate_limited` | The client exceeded its request limit. |
| 503 | `unavailable` | The service is temporarily unavailable. Retry with backoff. |

9.2 Clients should retry on 429 and 503 and on network errors, using the same idempotency key. Clients should not retry on other 4xx statuses without changing the request.

9.3 Include the `request_id` when you contact support.

## 10. Versioning and deprecation

10.1 The version is part of the path. Additive changes, such as new optional fields and new endpoints, are made within a version without notice. Clients must ignore fields they do not recognize.

10.2 Breaking changes require a new version. Cardinal Energy gives at least 12 months of notice before retiring a version.

10.3 API version 1 will be shut down on 2026-12-31. After that date, requests to `/v1` paths return status 410. Version 1 differs from version 2 mainly in authentication (static API keys) and in batch size (1,000 readings). Customer Success is contacting every customer that still sends version 1 traffic.

## 11. Service levels

The API is covered by the availability commitment in the customer's GridLens agreement, which is described in the GridLens Product FAQ. Planned maintenance is announced on the status page at least 5 business days ahead and is scheduled on Sundays between 02:00 and 05:00 Pacific.

## 12. Revision history

| Version | Date | Changes |
|---|---|---|
| 2.1 | 2026-02-20 | Webhook event `ingest.rejected`. Undelivered event endpoint (8.3). Version 1 shutdown date (10.3). |
| 2.0 | 2025-08-05 | First release of API version 2. OAuth 2.0, batches of 5,000, idempotency keys. |
