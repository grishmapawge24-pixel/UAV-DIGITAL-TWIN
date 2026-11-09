import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import { severityHex } from '../../utils/status.js';

export default function FaultMarker({ position, severity, label, onClick }) {
  const ringRef = useRef();
  const color = severityHex[severity] || severityHex.warning;
  const pulse = severity === 'critical';

  useFrame(({ clock }) => {
    if (!ringRef.current) return;
    const t = clock.getElapsedTime();
    const scale = pulse ? 1 + Math.sin(t * 5) * 0.35 : 1;
    ringRef.current.scale.setScalar(scale);
    ringRef.current.material.opacity = pulse ? 0.5 + Math.sin(t * 5) * 0.3 : 0.6;
  });

  return (
    <group position={position}>
      <mesh ref={ringRef}>
        <ringGeometry args={[0.09, 0.14, 24]} />
        <meshBasicMaterial color={color} transparent opacity={0.6} side={2} />
      </mesh>
      <mesh>
        <sphereGeometry args={[0.045, 12, 12]} />
        <meshBasicMaterial color={color} />
      </mesh>
      <Html position={[0, 0.22, 0]} center style={{ pointerEvents: 'auto', userSelect: 'none' }}>
        <div
          onClick={onClick}
          className={`component-callout-tag fault-${severity}`}
          style={{
            fontSize: '9px',
            fontWeight: 800,
            padding: '2px 6px',
            borderRadius: '3px',
            border: `1.5px solid ${color}`,
            background: 'rgba(255, 255, 255, 0.96)',
            color: color,
            boxShadow: '0 2px 4px rgba(0,0,0,0.12)',
            whiteSpace: 'nowrap',
            transform: 'scale(0.8)',
            transformOrigin: 'center center',
            cursor: 'pointer'
          }}
        >
          ⚠️ {label.toUpperCase()}
        </div>
      </Html>
    </group>
  );
}
