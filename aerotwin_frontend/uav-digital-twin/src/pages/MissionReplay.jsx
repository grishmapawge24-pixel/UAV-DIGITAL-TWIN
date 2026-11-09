import React, { useEffect, useRef, useState } from 'react';
import { Play, Pause, RotateCcw } from 'lucide-react';
import OfflineMap from '../components/dashboard/OfflineMap.jsx';
import { getMissionReplay } from '../services/api.js';
import { severityHex } from '../utils/status.js';

function Readout({ label, value, unit }) {
  return (
    <div className="panel" style={{ padding: '10px 12px' }}>
      <div className="scalar-unit" style={{ marginBottom: 4 }}>{label}</div>
      <div className="mono" style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>
        {value}
        <span className="scalar-unit" style={{ fontSize: 11, marginLeft: 4 }}>{unit}</span>
      </div>
    </div>
  );
}

export default function MissionReplay({ uavId }) {
  const [data, setData] = useState(null);
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const intervalRef = useRef(null);

  useEffect(() => {
    setData(null);
    setStep(0);
    setPlaying(false);
    getMissionReplay(uavId).then(setData);
  }, [uavId]);

  useEffect(() => {
    if (playing && data) {
      intervalRef.current = setInterval(() => {
        setStep((s) => {
          if (s >= data.frames.length - 1) {
            setPlaying(false);
            return s;
          }
          return s + 1;
        });
      }, 250);
    }
    return () => clearInterval(intervalRef.current);
  }, [playing, data]);

  if (!data) {
    return <div className="page"><div className="empty-state">Loading mission replay…</div></div>;
  }

  const frame = data.frames[step];

  return (
    <div className="page">
      <div className="page-grid" style={{ gridTemplateColumns: '300px 1fr' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, minHeight: 0 }}>
          <div className="panel" style={{ flex: '0 0 auto' }}>
            <div className="panel-header">
              <span className="panel-title">MISSION REPLAY</span>
            </div>
            <div className="panel-body">
              <div className="scalar-row"><span className="scalar-label">Mission ID</span><span className="scalar-value mono">{data.missionId}</span></div>
              <div className="scalar-row"><span className="scalar-label">Date</span><span className="scalar-value mono">{data.date}</span></div>
              <div className="scalar-row"><span className="scalar-label">Duration</span><span className="scalar-value mono">{data.durationMin} min</span></div>
            </div>
          </div>
          <div className="map-wrap" style={{ flex: 1 }}>
            <OfflineMap route={data.route} currentIndex={frame.routeIndex} />
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, minHeight: 0 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 8 }}>
            <Readout label="RPM" value={frame.rpm} unit="rpm" />
            <Readout label="CHT" value={frame.cht} unit="°C" />
            <Readout label="EGT" value={frame.egt} unit="°C" />
            <Readout label="Altitude" value={frame.altitudeFt.toLocaleString()} unit="ft" />
            <Readout label="Fuel" value={frame.fuelPct} unit="%" />
            <Readout label="Health" value={frame.health} unit="%" />
          </div>

          <div className="panel" style={{ flex: '0 0 auto', padding: 14 }}>
            <div className="transport-controls">
              <button className="transport-btn" onClick={() => { setStep(0); setPlaying(false); }} aria-label="Reset">
                <RotateCcw size={15} />
              </button>
              <button className="transport-btn" onClick={() => setPlaying((p) => !p)} aria-label={playing ? 'Pause' : 'Play'}>
                {playing ? <Pause size={15} /> : <Play size={15} />}
              </button>
              <div className="timeline-track">
                <input
                  className="timeline-slider"
                  type="range"
                  min={0}
                  max={data.frames.length - 1}
                  value={step}
                  onChange={(e) => { setStep(Number(e.target.value)); setPlaying(false); }}
                />
                <div className="timeline-events">
                  {data.events.map((ev, i) => (
                    <div
                      key={i}
                      className="timeline-event-marker"
                      title={ev.label}
                      style={{
                        left: `${(ev.atStep / (data.frames.length - 1)) * 100}%`,
                        background: severityHex[ev.severity]
                      }}
                    />
                  ))}
                </div>
              </div>
              <span className="mono scalar-unit" style={{ minWidth: 54, textAlign: 'right' }}>
                {step + 1}/{data.frames.length}
              </span>
            </div>
          </div>

          <div className="panel" style={{ flex: 1, minHeight: 0 }}>
            <div className="panel-header">
              <span className="panel-title">FAULT EVENTS ON TIMELINE</span>
            </div>
            <div className="panel-body">
              {data.events.length === 0 ? (
                <div className="empty-state">No fault events recorded during this mission.</div>
              ) : (
                data.events.map((ev, i) => (
                  <div key={i} className={`fault-card ${ev.severity}`}>
                    <div className="fault-card-top">
                      <span className="fault-card-title">{ev.label}</span>
                      <span className={`badge ${ev.severity}`}>{ev.severity.toUpperCase()}</span>
                    </div>
                    <div className="fault-card-meta">Occurred at step {ev.atStep} of {data.frames.length}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
