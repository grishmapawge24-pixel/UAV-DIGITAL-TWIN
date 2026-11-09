// Baseline mock telemetry snapshots, one per UAV id.
// This is the shape the real backend/Digital Twin should eventually match —
// see src/services/api.js for where it plugs in.

export const baselineTelemetry = {
  'UAV-01': {
    uavId: 'UAV-01',
    status: 'AIRBORNE',
    flightTimeMin: 187,
    currentAltitudeFt: 18500,
    currentSpeedKts: 64,
    engine: {
      rpm: 5200,
      load: 78,
      torque: 142,
      throttlePosition: 74,
      manifoldPressure: 98
    },
    thermal: {
      cht: 165,
      egt: 690,
      oilTemperature: 95,
      coolantTemperature: 88,
      intakeTemperature: 42
    },
    fuel: {
      level: 62,
      flow: 18.5,
      pressure: 3.4,
      temperature: 38,
      injectorStatus: 'NOMINAL',
      pumpStatus: 'NOMINAL'
    },
    lubrication: {
      oilPressure: 4.8,
      oilTemperature: 95,
      oilLevel: 88
    },
    mechanical: {
      vibration: 2.1,
      propellerRpm: 2350,
      crankshaftRpm: 5200
    },
    electrical: {
      batteryVoltage: 24.8,
      batteryCurrent: 12.4,
      alternatorVoltage: 27.6,
      alternatorCurrent: 18.2,
      ecuVoltage: 12.1,
      electricalLoad: 64
    },
    sensorHealth: {
      drift: 0.6,
      noise: 1.2,
      confidence: 96,
      signalQuality: 97,
      grounding: 'OK',
      connectionStatus: 'OK',
      calibrationStatus: 'VALID'
    },
    environment: {
      altitudeFt: 18500,
      pressureKpa: 56.2,
      temperatureC: 39,
      humidityPct: 42,
      windSpeedKmh: 18,
      windDirection: 'NE'
    },
    health: {
      index: 92,
      trend: 'STABLE',
      change24h: -1,
      riskLevel: 'LOW',
      rulHours: 142,
      rulConfidence: 89,
      rulTrend: 'STABLE'
    },
    ai: {
      anomalyScore: 12,
      faultProbabilities: [
        { name: 'Cooling degradation', probability: 18 },
        { name: 'Injector abnormality', probability: 9 },
        { name: 'Lubrication issue', probability: 6 },
        { name: 'Sensor drift', probability: 4 }
      ],
      recommendation: 'No immediate action required. Continue scheduled monitoring.'
    },
    mission: {
      missionId: 'MSN-2026-0142',
      missionHealth: 94,
      engineReliability: 96,
      missionRisk: 8,
      progress: 68,
      predictedOutcome: 'NOMINAL COMPLETION'
    },
    flightPath: {
      // normalized 0-1 coordinates within the offline map canvas
      route: [
        [0.12, 0.82], [0.22, 0.6], [0.35, 0.42], [0.5, 0.3],
        [0.63, 0.24], [0.74, 0.32], [0.82, 0.48]
      ],
      currentIndex: 5
    },
    faults: []
  },

  'UAV-02': {
    uavId: 'UAV-02',
    status: 'AIRBORNE',
    flightTimeMin: 96,
    currentAltitudeFt: 13800,
    currentSpeedKts: 57,
    engine: { rpm: 4950, load: 71, torque: 130, throttlePosition: 68, manifoldPressure: 92 },
    thermal: { cht: 178, egt: 742, oilTemperature: 101, coolantTemperature: 93, intakeTemperature: 44 },
    fuel: { level: 48, flow: 16.9, pressure: 2.1, temperature: 41, injectorStatus: 'DEGRADED', pumpStatus: 'NOMINAL' },
    lubrication: { oilPressure: 4.2, oilTemperature: 101, oilLevel: 74 },
    mechanical: { vibration: 3.8, propellerRpm: 2260, crankshaftRpm: 4950 },
    electrical: { batteryVoltage: 23.9, batteryCurrent: 14.1, alternatorVoltage: 26.8, alternatorCurrent: 17.4, ecuVoltage: 12.0, electricalLoad: 70 },
    sensorHealth: { drift: 1.4, noise: 2.6, confidence: 84, signalQuality: 88, grounding: 'OK', connectionStatus: 'OK', calibrationStatus: 'VALID' },
    environment: { altitudeFt: 13800, pressureKpa: 62.4, temperatureC: 44, humidityPct: 31, windSpeedKmh: 24, windDirection: 'SW' },
    health: { index: 71, trend: 'DEGRADING', change24h: -6, riskLevel: 'MODERATE', rulHours: 58, rulConfidence: 76, rulTrend: 'DEGRADING' },
    ai: {
      anomalyScore: 61,
      faultProbabilities: [
        { name: 'Cooling degradation', probability: 74 },
        { name: 'Injector abnormality', probability: 42 },
        { name: 'Lubrication issue', probability: 22 },
        { name: 'Sensor drift', probability: 15 }
      ],
      recommendation: 'Inspect cooling system and fuel injector before next endurance mission.'
    },
    mission: { missionId: 'MSN-2026-0156', missionHealth: 74, engineReliability: 79, missionRisk: 34, progress: 41, predictedOutcome: 'MONITOR — DEGRADED MARGIN' },
    flightPath: { route: [[0.15, 0.75], [0.28, 0.55], [0.4, 0.5], [0.52, 0.4]], currentIndex: 3 },
    faults: []
  },

  'UAV-03': {
    uavId: 'UAV-03',
    status: 'STANDBY',
    flightTimeMin: 0,
    currentAltitudeFt: 0,
    currentSpeedKts: 0,
    engine: { rpm: 0, load: 0, torque: 0, throttlePosition: 0, manifoldPressure: 0 },
    thermal: { cht: 24, egt: 26, oilTemperature: 24, coolantTemperature: 23, intakeTemperature: 24 },
    fuel: { level: 96, flow: 0, pressure: 0, temperature: 24, injectorStatus: 'NOMINAL', pumpStatus: 'NOMINAL' },
    lubrication: { oilPressure: 0, oilTemperature: 24, oilLevel: 95 },
    mechanical: { vibration: 0.1, propellerRpm: 0, crankshaftRpm: 0 },
    electrical: { batteryVoltage: 25.9, batteryCurrent: 0.4, alternatorVoltage: 0, alternatorCurrent: 0, ecuVoltage: 12.3, electricalLoad: 8 },
    sensorHealth: { drift: 0.2, noise: 0.5, confidence: 99, signalQuality: 99, grounding: 'OK', connectionStatus: 'OK', calibrationStatus: 'VALID' },
    environment: { altitudeFt: 0, pressureKpa: 101.1, temperatureC: 31, humidityPct: 55, windSpeedKmh: 6, windDirection: 'N' },
    health: { index: 98, trend: 'STABLE', change24h: 0, riskLevel: 'LOW', rulHours: 210, rulConfidence: 95, rulTrend: 'STABLE' },
    ai: {
      anomalyScore: 3,
      faultProbabilities: [
        { name: 'Cooling degradation', probability: 4 },
        { name: 'Injector abnormality', probability: 2 },
        { name: 'Lubrication issue', probability: 2 },
        { name: 'Sensor drift', probability: 1 }
      ],
      recommendation: 'Pre-flight checks nominal. Ready for tasking.'
    },
    mission: { missionId: '—', missionHealth: 100, engineReliability: 100, missionRisk: 0, progress: 0, predictedOutcome: 'STANDBY' },
    flightPath: { route: [[0.5, 0.5]], currentIndex: 0 },
    faults: []
  }
};

export function getBaselineTelemetry(uavId) {
  return baselineTelemetry[uavId] || baselineTelemetry['UAV-01'];
}
