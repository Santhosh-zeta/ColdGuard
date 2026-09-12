/**
 * ColdGuard Arrhenius engine — JavaScript port of the Python core.
 *
 * All timestamps are Unix seconds (number).
 * All temperatures are in Celsius; converted to Kelvin internally.
 */

export const R_GAS = 8.314; // J/(mol·K)

// ---------------------------------------------------------------------------
// Vaccine database
// ---------------------------------------------------------------------------
export const VACCINE_DB = {
  DPT: {
    name: "DPT (Diphtheria-Pertussis-Tetanus)",
    Ea_mean: 83000,
    Ea_std: 4000,
    A: 3.37e10,
    A_log_std: 0.15,
    shelf_life_hours: 17280,
    ref_temp_K: 278.15,
    min_potency_threshold: 0.80,
    freeze_sensitive: true,
  },
  OPV: {
    name: "Oral Polio Vaccine",
    Ea_mean: 112000,
    Ea_std: 6000,
    A: 5.2e14,
    A_log_std: 0.20,
    shelf_life_hours: 4380,
    ref_temp_K: 278.15,
    min_potency_threshold: 0.67,
    freeze_sensitive: false,
  },
  MMR: {
    name: "Measles-Mumps-Rubella",
    Ea_mean: 108000,
    Ea_std: 7000,
    A: 8.1e15,
    A_log_std: 0.22,
    shelf_life_hours: 8760,
    ref_temp_K: 278.15,
    min_potency_threshold: 0.80,
    freeze_sensitive: false,
  },
  BCG: {
    name: "Bacillus Calmette-Guérin",
    Ea_mean: 90000,
    Ea_std: 5000,
    A: 1.2e12,
    A_log_std: 0.18,
    shelf_life_hours: 8760,
    ref_temp_K: 278.15,
    min_potency_threshold: 0.80,
    freeze_sensitive: false,
  },
  HepB: {
    name: "Hepatitis B",
    Ea_mean: 70000,
    Ea_std: 4500,
    A: 2.8e9,
    A_log_std: 0.16,
    shelf_life_hours: 17280,
    ref_temp_K: 278.15,
    min_potency_threshold: 0.80,
    freeze_sensitive: true,
  },
  IPV: {
    name: "Inactivated Polio Vaccine",
    Ea_mean: 92000,
    Ea_std: 5500,
    A: 4.6e12,
    A_log_std: 0.19,
    shelf_life_hours: 17280,
    ref_temp_K: 278.15,
    min_potency_threshold: 0.80,
    freeze_sensitive: true,
  },
  Rotavirus: {
    name: "Rotavirus Vaccine",
    Ea_mean: 100000,
    Ea_std: 6000,
    A: 9.3e13,
    A_log_std: 0.21,
    shelf_life_hours: 17520,
    ref_temp_K: 258.15,
    min_potency_threshold: 0.80,
    freeze_sensitive: false,
  },
  PCV: {
    name: "Pneumococcal Conjugate Vaccine",
    Ea_mean: 77000,
    Ea_std: 4000,
    A: 1.5e10,
    A_log_std: 0.15,
    shelf_life_hours: 17280,
    ref_temp_K: 278.15,
    min_potency_threshold: 0.80,
    freeze_sensitive: true,
  },
};

// ---------------------------------------------------------------------------
// Gaussian random (Box-Muller transform)
// ---------------------------------------------------------------------------
export function gaussianRandom(mean = 0, std = 1) {
  let u1, u2;
  do {
    u1 = Math.random();
  } while (u1 === 0);
  u2 = Math.random();
  const z = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
  return mean + std * z;
}

// ---------------------------------------------------------------------------
// Arrhenius rate constant
// ---------------------------------------------------------------------------
/**
 * @param {number} T_kelvin  Absolute temperature in K
 * @param {number} Ea        Activation energy J/mol
 * @param {number} A         Pre-exponential factor hr^-1
 * @returns {number} rate constant in hr^-1
 */
export function arrheniusK(T_kelvin, Ea, A) {
  return A * Math.exp(-Ea / (R_GAS * T_kelvin));
}

// ---------------------------------------------------------------------------
// Trapezoidal degradation integrator
// ---------------------------------------------------------------------------
/**
 * @param {number[]} timestamps   Unix seconds
 * @param {number[]} temperaturesC  Celsius readings
 * @param {number}   Ea
 * @param {number}   A
 * @returns {number} cumulative degradation D
 */
export function integrateDegradation(timestamps, temperaturesC, Ea, A) {
  if (timestamps.length < 2) return 0;
  let D = 0;
  for (let i = 0; i < timestamps.length - 1; i++) {
    const dt_hours = (timestamps[i + 1] - timestamps[i]) / 3600;
    const k0 = arrheniusK(temperaturesC[i] + 273.15, Ea, A);
    const k1 = arrheniusK(temperaturesC[i + 1] + 273.15, Ea, A);
    D += 0.5 * (k0 + k1) * dt_hours;
  }
  return D;
}

// ---------------------------------------------------------------------------
// Monte-Carlo sampling
// ---------------------------------------------------------------------------
/**
 * @param {number[]} timestamps
 * @param {number[]} temperaturesC
 * @param {Object}   params          entry from VACCINE_DB
 * @param {number}   nSamples
 * @param {number}   loggerAccuracyC  1-sigma logger error
 * @returns {number[]} array of potency fractions
 */
export function monteCarloSamples(
  timestamps,
  temperaturesC,
  params,
  nSamples = 1000,
  loggerAccuracyC = 0.5
) {
  const samples = [];
  const logA = Math.log(params.A);

  for (let s = 0; s < nSamples; s++) {
    const Ea = gaussianRandom(params.Ea_mean, params.Ea_std);
    const A = Math.exp(gaussianRandom(logA, params.A_log_std));

    // Perturb temperatures
    const pertTemps = temperaturesC.map((t) => t + gaussianRandom(0, loggerAccuracyC));

    const D = integrateDegradation(timestamps, pertTemps, Ea, A);
    const potency = Math.min(1.0, Math.max(0.0, Math.exp(-D)));
    samples.push(potency);
  }
  return samples;
}

// ---------------------------------------------------------------------------
// Posterior summary
// ---------------------------------------------------------------------------
/**
 * @param {number[]} samples  potency fractions
 * @returns {Object} summary statistics
 */
export function computePosteriorSummary(samples) {
  const sorted = [...samples].sort((a, b) => a - b);
  const n = sorted.length;
  const mean = samples.reduce((s, v) => s + v, 0) / n;
  const median = sorted[Math.floor(n / 2)];
  const variance =
    samples.reduce((s, v) => s + (v - mean) ** 2, 0) / (n - 1);
  const std = Math.sqrt(variance);

  const percentile = (p) => sorted[Math.floor((p / 100) * n)];

  const probAbove80 = samples.filter((v) => v >= 0.8).length / n;
  const probAbove67 = samples.filter((v) => v >= 0.67).length / n;

  return {
    mean,
    median,
    std,
    ci_90_lower: percentile(5),
    ci_90_upper: percentile(95),
    ci_95_lower: percentile(2.5),
    ci_95_upper: percentile(97.5),
    prob_above_80pct: probAbove80,
    prob_above_67pct: probAbove67,
  };
}

// ---------------------------------------------------------------------------
// Decision
// ---------------------------------------------------------------------------
/**
 * @param {Object} summary     from computePosteriorSummary
 * @param {string} vaccineKey  key into VACCINE_DB
 * @returns {{ decision: string, confidence: number, meanPotencyPct: number }}
 */
export function makeDecision(summary, vaccineKey) {
  const params = VACCINE_DB[vaccineKey];
  if (!params) throw new Error(`Unknown vaccine: ${vaccineKey}`);

  const threshold = params.min_potency_threshold;
  let p_ok;
  if (threshold >= 0.8) {
    p_ok = summary.prob_above_80pct;
  } else if (threshold >= 0.67) {
    p_ok = summary.prob_above_67pct;
  } else {
    p_ok = summary.prob_above_80pct; // fallback
  }

  let decision;
  if (p_ok > 0.9) {
    decision = "USE";
  } else if (p_ok > 0.7) {
    decision = "INVESTIGATE";
  } else {
    decision = "DISCARD";
  }

  return {
    decision,
    confidence: p_ok,
    meanPotencyPct: summary.mean * 100,
    ci90: [summary.ci_90_lower * 100, summary.ci_90_upper * 100],
  };
}
