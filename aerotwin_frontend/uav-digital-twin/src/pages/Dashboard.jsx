import React, { useEffect, useRef, useState } from 'react';
import UAVViewer from '../components/3d/UAVViewer.jsx';
import UAVInfo from '../components/dashboard/UAVInfo.jsx';
import EnvironmentPanel from '../components/dashboard/EnvironmentPanel.jsx';
import CurrentStatus from '../components/dashboard/CurrentStatus.jsx';
import MissionReliability from '../components/dashboard/MissionReliability.jsx';
import FaultDetection from '../components/dashboard/FaultDetection.jsx';
import EngineTrends from '../components/charts/EngineTrends';
import { uavProfiles } from '../data/uavProfiles.js';
import { getUAVStatus, getEngineData, getFaults } from '../services/api.js';
import { startRealtimeFeed } from '../services/realtime.js';

const HISTORY_LENGTH = 30;

export default function Dashboard({ uavId, onSelectUAV }) {
  const [profile, setProfile] = useState(null);
  const [telemetry, setTelemetry] = useState(null);
  const [faults, setFaults] = useState({ active: [], historical: [] });
  const [loadError, setLoadError] = useState(null);
  const [retryToken, setRetryToken] = useState(0);
  const [selectedComponentId, setSelectedComponentId] = useState(null);
  const [history, setHistory] = useState([]);
  const tickRef = useRef(0);

  useEffect(() => {
    let cancelled = false;
    setSelectedComponentId(null);
    setHistory([]);
    tickRef.current = 0;
    setLoadError(null);

    Promise.all([getUAVStatus(uavId), getEngineData(uavId), getFaults(uavId)]).then(
      ([status, engineData, faultData]) => {
        if (cancelled) return;
        setProfile(status.profile);
        setTelemetry(engineData);
        setFaults(faultData);
      }
    ).catch((error) => {
      if (!cancelled) setLoadError(error.message || 'Unable to load telemetry.');
    });

    return () => {
      cancelled = true;
    };
  }, [uavId, retryToken]);

  useEffect(() => {
    if (!telemetry) return undefined;
    const stop = startRealtimeFeed(telemetry, (next) => setTelemetry(next));
    return stop;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [telemetry?.uavId]);

  const effectiveTelemetry = telemetry;
  const effectiveActiveFaults = faults.active;

  // Rolling history buffer so the trend charts show real motion (built from
  // whatever is currently effective — live feed, or manual override values).
  useEffect(() => {
    if (!effectiveTelemetry) return;
    tickRef.current += 1;
    const t = effectiveTelemetry;
    setHistory((prev) => {
      const sample = {
        t: tickRef.current,
        rpm: t.engine.rpm,
        cht: t.thermal.cht,
        egt: t.thermal.egt,
        oilPressure: t.lubrication.oilPressure,
        fuelFlow: t.fuel.flow,
        vibration: t.mechanical.vibration
      };
      const next = [...prev, sample];
      return next.length > HISTORY_LENGTH ? next.slice(next.length - HISTORY_LENGTH) : next;
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [effectiveTelemetry]);

  if (!profile || !telemetry) {
    if (loadError) {
      return (
        <div className="empty-state" style={{ margin: 'auto', display: 'grid', gap: 10, justifyItems: 'center' }}>
          <strong>Telemetry unavailable</strong>
          <span>{loadError}</span>
          <button type="button" onClick={() => setRetryToken((token) => token + 1)}>Retry</button>
        </div>
      );
    }
    return <div className="empty-state" style={{ margin: 'auto' }}>Loading telemetry…</div>;
  }

  return (
    <div className="dashboard-scroll-wrap" style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'grid', gridTemplateColumns: '310px minmax(560px, 1fr) 320px', gap: 14, alignItems: 'start' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <UAVInfo profile={profile} telemetry={effectiveTelemetry} />
          <EnvironmentPanel
            environment={effectiveTelemetry.environment}
            mechanical={effectiveTelemetry.mechanical}
            flightPath={effectiveTelemetry.flightPath}
          />
          <MissionReliability health={effectiveTelemetry.health} mission={effectiveTelemetry.mission} />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div className="uav-selector" style={{ display: 'flex', alignItems: 'center', gap: 4, background: "var(--bg-plate)", padding: '5px 8px', borderRadius: "var(--radius-md)", border: "1px solid var(--line)" }}>
            <span className="scalar-label" style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-dim)', marginRight: 4 }}>ACTIVE UAV:</span>
            {uavProfiles.map((p) => (
              <button
                key={p.id}
                className={p.id === uavId ? 'active' : ''}
                onClick={() => onSelectUAV(p.id)}
                style={{
                  padding: '4px 10px',
                  fontSize: 11,
                  fontWeight: 700,
                  borderRadius: 4,
                  border: p.id === uavId ? '1px solid var(--ember)' : '1px solid var(--line)',
                  background: p.id === uavId ? 'var(--ember)' : 'var(--bg-panel)',
                  color: p.id === uavId ? '#ffffff' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                {p.name}
              </button>
            ))}
          </div>

          <UAVViewer
            telemetry={effectiveTelemetry}
            activeFaults={effectiveActiveFaults}
            selectedComponentId={selectedComponentId}
            onSelectComponent={setSelectedComponentId}
            onSelectUAV={onSelectUAV}
          />

          <EngineTrends telemetry={effectiveTelemetry} history={history} />

        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <FaultDetection activeFaults={effectiveActiveFaults} ai={effectiveTelemetry.ai} />
          <CurrentStatus telemetry={effectiveTelemetry} limits={profile.operatingLimits} />
        </div>
      </div>
    </div>
  );
}
