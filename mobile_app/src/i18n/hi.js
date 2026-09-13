/**
 * ColdGuard Hindi translations (हिन्दी)
 */
export default {
  // App-wide
  appName: "कोल्डगार्ड",
  appTagline: "वैक्सीन शक्ति अनुमानक",

  // Input screen
  inputTitle: "वैक्सीन विवरण दर्ज करें",
  vaccineType: "वैक्सीन प्रकार",
  selectVaccine: "वैक्सीन चुनें…",
  initialPotency: "प्रारंभिक शक्ति (%)",
  temperatureLog: "तापमान लॉग",
  addReading: "रीडिंग जोड़ें",
  addRow: "रीडिंग जोड़ें",
  removeReading: "हटाएँ",
  temperatureC: "तापमान (°C)",
  timestampLabel: "दिनांक और समय",
  analyseButton: "शक्ति विश्लेषण करें",
  analyze: "शक्ति विश्लेषण करें",
  clearForm: "फ़ॉर्म साफ़ करें",
  uploadCSV: "CSV अपलोड करें",
  manualEntry: "मैनुअल प्रविष्टि",
  minReadingsError: "कम से कम 2 तापमान रीडिंग आवश्यक हैं।",
  needTwoReadings: "कम से कम 2 तापमान रीडिंग आवश्यक हैं।",
  invalidTempError: "तापमान −30°C और 60°C के बीच होना चाहिए।",
  invalidData: "अमान्य दिनांक या तापमान डेटा।",
  formatHint: "दिनांक-समय और तापमान (°C) दर्ज करें",
  error: "त्रुटि",

  // Processing screen
  processingTitle: "विश्लेषण हो रहा है…",
  analyzing: "विश्लेषण हो रहा है…",
  processingMessage: "बेयजियन मोंटे-कार्लो सिमुलेशन चल रहा है। कृपया प्रतीक्षा करें।",
  runningMonteCarlo: "बेयजियन मोंटे-कार्लो सिमुलेशन चल रहा है। कृपया प्रतीक्षा करें।",
  stepArrhenius: "अरेनियस गतिज गणना",
  stepMonteCarlo: "मोंटे-कार्लो नमूनाकरण",
  stepDecision: "निर्णय उत्पन्न हो रहा है",

  // Results screen
  resultsTitle: "विश्लेषण परिणाम",
  vaccine: "वैक्सीन",
  decision: "निर्णय",
  use: "उपयोग करें",
  investigate: "जांच करें",
  discard: "नष्ट करें",
  estimatedPotency: "अनुमानित शक्ति",
  potencyEstimate: "अनुमानित शक्ति",
  confidenceInterval: "90% विश्वास अंतराल",
  ci90: "90% विश्वास अंतराल",
  confidence: "विश्वसनीयता",
  primaryCause: "प्राथमिक गिरावट कारण",
  explanation: "विवरण",
  auditHash: "ऑडिट हैश",
  downloadReport: "रिपोर्ट डाउनलोड करें",
  analyseAnother: "अन्य वैक्सीन का विश्लेषण",
  analyzeAnother: "अन्य वैक्सीन का विश्लेषण",
  mktLabel: "माध्य गतिज तापमान",
  freezeWarning: "फ्रीज़ घटना का पता चला!",
  freezeSensitiveWarning: "यह वैक्सीन जमने के प्रति संवेदनशील है। शेक परीक्षण करें।",
  details: "विवरण",
  mean: "औसत अनुमान",
  probAboveThreshold: "न्यूनतम सीमा से ऊपर संभावना",
  temperatureHistory: "तापमान इतिहास",

  // Decision banners
  useMessage: "इस वैक्सीन की शक्ति पर्याप्त है। उपयोग के लिए सुरक्षित।",
  investigateMessage: "उपयोग से पहले आगे की जांच अनुशंसित है।",
  discardMessage: "इस वैक्सीन में न्यूनतम शक्ति नहीं है। उपयोग न करें।",

  // Chart labels
  tempHistoryTitle: "तापमान इतिहास",
  potencyDistTitle: "शक्ति वितरण",
  tempAxisLabel: "तापमान (°C)",
  timeAxisLabel: "समय",
  potencyAxisLabel: "शक्ति (%)",
  minPotencyLine: "न्यूनतम सीमा",
  meanPotencyLine: "औसत अनुमान",

  // Vaccine names
  vaccines: {
    DPT: "डीपीटी (डिफ्थीरिया-परटुसिस-टेटनस)",
    OPV: "ओरल पोलियो वैक्सीन",
    MMR: "खसरा-कण्ठमाला-रूबेला",
    BCG: "बीसीजी",
    HepB: "हेपेटाइटिस बी",
    IPV: "निष्क्रिय पोलियो वैक्सीन",
    Rotavirus: "रोटावायरस वैक्सीन",
    PCV: "न्यूमोकोकल कंजुगेट वैक्सीन",
    YF: "पीला बुखार का टीका (येलो फीवर)",
  },

  // Errors
  errorGeneric: "एक त्रुटि हुई। कृपया पुनः प्रयास करें।",
  errorNetwork: "नेटवर्क त्रुटि। कृपया अपना कनेक्शन जांचें।",
};
