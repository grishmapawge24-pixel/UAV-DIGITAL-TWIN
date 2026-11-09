import React, { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { statusForMax, statusForRange, statusForMin } from '../../utils/status.js';

function Category({ title, defaultOpen = true, children }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="category">
      <button className="category-header" onClick={() => setOpen((o) => !o)}>
        <span>{title}</span>
        {open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
      </button>
      {open && <div className="category-body">{children}</div>}
    </div>
  );
}

function Row({ label, value, unit, status }) {
  return (
    <div className="scalar-row">
      <span className="scalar-label">{label}</span>
      <div className="scalar-value-group">
        <span className={`scalar-value status-text ${status}`}>{value}</span>
        {unit && <span className="scalar-unit">{unit}</span>}
        <span className={`status-dot ${status}`} />
      </div>
    </div>
  );
}

export default function CurrentStatus({ telemetry, limits }) {
  const { engine, thermal, fuel, lubrication, mechanical, electrical, sensorHealth } = telemetry;

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">CURRENT STATUS</span>
      </div>
      <div className="panel-body">
        <Category title="ENGINE">
          <Row label="RPM" value={engine.rpm} unit="rpm" status={statusForMax(engine.rpm, limits.rpmMax)} />
          <Row label="Load" value={engine.load} unit="%" status={statusForMax(engine.load, 95, { warnFraction: 0.85 })} />
          <Row label="Torque" value={engine.torque} unit="Nm" status="normal" />
          <Row label="Throttle Position" value={engine.throttlePosition} unit="%" status="normal" />
          <Row label="Manifold Pressure" value={engine.manifoldPressure} unit="kPa" status="normal" />
        </Category>

        <Category title="THERMAL">
          <Row label="CHT" value={thermal.cht} unit="°C" status={statusForMax(thermal.cht, limits.chtMax)} />
          <Row label="EGT" value={thermal.egt} unit="°C" status={statusForMax(thermal.egt, limits.egtMax)} />
          <Row label="Oil Temp" value={thermal.oilTemperature} unit="°C" status={statusForMax(thermal.oilTemperature, limits.oilTempMax)} />
          <Row label="Coolant Temp" value={thermal.coolantTemperature} unit="°C" status={statusForMax(thermal.coolantTemperature, limits.oilTempMax)} />
          <Row label="Intake Temp" value={thermal.intakeTemperature} unit="°C" status="normal" />
        </Category>

        <Category title="LUBRICATION">
          <Row
            label="Oil Pressure"
            value={lubrication.oilPressure}
            unit="bar"
            status={statusForRange(lubrication.oilPressure, limits.oilPressureMin, limits.oilPressureMax)}
          />
          <Row label="Oil Level" value={lubrication.oilLevel} unit="%" status={statusForMin(lubrication.oilLevel, 30)} />
        </Category>

        <Category title="FUEL">
          <Row label="Fuel Level" value={fuel.level} unit="%" status={statusForMin(fuel.level, 15)} />
          <Row label="Fuel Flow" value={fuel.flow} unit="L/h" status="normal" />
          <Row label="Fuel Pressure" value={fuel.pressure} unit="bar" status={statusForMin(fuel.pressure, 1.5)} />
          <Row label="Injector Status" value={fuel.injectorStatus} status={fuel.injectorStatus === 'NOMINAL' ? 'normal' : 'warning'} />
          <Row label="Pump Status" value={fuel.pumpStatus} status={fuel.pumpStatus === 'NOMINAL' ? 'normal' : 'warning'} />
        </Category>

        <Category title="MECHANICAL">
          <Row label="Vibration" value={mechanical.vibration} unit="mm/s" status={statusForMax(mechanical.vibration, limits.vibrationMax)} />
          <Row label="Propeller RPM" value={mechanical.propellerRpm} unit="rpm" status="normal" />
          <Row label="Crankshaft RPM" value={mechanical.crankshaftRpm} unit="rpm" status="normal" />
        </Category>

        <Category title="ELECTRICAL">
          <Row label="Battery" value={electrical.batteryVoltage} unit="V" status={statusForMin(electrical.batteryVoltage, limits.batteryVoltageMin)} />
          <Row label="Battery Current" value={electrical.batteryCurrent} unit="A" status="normal" />
          <Row label="Alternator" value={electrical.alternatorVoltage} unit="V" status="normal" />
          <Row label="ECU Voltage" value={electrical.ecuVoltage} unit="V" status="normal" />
          <Row label="Electrical Load" value={electrical.electricalLoad} unit="%" status={statusForMax(electrical.electricalLoad, 90)} />
        </Category>

        <Category title="SENSOR HEALTH" defaultOpen={false}>
          <Row label="Confidence" value={sensorHealth.confidence} unit="%" status={statusForMin(sensorHealth.confidence, 80)} />
          <Row label="Signal Quality" value={sensorHealth.signalQuality} unit="%" status={statusForMin(sensorHealth.signalQuality, 80)} />
          <Row label="Drift" value={sensorHealth.drift} unit="%" status={statusForMax(sensorHealth.drift, 3)} />
          <Row label="Noise" value={sensorHealth.noise} unit="%" status={statusForMax(sensorHealth.noise, 4)} />
          <Row label="Grounding" value={sensorHealth.grounding} status="normal" />
          <Row label="Calibration" value={sensorHealth.calibrationStatus} status="normal" />
        </Category>
      </div>
    </div>
  );
}
