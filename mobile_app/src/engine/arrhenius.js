/**
 * ColdGuard Arrhenius engine — JavaScript port of the Python core.
 *
 * All timestamps are Unix seconds (number).
 * All temperatures are in Celsius; converted to Kelvin internally.
 */

export const R_GAS = 8.314; // J/(mol·K)

// ---------------------------------------------------------------------------
// Vaccine database  (A values derived from shelf-life specifications)
// ---------------------------------------------------------------------------
export const VACCINE_DB = {
  DPT: {
    name: "DPT (Diphtheria-Pertussis-Tetanus)",
    Ea_mean: 83000,
    Ea_std: 4000,
    A: 4.994e10,
    A_log_std: 0.15,
    shelf_life_hours: 17280,
    ref_temp_K: 278.15,
    min_potency_threshold: 0.80,
    minPotencyThreshold: 0.80,
    freeze_sensitive: true,
  },
  OPV: {
    name: "Oral Polio Vaccine",
    Ea_mean: 112000,
    Ea_std: 6000,
    A: 9.878e16,
    A_log_std: 0.20,
    shelf_life_hours: 4380,
    ref_temp_K: 278.15,
    min_potency_threshold: 0.67,
    minPotencyThreshold: 0.67,
    freeze_sensitive: false,
  },
  MMR: {
    name: "Measles-Mumps-Rubella",
    Ea_mean: 108000,
    Ea_std: 7000,
    A: 4.880e15,
    A_log_std: 0.22,
    shelf_life_hours: 8760,
    ref_temp_K: 278.15,
    min_potency_threshold: 0.80,
    minPotencyThreshold: 0.80,
    freeze_sensitive: false,
  },
  BCG: {
    name: "Bacillus Calmette-Guérin",
    Ea_mean: 90000,
    Ea_std: 5000,
    A: 2.033e12,
    A_log_std: 0.18,
    shelf_life_hours: 8760,
    ref_temp_K: 278.15,
    min_potency_threshold: 0.80,
    minPotencyThreshold: 0.80,
    freeze_sensitive: false,
  },
  HepB: {
    name: "Hepatitis B",
    Ea_mean: 70000,
    Ea_std: 4500,
    A: 1.807e8,
    A_log_std: 0.16,
    shelf_life_hours: 17280,
    ref_temp_K: 278.15,
    min_potency_threshold: 0.80,
    minPotencyThreshold: 0.80,
    freeze_sensitive: true,
  },
  IPV: {
    name: "Inactivated Polio Vaccine",
    Ea_mean: 92000,
    Ea_std: 5500,
    A: 2.447e12,
    A_log_std: 0.19,
    shelf_life_hours: 17280,
    ref_temp_K: 278.15,
    min_potency_threshold: 0.80,
    minPotencyThreshold: 0.80,
    freeze_sensitive: true,
  },
  Rotavirus: {
    name: "Rotavirus Vaccine",
    Ea_mean: 100000,
    Ea_std: 6000,
    A: 2.188e15,
    A_log_std: 0.21,
    shelf_life_hours: 17520,
    ref_temp_K: 258.15,
    min_potency_threshold: 0.80,
    minPotencyThreshold: 0.80,
    freeze_sensitive: false,
  },
  PCV: {
    name: "Pneumococcal Conjugate Vaccine",
    Ea_mean: 77000,
    Ea_std: 4000,
    A: 3.729e9,
    A_log_std: 0.15,
    shelf_life_hours: 17280,
    ref_temp_K: 278.15,
    min_potency_threshold: 0.80,
    minPotencyThreshold: 0.80,
    freeze_sensitive: true,
  },
  YF: {
    name: "Yellow Fever Vaccine",
    Ea_mean: 110000,
    Ea_std: 7000,
    A: 5.916e15,
    A_log_std: 0.20,
    shelf_life_hours: 17280,
    ref_temp_K: 278.15,
    min_potency_threshold: 0.80,
    minPotencyThreshold: 0.80,
    freeze_sensitive: false,
  },
  JE: {
    name: "Japanese Encephalitis Vaccine",
    Ea_mean: 95000,
    Ea_std: 5500,
    A: 8.89e12,
    A_log_std: 0.18,
    shelf_life_hours: 17280,
    ref_temp_K: 278.15,
    min_potency_threshold: 0.80,
    minPotencyThreshold: 0.80,
    freeze_sensitive: false,
  },
};

// ---------------------------------------------------------------------------
// Gaussian random (Box-Muller transform)
// ---------------------------------------------------------------------------
export function gaussianRandom(mean = 0, std = 1) {
  let u1;
  do {
    u1 = Math.random();
  } while (u1 === 0);
  const u2 = Math.random();
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
// Freeze damage accumulator (mirrors core/arrhenius.py)
// ---------------------------------------------------------------------------
const FREEZE_DAMAGE_RATE = 0.5; // hr^-1

/**
 * Compute potency retention factor from freeze exposure.
 * Returns 1.0 for non-freeze-sensitive vaccines.
 * @param {number[]} timestamps      Unix seconds
 * @param {number[]} temperaturesC   Celsius readings
 * @param {Object}   params          Entry from VACCINE_DB
 * @param {number}   [freezeThresholdC=0.0]
 * @returns {number}  Freeze retention fraction in [0, 1]
 */
export function computeFreezeDamageFraction(timestamps, temperaturesC, params, freezeThresholdC = 0.0) {
  if (!params.freeze_sensitive) return 1.0;
  if (timestamps.length < 2) return 1.0;

  let totalFreezeHours = 0;
  for (let i = 0; i < timestamps.length - 1; i++) {
    if (temperaturesC[i] < freezeThresholdC || temperaturesC[i + 1] < freezeThresholdC) {
      totalFreezeHours += (timestamps[i + 1] - timestamps[i]) / 3600;
    }
  }
  if (totalFreezeHours === 0) return 1.0;
  return Math.exp(-FREEZE_DAMAGE_RATE * totalFreezeHours);
}

// ---------------------------------------------------------------------------
// Monte-Carlo sampling
// ---------------------------------------------------------------------------
/**
 * @param {number[]} timestamps
 * @param {number[]} temperaturesC
 * @param {Object|string} paramsOrKey  entry from VACCINE_DB or vaccine key string
 * @param {number}   nSamples
 * @param {number}   loggerAccuracyC  1-sigma logger error
 * @returns {number[]} array of potency fractions
 */
export function monteCarloSamples(
  timestamps,
  temperaturesC,
  paramsOrKey,
  nSamples = 1000,
  loggerAccuracyC = 0.5
) {
  const params = typeof paramsOrKey === "string"
    ? VACCINE_DB[paramsOrKey]
    : paramsOrKey;

  if (!params) throw new Error(`Unknown vaccine: ${paramsOrKey}`);

  const samples = [];
  const logA = Math.log(params.A);
  // Freeze damage is determined from original measured temperatures (not perturbed),
  // because freeze damage is a binary event based on observed data.
  const freezeRetention = computeFreezeDamageFraction(timestamps, temperaturesC, params);

  for (let s = 0; s < nSamples; s++) {
    const Ea = gaussianRandom(params.Ea_mean, params.Ea_std);
    const A = Math.exp(gaussianRandom(logA, params.A_log_std));
    const pertTemps = temperaturesC.map((t) => t + gaussianRandom(0, loggerAccuracyC));
    const D = integrateDegradation(timestamps, pertTemps, Ea, A);
    const potency = Math.min(1.0, Math.max(0.0, Math.exp(-D) * freezeRetention));
    samples.push(potency);
  }
  return samples;
}

// ---------------------------------------------------------------------------
// Posterior summary
// ---------------------------------------------------------------------------
/**
 * Returns summary with both underscore (Python-compat) and camelCase keys.
 * @param {number[]} samples  potency fractions
 * @returns {Object} summary statistics
 */
export function computePosteriorSummary(samples) {
  const sorted = [...samples].sort((a, b) => a - b);
  const n = sorted.length;
  const mean = samples.reduce((s, v) => s + v, 0) / n;
  const median = sorted[Math.floor(n / 2)];
  const variance = samples.reduce((s, v) => s + (v - mean) ** 2, 0) / (n - 1);
  const std = Math.sqrt(variance);

  const percentile = (p) => sorted[Math.min(Math.floor((p / 100) * n), n - 1)];

  const ci90Lower = percentile(5);
  const ci90Upper = percentile(95);
  const ci95Lower = percentile(2.5);
  const ci95Upper = percentile(97.5);
  const probAbove80 = samples.filter((v) => v >= 0.8).length / n;
  const probAbove67 = samples.filter((v) => v >= 0.67).length / n;

  return {
    mean,
    median,
    std,
    // camelCase (mobile app)
    ci90Lower,
    ci90Upper,
    ci95Lower,
    ci95Upper,
    probAbove80,
    probAbove67,
    // underscore aliases (Python compat)
    ci_90_lower: ci90Lower,
    ci_90_upper: ci90Upper,
    ci_95_lower: ci95Lower,
    ci_95_upper: ci95Upper,
    prob_above_80pct: probAbove80,
    prob_above_67pct: probAbove67,
  };
}

// ---------------------------------------------------------------------------
// Decision
// ---------------------------------------------------------------------------
/**
 * @param {Object} summary     from computePosteriorSummary
 * @param {string|Object} vaccineKeyOrParams  key into VACCINE_DB or params object
 * @returns {{ decision: string, confidence: number, meanPotencyPct: number,
 *             ci90: number[], explanation: string }}
 */
export function makeDecision(summary, vaccineKeyOrParams) {
  const params = typeof vaccineKeyOrParams === "string"
    ? VACCINE_DB[vaccineKeyOrParams]
    : vaccineKeyOrParams;
  if (!params) throw new Error(`Unknown vaccine: ${vaccineKeyOrParams}`);

  const threshold = params.min_potency_threshold ?? params.minPotencyThreshold ?? 0.80;
  let p_ok;
  if (threshold >= 0.8) {
    p_ok = summary.probAbove80 ?? summary.prob_above_80pct;
  } else if (threshold >= 0.67) {
    p_ok = summary.probAbove67 ?? summary.prob_above_67pct;
  } else {
    p_ok = summary.probAbove80 ?? summary.prob_above_80pct;
  }

  let decision;
  if (p_ok > 0.9) {
    decision = "USE";
  } else if (p_ok > 0.7) {
    decision = "INVESTIGATE";
  } else {
    decision = "DISCARD";
  }

  const meanPct = (summary.mean * 100).toFixed(1);
  const lo = ((summary.ci90Lower ?? summary.ci_90_lower) * 100).toFixed(1);
  const hi = ((summary.ci90Upper ?? summary.ci_90_upper) * 100).toFixed(1);
  const threshPct = (threshold * 100).toFixed(0);

  const explanations = {
    USE: `Estimated potency ${meanPct}% (90% CI: ${lo}–${hi}%). ` +
         `Probability of meeting the ${threshPct}% threshold: ${(p_ok * 100).toFixed(0)}%. ` +
         `This batch is likely potent. Safe to use.`,
    INVESTIGATE: `Estimated potency ${meanPct}% (90% CI: ${lo}–${hi}%). ` +
                 `There is some uncertainty (${(p_ok * 100).toFixed(0)}% probability of meeting threshold). ` +
                 `Check VVM indicator and consult supervisor before administration.`,
    DISCARD: `Estimated potency ${meanPct}% (90% CI: ${lo}–${hi}%). ` +
             `Only ${(p_ok * 100).toFixed(0)}% probability of meeting the ${threshPct}% threshold. ` +
             `Do not administer. Discard this batch.`,
  };

  return {
    decision,
    confidence: p_ok,
    meanPotencyPct: summary.mean * 100,
    ci90: [
      (summary.ci90Lower ?? summary.ci_90_lower) * 100,
      (summary.ci90Upper ?? summary.ci_90_upper) * 100,
    ],
    explanation: explanations[decision],
  };
}
