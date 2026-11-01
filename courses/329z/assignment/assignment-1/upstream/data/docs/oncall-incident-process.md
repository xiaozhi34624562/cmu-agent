# On-Call and Incident Process

Document number: ENG-300
Effective: 2025-06-01
Owner: Site Reliability Engineering (Grace Nwosu, Director)
Audience: Engineering, Customer Success

## 1. Purpose

Utilities depend on GridLens and on our devices to run their grids. This document describes how Cardinal Energy staffs on-call rotations, how we classify and respond to incidents, and what happens afterward. It applies to every team that carries a pager.

## 2. Rotations

Five teams run on-call rotations.

| Rotation | Covers | Hours |
|---|---|---|
| SRE | Cloud infrastructure, ingestion pipeline, databases | 24 hours, 7 days |
| Platform | GridLens backend services and the public API | 24 hours, 7 days |
| Apps | Web application and the FieldKit mobile application | 24 hours, 7 days |
| Firmware | Device fleet health and over-the-air updates | 24 hours, 7 days |
| Forecasting | Forecast quality and model pipelines | Business hours only |

Each 24-hour rotation has a primary and a secondary engineer. The Forecasting rotation has one engineer.

A rotation shift lasts one week. Handoff is on Monday at 10:00 Pacific. The outgoing primary writes a handoff note in the rotation's channel that lists open issues, noisy alerts, and any change planned for the week.

Schedules are kept in PagerLine. Hiro Matsuda on the SRE team is the on-call coordinator and publishes the schedule six weeks ahead.

## 3. Who can be on call

An engineer joins a rotation after 90 days at Cardinal Energy and after shadowing at least one full week with an experienced primary. No engineer is on call more than one week in four, counting primary and secondary weeks together. If a team is too small to meet that limit, its manager must tell Grace Nwosu, and SRE will help cover the gap.

To swap a shift, find a colleague on the same rotation, agree on the swap, and record it in PagerLine before the handoff. You do not need your manager's approval for a swap, but tell the rotation channel.

## 4. On-call stipend

Engineers are paid a stipend for each week on call, in addition to salary.

- Primary: $350 per week.
- Secondary: $150 per week.
- The Forecasting rotation, which covers business hours only, is paid at the secondary rate.

Stipends are paid through payroll in the pay period after the rotation week ends.

## 5. Expectations while on call

The primary must be able to acknowledge a page within the time set for its severity and be at a laptop with a working connection within 15 minutes. Keep your phone charged and PagerLine notifications on. Do not be on call while traveling by air or while impaired. If you become unable to respond, hand the pager to the secondary and tell the rotation channel.

The secondary is the backup. The secondary responds if the primary does not acknowledge, and joins any SEV1 incident on the rotation's systems.

## 6. Severity levels

The first responder sets the severity. If in doubt, choose the higher severity. It can be lowered later.

| Level | Definition | Acknowledge within | Other requirements |
|---|---|---|---|
| SEV1 | Customer-facing outage, loss or corruption of customer data, a security breach, or a fault that affects more than 5 percent of the device fleet | 5 minutes | Incident commander assigned. Status page updated within 15 minutes. CTO notified. |
| SEV2 | Degraded service with a workaround, a delay in data of more than 30 minutes, or a single customer fully affected | 15 minutes | Incident commander assigned. Status page updated within 30 minutes. |
| SEV3 | Minor fault with no customer impact yet, or an internal tool outage | 4 business hours | Ticket filed. No incident commander needed. |

## 7. Escalation

PagerLine escalates automatically.

1. The page goes to the primary.
2. If the primary has not acknowledged after 5 minutes, the page goes to the secondary.
3. If neither has acknowledged after a further 10 minutes, the page goes to the engineering manager on call. The managers of the five rotation teams share this duty week by week.
4. If the page is still unacknowledged, PagerLine calls Grace Nwosu.

Anyone may escalate by hand at any time. Asking for help early is expected and is never held against the responder.

## 8. Running an incident

**Open a channel.** For SEV1 and SEV2, open a chat channel named `#inc-YYYYMMDD-short-name`, for example `#inc-20250714-ingest-lag`. All discussion of the incident goes in this channel.

**Assign roles.** The incident commander coordinates and makes decisions. The commander does not debug. The operations lead does the technical work and may bring in others. The communications lead writes status page updates and works with Customer Success. For a SEV2, one person may hold the commander and communications roles.

**Communicate.** The status page is status.cardinal-energy.example. After the first update, post an update at least every 30 minutes during a SEV1 and every 60 minutes during a SEV2, even if nothing has changed. The Customer Success on-call liaison contacts affected customers directly. Engineers do not contact customers during an incident unless the liaison asks.

**Mitigate first.** Restore service before finding the root cause. Roll back a recent deploy if one is suspected. The architecture overview describes the rollback procedure for each service.

**Close.** The incident commander declares the incident resolved when service is restored and stable for 30 minutes. The commander posts a summary in the channel and files the incident record.

## 9. Device fleet incidents

Incidents that involve firmware have extra rules, because a bad update cannot always be undone remotely.

- Pause any over-the-air rollout in progress as the first action.
- Do not start a new rollout during an open SEV1 or SEV2, on any device model.
- If devices in the field may be unsafe, the incident commander calls Nadia Ferreira, Firmware Engineering Manager, and Owen Castellanos, Director of Hardware Engineering, regardless of the hour.
- Field Operations dispatches technicians only on the incident commander's request.

## 10. After the incident

A written postmortem is required for every SEV1 and SEV2. The incident commander names the author, who is usually the operations lead. The draft is due within 5 business days of resolution. Postmortems are blameless: they describe what happened, what the systems and the process allowed, and what will change. They do not assign fault to a person.

Postmortems are presented at Incident Review, which is held on Thursdays at 13:00 Pacific. Every action item has an owner and a due date and is tracked in the engineering issue tracker with the label `postmortem-action`. SRE reports on overdue action items at the start of each Incident Review.

## 11. Rest after night pages

If you are paged between 22:00 and 06:00 local time and the work totals more than 2 hours, you may take a compensatory half day off within the following week. Tell your manager. This time is not deducted from PTO. After a SEV1 that runs through the night, the incident commander will arrange for fresh responders to take over.

## 12. Alert hygiene

Every alert that pages a person must be actionable and must link to a runbook. The rotation reviews its alerts at each handoff. An alert that paged and needed no action is either fixed or removed within two weeks. SRE publishes the number of pages per rotation each month.

## 13. Security incidents

A suspected security incident is always at least SEV2. Page the SRE primary through PagerLine and call the Security hotline listed in the IT and Security Policy. Ibrahim Saleh, the CISO, or his delegate acts as incident commander. Do not discuss a suspected security incident in public channels.

## 14. Contacts

- On-call coordinator: Hiro Matsuda, SRE.
- Director of SRE: Grace Nwosu.
- Customer Success on-call liaison schedule: maintained by Hannah Kowalski, Director of Customer Success.
