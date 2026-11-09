import React, { useEffect, useState } from 'react';
import { uavProfiles } from '../../data/uavProfiles.js';

function useClock() {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  return now;
}

export default function Header({ selectedUAVId, onSelectUAV, navSlot }) {
  const now = useClock();
  const timeStr = now.toISOString().slice(11, 19) + ' UTC';

  return (
    <header className="app-header">
      <div className="app-header-row">
        <div className="app-header-left">
          <div className="brand">
            <span className="brand-title">UAV DIGITAL TWIN</span>
            <span className="brand-subtitle">MALE UAV ENGINE HEALTH MONITORING</span>
          </div>
        </div>
        <div className="app-header-right">
          <span className="header-clock mono">{timeStr}</span>
          <div className="system-status">
            <span className="status-dot normal" />
            <span className="status-text normal">SYSTEM ONLINE</span>
          </div>
        </div>
      </div>
      <div className="app-header-row secondary">
        {navSlot}
      </div>
    </header>
  );
}
