import React, { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import Header from './components/layout/Header.jsx';
import RouteNav from './components/layout/RouteNav.jsx';
import Dashboard from './pages/Dashboard.jsx';
import MapSimulation from './pages/MapSimulation.jsx';
import Simulation from './pages/Simulation.jsx';
import MissionReplay from './pages/MissionReplay.jsx';
import Diagnostics from './pages/Diagnostics.jsx';
import { uavProfiles } from './data/uavProfiles.js';

export default function App() {
  const [selectedUAVId, setSelectedUAVId] = useState(uavProfiles[0].id);

  return (
    <div className="app-shell">
      <Header
        selectedUAVId={selectedUAVId}
        onSelectUAV={setSelectedUAVId}
        navSlot={<RouteNav />}
      />
      <div className="app-body">
        <Routes>
          <Route path="/" element={<Dashboard uavId={selectedUAVId} onSelectUAV={setSelectedUAVId} />} />
          <Route path="/map-simulation" element={<MapSimulation selectedUAVId={selectedUAVId} onSelectUAV={setSelectedUAVId} />} />
          <Route path="/simulation" element={<Simulation uavId={selectedUAVId} />} />
          <Route path="/replay" element={<MissionReplay uavId={selectedUAVId} />} />
          <Route path="/diagnostics" element={<Diagnostics uavId={selectedUAVId} />} />
        </Routes>
      </div>
    </div>
  );
}
