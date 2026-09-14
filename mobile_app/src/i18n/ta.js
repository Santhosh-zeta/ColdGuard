/**
 * ColdGuard Tamil (தமிழ்) translations
 * Reviewed for medical accuracy in cold chain / immunisation context
 */
export default {
  // App-wide
  appName: "ColdGuard",
  appTagline: "தடுப்பூசி வலிமை மதிப்பீட்டாளர்",

  // Input screen
  inputTitle: "தடுப்பூசி விவரங்களை உள்ளிடவும்",
  vaccineType: "தடுப்பூசி வகை",
  selectVaccine: "ஒரு தடுப்பூசியை தேர்ந்தெடுக்கவும்…",
  initialPotency: "ஆரம்ப வலிமை (%)",
  temperatureLog: "வெப்பநிலை பதிவு",
  addReading: "வாசிப்பு சேர்க்கவும்",
  removeReading: "நீக்கு",
  temperatureC: "வெப்பநிலை (°C)",
  timestampLabel: "தேதி & நேரம்",
  analyseButton: "வலிமையை பகுப்பாய்வு செய்யவும்",
  clearForm: "படிவத்தை அழிக்கவும்",
  uploadCSV: "CSV பதிவேற்றம்",
  manualEntry: "கைமுறை உள்ளீடு",
  minReadingsError: "குறைந்தது 2 வெப்பநிலை வாசிப்புகள் தேவை.",
  invalidTempError: "வெப்பநிலை −30°C முதல் 60°C வரை இருக்க வேண்டும்.",

  // Processing screen
  processingTitle: "பகுப்பாய்வு செய்கிறது…",
  processingMessage: "பேசியன் மான்டே-கார்லோ உருவகப்படுத்துதல் இயங்குகிறது. தயவுசெய்து காத்திருங்கள்.",
  stepArrhenius: "அர்ரேனியஸ் இயக்கவியல் கணக்கிடுகிறது",
  stepMonteCarlo: "மான்டே-கார்லோ மாதிரி இயங்குகிறது",
  stepDecision: "முடிவை உருவாக்குகிறது",

  // Results screen
  resultsTitle: "பகுப்பாய்வு முடிவுகள்",
  vaccine: "தடுப்பூசி",
  decision: "முடிவு",
  use: "பயன்படுத்தவும்",
  investigate: "விசாரணை செய்யவும்",
  discard: "நிராகரிக்கவும்",
  estimatedPotency: "மதிப்பிடப்பட்ட வலிமை",
  confidenceInterval: "90% நம்பகமான இடைவெளி",
  confidence: "நம்பகத்தன்மை",
  primaryCause: "முதன்மை சிதைவு காரணம்",
  explanation: "விளக்கம்",
  auditHash: "தணிக்கை குறியீடு",
  downloadReport: "அறிக்கையை பதிவிறக்கவும்",
  analyseAnother: "மற்றொரு தடுப்பூசியை பகுப்பாய்வு செய்யவும்",
  mktLabel: "சராசரி இயக்க வெப்பநிலை",
  freezeWarning: "உறைபனி நிகழ்வு கண்டறியப்பட்டது!",
  freezeSensitiveWarning: "இந்த தடுப்பூசி உறைபனிக்கு உணர்திறன் கொண்டது. குலுக்கல் சோதனையை சரிபார்க்கவும்.",

  // Decision banners
  useMessage: "இந்த தடுப்பூசி வலிமையாக இருப்பதாக மதிப்பிடப்படுகிறது. பயன்படுத்துவது பாதுகாப்பானது.",
  investigateMessage: "பயன்படுத்துவதற்கு முன் மேலும் விசாரணை பரிந்துரைக்கப்படுகிறது.",
  discardMessage: "இந்த தடுப்பூசி குறைந்தபட்ச வலிமையை பூர்த்தி செய்யாது. பயன்படுத்த வேண்டாம்.",

  // Chart labels
  tempHistoryTitle: "வெப்பநிலை வரலாறு",
  potencyDistTitle: "வலிமை விநியோகம்",
  tempAxisLabel: "வெப்பநிலை (°C)",
  timeAxisLabel: "நேரம்",
  potencyAxisLabel: "வலிமை (%)",
  minPotencyLine: "குறைந்தபட்ச வரம்பு",
  meanPotencyLine: "சராசரி மதிப்பீடு",

  // Vaccine names
  vaccines: {
    DPT: "டிபிடி (தொண்டை அழற்சி-கக்குவான்-தொடுகடி)",
    OPV: "வாய்வழி போலியோ தடுப்பூசி",
    MMR: "தட்டம்மை-காணாமுத்து-ருபெல்லா",
    BCG: "பாசிலஸ் கால்மட்-குவேரின்",
    HepB: "ஹெபடைடிஸ் பி",
    IPV: "செயலிழக்கப்பட்ட போலியோ தடுப்பூசி",
    Rotavirus: "ரோட்டாவைரஸ் தடுப்பூசி",
    PCV: "நுமோகாக்கல் இணைப்பு தடுப்பூசி",
    YF: "மஞ்சள் காய்ச்சல் தடுப்பூசி",
    JE: "ஜப்பானிய மூளை அழற்சி தடுப்பூசி",
    Typhoid: "டைபாய்டு (Vi பாலிசாக்கரைடு) தடுப்பூசி",
    MenA: "மூளைக்காய்ச்சல் A (MenA) இணைப்பு தடுப்பூசி",
  },

  // Errors
  errorGeneric: "ஒரு பிழை ஏற்பட்டது. மீண்டும் முயற்சிக்கவும்.",
  errorNetwork: "நெட்வொர்க் பிழை. உங்கள் இணைப்பை சரிபார்க்கவும்.",
};
