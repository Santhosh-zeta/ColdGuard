import React, { useContext, createContext } from 'react';
import en from './en';
import hi from './hi';
import ta from './ta';
import bn from './bn';
import te from './te';
import kn from './kn';

export const LangContext = createContext({ lang: 'en', setLang: () => {} });

const TRANSLATIONS = { en, hi, ta, bn, te, kn };

// Non-hook lookup for code that renders outside LangContext.Provider (e.g. App.js).
export function getStrings(lang) {
  return TRANSLATIONS[lang] || TRANSLATIONS.en;
}

export function useTranslation() {
  const { lang } = useContext(LangContext);
  const strings = getStrings(lang);

  function t(key) {
    return strings[key] ?? key;
  }

  return { t, lang };
}
