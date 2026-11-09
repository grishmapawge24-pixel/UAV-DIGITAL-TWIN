# UAV Digital Twin & Offline Simulation System — Development Summary

This document provides a comprehensive technical overview of all enhancements, features, architectural modifications, and bug fixes implemented in this codebase.

---

## 1. Light Cockpit Theme Transformation
- **Color Architecture**: Converted the entire application from a dark theme to a high-contrast off-white cockpit palette.
  - Background Base: `#f0f3f8` (Deep Cockpit Background)
  - Surface Panels: `#fcfdfe` (Elevated Card Surfaces)
  - Plates & Insets: `#f5f7fa` and `#edf2f7` (Categorized Sections & Gauge Backdrops)
  - Structural Lines & Borders: `#e2e8f0` and `#cbd5e1`
  - High-Contrast Text: `#0f172a` (Primary), `#334155` (Secondary), `#64748b` (Muted/Labels)
  - Telemetry Accents: `#ea580c` (Ember/Primary), `#0284c7` (Signal/Normal), `#16a34a` (Go-Green), `#d97706` (Amber Warning), `#dc2626` (Critical Red)

---

## 2. Offline UAV Map Simulation (`/map-simulation`)
- **100% Offline Vector Map Engine**:
  - Implemented completely self-contained SVG map simulation with zero external tile server or API dependencies.
  - Interactive tactical grid with sector rings (Base, Outer Patrol, Range Limits), terrain relief topography, compass rose, and coordinate grids.
- **Multi-UAV Fleet Simulation**:
  - Simulates 5 active UAVs simultaneously (`UAV-01` to `UAV-05`).
  - Smooth real-time coordinate interpolation along predefined flight paths.
  - Real-time breadcrumb trail polylines and heading indicator vectors.
- **Interactive Controls & Telemetry**:
  - Simulation transport controls: **Start**, **Pause**, **Resume**, and **Reset**.
  - Speed multipliers: **1x**, **2x**, and **5x**.
  - Interactive UAV selection with **Follow Cam** mode that centers and locks onto the selected UAV.
  - Live HUD telemetry overlay displaying coordinates, altitude, airspeed, heading, mission phase, and operational status.

---

## 3. Interactive 3D UAV Digital Twin Refinements
- **Half-Page Central Viewport**:
  - Resized the 3D twin canvas to a 420px viewport with closer camera positioning (`[2.8, 1.4, 2.8]`, `fov: 36`) to serve as the visual centerpiece.
- **Compact & Interactive 3D Tags**:
  - Sized down all 3D mesh callouts (`AVIONICS`, `ENGINE`, `FUEL SYSTEM`, `BATTERY`, `PAYLOAD`, etc.) to crisp pill badges with hover and click states.
  - Added a top parts filter bar (`PARTS:`) for rapid component selection.
- **Multi-UAV Engine Inspection Drawer**:
  - Clicking **`⚡ ENGINE`** or the engine mesh opens a dedicated comparison drawer.
  - Full technical comparison across all 3 primary UAV engines:
    - **UAV-01**: Rotax 914 Turbo (115 hp, 1,211 cc, Turbocharged)
    - **UAV-02**: Rotax 912 iS (100 hp, 1,352 cc, EFI)
    - **UAV-03**: Rotax 914 Recon (115 hp, 1,211 cc, High-Altitude Turbo)
  - Displays live engine telemetry, operating limits (RPM, CHT, EGT), and active fault details.

---

## 4. Real-time Propulsion Engine Trends (3x2 Grid)
- **Direct Sub-Viewport Placement**:
  - Positioned directly underneath the 3D UAV viewer without vertical overlap or dead space.
- **3-Across Grid Configuration**:
  - Structured using CSS Grid `repeat(3, 1fr)` to fit exactly **3 charts per line** across 2 rows (6 primary metrics total):
    - **Row 1**:
      1. Engine RPM (`rpm`)
      2. Cylinder Head Temperature (`cht` - °C)
      3. Exhaust Gas Temperature (`egt` - °C)
    - **Row 2**:
      4. Oil Pressure (`oilPressure` - bar)
      5. Fuel Flow (`fuelFlow` - L/h)
      6. Engine Vibration (`vibration` - mm/s)
- **Compact Sparklines**:
  - Lightweight Area charts with gradient fills, live numeric value indicators, and tooltips.

---

## 5. Left & Right Telemetry Columns
- **Left Column**:
  - **UAV Information**: Profile ID, airframe type, engine model, mission designation, flight time, altitude, airspeed, and airborne status.
  - **Atmospheric Conditions**: Altitude, ambient pressure, temperature, humidity, wind vector, vibration, and compact offline vector route preview.
  - **Mission Reliability**: Live Health Index gauge, Remaining Useful Life (RUL) hours, risk assessment, and progress meters.
- **Right Column**:
  - **Current Status**: Real-time telemetry categorized into collapsible sections (Engine, Thermal, Lubrication, Fuel, Mechanical, Electrical, Sensor Health) with live status indicators.
  - **Fault Detection**: Active diagnostic alert cards with severity color-coding, affected components, recommended actions, and AI/ML predictive anomaly probability meters.

---

## 6. Key Bug Fixes & Technical Resolutions
- **Three.js Drei `<Html>` Sizing Fix**:
  - Removed `distanceFactor` multipliers in `FaultMarker.jsx` and `UAVModel.jsx` that caused component labels and fault markers (e.g. `Cooling Degradation` on `UAV-02`) to balloon into screen-covering text boxes.
  - Standardized all 3D HTML overlays with explicit `scale(0.8)` CSS transforms and `fontSize: 9px`.
- **CSS Grid Collision Resolution**:
  - Replaced ambiguous grid row spans in `Dashboard.jsx` with a clean 3-column flex/grid hierarchy (`310px minmax(560px, 1fr) 320px`), ensuring graphs and sidebars render predictably without clipping.
- **JSX Structure Integrity**:
  - Fixed orphaned tag structures and validated error-free builds with Vite.

---

## 7. File Map of Key Modifications
- `src/pages/Dashboard.jsx`: Central telemetry dashboard with 3-column layout, 3D twin, and 3x2 engine sparklines.
- `src/pages/MapSimulation.jsx`: Offline multi-UAV vector map simulation page.
- `src/components/3d/UAVViewer.jsx`: 3D Canvas container, parts toolbar, and 3-UAV engine inspection drawer.
- `src/components/3d/UAVModel.jsx`: 3D airframe meshes, propeller rotation, and component click handlers.
- `src/components/3d/FaultMarker.jsx`: Pulsing 3D fault indicator with compact clickable badge.
- `src/components/charts/EngineTrends.jsx`: Container for real-time engine telemetry streaming.
- `src/components/charts/EngineCharts.jsx`: Recharts area sparklines configured in 3x2 grid.
- `src/components/dashboard/EnvironmentPanel.jsx`: Weather conditions and offline mini-map route.
- `src/components/dashboard/OfflineMap.jsx`: Self-contained vector flight path preview.
- `src/components/layout/RouteNav.jsx`: Top navigation including Map Simulation route.
- `src/styles/dashboard.css`: Core design system and off-white color variables.
- `src/styles/components.css`: Component-level styles, drawer, cards, badges, and layout utilities.
