import { getUAVProfile, uavProfiles } from '../data/uavProfiles.js';

// Override this for deployments; local development works without a frontend
// .env file once the FastAPI server is running on port 8000.
export const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api').replace(/\/$/, '');

const flightCache = new Map();
const celsius = (f) => (Number.isFinite(f) ? Number(((f - 32) * 5 / 9).toFixed(1)) : 'N/A');
const bar = (psi) => (Number.isFinite(psi) ? Number((psi * 0.0689476).toFixed(2)) : 'N/A');
const litresPerHour = (gph) => (Number.isFinite(gph) ? Number((gph * 3.78541).toFixed(1)) : 'N/A');
const value = (values, name, fallback = 'N/A') => values?.[name] ?? fallback;
const percent = (part, total) => Number.isFinite(part) && Number.isFinite(total) && total > 0
  ? Math.max(0, Math.min(100, Math.round((part / total) * 100)))
  : 'N/A';

async function request(path, options) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `API request failed (${response.status})`);
  }
  return response.json();
}

async function flightForUav(uavId) {
  if (flightCache.has(uavId)) return flightCache.get(uavId);
  const list = await request('/flights?page=1&page_size=25');
  const flight = list.flights[(uavProfiles.findIndex((p) => p.id === uavId) + list.flights.length) % list.flights.length];
  if (!flight) throw new Error('The backend returned no flights.');
  flightCache.set(uavId, flight.flight_id);
  return flight.flight_id;
}

function severityFor(status) {
  return status === 'CRITICAL' ? 'critical' : status === 'WARNING' ? 'warning' : 'normal';
}

export function mergeTelemetryPoint(base, point, health = base.health) {
  const v = point.values || point;
  const rpm = value(v, 'E1 RPM', base.engine.rpm);
  const cht = celsius(value(v, 'E1 CHT1', NaN));
  const egt = celsius(value(v, 'E1 EGT1', NaN));
  const oilTemp = celsius(value(v, 'E1 OilT', NaN));
  const fuelLeft = value(v, 'FQtyL', NaN);
  const fuelRight = value(v, 'FQtyR', NaN);
  const altitude = value(v, 'AltMSL', base.currentAltitudeFt);
  const speed = value(v, 'IAS', base.currentSpeedKts);
  const fuelLevel = percent((fuelLeft || 0) + (fuelRight || 0), 108);

  return {
    ...base,
    flightTimeMin: Number.isFinite(point.timestep) ? Math.round(point.timestep / 60) : base.flightTimeMin,
    currentAltitudeFt: altitude,
    currentSpeedKts: speed,
    engine: { ...base.engine, rpm, load: 'N/A', torque: 'N/A', throttlePosition: 'N/A', manifoldPressure: 'N/A' },
    thermal: { ...base.thermal, cht, egt, oilTemperature: oilTemp, coolantTemperature: 'N/A', intakeTemperature: celsius(value(v, 'OAT', NaN)) },
    fuel: { ...base.fuel, level: fuelLevel, flow: litresPerHour(value(v, 'E1 FFlow', NaN)), pressure: 'N/A', temperature: 'N/A', injectorStatus: 'DATA NOT AVAILABLE', pumpStatus: 'DATA NOT AVAILABLE' },
    lubrication: { ...base.lubrication, oilPressure: bar(value(v, 'E1 OilP', NaN)), oilTemperature: oilTemp, oilLevel: 'N/A' },
    mechanical: { ...base.mechanical, vibration: 'DATA NOT AVAILABLE', propellerRpm: 'DATA NOT AVAILABLE', crankshaftRpm: rpm },
    electrical: { ...base.electrical, batteryVoltage: value(v, 'volt1', 'N/A'), batteryCurrent: value(v, 'amp1', 'N/A'), alternatorVoltage: value(v, 'volt2', 'N/A'), alternatorCurrent: value(v, 'amp2', 'N/A'), ecuVoltage: 'N/A', electricalLoad: 'N/A' },
    environment: { ...base.environment, altitudeFt: altitude, temperatureC: celsius(value(v, 'OAT', NaN)), pressureKpa: 'N/A', humidityPct: 'DATA NOT AVAILABLE', windSpeedKmh: 'DATA NOT AVAILABLE', windDirection: 'DATA NOT AVAILABLE' },
    health
  };
}

function makeTelemetry(uavId, flightId, telemetry, health, rul, fault) {
  const profile = getUAVProfile(uavId);
  const last = telemetry.points.at(-1);
  const healthIndex = health.health_score;
  const base = {
    uavId,
    flightId,
    status: 'HISTORICAL REPLAY',
    flightTimeMin: 0,
    currentAltitudeFt: 0,
    currentSpeedKts: 0,
    engine: {}, thermal: {}, fuel: {}, lubrication: {}, mechanical: {}, electrical: {}, environment: {},
    sensorHealth: { drift: 'DATA NOT AVAILABLE', noise: 'DATA NOT AVAILABLE', confidence: 'N/A', signalQuality: 'N/A', grounding: 'DATA NOT AVAILABLE', connectionStatus: 'DATA NOT AVAILABLE', calibrationStatus: 'DATA NOT AVAILABLE' },
    health: {
      index: healthIndex,
      trend: health.health_status === 'CRITICAL' ? 'CRITICAL' : health.health_status === 'WARNING' ? 'DEGRADING' : 'STABLE',
      change24h: 'N/A', riskLevel: health.health_status, rulHours: rul.estimated_remaining_flights ?? 'N/A', rulConfidence: rul.confidence || 'LOW', rulTrend: health.health_status
    },
    ai: {
      anomalyScore: Number.isFinite(health.anomaly_score) ? Math.round(Math.max(0, Math.min(100, health.anomaly_score * 100))) : 'N/A',
      faultProbabilities: fault.fault_detected ? [{ name: fault.fault_type, probability: Math.round((fault.confidence || 0) * 100) }] : [],
      recommendation: fault.recommended_action || 'No fault detected by the trained model.'
    },
    mission: { missionId: `NGAFID-${flightId}`, missionHealth: healthIndex, engineReliability: healthIndex, missionRisk: 100 - healthIndex, progress: 100, predictedOutcome: health.health_status === 'NORMAL' ? 'HISTORICAL FLIGHT REVIEW' : 'MAINTENANCE REVIEW REQUIRED' },
    // NGAFID contains no GPS track. This is only a neutral UI route, never a claimed flight path.
    flightPath: { route: [[0.12, 0.82], [0.32, 0.58], [0.54, 0.4], [0.8, 0.22]], currentIndex: 3 },
    profile
  };
  return mergeTelemetryPoint(base, last, base.health);
}

export async function getUAVProfiles() {
  return uavProfiles;
}

export async function getEngineData(uavId) {
  const flightId = await flightForUav(uavId);
  const [telemetry, health, rul, fault] = await Promise.all([
    request(`/flights/${flightId}/telemetry?max_points=500`),
    request(`/flights/${flightId}/health`),
    request(`/flights/${flightId}/rul`),
    request(`/flights/${flightId}/faults`)
  ]);
  return makeTelemetry(uavId, flightId, telemetry, health, rul, fault);
}

export async function getUAVStatus(uavId) {
  const telemetry = await getEngineData(uavId);
  return { uavId, status: telemetry.status, flightTimeMin: telemetry.flightTimeMin, currentAltitudeFt: telemetry.currentAltitudeFt, currentSpeedKts: telemetry.currentSpeedKts, profile: getUAVProfile(uavId) };
}

export async function getFaults(uavId) {
  const flightId = await flightForUav(uavId);
  const fault = await request(`/flights/${flightId}/faults`);
  if (!fault.fault_detected) return { active: [], historical: [] };
  return {
    active: [{
      id: `NGAFID-${flightId}`, type: fault.fault_type, severity: fault.severity || 'warning',
      detectedAt: new Date().toISOString(), confidence: Math.round((fault.confidence || 0) * 100),
      probableCause: `Model prediction from historical flight ${flightId}.`,
      affectedComponents: [fault.uav_component || 'engine'], recommendedAction: fault.recommended_action || 'Inspect before the next flight.'
    }],
    historical: []
  };
}

export async function getMissionData(uavId) {
  const telemetry = await getEngineData(uavId);
  return { mission: telemetry.mission, flightPath: telemetry.flightPath, health: telemetry.health };
}

export async function getSimulationData(params, uavId = 'UAV-01') {
  const flightId = await flightForUav(uavId);
  const result = await request('/missions/simulate', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ base_flight_id: flightId, duration_scale: params.durationMin / 60, stress_factor: Math.max(0.5, Math.min(3, (params.throttle + params.load) / 140)) })
  });
  return { params, result };
}

export async function getMissionReplay(uavId) {
  const flightId = await flightForUav(uavId);
  const [replay, health] = await Promise.all([request(`/replay/${flightId}?max_points=120`), request(`/flights/${flightId}/health`)]);
  const frames = replay.points.map((point, index) => {
    const t = mergeTelemetryPoint({ engine: {}, thermal: {}, lubrication: {}, fuel: {}, mechanical: {}, electrical: {}, environment: {}, health: { index: health.health_score } }, point, { index: health.health_score });
    return { t: point.timestep, rpm: t.engine.rpm, cht: t.thermal.cht, egt: t.thermal.egt, altitudeFt: t.currentAltitudeFt, fuelPct: t.fuel.level, vibration: 'N/A', health: health.health_score, routeIndex: Math.min(3, Math.floor(index * 4 / replay.points.length)) };
  });
  return { missionId: `NGAFID-${flightId}`, date: 'Historical NGAFID data', durationMin: Math.round((replay.points.at(-1)?.timestep || 0) / 60), route: [[0.12, 0.82], [0.32, 0.58], [0.54, 0.4], [0.8, 0.22]], frames, events: [], note: replay.note };
}

// Uses a trailing window of the same historical flight being replayed. This
// does not send edited dashboard values back to the model.
export async function getReplayAnalysis(flightId, endIndex) {
  return request(`/analyze/${flightId}?end_index=${endIndex}&window=120`);
}

export function mergeAnalysis(telemetry, analysis) {
  if (!telemetry || !analysis) return telemetry;
  const health = analysis.health || {};
  const reliability = analysis.mission_reliability_index;
  return {
    ...telemetry,
    status: analysis.risk_level || telemetry.status,
    health: {
      ...telemetry.health,
      index: health.health_score ?? telemetry.health.index,
      trend: health.health_status === 'CRITICAL' ? 'CRITICAL' : health.health_status === 'WARNING' ? 'DEGRADING' : 'STABLE',
      reliabilityIndex: reliability,
      sensorQuality: analysis.sensor_quality
    },
    ai: {
      ...telemetry.ai,
      anomalyScore: Number.isFinite(health.anomaly_score) ? Math.max(0, Math.round(health.anomaly_score * 100)) : 'N/A',
      recommendation: analysis.engineering_advisories?.[0]?.interpretation || telemetry.ai.recommendation
    },
    mission: {
      ...telemetry.mission,
      missionHealth: health.health_score ?? telemetry.mission.missionHealth,
      engineReliability: reliability ?? telemetry.mission.engineReliability,
      missionRisk: Number.isFinite(reliability) ? 100 - reliability : telemetry.mission.missionRisk,
      predictedOutcome: analysis.risk_level === 'NORMAL' ? 'CONTINUE HISTORICAL REPLAY' : 'MAINTENANCE REVIEW REQUIRED'
    }
  };
}

export { severityFor };
