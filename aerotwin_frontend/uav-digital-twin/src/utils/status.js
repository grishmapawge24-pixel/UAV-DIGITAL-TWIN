// Shared helpers for mapping a numeric value against operating limits to a
// status level, and for severity <-> color/label lookups used across panels
// and the 3D viewer.

export const STATUS = {
  NORMAL: 'normal',
  WARNING: 'warning',
  MAJOR: 'major',
  CRITICAL: 'critical',
  INFO: 'info',
  OFFLINE: 'offline'
};

/**
 * Given a value and a [min, max] safe band, return a status level.
 * `warnMargin` / `majorMargin` are fractions of the band width used to
 * step down from normal -> warning -> major -> critical as the value
 * approaches or exceeds the limit.
 */
export function statusForRange(value, min, max, { warnMargin = 0.1, majorMargin = 0.03 } = {}) {
  if (value == null) return STATUS.OFFLINE;
  const span = max - min || 1;
  if (value < min || value > max) {
    const overshoot = value < min ? (min - value) / span : (value - max) / span;
    if (overshoot > majorMargin * 2) return STATUS.CRITICAL;
    return STATUS.MAJOR;
  }
  const distToEdge = Math.min(value - min, max - value) / span;
  if (distToEdge < warnMargin) return STATUS.WARNING;
  return STATUS.NORMAL;
}

/** Status for a value that only has an upper safe limit. */
export function statusForMax(value, max, { warnFraction = 0.9, majorFraction = 1.0 } = {}) {
  if (value == null) return STATUS.OFFLINE;
  if (value >= max * 1.08) return STATUS.CRITICAL;
  if (value >= max * majorFraction) return STATUS.MAJOR;
  if (value >= max * warnFraction) return STATUS.WARNING;
  return STATUS.NORMAL;
}

/** Status for a value that only has a lower safe limit. */
export function statusForMin(value, min, { warnFraction = 1.1, majorFraction = 1.0 } = {}) {
  if (value == null) return STATUS.OFFLINE;
  if (value <= min * 0.9) return STATUS.CRITICAL;
  if (value <= min * majorFraction) return STATUS.MAJOR;
  if (value <= min * warnFraction) return STATUS.WARNING;
  return STATUS.NORMAL;
}

export const severityColorVar = {
  normal: 'var(--status-normal)',
  warning: 'var(--status-warning)',
  major: 'var(--status-major)',
  critical: 'var(--status-critical)',
  info: 'var(--status-info)',
  offline: 'var(--status-offline)'
};

export const severityHex = {
  normal: '#2e7d46',
  warning: '#b8860b',
  major: '#c1671a',
  critical: '#b3261e',
  info: '#1f6f66',
  offline: '#8b9284'
};

export function worstStatus(...statuses) {
  const order = [STATUS.CRITICAL, STATUS.MAJOR, STATUS.WARNING, STATUS.INFO, STATUS.NORMAL, STATUS.OFFLINE];
  for (const s of order) {
    if (statuses.includes(s)) return s;
  }
  return STATUS.NORMAL;
}

export function formatDuration(minutes) {
  const h = Math.floor(minutes / 60);
  const m = Math.round(minutes % 60);
  return `${h}h ${m}m`;
}

export function formatClock(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}
