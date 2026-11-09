// Manual parameter override support.
//
// Lets an operator type/slide custom values for key engine parameters to
// demo fault-detection behavior on demand instead of waiting for the mock
// real-time feed to drift into an interesting state. Overrides are applied
// on top of whatever the live feed is doing (see applyOverrides), and any
// overridden value that crosses into 'major'/'critical' territory gets a
// synthetic fault injected into the same shape the fault list/3D twin
// already expect (see buildManualFaults) — so the effect is visible
// end-to-end: sensor tiles, current status, 3D component highlight, and the
// AI Engine Diagnostics panel.

import { statusForMax, statusForMin, statusForRange } from './status.js';
import { resolveFaultMeta } from '../data/mockFaults.js';

export const OVERRIDE_FIELDS = [
  {
    key: 'rpm',
    label: 'Engine RPM',
    unit: 'rpm',
    path: ['engine', 'rpm'],
    min: 0,
    max: 7500,
    step: 50,
    getStatus: (v, limits) => statusForMax(v, limits.rpmMax),
    faultType: 'rpmAbnormality'
  },
  {
    key: 'cht',
    label: 'Cylinder Head Temp',
    unit: '°C',
    path: ['thermal', 'cht'],
    min: 0,
    max: 260,
    step: 1,
    getStatus: (v, limits) => statusForMax(v, limits.chtMax),
    faultType: 'overheating'
  },
  {
    key: 'egt',
    label: 'Exhaust Gas Temp',
    unit: '°C',
    path: ['thermal', 'egt'],
    min: 0,
    max: 1000,
    step: 5,
    getStatus: (v, limits) => statusForMax(v, limits.egtMax),
    faultType: 'combustionInstability'
  },
  {
    key: 'oilPressure',
    label: 'Oil Pressure',
    unit: 'bar',
    path: ['lubrication', 'oilPressure'],
    min: 0,
    max: 7,
    step: 0.1,
    getStatus: (v, limits) => statusForRange(v, limits.oilPressureMin, limits.oilPressureMax),
    faultType: 'lowOilPressure'
  },
  {
    key: 'oilTemperature',
    label: 'Oil Temperature',
    unit: '°C',
    path: ['lubrication', 'oilTemperature'],
    min: 0,
    max: 160,
    step: 1,
    getStatus: (v, limits) => statusForMax(v, limits.oilTempMax),
    faultType: 'highOilTemperature'
  },
  {
    key: 'fuelFlow',
    label: 'Fuel Flow',
    unit: 'L/h',
    path: ['fuel', 'flow'],
    min: 0,
    max: 40,
    step: 0.5,
    getStatus: (v) => (v < 4 || v > 32 ? 'critical' : v < 8 || v > 26 ? 'major' : 'normal'),
    faultType: 'abnormalFuelFlow'
  },
  {
    key: 'vibration',
    label: 'Vibration',
    unit: 'mm/s',
    path: ['mechanical', 'vibration'],
    min: 0,
    max: 12,
    step: 0.1,
    getStatus: (v, limits) => statusForMax(v, limits.vibrationMax),
    faultType: 'abnormalVibration'
  },
  {
    key: 'batteryVoltage',
    label: 'Battery Voltage',
    unit: 'V',
    path: ['electrical', 'batteryVoltage'],
    min: 10,
    max: 30,
    step: 0.1,
    getStatus: (v, limits) => statusForMin(v, limits.batteryVoltageMin),
    faultType: 'batteryUndervoltage'
  }
];

function readPath(obj, path) {
  let v = obj;
  for (const k of path) v = v?.[k];
  return v;
}

/** Snapshot the current live telemetry values for every override-able field, used to seed the sliders when manual mode is switched on. */
export function snapshotOverrideValues(telemetry) {
  const values = {};
  for (const f of OVERRIDE_FIELDS) {
    const v = readPath(telemetry, f.path);
    values[f.key] = typeof v === 'number' ? Math.round(v * 100) / 100 : 0;
  }
  return values;
}

/** Returns a deep-cloned copy of telemetry with override values written into their target fields. */
export function applyOverrides(telemetry, overrides) {
  if (!overrides || Object.keys(overrides).length === 0) return telemetry;
  const next = JSON.parse(JSON.stringify(telemetry));
  for (const f of OVERRIDE_FIELDS) {
    const val = overrides[f.key];
    if (val == null || Number.isNaN(val)) continue;
    let target = next;
    for (let i = 0; i < f.path.length - 1; i++) target = target[f.path[i]];
    target[f.path[f.path.length - 1]] = val;
  }
  return next;
}

/** Build synthetic fault entries (same shape as mockFaults) for any manually-set value that has crossed into 'major' or 'critical' territory. */
export function buildManualFaults(overrides, limits) {
  const faults = [];
  for (const f of OVERRIDE_FIELDS) {
    const val = overrides[f.key];
    if (val == null || Number.isNaN(val)) continue;
    const status = f.getStatus(val, limits);
    if (status !== 'major' && status !== 'critical') continue;
    const meta = resolveFaultMeta(f.faultType);
    faults.push({
      id: `MANUAL-${f.key}`,
      type: f.faultType,
      severity: status,
      detectedAt: new Date().toISOString(),
      confidence: status === 'critical' ? 96 : 82,
      probableCause: `Operator-set test value for ${f.label}: ${val}${f.unit} (manual override, not a live sensor reading).`,
      affectedComponents: [meta.componentId],
      recommendedAction: 'Manual override active for demo/testing — turn off Manual Override to resume live telemetry.'
    });
  }
  return faults;
}
