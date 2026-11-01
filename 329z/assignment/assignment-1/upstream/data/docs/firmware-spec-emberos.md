# EmberOS 3 Firmware Specification

Document number: FW-SPEC-003
Revision: 3.2
Date: 2026-04-08
Owner: Firmware team (Nadia Ferreira, Firmware Engineering Manager)
Author: Sam Okonkwo, Senior Firmware Engineer
Status: Approved. Describes EmberOS 3.2.0.

## 1. Scope

EmberOS is the firmware that runs on Cardinal Energy devices. This specification defines the required behavior of EmberOS 3 on the two device models in production: the Meridian M4 meter gateway and the Pulse S2 line sensor. It is the reference for firmware engineers, for hardware test, and for the Platform team, which builds the cloud side of the device protocol.

The cloud interface for customers and integrators is a different document, the GridLens Ingestion API Specification (API-SPEC-002). When someone on the Firmware team says "the spec", they usually mean this document. When someone on the Platform team says it, they usually mean the API specification.

## 2. Device models

| | Meridian M4 | Pulse S2 |
|---|---|---|
| Role | Meter gateway installed at the service point or transformer | Clamp-on sensor for overhead and underground lines |
| Processor | 32-bit microcontroller, 1 MB flash, 256 KB RAM | 32-bit low-power microcontroller, 256 KB flash, 32 KB RAM |
| Power | Line powered, with a supercapacitor for last-gasp messages | Primary lithium cell, design life 10 years |
| Radio | LTE-M modem and sub-GHz mesh radio | Sub-GHz mesh radio only |
| Wired | Optional Ethernet | None |

A Pulse S2 has no direct connection to the cloud. It reports to a Meridian M4 over the mesh, and the M4 forwards its data.

## 3. Measurement

3.1 The M4 samples voltage and current on each phase at 4 kHz. From the samples it computes, for each 1-second window, RMS voltage, RMS current, active power, reactive power, and frequency.

3.2 The M4 accumulates energy registers (kWh delivered, kWh received, kVARh) continuously and stores them in non-volatile memory at least once per minute and on power failure.

3.3 Measurement accuracy for active energy must meet accuracy class 0.5, that is, an error of no more than 0.5 percent over the rated range. Hardware test verifies this for each firmware release candidate on the reference bench in Boulder.

3.4 The S2 measures line current and conductor temperature. It samples current at 1 kHz for 200 milliseconds once per reporting period and computes RMS current.

3.5 The M4 detects sags, swells, and outages. A sag is an RMS voltage below 90 percent of nominal for more than 3 cycles. A swell is an RMS voltage above 110 percent of nominal for more than 3 cycles. Events are time-stamped and sent immediately, outside the normal reporting schedule.

## 4. Time

4.1 The M4 synchronizes its clock from the cellular network at each attach and from the cloud time service once per hour. Clock error must not exceed 2 seconds. If the M4 cannot synchronize for more than 24 hours, it sets the `time_uncertain` flag on every message until it synchronizes again.

4.2 The S2 receives time from its parent M4 in each mesh acknowledgment.

4.3 All timestamps are UTC, in seconds since the Unix epoch, with a separate millisecond field for events.

## 5. Mesh networking

5.1 The mesh radio operates at 915 MHz in the United States and at 868 MHz in the European Union. The region is set at manufacture and cannot be changed in the field.

5.2 Each S2 joins the mesh of one M4. An M4 supports up to 32 sensors.

5.3 An S2 sends a report to its parent every 60 seconds. If the conductor current changes by more than 20 percent between two samples, the S2 sends an extra report at once.

5.4 If an S2 receives no acknowledgment for 10 consecutive reports, it scans for another M4 on the same network key and rejoins.

5.5 Mesh frames are encrypted with AES-128 in CCM mode using a per-network key that the M4 distributes at join time.

## 6. Cloud uplink

6.1 The M4 connects to the cloud over LTE-M. If Ethernet is present and has a link, the M4 prefers Ethernet and keeps LTE-M as a fallback.

6.2 The transport is MQTT version 5 over TLS 1.3 to the device broker on port 8883. The M4 authenticates with a client certificate whose private key is held in the secure element. Messages are encoded in CBOR.

6.3 The uplink cadence is set by the configuration key `uplink.interval_s`. The default is 300 seconds. The allowed range is 60 to 3600 seconds. At each uplink the M4 sends the 1-second aggregates reduced to the customer's configured resolution, the energy registers, and the reports it has collected from its sensors.

6.4 Events (outage, sag, swell, tamper, and the errors in Section 11) are sent immediately and do not wait for the next uplink.

6.5 On loss of line power, the M4 sends a last-gasp message using the energy in its supercapacitor. The message must leave the modem within 500 milliseconds of power loss detection.

6.6 Topic layout: devices publish to `dev/{device_id}/up` and subscribe to `dev/{device_id}/down`. The broker rejects any publish to a topic that does not match the certificate's device identifier.

## 7. Offline operation

7.1 If the uplink is unavailable, the M4 stores data in a ring buffer in flash. The buffer must hold at least 7 days of data at the default uplink cadence with 32 sensors attached.

7.2 When the connection returns, the M4 sends buffered data oldest first, at a rate limited to 4 messages per second so that a regional recovery does not overload the broker. Live events still take priority over buffered data.

7.3 When the buffer is full, the oldest data is overwritten, and the M4 raises error E-131 once the connection returns.

## 8. Configuration

8.1 Configuration is a set of keys and values held in non-volatile memory. The cloud changes configuration by publishing a signed configuration message to the device's down topic. The device applies the change, replies with the new configuration version, and keeps the previous configuration so that it can revert.

8.2 Principal keys:

| Key | Default | Range | Meaning |
|---|---|---|---|
| `uplink.interval_s` | 300 | 60 to 3600 | Seconds between scheduled uplinks |
| `mesh.report_s` | 60 | 15 to 900 | Seconds between sensor reports |
| `meas.resolution_s` | 60 | 1 to 900 | Resolution of aggregates sent to the cloud |
| `event.sag_pct` | 90 | 70 to 95 | Sag threshold, percent of nominal |
| `event.swell_pct` | 110 | 105 to 130 | Swell threshold, percent of nominal |
| `log.level` | warn | error, warn, info, debug | Device log level |

8.3 A device that loses its connection within 10 minutes of applying a configuration change reverts to the previous configuration.

## 9. Over-the-air updates

9.1 Firmware images are signed with Ed25519. The device verifies the signature with a public key stored in read-only memory before it writes any part of the image to the inactive partition, and again before it boots the image.

9.2 The M4 has two firmware partitions, A and B. An update is written to the inactive partition while the device continues to run from the active one. The maximum image size for the M4 is 480 KB. The S2 has a single partition and a recovery loader, and its image is delivered through the parent M4.

9.3 After an update, the device boots the new image and must report a successful health check to the cloud. If the new image fails to boot 3 times in a row, or if no health check succeeds, the boot loader rolls back to the previous partition and raises error E-302.

9.4 Rollouts are staged. The stages are 1 percent, 10 percent, 50 percent, and 100 percent of the fleet for the customer or region. Each stage must soak for at least 24 hours with no rollback and no rise in error rates before the next stage starts. The Firmware on-call engineer approves each stage.

9.5 No rollout may start or advance during an open SEV1 or SEV2 incident. See the On-Call and Incident Process.

9.6 A device never downgrades to a version lower than the minimum version recorded in its secure element, which prevents the reinstallation of an image with a known vulnerability.

## 10. Security

10.1 Secure boot is mandatory. The boot loader verifies the application image on every boot.

10.2 Each device has a unique identity key generated inside its secure element at manufacture. The key never leaves the secure element.

10.3 Device certificates are rotated every 12 months. The device requests a new certificate 30 days before the old one expires.

10.4 Debug ports are disabled in production units. Re-enabling a debug port requires a signed unlock token that is bound to the device identifier and expires after 24 hours.

10.5 The M4 has a tamper switch on its cover and a tilt sensor. A tamper event must be reported within 2 seconds of detection.

## 11. Watchdog and error codes

11.1 A hardware watchdog resets the device if the main loop does not service it for 8 seconds. After a watchdog reset the device raises error E-100 with the saved program counter.

11.2 Error codes are reported as events. The main codes are:

| Code | Meaning |
|---|---|
| E-100 | Watchdog reset |
| E-131 | Offline buffer overflow, data lost |
| E-207 | Measurement front end self-test failed |
| E-214 | Sensor mesh link lost |
| E-220 | Sensor battery low (S2) |
| E-302 | Update rolled back |
| E-305 | Update signature check failed |
| E-410 | Certificate renewal failed |
| E-415 | Clock not synchronized for more than 24 hours |

11.3 E-214 is raised by the M4 when a joined sensor has sent no report for 15 minutes. It is cleared when the sensor reports again.

## 12. Performance requirements

- Boot to first measurement: no more than 5 seconds.
- Boot to cloud connection over LTE-M: no more than 90 seconds in normal coverage.
- M4 processor load at the default configuration with 32 sensors: no more than 60 percent.
- S2 average current draw at the default reporting period: no more than 45 microamperes, which supports the 10-year battery design life.

## 13. Revision history

| Revision | Date | EmberOS release | Changes |
|---|---|---|---|
| 3.2 | 2026-04-08 | 3.2.0, released 2026-04-22 | Staged rollout stages and soak time (9.4). Minimum version rule (9.6). Error E-415. |
| 3.1 | 2025-10-30 | 3.1.0, released 2025-11-18 | Ethernet preference (6.1). Replay rate limit (7.2). |
| 3.0 | 2025-05-12 | 3.0.0, released 2025-06-03 | First revision for EmberOS 3. MQTT 5 and CBOR replace the EmberOS 2 binary protocol. |
