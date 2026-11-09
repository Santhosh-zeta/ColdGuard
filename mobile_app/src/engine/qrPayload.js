/**
 * Parsing of QR-code payloads from temperature loggers.
 *
 * Supported payload shapes (all work fully offline):
 *   1. JSON:              {"loggerId":"FT2-123","timestamps":[...],"temperatures":[...]}
 *   2. URL-encoded JSON:  the same JSON passed through encodeURIComponent
 *   3. URL with query:    https://example.org/log?loggerId=FT2-123
 *   4. URL whose query carries a `data` or `payload` parameter holding (2)
 *
 * Accepted keys (case as shown):
 *   logger id    loggerId | loggerID | logger_id
 *   timestamps   timestamps | times        (Unix seconds, Unix milliseconds or ISO-8601 strings)
 *   temperatures temperatures | temperaturesC | temperatures_c | temps
 *
 * NOTE: the exact payload of real Berlinger Fridge-tag QR codes is not
 * publicly documented here; the shape above follows issue #19. Vendor-specific
 * formats should be added as separate adapters.
 */

export const MIN_READINGS = 2;
export const MIN_TEMP_C = -30;
export const MAX_TEMP_C = 60;

/** Error with a stable `code` so the UI can show a translated message. */
export class QrPayloadError extends Error {
  constructor(code, message) {
    super(message);
    this.name = 'QrPayloadError';
    this.code = code;
  }
}

const ID_KEYS = ['loggerId', 'loggerID', 'logger_id'];
const TS_KEYS = ['timestamps', 'times'];
const TEMP_KEYS = ['temperatures', 'temperaturesC', 'temperatures_c', 'temps'];

function firstDefined(obj, keys) {
  for (const k of keys) {
    if (obj[k] !== undefined && obj[k] !== null) return obj[k];
  }
  return undefined;
}

function tryJson(text) {
  try {
    const value = JSON.parse(text);
    return value !== null && typeof value === 'object' && !Array.isArray(value) ? value : null;
  } catch {
    return null;
  }
}

function tryDecode(text) {
  try {
    return decodeURIComponent(text);
  } catch {
    return text;
  }
}

/** Find the JSON object carried by the raw QR text, or null. */
function extractObject(raw) {
  const direct = tryJson(raw);
  if (direct) return direct;

  const decoded = tryJson(tryDecode(raw));
  if (decoded) return decoded;

  // URL forms: look for loggerId or an embedded JSON payload in the query.
  const queryStart = raw.indexOf('?');
  if (queryStart !== -1) {
    const params = {};
    for (const part of raw.slice(queryStart + 1).split('&')) {
      if (!part) continue;
      const eq = part.indexOf('=');
      const key = tryDecode(eq === -1 ? part : part.slice(0, eq));
      const value = tryDecode(eq === -1 ? '' : part.slice(eq + 1).replace(/\+/g, ' '));
      params[key] = value;
    }
    const embedded = tryJson(params.data || params.payload || '');
    if (embedded) return { ...params, ...embedded };
    if (firstDefined(params, ID_KEYS) !== undefined) return params;
  }
  return null;
}

function toUnixSeconds(value, index) {
  let seconds;
  if (typeof value === 'number') {
    seconds = value > 1e11 ? value / 1000 : value; // milliseconds vs seconds
  } else if (typeof value === 'string' && value.trim() !== '') {
    const asNumber = Number(value);
    seconds = Number.isFinite(asNumber)
      ? (asNumber > 1e11 ? asNumber / 1000 : asNumber)
      : Date.parse(value) / 1000;
  } else {
    seconds = NaN;
  }
  if (!Number.isFinite(seconds)) {
    throw new QrPayloadError('badTimestamp', `Timestamp at index ${index} is not valid`);
  }
  return seconds;
}

function toTemperature(value, index) {
  const t = typeof value === 'string' && value.trim() !== '' ? Number(value) : value;
  if (typeof t !== 'number' || !Number.isFinite(t)) {
    throw new QrPayloadError('badTemperature', `Temperature at index ${index} is not a number`);
  }
  if (t < MIN_TEMP_C || t > MAX_TEMP_C) {
    throw new QrPayloadError(
      'temperatureOutOfRange',
      `Temperature at index ${index} (${t}) is outside ${MIN_TEMP_C} to ${MAX_TEMP_C} °C`
    );
  }
  return t;
}

/**
 * Parse the raw text of a scanned QR code.
 *
 * @param {string} raw
 * @returns {{loggerId: string|null, readings: Array<{timestamp: number, temperatureC: number}>|null}}
 *   `readings` is null when the QR carries only a logger id.
 * @throws {QrPayloadError} with code:
 *   'empty' | 'unrecognised' | 'lengthMismatch' | 'tooFewReadings' |
 *   'badTimestamp' | 'badTemperature' | 'temperatureOutOfRange' | 'notIncreasing'
 */
export function parseLoggerQr(raw) {
  if (typeof raw !== 'string' || raw.trim() === '') {
    throw new QrPayloadError('empty', 'The QR code is empty');
  }
  const obj = extractObject(raw.trim());
  if (!obj) {
    throw new QrPayloadError('unrecognised', 'This QR code is not a recognised logger format');
  }

  const idValue = firstDefined(obj, ID_KEYS);
  const loggerId = idValue === undefined ? null : String(idValue).trim() || null;

  const rawTs = firstDefined(obj, TS_KEYS);
  const rawTemps = firstDefined(obj, TEMP_KEYS);

  if (rawTs === undefined && rawTemps === undefined) {
    if (loggerId === null) {
      throw new QrPayloadError('unrecognised', 'This QR code is not a recognised logger format');
    }
    return { loggerId, readings: null };
  }

  if (!Array.isArray(rawTs) || !Array.isArray(rawTemps)) {
    throw new QrPayloadError('unrecognised', 'Timestamps and temperatures must both be lists');
  }
  if (rawTs.length !== rawTemps.length) {
    throw new QrPayloadError(
      'lengthMismatch',
      `Got ${rawTs.length} timestamps but ${rawTemps.length} temperatures`
    );
  }
  if (rawTs.length < MIN_READINGS) {
    throw new QrPayloadError('tooFewReadings', `At least ${MIN_READINGS} readings are required`);
  }

  const readings = rawTs.map((ts, i) => ({
    timestamp: toUnixSeconds(ts, i),
    temperatureC: toTemperature(rawTemps[i], i),
  }));

  for (let i = 1; i < readings.length; i += 1) {
    if (readings[i].timestamp <= readings[i - 1].timestamp) {
      throw new QrPayloadError(
        'notIncreasing',
        `Timestamps must be strictly increasing (problem at index ${i})`
      );
    }
  }

  return { loggerId, readings };
}

/** Convert parsed readings into the {time, temp} string rows used by InputScreen. */
export function readingsToRows(readings) {
  return readings.map(r => ({
    time: new Date(r.timestamp * 1000).toISOString(),
    temp: String(r.temperatureC),
  }));
}
