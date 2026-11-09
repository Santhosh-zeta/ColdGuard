import { parseLoggerQr, readingsToRows, QrPayloadError } from '../qrPayload';

const T0 = 1694592000; // 2023-09-13T08:00:00Z
const payload = (extra = {}) => ({
  loggerId: 'FT2-123',
  timestamps: [T0, T0 + 3600, T0 + 7200],
  temperatures: [5.2, 6.1, 4.8],
  ...extra,
});

function codeOf(fn) {
  try {
    fn();
  } catch (e) {
    expect(e).toBeInstanceOf(QrPayloadError);
    return e.code;
  }
  throw new Error('expected parseLoggerQr to throw');
}

describe('parseLoggerQr: accepted formats', () => {
  test('plain JSON with log and id', () => {
    const r = parseLoggerQr(JSON.stringify(payload()));
    expect(r.loggerId).toBe('FT2-123');
    expect(r.readings).toEqual([
      { timestamp: T0, temperatureC: 5.2 },
      { timestamp: T0 + 3600, temperatureC: 6.1 },
      { timestamp: T0 + 7200, temperatureC: 4.8 },
    ]);
  });

  test('URL-encoded JSON', () => {
    const r = parseLoggerQr(encodeURIComponent(JSON.stringify(payload())));
    expect(r.readings).toHaveLength(3);
    expect(r.loggerId).toBe('FT2-123');
  });

  test('URL whose query carries the encoded JSON in `data`', () => {
    const url = `https://example.org/log?data=${encodeURIComponent(JSON.stringify(payload()))}`;
    const r = parseLoggerQr(url);
    expect(r.readings).toHaveLength(3);
  });

  test('logger id only (JSON) returns no readings', () => {
    expect(parseLoggerQr('{"logger_id":"ABC"}')).toEqual({ loggerId: 'ABC', readings: null });
  });

  test('logger id only (URL query) returns no readings', () => {
    expect(parseLoggerQr('https://x.org/t?loggerID=XY9&a=1')).toEqual({
      loggerId: 'XY9',
      readings: null,
    });
  });

  test('ISO-8601 timestamps and string temperatures are converted', () => {
    const r = parseLoggerQr(
      JSON.stringify({
        timestamps: ['2023-09-13T08:00:00Z', '2023-09-13T09:00:00Z'],
        temperaturesC: ['5.5', '6'],
      })
    );
    expect(r.loggerId).toBeNull();
    expect(r.readings).toEqual([
      { timestamp: T0, temperatureC: 5.5 },
      { timestamp: T0 + 3600, temperatureC: 6 },
    ]);
  });

  test('millisecond timestamps are converted to seconds', () => {
    const r = parseLoggerQr(
      JSON.stringify({ timestamps: [T0 * 1000, (T0 + 60) * 1000], temps: [4, 5] })
    );
    expect(r.readings.map(x => x.timestamp)).toEqual([T0, T0 + 60]);
  });
});

describe('parseLoggerQr: rejected input', () => {
  test.each([
    ['empty string', '', 'empty'],
    ['whitespace', '   ', 'empty'],
    ['not a string', null, 'empty'],
    ['random text', 'hello world', 'unrecognised'],
    ['JSON array', '[1,2,3]', 'unrecognised'],
    ['JSON without id or log', '{"foo":1}', 'unrecognised'],
    ['URL without recognised params', 'https://example.org/?a=1', 'unrecognised'],
  ])('%s', (_name, raw, code) => {
    expect(codeOf(() => parseLoggerQr(raw))).toBe(code);
  });

  test('mismatched lengths', () => {
    expect(
      codeOf(() => parseLoggerQr(JSON.stringify(payload({ temperatures: [5, 6] }))))
    ).toBe('lengthMismatch');
  });

  test('too few readings', () => {
    expect(
      codeOf(() =>
        parseLoggerQr(JSON.stringify(payload({ timestamps: [T0], temperatures: [5] })))
      )
    ).toBe('tooFewReadings');
  });

  test('timestamps and temperatures must both be lists', () => {
    expect(
      codeOf(() => parseLoggerQr(JSON.stringify({ timestamps: [T0, T0 + 1], temperatures: 5 })))
    ).toBe('unrecognised');
  });

  test('bad timestamp', () => {
    expect(
      codeOf(() =>
        parseLoggerQr(JSON.stringify(payload({ timestamps: [T0, 'not a date', T0 + 7200] })))
      )
    ).toBe('badTimestamp');
  });

  test('non-numeric temperature', () => {
    expect(
      codeOf(() => parseLoggerQr(JSON.stringify(payload({ temperatures: [5, 'abc', 4] }))))
    ).toBe('badTemperature');
  });

  test('null temperature (blank reading) is rejected', () => {
    expect(
      codeOf(() => parseLoggerQr(JSON.stringify(payload({ temperatures: [5, null, 4] }))))
    ).toBe('badTemperature');
  });

  test('temperature outside -30..60 °C', () => {
    expect(
      codeOf(() => parseLoggerQr(JSON.stringify(payload({ temperatures: [5, 99, 4] }))))
    ).toBe('temperatureOutOfRange');
  });

  test('duplicate or out-of-order timestamps', () => {
    expect(
      codeOf(() =>
        parseLoggerQr(JSON.stringify(payload({ timestamps: [T0, T0, T0 + 7200] })))
      )
    ).toBe('notIncreasing');
    expect(
      codeOf(() =>
        parseLoggerQr(JSON.stringify(payload({ timestamps: [T0 + 7200, T0 + 3600, T0] })))
      )
    ).toBe('notIncreasing');
  });
});

describe('readingsToRows', () => {
  test('produces ISO time strings and string temperatures', () => {
    const rows = readingsToRows([
      { timestamp: T0, temperatureC: 5.2 },
      { timestamp: T0 + 3600, temperatureC: 6 },
    ]);
    expect(rows).toEqual([
      { time: '2023-09-13T08:00:00.000Z', temp: '5.2' },
      { time: '2023-09-13T09:00:00.000Z', temp: '6' },
    ]);
  });
});
