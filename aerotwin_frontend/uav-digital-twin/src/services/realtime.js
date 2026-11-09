import { getReplayAnalysis, mergeAnalysis, mergeTelemetryPoint } from './api.js';

export const WS_BASE = (import.meta.env.VITE_WS_BASE_URL || 'ws://127.0.0.1:8000').replace(/\/$/, '');

/**
 * Replays the selected real NGAFID flight over the backend WebSocket. The
 * backend labels every message as historical; this never simulates live data.
 */
export function startRealtimeFeed(baseline, onUpdate) {
  if (!baseline?.flightId) return () => {};

  const socket = new WebSocket(`${WS_BASE}/ws/telemetry/${baseline.flightId}?interval_ms=800&max_points=500`);
  socket.onmessage = ({ data }) => {
    const message = JSON.parse(data);
    if (!message.point) return;
    onUpdate((current) => mergeTelemetryPoint(current || baseline, message.point));
    // Analysis needs a temporal window. At this cadence the dashboard updates
    // its ML state every ten replay samples, while telemetry remains smooth.
    if (message.index >= 19 && message.index % 10 === 0) {
      getReplayAnalysis(baseline.flightId, message.point.timestep)
        .then((analysis) => onUpdate((current) => mergeAnalysis(current, analysis)))
        .catch(() => {}); // retain the last real-data analysis during a transient API failure
    }
  };
  // Keep the existing REST snapshot visible if a backend restart/network issue
  // closes the stream; no fabricated fallback telemetry is used.
  socket.onerror = () => socket.close();
  return () => socket.close();
}
