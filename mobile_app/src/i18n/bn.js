/**
 * ColdGuard Bengali (বাংলা) translations
 * Reviewed for medical accuracy in cold chain / immunisation context
 */
export default {
  // App-wide
  appName: "ColdGuard",
  appTagline: "ভ্যাকসিন শক্তি মূল্যায়নকারী",

  // Input screen
  inputTitle: "ভ্যাকসিনের বিবরণ লিখুন",
  vaccineType: "ভ্যাকসিনের ধরন",
  selectVaccine: "একটি ভ্যাকসিন বেছে নিন…",
  initialPotency: "প্রাথমিক শক্তি (%)",
  temperatureLog: "তাপমাত্রার লগ",
  addReading: "পাঠ যোগ করুন",
  removeReading: "সরান",
  temperatureC: "তাপমাত্রা (°C)",
  timestampLabel: "তারিখ ও সময়",
  analyseButton: "শক্তি বিশ্লেষণ করুন",
  clearForm: "ফর্ম মুছুন",
  uploadCSV: "CSV আপলোড করুন",
  manualEntry: "ম্যানুয়াল এন্ট্রি",
  minReadingsError: "কমপক্ষে ২টি তাপমাত্রা পাঠ প্রয়োজন।",
  invalidTempError: "তাপমাত্রা −30°C থেকে 60°C এর মধ্যে হতে হবে।",

  // Processing screen
  processingTitle: "বিশ্লেষণ চলছে…",
  processingMessage: "বেয়েসিয়ান মন্টে-কার্লো সিমুলেশন চালানো হচ্ছে। অনুগ্রহ করে অপেক্ষা করুন।",
  stepArrhenius: "অ্যারেনিয়াস গতিবিদ্যা গণনা করা হচ্ছে",
  stepMonteCarlo: "মন্টে-কার্লো স্যাম্পলিং চালানো হচ্ছে",
  stepDecision: "সিদ্ধান্ত তৈরি করা হচ্ছে",

  // Results screen
  resultsTitle: "বিশ্লেষণের ফলাফল",
  vaccine: "ভ্যাকসিন",
  decision: "সিদ্ধান্ত",
  use: "ব্যবহার করুন",
  investigate: "তদন্ত করুন",
  discard: "বাতিল করুন",
  estimatedPotency: "আনুমানিক শক্তি",
  confidenceInterval: "৯০% বিশ্বাস্যতা ব্যবধান",
  confidence: "বিশ্বাস্যতা",
  primaryCause: "প্রধান অবক্ষয়ের কারণ",
  explanation: "ব্যাখ্যা",
  auditHash: "অডিট হ্যাশ",
  downloadReport: "রিপোর্ট ডাউনলোড করুন",
  analyseAnother: "আরেকটি ভ্যাকসিন বিশ্লেষণ করুন",
  mktLabel: "মিন কাইনেটিক তাপমাত্রা",
  freezeWarning: "ফ্রিজ ইভেন্ট সনাক্ত হয়েছে!",
  freezeSensitiveWarning: "এই ভ্যাকসিন হিমায়নে সংবেদনশীল। শেক টেস্ট পরীক্ষা করুন।",

  // Decision banners
  useMessage: "এই ভ্যাকসিনটি কার্যকর বলে অনুমান করা হয়েছে। ব্যবহার করা নিরাপদ।",
  investigateMessage: "ব্যবহারের আগে আরও তদন্তের পরামর্শ দেওয়া হচ্ছে।",
  discardMessage: "এই ভ্যাকসিনটি সম্ভবত ন্যূনতম শক্তি পূরণ করে না। ব্যবহার করবেন না।",

  // Chart labels
  tempHistoryTitle: "তাপমাত্রার ইতিহাস",
  potencyDistTitle: "শক্তি বিতরণ",
  tempAxisLabel: "তাপমাত্রা (°C)",
  timeAxisLabel: "সময়",
  potencyAxisLabel: "শক্তি (%)",
  minPotencyLine: "ন্যূনতম সীমা",
  meanPotencyLine: "গড় অনুমান",

  // Vaccine names
  vaccines: {
    DPT: "ডিপিটি (ডিফথেরিয়া-পারটুসিস-টিটেনাস)",
    OPV: "ওরাল পোলিও ভ্যাকসিন",
    MMR: "মিজেলস-মাম্পস-রুবেলা",
    BCG: "ব্যাসিলাস ক্যালমেট-গুয়েরিন",
    HepB: "হেপাটাইটিস বি",
    IPV: "নিষ্ক্রিয় পোলিও ভ্যাকসিন",
    Rotavirus: "রোটাভাইরাস ভ্যাকসিন",
    PCV: "নিউমোকক্কাল কনজুগেট ভ্যাকসিন",
    YF: "ইয়েলো ফিভার ভ্যাকসিন",
    JE: "জাপানিজ এনসেফালাইটিস ভ্যাকসিন",
    Typhoid: "টাইফয়েড (Vi পলিস্যাকারাইড) ভ্যাকসিন",
    MenA: "মেনিনজাইটিস A (MenA) কনজুগেট ভ্যাকসিন",
  },

  // Errors
  errorGeneric: "একটি ত্রুটি হয়েছে। আবার চেষ্টা করুন।",
  errorNetwork: "নেটওয়ার্ক ত্রুটি। আপনার সংযোগ পরীক্ষা করুন।",
};
