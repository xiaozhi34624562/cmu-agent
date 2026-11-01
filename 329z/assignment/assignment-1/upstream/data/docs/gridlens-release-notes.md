# GridLens Release Notes, 2025 to 2026

Last updated: 2026-08-25
Owner: Product Management
Audience: All employees. A customer-facing version is published in the GridLens help center.

Releases are listed newest first. Each entry gives the release date, the main changes, and anything Customer Success needs to tell customers.

## GridLens 4.10

Released: 2026-08-25

- Loss Analytics: a new feeder ranking view that sorts feeders by unexplained loss, with a link from each feeder to the meters that contribute most.
- DER Visibility: estimates of electric vehicle charging now separate home charging from fleet depots.
- Web application: saved views can be shared with a team. The map loads large service territories about twice as fast.
- API: the `GET /v2/outages` endpoint accepts a `since` parameter.
- Fixed: exports scheduled for 00:00 local time ran an hour late after the daylight saving change in customers' time zones.

Note for Customer Success: requests to API version 1 paths now return a warning header that states the shutdown date.

## GridLens 4.9

Released: 2026-05-12

- Outage Detection: outages are now grouped by protective device as well as by feeder. In tests with three customers, the median time to identify the affected device fell from 9 minutes to 4 minutes.
- FieldKit 2.4: technicians can register a Pulse S2 by scanning its label and can see mesh signal strength before they leave the pole.
- Support for EmberOS 3.2.0, including the display of staged rollout progress on the device fleet page.
- Administrators can set a maintenance window for firmware updates.
- Fixed: the forecast chart showed the lower bound above the expected value for feeders with reverse power flow.

## GridLens 4.8

Released: 2026-02-24

- API version 2.1: the new webhook event `ingest.rejected` and an endpoint to fetch undelivered webhook events.
- Data quality report: a daily report of readings that failed validation, by meter and by reason.
- Load Forecasting: holiday calendars for Canada and the Netherlands.
- Single sign-on: support for OpenID Connect in addition to SAML.
- Fixed: a batch of exactly 5,000 readings was rejected as too large.

Note for Customer Success: the shutdown date for API version 1 is now stated in the API specification.

## GridLens 4.7

Released: 2025-12-09

- DER Visibility is out of beta and is included in the Professional and Enterprise tiers.
- Scheduled exports to customer cloud storage.
- Web application: dark mode, and keyboard navigation for the feeder tree.
- Support for EmberOS 3.1.0.
- Fixed: a time zone error in the daily rollup for customers in Arizona.

Note for Customer Success: customers that still use API version 1 were sent the 12-month shutdown notice with this release.

## GridLens 4.6

Released: 2025-10-14

- Loss Analytics: a transformer-level loss estimate for customers with Meridian M4 gateways at the transformer.
- Forecast horizon extended from 7 days to 10 days.
- Role-based access control: custom roles with permissions for each module.
- FieldKit 2.2: offline mode for areas without coverage.
- Fixed: duplicate outage notifications when a meter reported a last-gasp message twice.

## Planned

GridLens 5.0 is planned for February 2027. Its main change is the new forecasting engine from Project Kestrel. Dates for planned releases are targets and should not be given to customers.

## Release process

GridLens has a numbered release about every ten to twelve weeks. Fixes and small improvements are deployed continuously between numbered releases and are not listed here. Each numbered release is announced to customers by email two weeks ahead, and the help center notes are published on the day of the release. Elena Vasquez approves the content of these notes for forecasting features, and Rohan Kapoor approves it for device features.
