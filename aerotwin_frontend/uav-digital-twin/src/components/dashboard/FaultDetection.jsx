import React from 'react';
import { resolveFaultMeta } from '../../data/mockFaults.js';

function timeAgo(iso) {
  const mins = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (mins < 60) return `${mins}m ago`;
  return `${Math.round(mins / 60)}h ago`;
}

export default function FaultDetection({ activeFaults, ai }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">FAULT DETECTION</span>
        <span className={`badge ${activeFaults.length ? 'critical' : 'normal'}`}>
          {activeFaults.length ? `${activeFaults.length} ACTIVE` : 'CLEAR'}
        </span>
      </div>
      <div className="panel-body">
        {activeFaults.length === 0 ? (
          <div className="empty-state">No active faults. All systems nominal.</div>
        ) : (
          activeFaults.map((fault) => {
            const meta = resolveFaultMeta(fault.type);
            return (
              <div key={fault.id} className={`fault-card ${fault.severity}`}>
                <div className="fault-card-top">
                  <span className="fault-card-title">{meta.label}</span>
                  <span className={`badge ${fault.severity}`}>{fault.severity.toUpperCase()}</span>
                </div>
                <div className="fault-card-meta">
                  <b>Detected:</b> {timeAgo(fault.detectedAt)} &nbsp;·&nbsp; <b>Confidence:</b> {fault.confidence ?? '—'}%
                  <br />
                  <b>Probable cause:</b> {fault.probableCause}
                  <br />
                  <b>Affected:</b> {fault.affectedComponents.join(', ')}
                  <br />
                  <b>Action:</b> {fault.recommendedAction}
                </div>
              </div>
            );
          })
        )}

        <div className="category" style={{ marginTop: activeFaults.length ? 6 : 0 }}>
          <div className="category-header" style={{ cursor: 'default' }}>
            <span>AI/ML FAULT PROBABILITY</span>
          </div>
          <div className="category-body">
            {ai.faultProbabilities.map((p) => (
              <div key={p.name} className="predict-row">
                <span className="predict-label">{p.name}</span>
                <div className="predict-track">
                  <div className="predict-fill" style={{ width: `${p.probability}%` }} />
                </div>
                <span className="predict-value mono">{p.probability}%</span>
              </div>
            ))}
            <div className="scalar-row" style={{ marginTop: 4 }}>
              <span className="scalar-label">Anomaly Score</span>
              <span className="scalar-value mono" style={{ color: 'var(--text-primary)' }}>{ai.anomalyScore}%</span>
            </div>
            <div className="fault-card-meta" style={{ marginTop: 4 }}>
              <b>Recommendation:</b> {ai.recommendation}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
