/**
 * Jest unit tests for mobile_app/src/engine/arrhenius.js
 *
 * Monte Carlo tests use a deterministic Math.random mock (LCG seeded sequence)
 * so results are reproducible across runs.
 */

import {
  R_GAS,
  VACCINE_DB,
  arrheniusK,
  integrateDegradation,
  computeFreezeDamageFraction,
  monteCarloSamples,
  computePosteriorSummary,
  makeDecision,
} from "../arrhenius";

// ---------------------------------------------------------------------------
// Deterministic Math.random mock — simple LCG, seeded before each MC test
// ---------------------------------------------------------------------------
function makeLcgSequence(seed = 42) {
  let state = seed >>> 0;
  return () => {
    state = (Math.imul(1664525, state) + 1013904223) >>> 0;
    return state / 0x100000000;
  };
}

// ---------------------------------------------------------------------------
// arrheniusK
// ---------------------------------------------------------------------------
describe("arrheniusK", () => {
  const DPT = VACCINE_DB.DPT;

  test("returns a positive rate constant", () => {
    const k = arrheniusK(278.15, DPT.Ea_mean, DPT.A);
    expect(k).toBeGreaterThan(0);
  });

  test("rate increases with temperature (Arrhenius law)", () => {
    const k5C  = arrheniusK(278.15, DPT.Ea_mean, DPT.A);
    const k25C = arrheniusK(298.15, DPT.Ea_mean, DPT.A);
    expect(k25C).toBeGreaterThan(k5C);
  });

  test("matches Python reference value for DPT at 5°C within 1e-10", () => {
    // Python: k = 4.994e10 * exp(-83000 / (8.314 * 278.15))
    const expected = 4.994e10 * Math.exp(-83000 / (R_GAS * 278.15));
    const k = arrheniusK(278.15, 83000, 4.994e10);
    expect(Math.abs(k - expected)).toBeLessThan(1e-10);
  });

  test("uses R_GAS constant (8.314 J/mol·K)", () => {
    expect(R_GAS).toBeCloseTo(8.314, 5);
  });
});

// ---------------------------------------------------------------------------
// integrateDegradation
// ---------------------------------------------------------------------------
describe("integrateDegradation", () => {
  test("returns 0 for a single-point log (no interval)", () => {
    const D = integrateDegradation([0], [5], 83000, 4.994e10);
    expect(D).toBe(0);
  });

  test("returns positive degradation for two readings at room temperature", () => {
    // 1 hour at 25°C
    const ts = [0, 3600];
    const D = integrateDegradation(ts, [25, 25], 83000, 4.994e10);
    expect(D).toBeGreaterThan(0);
  });

  test("constant temperature matches analytic result", () => {
    // D = k * dt_hours for constant T
    const Ea = 83000;
    const A  = 4.994e10;
    const T  = 298.15; // 25°C
    const k  = arrheniusK(T, Ea, A);
    const ts = [0, 3600]; // 1 hour
    const D  = integrateDegradation(ts, [25, 25], Ea, A);
    expect(D).toBeCloseTo(k * 1, 8);
  });

  test("higher temperature produces more degradation over same interval", () => {
    const ts = [0, 3600];
    const D5  = integrateDegradation(ts, [5,  5],  83000, 4.994e10);
    const D25 = integrateDegradation(ts, [25, 25], 83000, 4.994e10);
    expect(D25).toBeGreaterThan(D5);
  });

  test("cold storage for 3 days produces potency near 1.0", () => {
    // 72 readings over 3 days at 5°C (every hour)
    const ts    = Array.from({ length: 73 }, (_, i) => i * 3600);
    const temps = Array(73).fill(5);
    const DPT   = VACCINE_DB.DPT;
    const D     = integrateDegradation(ts, temps, DPT.Ea_mean, DPT.A);
    expect(Math.exp(-D)).toBeGreaterThan(0.99);
  });
});

// ---------------------------------------------------------------------------
// computeFreezeDamageFraction
// ---------------------------------------------------------------------------
describe("computeFreezeDamageFraction", () => {
  const DPT = VACCINE_DB.DPT; // freeze_sensitive: true
  const YF  = VACCINE_DB.YF;  // freeze_sensitive: false

  test("returns 1.0 for non-freeze-sensitive vaccine regardless of temp", () => {
    const ts    = [0, 3600, 7200];
    const temps = [-5, -3, -2];
    expect(computeFreezeDamageFraction(ts, temps, YF)).toBe(1.0);
  });

  test("returns 1.0 for freeze-sensitive vaccine with no freeze event", () => {
    const ts    = [0, 3600, 7200];
    const temps = [4, 5, 6];
    expect(computeFreezeDamageFraction(ts, temps, DPT)).toBe(1.0);
  });

  test("returns < 1.0 for freeze-sensitive vaccine with freeze event", () => {
    const ts    = [0, 3600, 7200]; // 2 hours below 0°C
    const temps = [-3, -2, -1];
    const retention = computeFreezeDamageFraction(ts, temps, DPT);
    expect(retention).toBeLessThan(1.0);
    expect(retention).toBeGreaterThan(0.0);
  });

  test("matches exp(−0.5 × freeze_hours) formula for DPT", () => {
    // 2 hours frozen (0→1h and 1→2h both below 0°C)
    const ts    = [0, 3600, 7200];
    const temps = [-3, -2, -1];
    const retention = computeFreezeDamageFraction(ts, temps, DPT);
    const expected  = Math.exp(-0.5 * 2);
    expect(retention).toBeCloseTo(expected, 8);
  });

  test("returns 1.0 for a single-point log", () => {
    expect(computeFreezeDamageFraction([0], [-5], DPT)).toBe(1.0);
  });
});

// ---------------------------------------------------------------------------
// monteCarloSamples  (deterministic via Math.random mock)
// ---------------------------------------------------------------------------
describe("monteCarloSamples", () => {
  let randomSpy;

  beforeEach(() => {
    const lcg = makeLcgSequence(42);
    randomSpy = jest.spyOn(Math, "random").mockImplementation(lcg);
  });

  afterEach(() => {
    randomSpy.mockRestore();
  });

  test("returns the requested number of samples", () => {
    const ts    = [0, 3600, 7200];
    const temps = [5, 5, 5];
    const s = monteCarloSamples(ts, temps, "DPT", 50);
    expect(s).toHaveLength(50);
  });

  test("all samples are in [0, 1]", () => {
    const ts    = [0, 3600, 7200];
    const temps = [5, 5, 5];
    const s = monteCarloSamples(ts, temps, "DPT", 100);
    s.forEach((v) => {
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThanOrEqual(1);
    });
  });

  test("accepts a vaccine key string (DPT)", () => {
    const ts = [0, 3600];
    expect(() => monteCarloSamples(ts, [5, 5], "DPT", 10)).not.toThrow();
  });

  test("accepts a vaccine params object directly", () => {
    const ts = [0, 3600];
    expect(() => monteCarloSamples(ts, [5, 5], VACCINE_DB.OPV, 10)).not.toThrow();
  });

  test("throws for unknown vaccine key", () => {
    expect(() => monteCarloSamples([0, 3600], [5, 5], "UNKNOWN", 10)).toThrow();
  });

  test("same seed produces identical samples (reproducibility)", () => {
    const ts    = [0, 3600, 7200];
    const temps = [5, 5, 5];
    // First run already consumed the first LCG sequence via beforeEach mock.
    const s1 = monteCarloSamples(ts, temps, "DPT", 20);
    // Reset with the same seed for second run
    const lcg2 = makeLcgSequence(42);
    randomSpy.mockImplementation(lcg2);
    const s2 = monteCarloSamples(ts, temps, "DPT", 20);
    expect(s1).toEqual(s2);
  });

  test("cold-storage DPT samples are high potency (mean > 0.95)", () => {
    const ts    = Array.from({ length: 25 }, (_, i) => i * 3600);
    const temps = Array(25).fill(5);
    const s    = monteCarloSamples(ts, temps, "DPT", 200);
    const mean = s.reduce((a, v) => a + v, 0) / s.length;
    expect(mean).toBeGreaterThan(0.95);
  });

  test("freeze event reduces mean potency for freeze-sensitive DPT", () => {
    // 2 hours below 0°C
    const ts_freeze  = [0, 3600, 7200];
    const temps_norm = [5, 5, 5];
    const temps_frz  = [-3, -2, -1];

    const lcgA = makeLcgSequence(7);
    randomSpy.mockImplementation(lcgA);
    const normal = monteCarloSamples(ts_freeze, temps_norm, "DPT", 100);

    const lcgB = makeLcgSequence(7);
    randomSpy.mockImplementation(lcgB);
    const frozen = monteCarloSamples(ts_freeze, temps_frz, "DPT", 100);

    const meanNormal = normal.reduce((a, v) => a + v, 0) / normal.length;
    const meanFrozen = frozen.reduce((a, v) => a + v, 0) / frozen.length;
    expect(meanFrozen).toBeLessThan(meanNormal);
  });
});

// ---------------------------------------------------------------------------
// computePosteriorSummary
// ---------------------------------------------------------------------------
describe("computePosteriorSummary", () => {
  const samples = [0.80, 0.85, 0.90, 0.92, 0.95, 0.97, 0.98, 0.99, 1.00, 0.88];

  test("mean is within [0, 1]", () => {
    const s = computePosteriorSummary(samples);
    expect(s.mean).toBeGreaterThanOrEqual(0);
    expect(s.mean).toBeLessThanOrEqual(1);
  });

  test("CI is ordered: lower ≤ mean ≤ upper", () => {
    const s = computePosteriorSummary(samples);
    expect(s.ci90Lower).toBeLessThanOrEqual(s.mean);
    expect(s.mean).toBeLessThanOrEqual(s.ci90Upper);
  });

  test("exposes both camelCase and underscore keys", () => {
    const s = computePosteriorSummary(samples);
    expect(s).toHaveProperty("ci90Lower");
    expect(s).toHaveProperty("ci_90_lower");
    expect(s).toHaveProperty("probAbove80");
    expect(s).toHaveProperty("prob_above_80pct");
  });

  test("camelCase and underscore values are identical", () => {
    const s = computePosteriorSummary(samples);
    expect(s.ci90Lower).toBe(s.ci_90_lower);
    expect(s.ci90Upper).toBe(s.ci_90_upper);
    expect(s.probAbove80).toBe(s.prob_above_80pct);
  });

  test("probAbove80 is 1.0 when all samples exceed 0.80", () => {
    const s = computePosteriorSummary(samples); // all >= 0.80
    expect(s.probAbove80).toBe(1.0);
  });

  test("std is non-negative", () => {
    const s = computePosteriorSummary(samples);
    expect(s.std).toBeGreaterThanOrEqual(0);
  });
});

// ---------------------------------------------------------------------------
// makeDecision
// ---------------------------------------------------------------------------
describe("makeDecision", () => {
  function summaryWith(probAbove80) {
    return {
      mean: probAbove80,
      ci90Lower: probAbove80 - 0.05,
      ci90Upper: Math.min(1, probAbove80 + 0.05),
      ci_90_lower: probAbove80 - 0.05,
      ci_90_upper: Math.min(1, probAbove80 + 0.05),
      probAbove80,
      prob_above_80pct: probAbove80,
      probAbove67: 1.0,
      prob_above_67pct: 1.0,
    };
  }

  test("returns USE when probAbove80 > 0.90", () => {
    const result = makeDecision(summaryWith(0.95), "DPT");
    expect(result.decision).toBe("USE");
  });

  test("returns INVESTIGATE when probAbove80 is between 0.70 and 0.90", () => {
    const result = makeDecision(summaryWith(0.80), "DPT");
    expect(result.decision).toBe("INVESTIGATE");
  });

  test("returns DISCARD when probAbove80 ≤ 0.70", () => {
    const result = makeDecision(summaryWith(0.50), "DPT");
    expect(result.decision).toBe("DISCARD");
  });

  test("result includes required fields", () => {
    const result = makeDecision(summaryWith(0.95), "DPT");
    expect(result).toHaveProperty("decision");
    expect(result).toHaveProperty("confidence");
    expect(result).toHaveProperty("meanPotencyPct");
    expect(result).toHaveProperty("ci90");
    expect(result).toHaveProperty("explanation");
  });

  test("ci90 is an array of two numbers ordered low–high", () => {
    const result = makeDecision(summaryWith(0.95), "DPT");
    expect(Array.isArray(result.ci90)).toBe(true);
    expect(result.ci90).toHaveLength(2);
    expect(result.ci90[0]).toBeLessThanOrEqual(result.ci90[1]);
  });

  test("explanation string is non-empty", () => {
    const result = makeDecision(summaryWith(0.95), "DPT");
    expect(typeof result.explanation).toBe("string");
    expect(result.explanation.length).toBeGreaterThan(0);
  });

  test("throws for unknown vaccine key", () => {
    expect(() => makeDecision(summaryWith(0.95), "UNKNOWN")).toThrow();
  });

  test("accepts params object directly", () => {
    expect(() => makeDecision(summaryWith(0.95), VACCINE_DB.OPV)).not.toThrow();
  });
});

// ---------------------------------------------------------------------------
// VACCINE_DB
// ---------------------------------------------------------------------------
describe("VACCINE_DB", () => {
  const expectedVaccines = ["DPT", "OPV", "MMR", "BCG", "HepB", "IPV", "Rotavirus", "PCV", "YF", "JE"];

  test("contains all 10 supported vaccines", () => {
    expectedVaccines.forEach((key) => {
      expect(VACCINE_DB).toHaveProperty(key);
    });
  });

  test.each(expectedVaccines)("%s has required numeric fields", (key) => {
    const v = VACCINE_DB[key];
    expect(typeof v.Ea_mean).toBe("number");
    expect(typeof v.Ea_std).toBe("number");
    expect(typeof v.A).toBe("number");
    expect(typeof v.shelf_life_hours).toBe("number");
    expect(typeof v.min_potency_threshold).toBe("number");
  });

  test.each(expectedVaccines)("%s freeze_sensitive is a boolean", (key) => {
    expect(typeof VACCINE_DB[key].freeze_sensitive).toBe("boolean");
  });

  test("DPT and HepB are freeze-sensitive", () => {
    expect(VACCINE_DB.DPT.freeze_sensitive).toBe(true);
    expect(VACCINE_DB.HepB.freeze_sensitive).toBe(true);
  });

  test("OPV, YF, JE are not freeze-sensitive", () => {
    expect(VACCINE_DB.OPV.freeze_sensitive).toBe(false);
    expect(VACCINE_DB.YF.freeze_sensitive).toBe(false);
    expect(VACCINE_DB.JE.freeze_sensitive).toBe(false);
  });
});
