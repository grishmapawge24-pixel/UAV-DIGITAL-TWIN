// UAV configuration registry.
// To add a new UAV: append a new object to this array with a unique `id`.
// `modelPath` is where a real .glb should be placed later (see /public/models).
// Nothing else in the app needs to change — Header, Dashboard and the 3D
// viewer all read from this list.

export const uavProfiles = [
  {
    id: 'UAV-01',
    name: 'UAV-01',
    type: 'MALE UAV — Fixed Wing',
    engineType: 'Rotax 914 (Turbocharged Aero-Piston, 4-cyl)',
    modelPath: '/models/uav-01.glb', // drop a real .glb here to replace the procedural placeholder
    mission: 'ISR Endurance Patrol',
    sensorList: [
      'RPM Sensor', 'CHT Sensor x4', 'EGT Sensor x4', 'Oil Pressure Transducer',
      'Oil Temp Sensor', 'Fuel Flow Meter', 'Fuel Pressure Sensor', 'Vibration Accelerometer',
      'Coolant Temp Sensor', 'MAP Sensor', 'Battery Voltage/Current Sensor', 'Alternator Sensor'
    ],
    operatingLimits: {
      rpmMax: 5800,
      chtMax: 190,
      egtMax: 820,
      oilPressureMin: 2.0,
      oilPressureMax: 5.5,
      oilTempMax: 118,
      vibrationMax: 4.5,
      batteryVoltageMin: 22.0
    },
    missionParameters: {
      cruiseAltitudeFt: 18500,
      endurance: '24 hrs',
      cruiseSpeedKts: 65
    }
  },
  {
    id: 'UAV-02',
    name: 'UAV-02',
    type: 'MALE UAV — Fixed Wing',
    engineType: 'Rotax 912 iS (Naturally Aspirated Aero-Piston, 4-cyl)',
    modelPath: '/models/uav-02.glb',
    mission: 'Maritime Surveillance',
    sensorList: [
      'RPM Sensor', 'CHT Sensor x4', 'EGT Sensor x4', 'Oil Pressure Transducer',
      'Oil Temp Sensor', 'Fuel Flow Meter', 'Fuel Pressure Sensor', 'Vibration Accelerometer',
      'Coolant Temp Sensor', 'MAP Sensor', 'Battery Voltage/Current Sensor', 'Alternator Sensor'
    ],
    operatingLimits: {
      rpmMax: 5500,
      chtMax: 185,
      egtMax: 800,
      oilPressureMin: 1.8,
      oilPressureMax: 5.0,
      oilTempMax: 115,
      vibrationMax: 4.5,
      batteryVoltageMin: 22.0
    },
    missionParameters: {
      cruiseAltitudeFt: 14000,
      endurance: '18 hrs',
      cruiseSpeedKts: 58
    }
  },
  {
    id: 'UAV-03',
    name: 'UAV-03',
    type: 'MALE UAV — Fixed Wing',
    engineType: 'Rotax 914 (Turbocharged Aero-Piston, 4-cyl)',
    modelPath: '/models/uav-03.glb',
    mission: 'High-Altitude Reconnaissance',
    sensorList: [
      'RPM Sensor', 'CHT Sensor x4', 'EGT Sensor x4', 'Oil Pressure Transducer',
      'Oil Temp Sensor', 'Fuel Flow Meter', 'Fuel Pressure Sensor', 'Vibration Accelerometer',
      'Coolant Temp Sensor', 'MAP Sensor', 'Battery Voltage/Current Sensor', 'Alternator Sensor'
    ],
    operatingLimits: {
      rpmMax: 5800,
      chtMax: 190,
      egtMax: 820,
      oilPressureMin: 2.0,
      oilPressureMax: 5.5,
      oilTempMax: 118,
      vibrationMax: 4.5,
      batteryVoltageMin: 22.0
    },
    missionParameters: {
      cruiseAltitudeFt: 22000,
      endurance: '20 hrs',
      cruiseSpeedKts: 62
    }
  }
];

export function getUAVProfile(id) {
  return uavProfiles.find((p) => p.id === id) || uavProfiles[0];
}

// UAV component registry — every clickable part of the 3D model.
// `id` must match the mesh identifier used in UAVModel.jsx so that fault
// data (see mockFaults.js, keyed by componentId) can be mapped to the
// correct 3D part and to the correct panel in the component drawer.
export const uavComponents = [
  { id: 'engine', label: 'Engine' },
  { id: 'fuelSystem', label: 'Fuel System' },
  { id: 'coolingSystem', label: 'Cooling System' },
  { id: 'lubricationSystem', label: 'Lubrication System' },
  { id: 'electricalSystem', label: 'Electrical System' },
  { id: 'battery', label: 'Battery' },
  { id: 'avionics', label: 'Avionics' },
  { id: 'sensors', label: 'Sensors' },
  { id: 'propeller', label: 'Propeller' }
];
