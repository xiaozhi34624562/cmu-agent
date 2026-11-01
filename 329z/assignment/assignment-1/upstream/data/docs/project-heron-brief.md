# Project Heron Brief

Date: 2026-06-02
Sponsor: Tomas Lindqvist, CTO
Project lead: Owen Castellanos, Director of Hardware Engineering
Product manager: Rohan Kapoor
Firmware lead: Mei-Ling Chou, Firmware Engineer
Classification: Confidential. Do not share outside Cardinal Energy.

## Summary

Project Heron is the development of the Pulse S3, the successor to the Pulse S2 line sensor. The S3 keeps the clamp-on form of the S2 and adds voltage sensing, a longer battery life, and a lower cost.

## What changes from the Pulse S2

| | Pulse S2 | Pulse S3 target |
|---|---|---|
| Measures | Line current, conductor temperature | Line current, conductor temperature, line voltage (capacitive) |
| Battery design life | 10 years | 15 years |
| Unit cost | Not stated here | $58 |
| Mesh radio | 915 MHz or 868 MHz, set at manufacture | Both bands in one unit, selected at install |
| Firmware | EmberOS 3.2 | EmberOS 3.3 or later |

The longer battery life comes from a new radio chip and from energy harvesting from the line's magnetic field when the line current is above 20 amperes.

## Schedule

| Date | Milestone |
|---|---|
| October 2026 | Engineering validation build (EVT), 150 units |
| January 2027 | Design validation build (DVT), 600 units |
| April 2027 | Field trial with two utilities |
| Third quarter of 2027 | Production start |

## Firmware work

The S3 needs EmberOS 3.3, which adds a driver for the new radio, the voltage measurement, and a change to the mesh report format to carry voltage. The Meridian M4 must also run EmberOS 3.3 to accept the new report format. Older M4 firmware ignores the voltage field and accepts the rest of the report. Mei-Ling Chou leads this work, and the changes will be written into the next revision of the firmware specification before code review starts.

## Team

Seven people from Hardware Engineering and three from Firmware work on Heron. Field Operations, led by Luis Ortega, will run the field trial.

## Risks

- The capacitive voltage measurement is sensitive to conductor diameter and to rain. The accuracy target of 1 percent may need a calibration step at install.
- The supplier of the new radio chip has a lead time of 26 weeks. Orders for the DVT build must be placed by the end of July 2026.
- A $58 unit cost assumes volumes of 50,000 units per year.

## Communication

The Pulse S3 has not been announced. Sales and Customer Success may say that a successor to the Pulse S2 is in development and nothing more. The project channel is `#proj-heron`.
