# Sensor compatibility report

Generated from the currently available project data on 2026-09-09. The only
raw dataset present in this workspace is NGAFID (`data/2days/2days`). CAFUC2
and MALE Propulsion System Experimental Data were not found, so they are not
combined with NGAFID and are not used for training.

| Parameter group | Dataset | Available | Native unit | Used for training |
|---|---|---:|---|---:|
| RPM, CHT1-4, EGT1-4 | NGAFID | Yes | RPM; °F | Yes |
| Oil temperature / pressure | NGAFID | Yes | °F; psi | Yes |
| Fuel flow / quantities | NGAFID | Yes | gal/hr; gal | Yes |
| OAT, IAS, VSpd, normal acceleration, altitude | NGAFID | Yes | dataset-native | Yes (environment features) |
| Voltage / current | NGAFID | Yes | V; A | Yes |
| Vibration, injection timing | NGAFID | No | — | No |
| CAFUC2 | Workspace | No raw files found | — | No |
| MALE propulsion experimental data | Workspace | No raw files found | — | No |

The NGAFID raw array has 23 channels and `stats.csv` names 26 fields because
`timestep` and `cluster` are metadata, not telemetry channels. The checked
mapping is recorded in `data/config/sensor_mapping.json`. Sampling frequency
is not asserted because a time-unit field was not present in the inspected
raw array; replay uses sample indices, not seconds.
