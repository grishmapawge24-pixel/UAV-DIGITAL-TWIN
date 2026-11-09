import React from 'react';
import { SlidersHorizontal, RotateCcw, AlertTriangle } from 'lucide-react';
import { OVERRIDE_FIELDS } from '../../utils/manualOverride.js';

function OverrideRow({ field, value, status, disabled, onChange }) {
  return (
    <div className={`override-row${disabled ? ' disabled' : ''}`}>
      <div className="override-row-top">
        <span className="override-row-label">
          <span className={`status-dot ${status}`} />
          {field.label}
        </span>
        <span className="override-row-value">
          <input
            type="number"
            min={field.min}
            max={field.max}
            step={field.step}
            value={value}
            disabled={disabled}
            onChange={(e) => onChange(field.key, Number(e.target.value))}
          />
          <span className="scalar-unit">{field.unit}</span>
        </span>
      </div>
      <input
        type="range"
        min={field.min}
        max={field.max}
        step={field.step}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(field.key, Number(e.target.value))}
      />
    </div>
  );
}

export default function ManualOverride({ enabled, onToggle, values, statuses, onChange, onReset }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <SlidersHorizontal size={13} />
          Manual Parameter Override
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {enabled && (
            <button
              className="btn-secondary"
              style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '4px 9px', fontSize: 10 }}
              onClick={onReset}
            >
              <RotateCcw size={11} />
              Reset to Live
            </button>
          )}
          <button
            className={`toggle-switch${enabled ? ' on' : ''}`}
            onClick={() => onToggle(!enabled)}
            aria-pressed={enabled}
            aria-label="Toggle manual override mode"
          >
            <span className="toggle-switch-knob" />
          </button>
        </div>
      </div>
      <div className="panel-body">
        {enabled && (
          <div className="override-banner">
            <AlertTriangle size={13} />
            Manual override is active — displayed values are operator-set test inputs, not live sensor readings.
          </div>
        )}
        <div className="override-grid">
          {OVERRIDE_FIELDS.map((field) => (
            <OverrideRow
              key={field.key}
              field={field}
              value={values[field.key]}
              status={statuses[field.key] || 'normal'}
              disabled={!enabled}
              onChange={onChange}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
