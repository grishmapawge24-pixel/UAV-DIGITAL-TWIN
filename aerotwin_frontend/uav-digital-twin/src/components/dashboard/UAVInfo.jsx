import React from 'react';
import { formatDuration } from '../../utils/status.js';

function InfoRow({ label, value }) {
  return (
    <div className="scalar-row">
      <span className="scalar-label">{label}</span>
      <span className="scalar-value mono" style={{ color: 'var(--text-primary)' }}>{value}</span>
    </div>
  );
}

export default function UAVInfo({ profile, telemetry }) {
  const statusStyle =
    telemetry.status === 'AIRBORNE' ? 'normal' : telemetry.status === 'STANDBY' ? 'info' : 'offline';

  return (
    <div className="panel" style={{ flex: '0 0 auto', maxHeight: 262 }}>
      <div className="panel-header">
        <span className="panel-title">UAV INFORMATION</span>
        <span className={`badge ${statusStyle}`}>{telemetry.status}</span>
      </div>
      <div className="panel-body">
        <InfoRow label="UAV ID" value={profile.id} />
        <InfoRow label="Type" value={profile.type} />
        <InfoRow label="Engine" value={profile.engineType} />
        <InfoRow label="Mission" value={profile.mission} />
        <InfoRow label="Flight Time" value={formatDuration(telemetry.flightTimeMin)} />
        <InfoRow label="Altitude" value={`${telemetry.currentAltitudeFt.toLocaleString()} ft`} />
        <InfoRow label="Speed" value={`${telemetry.currentSpeedKts} kts`} />
      </div>
    </div>
  );
}
