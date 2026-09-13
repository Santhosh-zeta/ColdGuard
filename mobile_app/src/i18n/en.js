/**
 * ColdGuard English translations
 */
export default {
  // App-wide
  appName: "ColdGuard",
  appTagline: "Vaccine Potency Estimator",

  // Input screen
  inputTitle: "Enter Vaccine Details",
  vaccineType: "Vaccine Type",
  selectVaccine: "Select a vaccine…",
  initialPotency: "Initial Potency (%)",
  temperatureLog: "Temperature Log",
  addReading: "Add Reading",
  removeReading: "Remove",
  temperatureC: "Temperature (°C)",
  timestampLabel: "Date & Time",
  analyseButton: "Analyse Potency",
  clearForm: "Clear Form",
  uploadCSV: "Upload CSV",
  manualEntry: "Manual Entry",
  minReadingsError: "At least 2 temperature readings are required.",
  invalidTempError: "Temperature must be between −30°C and 60°C.",

  // Processing screen
  processingTitle: "Analysing…",
  processingMessage: "Running Bayesian Monte-Carlo simulation. Please wait.",
  stepArrhenius: "Computing Arrhenius kinetics",
  stepMonteCarlo: "Running Monte-Carlo sampling",
  stepDecision: "Generating decision",

  // Results screen
  resultsTitle: "Analysis Results",
  vaccine: "Vaccine",
  decision: "Decision",
  use: "USE",
  investigate: "INVESTIGATE",
  discard: "DISCARD",
  estimatedPotency: "Estimated Potency",
  confidenceInterval: "90% Confidence Interval",
  confidence: "Confidence",
  primaryCause: "Primary Degradation Cause",
  explanation: "Explanation",
  auditHash: "Audit Hash",
  downloadReport: "Download Report",
  analyseAnother: "Analyse Another Vaccine",
  mktLabel: "Mean Kinetic Temperature",
  freezeWarning: "Freeze event detected!",
  freezeSensitiveWarning: "This vaccine is freeze-sensitive. Check the shake test.",

  // Decision banners
  useMessage: "This vaccine is estimated to be potent. Safe to use.",
  investigateMessage: "Further investigation recommended before use.",
  discardMessage: "This vaccine likely does not meet minimum potency. Do not use.",

  // Chart labels
  tempHistoryTitle: "Temperature History",
  potencyDistTitle: "Potency Distribution",
  tempAxisLabel: "Temperature (°C)",
  timeAxisLabel: "Time",
  potencyAxisLabel: "Potency (%)",
  minPotencyLine: "Min Threshold",
  meanPotencyLine: "Mean Estimate",

  // Vaccine names
  vaccines: {
    DPT: "DPT (Diphtheria-Pertussis-Tetanus)",
    OPV: "Oral Polio Vaccine",
    MMR: "Measles-Mumps-Rubella",
    BCG: "Bacillus Calmette-Guérin",
    HepB: "Hepatitis B",
    IPV: "Inactivated Polio Vaccine",
    Rotavirus: "Rotavirus Vaccine",
    PCV: "Pneumococcal Conjugate Vaccine",
    YF: "Yellow Fever Vaccine",
    JE: "Japanese Encephalitis Vaccine",
  },

  // Errors
  errorGeneric: "An error occurred. Please try again.",
  errorNetwork: "Network error. Please check your connection.",
};
