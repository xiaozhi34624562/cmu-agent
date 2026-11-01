# GridLens Product FAQ

Updated: 2026-05-20
Owner: Product Management (Elena Vasquez, Product Manager)
Audience: Sales, Customer Success, and anyone who answers customer questions

This FAQ gives the approved answers to the questions customers and prospects ask most often. If a customer asks something that is not covered here, ask in the product questions channel before you answer. Commercial terms in a signed agreement take precedence over this page.

## Product basics

**What is GridLens?**
GridLens is a cloud service for electric distribution utilities. It collects measurements from meters and line sensors, and it gives planners and operators forecasts, outage alerts, and loss reports.

**Who uses it?**
Investor-owned utilities, municipal utilities, and rural electric cooperatives. We serve 61 utilities, and 1.4 million meters are connected.

**What modules are there?**
There are four modules.

- Load Forecasting: forecasts of load for each feeder, each substation, and the whole system.
- Outage Detection: detection and grouping of outages from meter and sensor signals, usually before customers call.
- Loss Analytics: comparison of energy delivered to a feeder with energy metered on it, to find technical losses and theft.
- DER Visibility: estimates of rooftop solar, batteries, and electric vehicle charging behind the meter. DER stands for distributed energy resources.

**Do customers need Cardinal hardware?**
No. GridLens accepts readings from any meter through the Ingestion API. Cardinal devices add measurements that most third-party meters cannot provide, such as 1-second data and line sensor readings.

## Forecasting

**How far ahead does GridLens forecast?**
The forecast horizon runs from 15 minutes to 10 days ahead.

**How accurate is it?**
For day-ahead system load, the typical error across our customers is a mean absolute percentage error (MAPE) of 3.2 percent. Accuracy for a single feeder is lower and depends on the number of meters on the feeder. Do not promise a customer a specific figure. Offer a pilot.

**How often are forecasts updated?**
A forecast run starts every 15 minutes.

**Is a new forecasting engine coming?**
Yes. It is being developed under the name Project Kestrel and is planned for GridLens 5.0. Do not give customers a date or accuracy figures for it. Refer questions to Elena Vasquez.

## Data

**How often do Cardinal meters report?**
The Meridian M4 reports on a schedule that can be configured for each customer. The factory default is defined in the firmware specification. Outage and power quality events are sent immediately and do not wait for the schedule.

**How long is data kept?**
Raw readings are kept for 13 months. Rollups at 15 minutes are kept for 7 years. A customer can export its data at any time.

**Where is data stored?**
Data for customers in North America is stored in the United States. Data for customers in the European Union is stored in Frankfurt and does not leave the EU.

**Who owns the data?**
The customer owns its data. Cardinal Energy uses it only to provide the service and, in aggregated and anonymized form, to improve the models. Customers can opt out of the second use.

**Can customers get their data out?**
Yes. They can export from the web application as CSV, read it through the API, or schedule a nightly export to their own cloud storage.

## Service commitments

**How available is GridLens?**
Our agreement includes an availability commitment of 99.95 percent per calendar month for the web application and the API, not counting announced maintenance. If we miss the commitment, the customer receives a service credit: 10 percent of the monthly fee if availability falls below 99.95 percent, and 25 percent if it falls below 99.0 percent.

**When is maintenance done?**
Planned maintenance is announced on the status page at least 5 business days ahead. It is scheduled on Sundays between 02:00 and 05:00 Pacific.

**What support do customers get?**
There are two support plans.

- Standard support is included. It is available on business days from 06:00 to 18:00 Pacific, with a first response within 4 business hours.
- Premier support is available 24 hours a day, every day. The first response for a priority 1 issue is within 30 minutes. Premier support is included in the Enterprise tier and can be added to the Professional tier.

**Where do customers see service status?**
At status.cardinal-energy.example. They can subscribe to updates by email.

## Security and compliance

**Is GridLens audited?**
Yes. Cardinal Energy holds a SOC 2 Type II report, renewed each year. Customer Success can share the report under a confidentiality agreement.

**How do users sign in?**
With single sign-on through SAML or OpenID Connect from the customer's identity provider, or with a GridLens account protected by multi-factor authentication.

**Is data encrypted?**
Yes, in transit and at rest. Each customer's data is encrypted with a key that belongs to that customer.

## Pricing and contracts

**How is GridLens priced?**
By connected meter per month, in three tiers.

| Tier | Price per meter per month | Includes |
|---|---|---|
| Essentials | $0.85 | Load Forecasting and Outage Detection |
| Professional | $1.40 | All four modules, API access, scheduled exports |
| Enterprise | Custom | Professional plus Premier support, single-tenant options, and custom retention |

The minimum contract size is 10,000 meters. The standard term is three years, billed each year in advance.

**Is there a trial?**
We offer a paid pilot of 60 days that covers up to 2,500 meters. The pilot fee is credited against the first year if the customer signs. Sales needs approval from Jamal Whitfield for any pilot larger or longer than this.

**Are discounts available?**
Volume discounts start at 250,000 meters. Account executives may offer up to 10 percent without approval. Anything beyond that goes to the deal desk.

## Hardware

**What hardware does Cardinal sell?**
Two devices.

| Device | List price | Warranty |
|---|---|---|
| Meridian M4 meter gateway | $189 | 5 years |
| Pulse S2 line sensor | $74 | 3 years |

**How long does the Pulse S2 battery last?**
The design life is 10 years at the default reporting period.

**Who installs the devices?**
The utility's own crews, or Cardinal's Field Operations team under a separate statement of work. Installers use the FieldKit mobile application to register each device and to check its signal.

**How are devices updated?**
Over the air. Updates are signed and are rolled out in stages. A utility can set a maintenance window for updates to its fleet.

**Is a new sensor coming?**
A successor to the Pulse S2 is in development. There is nothing to announce to customers yet.

## Integrations

**What systems does GridLens connect to?**
Meter data management systems, outage management systems, SCADA historians, and geographic information systems. Most integrations use the Ingestion API and webhooks. Customer Success maintains the list of tested integrations on Perch.

**Is the older API still supported?**
API version 1 is supported until its shutdown date, which is given in the API specification. Customers on version 1 should plan their move to version 2 now, and their Customer Success Manager can help.

## Who to ask

- Forecasting and analytics: Elena Vasquez.
- Devices: Rohan Kapoor.
- Pricing exceptions: Jamal Whitfield.
- Security questionnaires: the Security team, through the security reviews queue.
