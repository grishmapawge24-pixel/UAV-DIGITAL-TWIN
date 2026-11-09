// Fault taxonomy. Each entry maps a fault type to the component it belongs
// to (componentId must match an id in uavProfiles.uavComponents).
//
// To add a new fault type: add an entry here with a unique `type`, its
// `componentId`, and default `probableCause` / `recommendedAction` text.
// Then reference that `type` from an active fault object below (or from
// a real backend payload later — the shape is identical).

export const faultCatalog = {
  // Engine
  misfire: { componentId: 'engine', label: 'Engine Misfire', category: 'Engine' },
  injectorAbnormality: { componentId: 'fuelSystem', label: 'Injector Abnormality', category: 'Fuel' },
  combustionInstability: { componentId: 'engine', label: 'Combustion Instability', category: 'Engine' },
  overheating: { componentId: 'engine', label: 'Engine Overheating', category: 'Thermal' },
  rpmAbnormality: { componentId: 'engine', label: 'RPM Abnormality', category: 'Engine' },
  engineDegradation: { componentId: 'engine', label: 'Engine Degradation', category: 'Engine' },

  // Fuel
  lowFuelPressure: { componentId: 'fuelSystem', label: 'Low Fuel Pressure', category: 'Fuel' },
  abnormalFuelFlow: { componentId: 'fuelSystem', label: 'Abnormal Fuel Flow', category: 'Fuel' },
  fuelPumpFailure: { componentId: 'fuelSystem', label: 'Fuel Pump Failure', category: 'Fuel' },
  fuelSensorFailure: { componentId: 'sensors', label: 'Fuel Sensor Failure', category: 'Sensor' },

  // Lubrication
  lowOilPressure: { componentId: 'lubricationSystem', label: 'Low Oil Pressure', category: 'Lubrication' },
  highOilTemperature: { componentId: 'lubricationSystem', label: 'High Oil Temperature', category: 'Lubrication' },
  lowOilLevel: { componentId: 'lubricationSystem', label: 'Low Oil Level', category: 'Lubrication' },
  lubricationDegradation: { componentId: 'lubricationSystem', label: 'Lubrication Degradation', category: 'Lubrication' },

  // Cooling
  highCoolantTemperature: { componentId: 'coolingSystem', label: 'High Coolant Temperature', category: 'Thermal' },
  coolingDegradation: { componentId: 'coolingSystem', label: 'Cooling Degradation', category: 'Thermal' },
  coolingFlowAbnormality: { componentId: 'coolingSystem', label: 'Cooling Flow Abnormality', category: 'Thermal' },

  // Mechanical
  abnormalVibration: { componentId: 'engine', label: 'Abnormal Vibration', category: 'Mechanical' },
  propellerImbalance: { componentId: 'propeller', label: 'Propeller Imbalance', category: 'Mechanical' },
  bearingDegradation: { componentId: 'engine', label: 'Bearing Degradation', category: 'Mechanical' },
  crankshaftAbnormality: { componentId: 'engine', label: 'Crankshaft Abnormality', category: 'Mechanical' },

  // Electrical
  batteryUndervoltage: { componentId: 'battery', label: 'Battery Undervoltage', category: 'Electrical' },
  batteryOvertemperature: { componentId: 'battery', label: 'Battery Overtemperature', category: 'Electrical' },
  alternatorAbnormality: { componentId: 'electricalSystem', label: 'Alternator Abnormality', category: 'Electrical' },
  excessiveCurrent: { componentId: 'electricalSystem', label: 'Excessive Current', category: 'Electrical' },
  powerSupplyProblem: { componentId: 'electricalSystem', label: 'Power Supply Problem', category: 'Electrical' },
  groundingProblem: { componentId: 'electricalSystem', label: 'Grounding Problem', category: 'Electrical' },
  electricalConnectionFault: { componentId: 'electricalSystem', label: 'Electrical Connection Fault', category: 'Electrical' },

  // Sensors
  sensorDrift: { componentId: 'sensors', label: 'Sensor Drift', category: 'Sensor' },
  sensorNoise: { componentId: 'sensors', label: 'Sensor Noise', category: 'Sensor' },
  sensorFailure: { componentId: 'sensors', label: 'Sensor Failure', category: 'Sensor' },
  sensorConnectionFailure: { componentId: 'sensors', label: 'Sensor Connection Failure', category: 'Sensor' },
  sensorCalibrationProblem: { componentId: 'sensors', label: 'Sensor Calibration Problem', category: 'Sensor' },
  sensorSupplyVoltageProblem: { componentId: 'sensors', label: 'Sensor Supply Voltage Problem', category: 'Sensor' }
};

// Active + historical faults per UAV. `severity` is one of
// 'warning' | 'major' | 'critical'.
export const mockFaultsByUAV = {
  'UAV-01': {
    active: [],
    historical: [
      {
        id: 'FLT-0091',
        type: 'sensorNoise',
        severity: 'warning',
        detectedAt: '2026-08-30T06:12:00Z',
        clearedAt: '2026-08-30T06:41:00Z',
        probableCause: 'Transient EMI near EGT sensor harness.',
        affectedComponents: ['sensors', 'engine'],
        recommendedAction: 'Inspect harness shielding at next ground stop.'
      }
    ]
  },
  'UAV-02': {
    active: [
      {
        id: 'FLT-0142',
        type: 'coolingDegradation',
        severity: 'major',
        detectedAt: '2026-09-02T04:05:00Z',
        confidence: 87,
        probableCause: 'Coolant flow restriction reducing heat rejection capacity.',
        affectedComponents: ['coolingSystem', 'engine'],
        recommendedAction: 'Inspect cooling system before next endurance mission.'
      },
      {
        id: 'FLT-0143',
        type: 'injectorAbnormality',
        severity: 'warning',
        detectedAt: '2026-09-02T04:22:00Z',
        confidence: 62,
        probableCause: 'Injector pulse-width deviation on cylinder 3.',
        affectedComponents: ['fuelSystem'],
        recommendedAction: 'Schedule injector diagnostic on ground.'
      }
    ],
    historical: [
      {
        id: 'FLT-0098',
        type: 'sensorDrift',
        severity: 'warning',
        detectedAt: '2026-08-28T11:00:00Z',
        clearedAt: '2026-08-28T13:10:00Z',
        probableCause: 'Oil temp sensor drift beyond calibration band.',
        affectedComponents: ['sensors', 'lubricationSystem'],
        recommendedAction: 'Recalibrated on ground — no further action.'
      }
    ]
  },
  'UAV-03': {
    active: [],
    historical: []
  }
};

export function getFaultsForUAV(uavId) {
  return mockFaultsByUAV[uavId] || { active: [], historical: [] };
}

export function resolveFaultMeta(type) {
  return faultCatalog[type] || { componentId: 'engine', label: type, category: 'Engine' };
}

export const severityRank = { critical: 3, major: 2, warning: 1 };

// Highest-severity active fault per component, for 3D highlighting.
export function faultsByComponent(activeFaults) {
  const map = {};
  for (const fault of activeFaults) {
    const meta = resolveFaultMeta(fault.type);
    for (const compId of fault.affectedComponents?.length ? fault.affectedComponents : [meta.componentId]) {
      const existing = map[compId];
      if (!existing || severityRank[fault.severity] > severityRank[existing.severity]) {
        map[compId] = fault;
      }
    }
  }
  return map;
}
