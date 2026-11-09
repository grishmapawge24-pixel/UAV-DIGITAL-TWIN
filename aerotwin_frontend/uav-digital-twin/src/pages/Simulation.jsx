import React, { useState } from 'react';
import { Play, Loader2 } from 'lucide-react';
import { getSimulationData } from '../services/api.js';

const SCENARIOS = [
  { id: 'highAltitude', label: 'High Altitude', preset: { altitude: 24000, temperature: 15, throttle: 70, load: 65, durationMin: 90 } },
  { id: 'endurance', label: 'Endurance Mission', preset: { altitude: 16000, temperature: 28, throttle: 55, load: 50, durationMin: 240 } },
  { id: 'hotWeather', label: 'Hot Weather', preset: { altitude: 8000, temperature: 46, throttle: 65, load: 68, durationMin: 60 } },
  { id: 'rapidThrottle', label: 'Rapid Throttle Transition', preset: { altitude: 12000, temperature: 30, throttle: 92, load: 88, durationMin: 30 } },
  { id: 'custom', label: 'Custom Mission', preset: null }
];

function Slider({ label, value, min, max, step = 1, unit, onChange }) {
  return (
    <div className="field-group">
      <div className="field-label" style={{ display: 'flex', justifyContent: 'space-between' }}>
        <span>{label}</span>
        <span className="field-value">{value}{unit}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(e) => onChange(Number(e.target.value))} />
    </div>
  );
}

export default function Simulation() {
  const [scenarioId, setScenarioId] = useState('highAltitude');
  const [params, setParams] = useState(SCENARIOS[0].preset);
  const [result, setResult] = useState(null);
  const [running, setRunning] = useState(false);

  function selectScenario(id) {
    setScenarioId(id);
    const scenario = SCENARIOS.find((s) => s.id === id);
    if (scenario.preset) setParams(scenario.preset);
  }

  function updateParam(key, value) {
    setParams((p) => ({ ...p, [key]: value }));
  }

  async function runSimulation() {
    setRunning(true);
    const res = await getSimulationData(params);
    setResult(res.result);
    setRunning(false);
  }

  return (
    <div className="page">
      <div className="page-grid">
        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">MISSION SCENARIO</span>
          </div>
          <div className="panel-body">
            <div className="field-group">
              <div className="field-label" style={{ marginBottom: 4 }}>Scenario</div>
              <div className="select-chip-group">
                {SCENARIOS.map((s) => (
                  <button
                    key={s.id}
                    className={`select-chip${scenarioId === s.id ? ' active' : ''}`}
                    onClick={() => selectScenario(s.id)}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            <Slider label="Altitude" value={params.altitude} min={0} max={30000} step={500} unit=" ft" onChange={(v) => updateParam('altitude', v)} />
            <Slider label="Ambient Temperature" value={params.temperature} min={-20} max={55} unit=" °C" onChange={(v) => updateParam('temperature', v)} />
            <Slider label="Throttle" value={params.throttle} min={0} max={100} unit=" %" onChange={(v) => updateParam('throttle', v)} />
            <Slider label="Load" value={params.load} min={0} max={100} unit=" %" onChange={(v) => updateParam('load', v)} />
            <Slider label="Mission Duration" value={params.durationMin} min={10} max={480} step={10} unit=" min" onChange={(v) => updateParam('durationMin', v)} />

            <button className="btn-primary" onClick={runSimulation} disabled={running} style={{ marginTop: 6, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 7 }}>
              {running ? <Loader2 size={14} className="mono" /> : <Play size={14} />}
              {running ? 'RUNNING SIMULATION…' : 'RUN SIMULATION'}
            </button>
          </div>
        </div>

        <div style={{ minHeight: 0, overflowY: 'auto' }}>
          {result ? (
            <div className="panel" style={{ height: '100%' }}>
              <div className="panel-header"><span className="panel-title">BACKEND MISSION SIMULATION</span></div>
              <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div className="scalar-row"><span className="scalar-label">Overall Risk</span><span className="scalar-value mono">{result.overall_risk}</span></div>
                <div className="scalar-row"><span className="scalar-label">Predicted Fault</span><span className="scalar-value mono">{result.fault_prediction.fault_type || 'No fault detected'}</span></div>
                <div className="scalar-row"><span className="scalar-label">Model Confidence</span><span className="scalar-value mono">{result.fault_prediction.confidence == null ? 'N/A' : `${Math.round(result.fault_prediction.confidence * 100)}%`}</span></div>
                <div className="category">
                  <div className="category-header"><span>PREDICTED HEALTH TRAJECTORY</span></div>
                  <div className="category-body">
                    {result.predicted_trajectory.map((step) => (
                      <div className="scalar-row" key={step.checkpoint}>
                        <span className="scalar-label">{Math.round(step.checkpoint * 100)}% complete</span>
                        <span className="scalar-value mono">{step.predicted_health_score}% · {step.predicted_status}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="fault-card-meta">{result.note}</div>
              </div>
            </div>
          ) : (
            <div className="panel" style={{ height: '100%' }}>
              <div className="empty-state" style={{ margin: 'auto' }}>
                Configure a scenario and run the simulation to see predicted engine trends.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
