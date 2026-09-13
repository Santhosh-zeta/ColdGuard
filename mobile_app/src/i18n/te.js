/**
 * ColdGuard Telugu translations (తెలుగు)
 * 
 * Medically-reviewed translations for Andhra Pradesh and Telangana
 * immunization field operations (UIP / eVIN / ANM usage).
 */
export default {
  // App-wide
  appName: "కోల్డ్‌గార్డ్",
  appTagline: "టీకా శక్తి అంచనా సాధనం",

  // Input screen
  inputTitle: "టీకా వివరాలను నమోదు చేయండి",
  vaccineType: "టీకా రకం",
  selectVaccine: "టీకాను ఎంచుకోండి…",
  initialPotency: "ప్రారంభ శక్తి (%)",
  temperatureLog: "ఉష్ణోగ్రత లాగ్",
  addReading: "రీడింగ్‌ను జోడించండి",
  addRow: "రీడింగ్‌ను జోడించండి",
  removeReading: "తొలగించు",
  temperatureC: "ఉష్ణోగ్రత (°C)",
  timestampLabel: "తేదీ & సమయం",
  analyseButton: "శక్తిని విశ్లేషించండి",
  analyze: "శక్తిని విశ్లేషించండి",
  clearForm: "ఫారమ్‌ను క్లియర్ చేయండి",
  uploadCSV: "CSV అప్‌లోడ్ చేయండి",
  manualEntry: "మాన్యువల్ నమోదు",
  minReadingsError: "కనీసం 2 ఉష్ణోగ్రత రీడింగ్‌లు అవసరం.",
  needTwoReadings: "కనీసం 2 ఉష్ణోగ్రత రీడింగ్‌లు అవసరం.",
  invalidTempError: "ఉష్ణోగ్రత −30°C మరియు 60°C మధ్య ఉండాలి.",
  invalidData: "దయచేసి సరైన తేదీ మరియు ఉష్ణోగ్రత వివరాలను నమోదు చేయండి.",
  formatHint: "తేదీ సమయం (ISO) మరియు ఉష్ణోగ్రత (°C) నమోదు చేయండి",
  error: "లోపం",

  // Processing screen
  processingTitle: "విశ్లేషిస్తోంది…",
  analyzing: "విశ్లేషిస్తోంది…",
  processingMessage: "బయేసియన్ మోంటే-కార్లో సిమ్యులేషన్ నడుస్తోంది. దయచేసి వేచి ఉండండి.",
  runningMonteCarlo: "బయేసియన్ మోంటే-కార్లో విశ్లేషణ జరుగుతోంది…",
  stepArrhenius: "అర్హేనియస్ గతిజ సమీకరణ గణన",
  stepMonteCarlo: "మోంటే-కార్లో సాంప్లింగ్ గణన",
  stepDecision: "నిర్ణయాన్ని రూపొందిస్తోంది",

  // Results screen
  resultsTitle: "విశ్లేషణ ఫలితాలు",
  vaccine: "టీకా",
  decision: "నిర్ణయం",
  use: "ఉపయోగించండి",
  investigate: "పరిశీలించండి",
  discard: "విసర్జించండి / వాడవద్దు",
  estimatedPotency: "అంచనా వేసిన శక్తి",
  potencyEstimate: "అంచనా వేసిన శక్తి",
  confidenceInterval: "90% విశ్వసనీయతా వ్యవధి",
  ci90: "90% విశ్వసనీయతా వ్యవధి (CI)",
  confidence: "విశ్వసనీయత",
  primaryCause: "ప్రధాన క్షీణత కారణం",
  explanation: "వివరణ",
  auditHash: "ఆడిట్ హాష్",
  downloadReport: "నివేదికను డౌన్‌లోడ్ చేయండి",
  analyseAnother: "మరొక టీకాను విశ్లేషించండి",
  analyzeAnother: "మరొక టీకాను విశ్లేషించండి",
  mktLabel: "సగటు గతిజ ఉష్ణోగ్రత (MKT)",
  freezeWarning: "గడ్డకట్టే ఉష్ణోగ్రత (Freeze event) నమోదైంది!",
  freezeSensitiveWarning: "ఈ టీకా గడ్డకట్టడానికి సున్నితమైనది. దయచేసి షేక్ టెస్ట్ (Shake test) నిర్వహించండి.",
  details: "వివరాలు",
  mean: "సగటు అంచనా",
  probAboveThreshold: "కనీస పరిమితిని మించే సంభావ్యత",
  temperatureHistory: "ఉష్ణోగ్రత చరిత్ర",

  // Decision banners
  useMessage: "ఈ టీకా తగినంత సమర్థవంతంగా (potent) ఉందని అంచనా వేయబడింది. ఉపయోగించడానికి సురక్షితమైనది.",
  investigateMessage: "ఉపయోగించే ముందు మరింత లోతైన పరిశీలన మరియు పరీక్షలు సిఫార్సు చేయబడ్డాయి.",
  discardMessage: "ఈ టీకా కనీస అవసరమైన శక్తిని చేరుకోలేదు. ఉపయోగించవద్దు, విసర్జించండి.",

  // Chart labels
  tempHistoryTitle: "ఉష్ణోగ్రత చరిత్ర",
  potencyDistTitle: "శక్తి పంపిణీ",
  tempAxisLabel: "ఉష్ణోగ్రత (°C)",
  timeAxisLabel: "సమయం",
  potencyAxisLabel: "శక్తి (%)",
  minPotencyLine: "కనీస పరిమితి",
  meanPotencyLine: "సగటు అంచనా",

  // Vaccine names
  vaccines: {
    DPT: "డిపిటి (డిఫ్తీరియా-పెర్టుసిస్-టెటానస్)",
    OPV: "ఓరల్ పోలియో వ్యాక్సిన్",
    MMR: "మీజిల్స్-మంప్స్-రుబెల్లా (ఎంఎంఆర్)",
    BCG: "బిసిజి (క్షయ నివారణ టీకా)",
    HepB: "హెపటైటిస్ బి",
    IPV: "ఇనాక్టివేటెడ్ పోలియో వ్యాక్సిన్ (ఐపివి)",
    Rotavirus: "రోటావైరస్ టీకా",
    PCV: "న్యుమోకోకల్ కంజుగేట్ టీకా (పిసివి)",
    YF: "పసుపు జ్వరం (ఎల్లో ఫీవర్) టీకా",
  },

  // Errors
  errorGeneric: "ఒక లోపం సంభవించింది. దయచేసి మళ్లీ ప్రయత్నించండి.",
  errorNetwork: "నెట్‌వర్క్ లోపం. దయచేసి మీ ఇంటర్నెట్ కనెక్షన్‌ను తనిఖీ చేయండి.",
};
