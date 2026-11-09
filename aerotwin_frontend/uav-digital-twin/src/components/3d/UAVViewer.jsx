import React, { Suspense, useMemo, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, ContactShadows } from '@react-three/drei';
import UAVModel from './UAVModel.jsx';
import { uavComponents, uavProfiles } from '../../data/uavProfiles.js';
import { resolveFaultMeta, faultsByComponent } from '../../data/mockFaults.js';
import { baselineTelemetry } from '../../data/mockUAVData.js';
import { X, Check, ArrowRight, Gauge, Activity, Zap } from 'lucide-react';

const COMPONENT_DETAILS = {
  engine: {
    description: 'Rotax aero-piston 4-cylinder engine — primary propulsion source. Drives the propeller shaft, coolant pump, and alternator with electronic wastegate control.',
    parameterKeys: ['RPM', 'CHT', 'EGT', 'Manifold Pressure', 'Load', 'Torque']
  },
  fuelSystem: {
    description: 'Delivers fuel from tank to injectors under regulated pressure; includes pump and injector array.',
    parameterKeys: ['Fuel Flow', 'Fuel Pressure', 'Fuel Level', 'Injector Status']
  },
  coolingSystem: {
    description: 'Rejects heat from cylinder heads via coolant loop and radiator to keep CHT within limits.',
    parameterKeys: ['Coolant Temperature', 'CHT']
  },
  lubricationSystem: {
    description: 'Circulates oil to reduce friction and carry heat away from moving engine components.',
    parameterKeys: ['Oil Pressure', 'Oil Temperature', 'Oil Level']
  },
  electricalSystem: {
    description: 'Distributes electrical power from the alternator to avionics, sensors, and actuators.',
    parameterKeys: ['Alternator Voltage', 'Alternator Current', 'Electrical Load']
  },
  battery: {
    description: 'Backup electrical power source, sustains avionics and ECU during alternator dropouts.',
    parameterKeys: ['Battery Voltage', 'Battery Current']
  },
  avionics: {
    description: 'Flight control computer, ECU, and communication systems governing autonomous flight.',
    parameterKeys: ['ECU Voltage', 'Signal Quality']
  },
  sensors: {
    description: 'Distributed sensor suite feeding telemetry into the Digital Twin and AI/ML diagnostic models.',
    parameterKeys: ['Sensor Confidence', 'Signal Quality', 'Calibration Status']
  },
  propeller: {
    description: 'Converts engine shaft power into thrust. Imbalance here shows up as elevated vibration.',
    parameterKeys: ['Propeller RPM', 'Vibration']
  }
};

const ALL_UAV_ENGINES = [
  {
    uavId: 'UAV-01',
    name: 'UAV-01 Falcon Alpha',
    engineModel: 'Rotax 914 Turbocharged',
    engineType: 'Turbocharged 4-cylinder 4-stroke Aero-Piston with automatic wastegate',
    powerHp: '115 HP @ 5800 RPM',
    displacement: '1,211 cc',
    compression: '9.0:1',
    turbo: 'Garrett TLS with automatic altitude compensation boost control',
    cooling: 'Liquid-cooled cylinder heads, air-cooled cylinders',
    fuelDelivery: 'Dual constant-depression carburetors with manifold boost sensing',
    status: 'AIRBORNE - NOMINAL',
    statusBadge: 'normal',
    limits: { rpmMax: 5800, chtMax: 190, egtMax: 820, oilPress: '2.0 - 5.5 bar' },
    telemetry: baselineTelemetry['UAV-01']
  },
  {
    uavId: 'UAV-02',
    name: 'UAV-02 Sea Guardian',
    engineModel: 'Rotax 912 iS Sport',
    engineType: 'Naturally Aspirated 4-cylinder with Dual Redundant Engine Control Units (ECU)',
    powerHp: '100 HP @ 5500 RPM',
    displacement: '1,352 cc',
    compression: '10.8:1',
    turbo: 'None (Optimized intake runner with dual throttle bodies)',
    cooling: 'Integrated liquid / air hybrid with dual radiator loops',
    fuelDelivery: 'Electronic multi-point sequential fuel injection with dual fuel pumps',
    status: 'AIRBORNE - CAUTION',
    statusBadge: 'warning',
    limits: { rpmMax: 5500, chtMax: 185, egtMax: 800, oilPress: '1.8 - 5.0 bar' },
    telemetry: baselineTelemetry['UAV-02']
  },
  {
    uavId: 'UAV-03',
    name: 'UAV-03 Sky Sentinel',
    engineModel: 'Rotax 914 High-Altitude Recon',
    engineType: 'Turbocharged 4-cylinder with high-density intercooler and high-altitude mapping',
    powerHp: '115 HP @ 5800 RPM',
    displacement: '1,211 cc',
    compression: '9.0:1',
    turbo: 'Garrett TLS Turbo with dual high-altitude wastegate actuators',
    cooling: 'High-altitude radiator matrix with glycol-water mix',
    fuelDelivery: 'Direct pressurized fuel rail with altitude barometric enrichment',
    status: 'STANDBY - READY',
    statusBadge: 'info',
    limits: { rpmMax: 5800, chtMax: 190, egtMax: 820, oilPress: '2.0 - 5.5 bar' },
    telemetry: baselineTelemetry['UAV-03']
  }
];

export default function UAVViewer({ telemetry, activeFaults, selectedComponentId, onSelectComponent, onSelectUAV }) {
  const [engineTabUAV, setEngineTabUAV] = useState(telemetry.uavId || 'UAV-01');
  const faultsByComp = useMemo(() => faultsByComponent(activeFaults), [activeFaults]);

  const selected = uavComponents.find((c) => c.id === selectedComponentId);
  const selectedFault = selectedComponentId ? faultsByComp[selectedComponentId] : null;
  const detail = selectedComponentId ? COMPONENT_DETAILS[selectedComponentId] : null;

  const currentEngineInfo = useMemo(() => {
    return ALL_UAV_ENGINES.find((e) => e.uavId === engineTabUAV) || ALL_UAV_ENGINES[0];
  }, [engineTabUAV]);

  const liveEngineData = engineTabUAV === telemetry.uavId ? telemetry : currentEngineInfo.telemetry;

  return (
    <div className="panel viewer-panel" style={{ minHeight: 400 }}>
      <div className="panel-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="panel-title">INTERACTIVE 3D UAV DIGITAL TWIN</span>
          <span className="badge normal" style={{ fontSize: 9 }}>{telemetry.uavId}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <button
            onClick={() => onSelectComponent(selectedComponentId === 'engine' ? null : 'engine')}
            className={`btn-secondary${selectedComponentId === 'engine' ? ' active' : ''}`}
            style={{
              padding: '3px 9px',
              fontSize: 10,
              fontWeight: 700,
              background: selectedComponentId === 'engine' ? 'var(--ember)' : 'var(--bg-plate)',
              color: selectedComponentId === 'engine' ? '#ffffff' : 'var(--text-primary)',
              border: '1px solid var(--line-bright)'
            }}
          >
            ⚡ ENGINE INFO (ALL 3 UAV)
          </button>
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '5px 10px', background: 'var(--bg-plate)', borderBottom: '1px solid var(--line)', overflowX: 'auto' }}>
        <span style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-dim)', marginRight: 2 }}>PARTS:</span>
        {uavComponents.map((c) => (
          <button
            key={c.id}
            onClick={() => onSelectComponent(selectedComponentId === c.id ? null : c.id)}
            style={{
              padding: '2px 6px',
              fontSize: 9,
              fontWeight: 700,
              borderRadius: 3,
              border: selectedComponentId === c.id ? '1px solid var(--ember)' : '1px solid var(--line)',
              background: selectedComponentId === c.id ? 'var(--ember)' : 'var(--bg-panel)',
              color: selectedComponentId === c.id ? '#ffffff' : 'var(--text-secondary)',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'all 0.15s ease'
            }}
          >
            {c.id === 'engine' ? '⚡ ENGINE' : c.label.toUpperCase()}
          </button>
        ))}
      </div>
      <div className="viewer-canvas-wrap" style={{ position: 'relative', height: 420 }}>
        <div className="viewer-live-indicator">
          <span className="status-dot normal" style={{ boxShadow: 'none' }} />
          ● LIVE 3D
        </div>

        <Canvas shadows camera={{ position: [2.8, 1.4, 2.8], fov: 36 }}>
          <Suspense fallback={null}>
            <ambientLight intensity={0.7} />
            <directionalLight position={[5, 8, 4]} intensity={1.5} castShadow />
            <directionalLight position={[-4, 3, -3]} intensity={0.6} color="#2f8f7f" />
            <directionalLight position={[0, -4, 0]} intensity={0.3} color="#f4f5ef" />
            <UAVModel
              selectedComponentId={selectedComponentId}
              onComponentClick={onSelectComponent}
              faultsByComponent={faultsByComp}
            />
            <ContactShadows position={[0, -0.55, 0]} opacity={0.3} scale={7} blur={2} far={2} />
          </Suspense>
          <OrbitControls
            enablePan
            enableZoom
            minDistance={2}
            maxDistance={9}
            maxPolarAngle={Math.PI / 1.7}
          />
        </Canvas>

        {selected && (
          <div className="component-drawer">
            <div className="component-drawer-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span className="component-drawer-title">{selected.label.toUpperCase()}</span>
                {selectedComponentId === 'engine' && (
                  <span className="badge info" style={{ fontSize: 8.5 }}>3 UAV COMPARISON</span>
                )}
              </div>
              <button className="component-drawer-close" onClick={() => onSelectComponent(null)} aria-label="Close">
                <X size={14} />
              </button>
            </div>

            {selectedComponentId === 'engine' ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div>
                  <div className="field-label" style={{ marginBottom: 4 }}>SELECT UAV ENGINE TO INSPECT:</div>
                  <div style={{ display: 'flex', gap: 4 }}>
                    {ALL_UAV_ENGINES.map((e) => (
                      <button
                        key={e.uavId}
                        onClick={() => {
                          setEngineTabUAV(e.uavId);
                          if (onSelectUAV) onSelectUAV(e.uavId);
                        }}
                        style={{
                          flex: 1,
                          padding: '5px 4px',
                          fontSize: 10,
                          fontWeight: 700,
                          borderRadius: 4,
                          border: engineTabUAV === e.uavId ? '1.5px solid var(--ember)' : '1px solid var(--line)',
                          background: engineTabUAV === e.uavId ? 'rgba(75, 86, 34, 0.1)' : 'var(--bg-inset)',
                          color: engineTabUAV === e.uavId ? 'var(--ember)' : 'var(--text-secondary)',
                          cursor: 'pointer',
                          transition: 'all 0.15s ease'
                        }}
                      >
                        {e.uavId}
                      </button>
                    ))}
                  </div>
                </div>

                <div style={{ background: 'var(--bg-inset)', padding: 10, borderRadius: 6, border: '1px solid var(--line)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 4 }}>
                    <span style={{ fontSize: 12, fontWeight: 800, color: 'var(--text-hi)' }}>{currentEngineInfo.engineModel}</span>
                    <span className={`badge ${currentEngineInfo.statusBadge}`} style={{ fontSize: 8.5 }}>
                      {currentEngineInfo.status}
                    </span>
                  </div>
                  <div style={{ fontSize: 10.5, color: 'var(--text-secondary)', lineHeight: 1.4, marginBottom: 6 }}>
                    {currentEngineInfo.engineType}
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4, fontSize: 10, color: 'var(--text-dim)' }}>
                    <div><b>Power:</b> {currentEngineInfo.powerHp}</div>
                    <div><b>Displ:</b> {currentEngineInfo.displacement}</div>
                    <div><b>Compress:</b> {currentEngineInfo.compression}</div>
                    <div><b>Cooling:</b> Liquid/Air Hybrid</div>
                  </div>
                </div>

                <div style={{ borderTop: '1px solid var(--line)', paddingTop: 8 }}>
                  <div className="component-drawer-section-title">LIVE ENGINE TELEMETRY ({engineTabUAV})</div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, marginTop: 4 }}>
                    <div style={{ background: 'var(--bg-plate)', padding: 6, borderRadius: 4, border: '1px solid var(--line)' }}>
                      <div className="scalar-label">Engine RPM</div>
                      <div className="mono" style={{ fontSize: 13, fontWeight: 700, color: 'var(--signal)' }}>
                        {liveEngineData.engine?.rpm || 0} <span style={{ fontSize: 9 }}>rpm</span>
                      </div>
                    </div>
                    <div style={{ background: 'var(--bg-plate)', padding: 6, borderRadius: 4, border: '1px solid var(--line)' }}>
                      <div className="scalar-label">CHT Temperature</div>
                      <div className="mono" style={{ fontSize: 13, fontWeight: 700, color: 'var(--amber)' }}>
                        {liveEngineData.thermal?.cht || 0} <span style={{ fontSize: 9 }}>°C</span>
                      </div>
                    </div>
                    <div style={{ background: 'var(--bg-plate)', padding: 6, borderRadius: 4, border: '1px solid var(--line)' }}>
                      <div className="scalar-label">EGT Temperature</div>
                      <div className="mono" style={{ fontSize: 13, fontWeight: 700, color: 'var(--ember)' }}>
                        {liveEngineData.thermal?.egt || 0} <span style={{ fontSize: 9 }}>°C</span>
                      </div>
                    </div>
                    <div style={{ background: 'var(--bg-plate)', padding: 6, borderRadius: 4, border: '1px solid var(--line)' }}>
                      <div className="scalar-label">Oil Pressure</div>
                      <div className="mono" style={{ fontSize: 13, fontWeight: 700, color: 'var(--go-green)' }}>
                        {liveEngineData.lubrication?.oilPressure || 0} <span style={{ fontSize: 9 }}>bar</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div style={{ borderTop: '1px solid var(--line)', paddingTop: 8 }}>
                  <div className="component-drawer-section-title">ENGINE COMPARISON ACROSS ALL 3 UAVs</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 4 }}>
                    {ALL_UAV_ENGINES.map((u) => (
                      <div
                        key={u.uavId}
                        style={{
                          padding: 6,
                          borderRadius: 4,
                          background: u.uavId === engineTabUAV ? 'rgba(75, 86, 34, 0.06)' : 'var(--bg-plate)',
                          border: u.uavId === engineTabUAV ? '1px solid var(--ember)' : '1px solid var(--line)',
                          fontSize: 9.5
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700, marginBottom: 2 }}>
                          <span>{u.uavId}: {u.engineModel}</span>
                          <span className={`status-text ${u.statusBadge}`}>{u.status}</span>
                        </div>
                        <div style={{ color: 'var(--text-dim)', display: 'flex', justifyContent: 'space-between' }}>
                          <span>Max RPM: {u.limits.rpmMax}</span>
                          <span>Max CHT: {u.limits.chtMax}°C</span>
                          <span>Max EGT: {u.limits.egtMax}°C</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div>
                <div
                  className={`badge ${selectedFault ? selectedFault.severity : 'normal'}`}
                >
                  {selectedFault ? selectedFault.severity.toUpperCase() : 'NORMAL'}
                </div>

                <div className="component-drawer-text" style={{ marginTop: 8 }}>
                  {detail?.description}
                </div>

                <div className="component-drawer-section">
                  <div className="component-drawer-section-title">MONITORED PARAMETERS</div>
                  <div className="chip-row">
                    {detail?.parameterKeys.map((k) => (
                      <span key={k} className="chip">{k}</span>
                    ))}
                  </div>
                </div>

                {selectedFault && (
                  <div className="component-drawer-section">
                    <div className="component-drawer-section-title">ACTIVE FAULT</div>
                    <div className="component-drawer-text">
                      <b>{resolveFaultMeta(selectedFault.type).label}</b>
                      <br />
                      Probable cause: {selectedFault.probableCause}
                      <br />
                      Recommended action: {selectedFault.recommendedAction}
                    </div>
                    <div className="component-drawer-section-title" style={{ marginTop: 7 }}>AFFECTED COMPONENTS</div>
                    <div className="chip-row">
                      {selectedFault.affectedComponents.map((c) => (
                        <span key={c} className="chip">{c}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        <div className="viewer-hint">Drag to rotate · Scroll to zoom · Click any label or part for details</div>
      </div>
    </div>
  );
}
