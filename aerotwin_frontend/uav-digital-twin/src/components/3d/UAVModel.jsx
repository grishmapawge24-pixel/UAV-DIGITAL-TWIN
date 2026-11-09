import React, { useMemo, useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import FaultMarker from './FaultMarker.jsx';
import { severityHex } from '../../utils/status.js';
import { resolveFaultMeta } from '../../data/mockFaults.js';

const NEUTRAL = '#6d7869';
const NEUTRAL_LIGHT = '#8b9284';
const SIGNAL = '#1f6f66';
const PRIMARY_RED = '#b3261e';
const SECONDARY_ORANGE = '#c1671a';

function partMaterial(status, isSelected, isHovered, isPrimaryFault) {
  if (isSelected) return { color: SIGNAL, emissive: SIGNAL, emissiveIntensity: 0.45 };
  if (isHovered) return { color: '#2f8f7f', emissive: '#1f6f66', emissiveIntensity: 0.25 };
  if (status && status !== 'normal' && status !== 'offline') {
    const c = severityHex[status];
    if (isPrimaryFault) return { color: PRIMARY_RED, emissive: PRIMARY_RED, emissiveIntensity: status === 'critical' ? 0.9 : 0.5 };
    return { color: SECONDARY_ORANGE, emissive: SECONDARY_ORANGE, emissiveIntensity: status === 'major' ? 0.6 : 0.4 };
  }
  return { color: NEUTRAL, emissive: '#000000', emissiveIntensity: 0 };
}

export default function UAVModel({
  selectedComponentId,
  onComponentClick,
  faultsByComponent,
  spinPropeller = true
}) {
  const [hoveredId, setHoveredId] = useState(null);
  const propRef = useRef();

  useFrame((_, delta) => {
    if (propRef.current && spinPropeller) {
      propRef.current.rotation.z += delta * 14;
    }
  });

  const componentPositions = useMemo(
    () => ({
      propeller: [0, 0, 2.05],
      engine: [0, 0, 1.55],
      lubricationSystem: [0.28, 0.05, 1.3],
      coolingSystem: [-0.28, 0.05, 1.25],
      fuelSystem: [0, -0.28, 0.1],
      avionics: [0, 0.22, 0.5],
      electricalSystem: [0, -0.15, -0.5],
      battery: [0, -0.15, -0.95],
      sensors: [0, 0.18, 1.85]
    }),
    []
  );

  function getFaultStatus(id) {
    const f = faultsByComponent[id];
    if (!f) return { severity: 'normal', isPrimary: false };
    const meta = resolveFaultMeta(f.type);
    const isPrimary = f.affectedComponents?.[0] === id;
    return { severity: f.severity, isPrimary };
  }

  function renderPart(id, geometryEl, labelPos) {
    const { severity, isPrimary } = getFaultStatus(id);
    const isSelected = selectedComponentId === id;
    const isHovered = hoveredId === id;
    const mat = partMaterial(severity, isSelected, isHovered, isPrimary);
    const fault = faultsByComponent[id];

    return (
      <group
        position={componentPositions[id]}
        onClick={(e) => {
          e.stopPropagation();
          onComponentClick(id);
        }}
        onPointerOver={(e) => {
          e.stopPropagation();
          setHoveredId(id);
          document.body.style.cursor = 'pointer';
        }}
        onPointerOut={() => {
          setHoveredId(null);
          document.body.style.cursor = 'auto';
        }}
      >
        <mesh castShadow receiveShadow>
          {geometryEl.props.children}
          <meshStandardMaterial
            color={mat.color}
            emissive={mat.emissive}
            emissiveIntensity={mat.emissiveIntensity}
            roughness={0.4}
            metalness={0.5}
          />
        </mesh>
        {(isHovered || isSelected) && (
          <Html position={labelPos || [0, 0.28, 0]} center style={{ pointerEvents: 'auto', userSelect: 'none' }}>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onComponentClick(id);
              }}
              style={{
                cursor: 'pointer',
                fontSize: '9px',
                padding: '2px 6px',
                borderRadius: '3px',
                pointerEvents: 'auto',
                border: isSelected ? '1.5px solid var(--ember)' : '1px solid #b7bfa8',
                background: isSelected ? 'var(--ember)' : 'rgba(255, 255, 255, 0.96)',
                color: isSelected ? '#ffffff' : '#1a2420',
                fontWeight: 700,
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
                boxShadow: '0 2px 4px rgba(0,0,0,0.12)',
                whiteSpace: 'nowrap',
                transform: 'scale(0.8)',
                transformOrigin: 'center center'
              }}
            >
              {id === 'engine' ? '⚡ ENGINE' : id.replace(/([A-Z])/g, ' $1')}
            </button>
          </Html>
        )}
        {fault && (
          <FaultMarker
            position={[0, (labelPos ? labelPos[1] : 0.28) + 0.14, 0]}
            severity={fault.severity}
            label={resolveFaultMeta(fault.type).label}
            onClick={() => onComponentClick(id)}
          />
        )}
      </group>
    );
  }

  return (
    <group rotation={[0, Math.PI, 0]}>
      <mesh position={[0, 0, 0.3]} rotation={[Math.PI / 2, 0, 0]}>
        <capsuleGeometry args={[0.32, 2.9, 8, 16]} />
        <meshStandardMaterial color="#b7bfa8" transparent opacity={0.45} roughness={0.3} metalness={0.4} />
      </mesh>

      <mesh position={[0, 0, 0.15]}>
        <boxGeometry args={[3.6, 0.06, 0.55]} />
        <meshStandardMaterial color="#8b9284" roughness={0.4} metalness={0.5} />
      </mesh>

      <group position={[0, 0, -1.75]}>
        <mesh position={[0, 0.35, 0]}>
          <boxGeometry args={[0.06, 0.7, 0.4]} />
          <meshStandardMaterial color="#8b9284" roughness={0.4} metalness={0.5} />
        </mesh>
        <mesh position={[0, 0.06, 0]}>
          <boxGeometry args={[1.3, 0.05, 0.35]} />
          <meshStandardMaterial color="#8b9284" roughness={0.4} metalness={0.5} />
        </mesh>
      </group>

      {renderPart('propeller', <mesh><cylinderGeometry args={[0.07, 0.07, 0.12, 12]} /></mesh>, [0, 0.38, 0])}
      {renderPart('engine', <mesh><cylinderGeometry args={[0.26, 0.3, 0.5, 12]} /></mesh>, [0, 0.32, 0])}
      {renderPart('lubricationSystem', <mesh><boxGeometry args={[0.16, 0.16, 0.22]} /></mesh>, [0, 0.22, 0])}
      {renderPart('coolingSystem', <mesh><boxGeometry args={[0.18, 0.18, 0.3]} /></mesh>, [0, 0.22, 0])}
      {renderPart('fuelSystem', <mesh><boxGeometry args={[0.3, 0.2, 0.7]} /></mesh>, [0, 0.26, 0])}
      {renderPart('avionics', <mesh><boxGeometry args={[0.34, 0.18, 0.4]} /></mesh>, [0, 0.22, 0])}
      {renderPart('electricalSystem', <mesh><boxGeometry args={[0.24, 0.16, 0.34]} /></mesh>, [0, 0.20, 0])}
      {renderPart('battery', <mesh><boxGeometry args={[0.26, 0.18, 0.3]} /></mesh>, [0, 0.22, 0])}
      {renderPart('sensors', <mesh><sphereGeometry args={[0.09, 12, 12]} /></mesh>, [0, 0.18, 0])}

      <group position={componentPositions.propeller} ref={propRef}>
        <mesh>
          <boxGeometry args={[0.045, 0.85, 0.03]} />
          <meshStandardMaterial color="#46503f" roughness={0.3} metalness={0.7} />
        </mesh>
        <mesh rotation={[0, 0, Math.PI / 2]}>
          <boxGeometry args={[0.045, 0.85, 0.03]} />
          <meshStandardMaterial color="#46503f" roughness={0.3} metalness={0.7} />
        </mesh>
      </group>
    </group>
  );
}
