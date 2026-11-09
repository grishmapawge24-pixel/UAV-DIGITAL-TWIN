import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Play, Pause, RotateCcw, Navigation, Crosshair, ZoomIn, ZoomOut,
  Maximize2, Activity, Gauge, Radio, Shield, MapPin, FastForward, Check
} from 'lucide-react';
import { uavProfiles } from '../data/uavProfiles.js';

const MAP_BOUNDS = {
  minLat: 12.80,
  maxLat: 13.80,
  minLon: 77.00,
  maxLon: 78.40,
  width: 1000,
  height: 700
};

const BASE_STATION = {
  name: 'Yelahanka AFB (Base)',
  lat: 13.1355,
  lon: 77.6062,
  x: 433,
  y: 465
};

const FLEET_DATA = [
  {
    id: 'UAV-01',
    name: 'UAV-01 Falcon Alpha',
    callsign: 'FALCON-01',
    type: 'MALE Fixed-Wing ISR',
    color: '#1f6f66',
    baseSpeedKts: 68,
    altitudeFt: 18500,
    status: 'AIRBORNE',
    engineRpm: 5200,
    cht: 165,
    egt: 690,
    oilPressure: 4.8,
    fuelPct: 62,
    signalQuality: 98,
    waypoints: [
      { id: 'WP-101', name: 'Departure Point', lat: 13.15, lon: 77.62 },
      { id: 'WP-102', name: 'Corridor North', lat: 13.38, lon: 77.75 },
      { id: 'WP-103', name: 'Surveillance Ridge', lat: 13.62, lon: 77.88 },
      { id: 'WP-104', name: 'Sector Apex', lat: 13.72, lon: 78.15 },
      { id: 'WP-105', name: 'East Boundary', lat: 13.52, lon: 78.30 },
      { id: 'WP-106', name: 'Loiter Alpha', lat: 13.30, lon: 78.08 },
      { id: 'WP-107', name: 'Return Corridor', lat: 13.20, lon: 77.80 }
    ]
  },
  {
    id: 'UAV-02',
    name: 'UAV-02 Sea Guardian',
    callsign: 'GUARDIAN-02',
    type: 'Maritime Surveillance',
    color: '#2e7d46',
    baseSpeedKts: 58,
    altitudeFt: 13800,
    status: 'PATROL',
    engineRpm: 4950,
    cht: 178,
    egt: 742,
    oilPressure: 4.2,
    fuelPct: 48,
    signalQuality: 88,
    waypoints: [
      { id: 'WP-201', name: 'Coastal Entry', lat: 13.05, lon: 77.40 },
      { id: 'WP-202', name: 'Bay Sweep 1', lat: 12.92, lon: 77.65 },
      { id: 'WP-203', name: 'Estuary Patrol', lat: 12.88, lon: 78.05 },
      { id: 'WP-204', name: 'Offshore Track', lat: 13.08, lon: 78.25 },
      { id: 'WP-205', name: 'Maritime Grid 4', lat: 13.28, lon: 77.95 },
      { id: 'WP-206', name: 'Inbound Coast', lat: 13.18, lon: 77.58 }
    ]
  },
  {
    id: 'UAV-03',
    name: 'UAV-03 Sky Sentinel',
    callsign: 'SENTINEL-03',
    type: 'High-Altitude Recon',
    color: '#4b5622',
    baseSpeedKts: 76,
    altitudeFt: 22500,
    status: 'SURVEILLANCE',
    engineRpm: 5600,
    cht: 154,
    egt: 660,
    oilPressure: 5.1,
    fuelPct: 82,
    signalQuality: 99,
    waypoints: [
      { id: 'WP-301', name: 'High Orbit North', lat: 13.68, lon: 77.32 },
      { id: 'WP-302', name: 'High Orbit East', lat: 13.65, lon: 77.72 },
      { id: 'WP-303', name: 'High Orbit South', lat: 13.45, lon: 77.58 },
      { id: 'WP-304', name: 'High Orbit West', lat: 13.48, lon: 77.18 }
    ]
  },
  {
    id: 'UAV-04',
    name: 'UAV-04 Shadow Strike',
    callsign: 'SHADOW-04',
    type: 'Tactical Recon / Escort',
    color: '#6b4f8a',
    baseSpeedKts: 94,
    altitudeFt: 11200,
    status: 'MISSION',
    engineRpm: 5750,
    cht: 182,
    egt: 765,
    oilPressure: 4.6,
    fuelPct: 39,
    signalQuality: 92,
    waypoints: [
      { id: 'WP-401', name: 'Tactical IP', lat: 13.22, lon: 77.12 },
      { id: 'WP-402', name: 'Low-Pass Check', lat: 13.42, lon: 77.35 },
      { id: 'WP-403', name: 'Recon Target A', lat: 13.58, lon: 77.52 },
      { id: 'WP-404', name: 'Egress Route', lat: 13.40, lon: 77.70 },
      { id: 'WP-405', name: 'Holding Point', lat: 13.25, lon: 77.45 }
    ]
  },
  {
    id: 'UAV-05',
    name: 'UAV-05 Vanguard',
    callsign: 'VANGUARD-05',
    type: 'Border Patrol / SAR',
    color: '#8a7b32',
    baseSpeedKts: 62,
    altitudeFt: 16800,
    status: 'PATROL',
    engineRpm: 5100,
    cht: 160,
    egt: 680,
    oilPressure: 4.9,
    fuelPct: 71,
    signalQuality: 96,
    waypoints: [
      { id: 'WP-501', name: 'Border Post 1', lat: 13.75, lon: 77.10 },
      { id: 'WP-502', name: 'Border Post 2', lat: 13.78, lon: 77.50 },
      { id: 'WP-503', name: 'Border Post 3', lat: 13.72, lon: 77.90 },
      { id: 'WP-504', name: 'Border Post 4', lat: 13.68, lon: 78.35 },
      { id: 'WP-505', name: 'Turnaround Sector', lat: 13.50, lon: 78.20 },
      { id: 'WP-506', name: 'Border Return West', lat: 13.58, lon: 77.60 }
    ]
  }
];

function latLonToXY(lat, lon) {
  const normX = (lon - MAP_BOUNDS.minLon) / (MAP_BOUNDS.maxLon - MAP_BOUNDS.minLon);
  const normY = 1 - (lat - MAP_BOUNDS.minLat) / (MAP_BOUNDS.maxLat - MAP_BOUNDS.minLat);
  return {
    x: Math.round(normX * MAP_BOUNDS.width * 10) / 10,
    y: Math.round(normY * MAP_BOUNDS.height * 10) / 10
  };
}

function xyToLatLon(x, y) {
  const normX = x / MAP_BOUNDS.width;
  const normY = 1 - y / MAP_BOUNDS.height;
  return {
    lat: MAP_BOUNDS.minLat + normY * (MAP_BOUNDS.maxLat - MAP_BOUNDS.minLat),
    lon: MAP_BOUNDS.minLon + normX * (MAP_BOUNDS.maxLon - MAP_BOUNDS.minLon)
  };
}

function calculateDistance(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

export default function MapSimulation({ selectedUAVId, onSelectUAV }) {
  const navigate = useNavigate();
  const [selectedId, setSelectedId] = useState(selectedUAVId || FLEET_DATA[0].id);
  const [isPlaying, setIsPlaying] = useState(true);
  const [simSpeed, setSimSpeed] = useState(1);
  const [simTimeSec, setSimTimeSec] = useState(0);
  const [followSelected, setFollowSelected] = useState(true);
  const [showAirspace, setShowAirspace] = useState(true);
  const [showWaypoints, setShowWaypoints] = useState(true);
  const [showTrails, setShowTrails] = useState(true);
  const [viewBox, setViewBox] = useState({ x: 0, y: 0, w: MAP_BOUNDS.width, h: MAP_BOUNDS.height });

  const uavsRef = useRef(
    FLEET_DATA.map((uav) => {
      const xyWaypoints = uav.waypoints.map((wp) => ({
        ...wp,
        ...latLonToXY(wp.lat, wp.lon)
      }));
      return {
        ...uav,
        xyWaypoints,
        currentLeg: 0,
        legProgress: 0,
        x: xyWaypoints[0].x,
        y: xyWaypoints[0].y,
        lat: uav.waypoints[0].lat,
        lon: uav.waypoints[0].lon,
        heading: 0,
        currentSpeedKts: uav.baseSpeedKts,
        trail: [{ x: xyWaypoints[0].x, y: xyWaypoints[0].y, lat: uav.waypoints[0].lat, lon: uav.waypoints[0].lon }]
      };
    })
  );

  const [uavStates, setUavStates] = useState(uavsRef.current);
  const animFrameRef = useRef(null);
  const lastTickRef = useRef(performance.now());

  useEffect(() => {
    if (selectedUAVId) {
      setSelectedId(selectedUAVId);
    }
  }, [selectedUAVId]);

  function handleSelect(id) {
    setSelectedId(id);
    if (onSelectUAV) {
      onSelectUAV(id);
    }
  }

  useEffect(() => {
    let active = true;

    function step(now) {
      const deltaSec = Math.min((now - lastTickRef.current) / 1000, 0.1);
      lastTickRef.current = now;

      if (isPlaying && active) {
        setSimTimeSec((t) => t + deltaSec * simSpeed);

        uavsRef.current = uavsRef.current.map((uav) => {
          const numWp = uav.xyWaypoints.length;
          const fromWp = uav.xyWaypoints[uav.currentLeg];
          const toIndex = (uav.currentLeg + 1) % numWp;
          const toWp = uav.xyWaypoints[toIndex];

          const dx = toWp.x - fromWp.x;
          const dy = toWp.y - fromWp.y;
          const legPixelDist = Math.sqrt(dx * dx + dy * dy) || 1;

          const pixelsPerSec = (uav.baseSpeedKts * 0.45 * simSpeed);
          const progressDelta = (pixelsPerSec * deltaSec) / legPixelDist;

          let newProgress = uav.legProgress + progressDelta;
          let newLeg = uav.currentLeg;

          if (newProgress >= 1) {
            newLeg = (uav.currentLeg + 1) % numWp;
            newProgress = newProgress - 1;
          }

          const curFrom = uav.xyWaypoints[newLeg];
          const curTo = uav.xyWaypoints[(newLeg + 1) % numWp];
          const curDx = curTo.x - curFrom.x;
          const curDy = curTo.y - curFrom.y;

          const curX = curFrom.x + curDx * newProgress;
          const curY = curFrom.y + curDy * newProgress;

          const targetAngleDeg = (Math.atan2(curDy, curDx) * 180) / Math.PI + 90;
          let heading = (targetAngleDeg + 360) % 360;

          const geo = xyToLatLon(curX, curY);

          const jitterSpeed = uav.baseSpeedKts + Math.sin(now / 1200 + newLeg) * 2.5;

          const lastTrail = uav.trail[uav.trail.length - 1];
          let nextTrail = uav.trail;
          if (!lastTrail || Math.hypot(curX - lastTrail.x, curY - lastTrail.y) > 3) {
            nextTrail = [...uav.trail.slice(-80), { x: curX, y: curY, lat: geo.lat, lon: geo.lon }];
          }

          return {
            ...uav,
            currentLeg: newLeg,
            legProgress: newProgress,
            x: curX,
            y: curY,
            lat: geo.lat,
            lon: geo.lon,
            heading: Math.round(heading),
            currentSpeedKts: Math.round(jitterSpeed),
            fuelPct: Math.max(5, uav.fuelPct - (deltaSec * simSpeed * 0.005)),
            trail: nextTrail
          };
        });

        setUavStates([...uavsRef.current]);
      }

      if (active) {
        animFrameRef.current = requestAnimationFrame(step);
      }
    }

    lastTickRef.current = performance.now();
    animFrameRef.current = requestAnimationFrame(step);

    return () => {
      active = false;
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [isPlaying, simSpeed]);

  const selectedUav = useMemo(() => {
    return uavStates.find((u) => u.id === selectedId) || uavStates[0];
  }, [uavStates, selectedId]);

  useEffect(() => {
    if (followSelected && selectedUav) {
      const zoomW = 600;
      const zoomH = 420;
      const targetX = Math.max(0, Math.min(MAP_BOUNDS.width - zoomW, selectedUav.x - zoomW / 2));
      const targetY = Math.max(0, Math.min(MAP_BOUNDS.height - zoomH, selectedUav.y - zoomH / 2));
      setViewBox({ x: targetX, y: targetY, w: zoomW, h: zoomH });
    }
  }, [selectedUav?.x, selectedUav?.y, followSelected]);

  function handleReset() {
    uavsRef.current = FLEET_DATA.map((uav) => {
      const xyWaypoints = uav.waypoints.map((wp) => ({
        ...wp,
        ...latLonToXY(wp.lat, wp.lon)
      }));
      return {
        ...uav,
        xyWaypoints,
        currentLeg: 0,
        legProgress: 0,
        x: xyWaypoints[0].x,
        y: xyWaypoints[0].y,
        lat: uav.waypoints[0].lat,
        lon: uav.waypoints[0].lon,
        heading: 0,
        currentSpeedKts: uav.baseSpeedKts,
        fuelPct: uav.fuelPct,
        trail: [{ x: xyWaypoints[0].x, y: xyWaypoints[0].y, lat: uav.waypoints[0].lat, lon: uav.waypoints[0].lon }]
      };
    });
    setSimTimeSec(0);
    setUavStates([...uavsRef.current]);
  }

  function zoomIn() {
    setFollowSelected(false);
    setViewBox((v) => {
      const nw = Math.max(300, v.w * 0.8);
      const nh = Math.max(210, v.h * 0.8);
      return {
        x: Math.max(0, v.x + (v.w - nw) / 2),
        y: Math.max(0, v.y + (v.h - nh) / 2),
        w: nw,
        h: nh
      };
    });
  }

  function zoomOut() {
    setFollowSelected(false);
    setViewBox((v) => {
      const nw = Math.min(MAP_BOUNDS.width, v.w * 1.25);
      const nh = Math.min(MAP_BOUNDS.height, v.h * 1.25);
      return {
        x: Math.max(0, Math.min(MAP_BOUNDS.width - nw, v.x - (nw - v.w) / 2)),
        y: Math.max(0, Math.min(MAP_BOUNDS.height - nh, v.y - (nh - v.h) / 2)),
        w: nw,
        h: nh
      };
    });
  }

  function resetZoom() {
    setFollowSelected(false);
    setViewBox({ x: 0, y: 0, w: MAP_BOUNDS.width, h: MAP_BOUNDS.height });
  }

  function formatTime(totalSec) {
    const mins = Math.floor(totalSec / 60);
    const secs = Math.floor(totalSec % 60);
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }

  const nextWaypoint = selectedUav ? selectedUav.xyWaypoints[(selectedUav.currentLeg + 1) % selectedUav.xyWaypoints.length] : null;
  const distToNextKm = selectedUav && nextWaypoint ? calculateDistance(selectedUav.lat, selectedUav.lon, nextWaypoint.lat, nextWaypoint.lon).toFixed(1) : 0;

  return (
    <div className="page" style={{ padding: 12, height: '100%', overflow: 'hidden' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr 310px', gap: 12, height: '100%', minHeight: 0 }}>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, minHeight: 0, overflowY: 'auto' }}>
          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">SIMULATION CONTROLS</span>
              <span className="badge normal">OFFLINE MODE</span>
            </div>
            <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span className="scalar-label">SIMULATION CLOCK</span>
                <span className="scalar-value mono" style={{ fontSize: 13, color: 'var(--ember)' }}>
                  +{formatTime(simTimeSec)}
                </span>
              </div>

              <div style={{ display: 'flex', gap: 6 }}>
                <button
                  className="btn-primary"
                  onClick={() => setIsPlaying((p) => !p)}
                  style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 6,
                    background: isPlaying ? 'var(--ember)' : 'var(--go-green)'
                  }}
                >
                  {isPlaying ? <Pause size={14} /> : <Play size={14} />}
                  {isPlaying ? 'PAUSE' : 'RESUME'}
                </button>
                <button
                  className="btn-secondary"
                  onClick={handleReset}
                  title="Reset Simulation"
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0 12px' }}
                >
                  <RotateCcw size={14} />
                </button>
              </div>

              <div className="field-group" style={{ marginBottom: 0 }}>
                <div className="field-label">SIMULATION SPEED</div>
                <div className="select-chip-group">
                  {[1, 2, 5].map((s) => (
                    <button
                      key={s}
                      className={`select-chip${simSpeed === s ? ' active' : ''}`}
                      onClick={() => setSimSpeed(s)}
                      style={{ flex: 1, textAlign: 'center', padding: '5px 0' }}
                    >
                      {s}x SPEED
                    </button>
                  ))}
                </div>
              </div>

              <div style={{ borderTop: '1px solid var(--line)', paddingTop: 8, display: 'flex', flexDirection: 'column', gap: 6 }}>
                <div className="field-label">MAP OVERLAYS</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', cursor: 'pointer' }}>
                    <input type="checkbox" checked={followSelected} onChange={(e) => setFollowSelected(e.target.checked)} />
                    Auto-follow Selected UAV
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', cursor: 'pointer' }}>
                    <input type="checkbox" checked={showTrails} onChange={(e) => setShowTrails(e.target.checked)} />
                    Show Dynamic Flight Trails
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', cursor: 'pointer' }}>
                    <input type="checkbox" checked={showWaypoints} onChange={(e) => setShowWaypoints(e.target.checked)} />
                    Show Flight Waypoints
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', cursor: 'pointer' }}>
                    <input type="checkbox" checked={showAirspace} onChange={(e) => setShowAirspace(e.target.checked)} />
                    Show Tactical Sectors
                  </label>
                </div>
              </div>
            </div>
          </div>

          <div className="panel" style={{ flex: 1, minHeight: 0 }}>
            <div className="panel-header">
              <span className="panel-title">ACTIVE UAV FLEET ({uavStates.length})</span>
            </div>
            <div className="panel-body" style={{ padding: 6, display: 'flex', flexDirection: 'column', gap: 6 }}>
              {uavStates.map((uav) => {
                const isSel = uav.id === selectedId;
                return (
                  <div
                    key={uav.id}
                    onClick={() => handleSelect(uav.id)}
                    style={{
                      padding: '8px 10px',
                      borderRadius: 'var(--radius-sm)',
                      background: isSel ? 'rgba(75, 86, 34, 0.08)' : 'var(--bg-plate)',
                      border: isSel ? '1.5px solid var(--ember)' : '1px solid var(--line)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 3 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ width: 8, height: 8, borderRadius: '50%', background: uav.color }} />
                        <span style={{ fontSize: 11.5, fontWeight: 700, color: isSel ? 'var(--ember)' : 'var(--text-primary)' }}>
                          {uav.id}
                        </span>
                      </div>
                      <span className="badge normal" style={{ fontSize: 9, padding: '1px 6px' }}>
                        {uav.status}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-dim)' }}>
                      <span>{uav.currentSpeedKts} kts · {uav.altitudeFt.toLocaleString()} ft</span>
                      <span className="mono">{uav.heading}° HDG</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="panel" style={{ position: 'relative', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="panel-title">OFFLINE TACTICAL MAP SIMULATION</span>
              <span className="badge info" style={{ fontSize: 9 }}>GEO-GRID 13.0°N / 77.5°E</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <button className="transport-btn" onClick={zoomIn} title="Zoom In" style={{ width: 28, height: 28 }}>
                <ZoomIn size={13} />
              </button>
              <button className="transport-btn" onClick={zoomOut} title="Zoom Out" style={{ width: 28, height: 28 }}>
                <ZoomOut size={13} />
              </button>
              <button className="transport-btn" onClick={resetZoom} title="Reset View" style={{ width: 28, height: 28 }}>
                <Maximize2 size={13} />
              </button>
            </div>
          </div>

          <div style={{ flex: 1, position: 'relative', background: '#f4f5ef', overflow: 'hidden' }}>
            <svg
              viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`}
              style={{ width: '100%', height: '100%', display: 'block', cursor: 'grab' }}
            >
              <defs>
                <pattern id="tacticalGridMajor" width="100" height="100" patternUnits="userSpaceOnUse">
                  <path d="M 100 0 L 0 0 0 100" fill="none" stroke="#d7dbcd" strokeWidth="1" />
                </pattern>
                <pattern id="tacticalGridMinor" width="20" height="20" patternUnits="userSpaceOnUse">
                  <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#eef0ea" strokeWidth="0.6" />
                </pattern>
                <radialGradient id="airbaseRing" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="#1f6f66" stopOpacity="0.12" />
                  <stop offset="100%" stopColor="#1f6f66" stopOpacity="0" />
                </radialGradient>
              </defs>

              <rect x="0" y="0" width={MAP_BOUNDS.width} height={MAP_BOUNDS.height} fill="#f4f5ef" />
              <rect x="0" y="0" width={MAP_BOUNDS.width} height={MAP_BOUNDS.height} fill="url(#tacticalGridMinor)" />
              <rect x="0" y="0" width={MAP_BOUNDS.width} height={MAP_BOUNDS.height} fill="url(#tacticalGridMajor)" />

              <path
                d="M 50 180 Q 220 140 380 220 T 700 190 T 950 240"
                fill="none"
                stroke="#d7dbcd"
                strokeWidth="1.5"
                strokeDasharray="4 3"
              />
              <path
                d="M 80 480 Q 300 420 520 510 T 880 470"
                fill="none"
                stroke="#d7dbcd"
                strokeWidth="1.5"
                strokeDasharray="4 3"
              />

              {showAirspace && (
                <g>
                  <polygon
                    points="320,100 780,90 880,320 620,410 280,260"
                    fill="rgba(31, 111, 102, 0.04)"
                    stroke="#1f6f66"
                    strokeWidth="1.2"
                    strokeDasharray="6 4"
                  />
                  <text x="520" y="130" fill="#1f6f66" fontSize="10" fontWeight="700" opacity="0.7" letterSpacing="1">
                    SECTOR ALPHA (ISR PATROL ZONE)
                  </text>

                  <polygon
                    points="120,440 380,390 440,620 160,650"
                    fill="rgba(184, 134, 11, 0.04)"
                    stroke="#b8860b"
                    strokeWidth="1.2"
                    strokeDasharray="4 3"
                  />
                  <text x="210" y="470" fill="#b8860b" fontSize="9" fontWeight="700" opacity="0.8">
                    RESTRICTED AIRSPACE R-104
                  </text>

                  <circle cx={BASE_STATION.x} cy={BASE_STATION.y} r="180" fill="none" stroke="#8b9284" strokeWidth="0.8" strokeDasharray="3 3" opacity="0.6" />
                  <circle cx={BASE_STATION.x} cy={BASE_STATION.y} r="100" fill="none" stroke="#8b9284" strokeWidth="0.8" strokeDasharray="3 3" opacity="0.6" />
                  <circle cx={BASE_STATION.x} cy={BASE_STATION.y} r="40" fill="url(#airbaseRing)" stroke="#1f6f66" strokeWidth="1" />
                </g>
              )}

              <g transform={`translate(${BASE_STATION.x}, ${BASE_STATION.y})`}>
                <rect x="-18" y="-4" width="36" height="8" fill="#46503f" rx="1" transform="rotate(-35)" />
                <line x1="-15" y1="0" x2="15" y2="0" stroke="#ffffff" strokeWidth="1" strokeDasharray="3 2" transform="rotate(-35)" />
                <circle cx="0" cy="0" r="3" fill="#1f6f66" />
                <text x="14" y="14" fill="#3f4a3a" fontSize="10" fontWeight="800">
                  {BASE_STATION.name}
                </text>
              </g>

              {showWaypoints &&
                uavStates.map((uav) => {
                  const isSel = uav.id === selectedId;
                  const pts = uav.xyWaypoints.map((w) => `${w.x},${w.y}`).join(' ');
                  return (
                    <g key={`wp-group-${uav.id}`} opacity={isSel ? 1 : 0.45}>
                      <polygon
                        points={pts}
                        fill="none"
                        stroke={uav.color}
                        strokeWidth={isSel ? 1.5 : 1}
                        strokeDasharray={isSel ? '5 3' : '2 2'}
                      />
                      {uav.xyWaypoints.map((wp, idx) => (
                        <g key={wp.id} transform={`translate(${wp.x}, ${wp.y})`}>
                          <circle r={isSel ? 3.5 : 2.5} fill="#ffffff" stroke={uav.color} strokeWidth={isSel ? 1.8 : 1.2} />
                          {isSel && (
                            <text x="6" y="-6" fill="var(--text-secondary)" fontSize="8.5" fontWeight="700">
                              {wp.name}
                            </text>
                          )}
                        </g>
                      ))}
                    </g>
                  );
                })}

              {showTrails &&
                uavStates.map((uav) => {
                  if (uav.trail.length < 2) return null;
                  const isSel = uav.id === selectedId;
                  const trailPoints = uav.trail.map((p) => `${p.x},${p.y}`).join(' ');
                  return (
                    <polyline
                      key={`trail-${uav.id}`}
                      points={trailPoints}
                      fill="none"
                      stroke={uav.color}
                      strokeWidth={isSel ? 2.2 : 1.4}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      opacity={isSel ? 0.9 : 0.55}
                    />
                  );
                })}

              {uavStates.map((uav) => {
                const isSel = uav.id === selectedId;
                return (
                  <g
                    key={uav.id}
                    transform={`translate(${uav.x}, ${uav.y})`}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSelect(uav.id);
                    }}
                    style={{ cursor: 'pointer' }}
                  >
                    {isSel && (
                      <circle r="18" fill="none" stroke={uav.color} strokeWidth="1.5" opacity="0.7">
                        <animate attributeName="r" values="10;24;10" dur="2.4s" repeatCount="indefinite" />
                        <animate attributeName="opacity" values="0.8;0.1;0.8" dur="2.4s" repeatCount="indefinite" />
                      </circle>
                    )}

                    <g transform={`rotate(${uav.heading})`}>
                      <path
                        d="M 0 -11 L 8 9 L 0 5 L -8 9 Z"
                        fill={uav.color}
                        stroke="#ffffff"
                        strokeWidth="1.2"
                      />
                      <line x1="-12" y1="2" x2="12" y2="2" stroke={uav.color} strokeWidth="2.5" strokeLinecap="round" />
                    </g>

                    <rect
                      x="12"
                      y="-16"
                      width="74"
                      height="26"
                      rx="3"
                      fill="rgba(255, 255, 255, 0.96)"
                      stroke={isSel ? uav.color : 'var(--line-bright)'}
                      strokeWidth={isSel ? 1.5 : 1}
                      filter="drop-shadow(0 2px 4px rgba(0,0,0,0.08))"
                    />
                    <text x="17" y="-5" fill="var(--text-primary)" fontSize="9" fontWeight="800">
                      {uav.id}
                    </text>
                    <text x="17" y="5" fill="var(--text-dim)" fontSize="7.5" fontWeight="600">
                      {uav.currentSpeedKts} kts · {uav.altitudeFt}ft
                    </text>
                  </g>
                );
              })}

              <g transform="translate(30, 40)">
                <circle cx="0" cy="0" r="14" fill="#ffffff" stroke="#b7bfa8" strokeWidth="1" />
                <path d="M 0 -12 L 3 -3 L 0 0 L -3 -3 Z" fill="#4b5622" />
                <path d="M 0 12 L 3 3 L 0 0 L -3 3 Z" fill="#8b9284" />
                <text x="0" y="-15" textAnchor="middle" fill="#4b5622" fontSize="8" fontWeight="800">N</text>
              </g>

              <g transform="translate(30, 670)">
                <rect x="0" y="-12" width="100" height="4" fill="#3f4a3a" />
                <rect x="0" y="-12" width="50" height="4" fill="#ffffff" stroke="#3f4a3a" strokeWidth="0.5" />
                <text x="0" y="-1" fill="#6d7869" fontSize="8" fontWeight="700">0</text>
                <text x="50" y="-1" fill="#6d7869" fontSize="8" fontWeight="700">10 NM</text>
                <text x="100" y="-1" fill="#6d7869" fontSize="8" fontWeight="700">20 NM</text>
              </g>
            </svg>

            <div style={{ position: 'absolute', bottom: 10, right: 12, display: 'flex', gap: 8 }}>
              <span className="badge normal" style={{ background: 'rgba(255, 255, 255, 0.95)', border: '1px solid var(--line-bright)' }}>
                ● 100% OFFLINE VECTOR MAP
              </span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, minHeight: 0, overflowY: 'auto' }}>
          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">LIVE TELEMETRY HUD</span>
              <span className="badge normal" style={{ background: 'rgba(75, 86, 34, 0.1)', color: 'var(--ember)' }}>
                {selectedUav.id}
              </span>
            </div>
            <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 800, color: 'var(--text-hi)' }}>{selectedUav.name}</div>
                <div style={{ fontSize: 10, color: 'var(--text-dim)', fontWeight: 600 }}>{selectedUav.type}</div>
              </div>

              <div style={{ borderTop: '1px solid var(--line)', paddingTop: 6, display: 'flex', flexDirection: 'column', gap: 3 }}>
                <div className="scalar-row">
                  <span className="scalar-label">Latitude</span>
                  <span className="scalar-value mono">{selectedUav.lat.toFixed(5)}° N</span>
                </div>
                <div className="scalar-row">
                  <span className="scalar-label">Longitude</span>
                  <span className="scalar-value mono">{selectedUav.lon.toFixed(5)}° E</span>
                </div>
                <div className="scalar-row">
                  <span className="scalar-label">Heading</span>
                  <span className="scalar-value mono" style={{ color: 'var(--ember)' }}>{selectedUav.heading}°</span>
                </div>
                <div className="scalar-row">
                  <span className="scalar-label">Airspeed</span>
                  <span className="scalar-value mono">{selectedUav.currentSpeedKts} kts ({Math.round(selectedUav.currentSpeedKts * 1.852)} km/h)</span>
                </div>
                <div className="scalar-row">
                  <span className="scalar-label">Altitude</span>
                  <span className="scalar-value mono">{selectedUav.altitudeFt.toLocaleString()} ft</span>
                </div>
                <div className="scalar-row">
                  <span className="scalar-label">Target WP</span>
                  <span className="scalar-value mono" style={{ color: 'var(--signal)' }}>{nextWaypoint ? nextWaypoint.name : '—'}</span>
                </div>
                <div className="scalar-row">
                  <span className="scalar-label">Distance to WP</span>
                  <span className="scalar-value mono">{distToNextKm} km</span>
                </div>
              </div>

              <div style={{ borderTop: '1px solid var(--line)', paddingTop: 6, display: 'flex', flexDirection: 'column', gap: 3 }}>
                <div className="field-label" style={{ marginBottom: 2 }}>PROPULSION & ENGINE HEALTH</div>
                <div className="scalar-row">
                  <span className="scalar-label">Engine RPM</span>
                  <span className="scalar-value mono">{selectedUav.engineRpm} rpm</span>
                </div>
                <div className="scalar-row">
                  <span className="scalar-label">CHT / EGT</span>
                  <span className="scalar-value mono">{selectedUav.cht}°C / {selectedUav.egt}°C</span>
                </div>
                <div className="scalar-row">
                  <span className="scalar-label">Oil Pressure</span>
                  <span className="scalar-value mono">{selectedUav.oilPressure} bar</span>
                </div>
                <div className="scalar-row">
                  <span className="scalar-label">Fuel Level</span>
                  <span className="scalar-value mono" style={{ color: selectedUav.fuelPct < 25 ? 'var(--heat-red)' : 'var(--go-green)' }}>
                    {selectedUav.fuelPct.toFixed(1)}%
                  </span>
                </div>
                <div className="scalar-row">
                  <span className="scalar-label">Signal Quality</span>
                  <span className="scalar-value mono">{selectedUav.signalQuality}%</span>
                </div>
              </div>

              <button
                className="btn-primary"
                onClick={() => navigate('/')}
                style={{ marginTop: 4, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}
              >
                <Activity size={13} />
                VIEW 3D DIGITAL TWIN
              </button>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
