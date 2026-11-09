import React, { useEffect, useMemo, useState } from 'react';
import { getFaults } from '../services/api.js';
import { resolveFaultMeta } from '../data/mockFaults.js';

const FILTERS = ['All', 'Critical', 'Warning', 'Sensor', 'Electrical', 'Mechanical', 'Thermal', 'Fuel'];

function FaultRow({ fault, isHistorical }) {
  const meta = resolveFaultMeta(fault.type);
  return (
    <div className={`fault-card ${fault.severity}`}>
      <div className="fault-card-top">
        <span className="fault-card-title">{meta.label}</span>
        <span className={`badge ${fault.severity}`}>{fault.severity.toUpperCase()}</span>
      </div>
      <div className="fault-card-meta">
        <b>Category:</b> {meta.category} &nbsp;·&nbsp; <b>Confidence:</b> {fault.confidence ?? '—'}%
        <br />
        <b>Probable cause:</b> {fault.probableCause}
        <br />
        <b>Affected components:</b> {fault.affectedComponents.join(', ')}
        <br />
        <b>Recommended action:</b> {fault.recommendedAction}
        <br />
        <b>Detected:</b> {new Date(fault.detectedAt).toLocaleString()}
        {isHistorical && fault.clearedAt && (
          <>
            {' '}· <b>Cleared:</b> {new Date(fault.clearedAt).toLocaleString()}
          </>
        )}
      </div>
    </div>
  );
}

export default function Diagnostics({ uavId }) {
  const [faults, setFaults] = useState({ active: [], historical: [] });
  const [filter, setFilter] = useState('All');

  useEffect(() => {
    getFaults(uavId).then(setFaults);
  }, [uavId]);

  const matchesFilter = (fault) => {
    if (filter === 'All') return true;
    if (filter === 'Critical' || filter === 'Warning') return fault.severity === filter.toLowerCase();
    return resolveFaultMeta(fault.type).category === filter;
  };

  const activeFiltered = useMemo(() => faults.active.filter(matchesFilter), [faults, filter]);
  const historicalFiltered = useMemo(() => faults.historical.filter(matchesFilter), [faults, filter]);

  return (
    <div className="page">
      <div className="filter-row">
        {FILTERS.map((f) => (
          <button key={f} className={`select-chip${filter === f ? ' active' : ''}`} onClick={() => setFilter(f)}>
            {f}
          </button>
        ))}
      </div>

      <div className="panel" style={{ flex: '0 0 auto', maxHeight: '48%' }}>
        <div className="panel-header">
          <span className="panel-title">ACTIVE FAULTS</span>
          <span className={`badge ${activeFiltered.length ? 'critical' : 'normal'}`}>{activeFiltered.length}</span>
        </div>
        <div className="panel-body">
          {activeFiltered.length === 0 ? (
            <div className="empty-state">No active faults match this filter.</div>
          ) : (
            <div className="card-grid">
              {activeFiltered.map((f) => <FaultRow key={f.id} fault={f} />)}
            </div>
          )}
        </div>
      </div>

      <div className="panel" style={{ flex: 1, minHeight: 0 }}>
        <div className="panel-header">
          <span className="panel-title">HISTORICAL FAULTS</span>
          <span className="badge offline">{historicalFiltered.length}</span>
        </div>
        <div className="panel-body">
          {historicalFiltered.length === 0 ? (
            <div className="empty-state">No historical faults match this filter.</div>
          ) : (
            <div className="card-grid">
              {historicalFiltered.map((f) => <FaultRow key={f.id} fault={f} isHistorical />)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
