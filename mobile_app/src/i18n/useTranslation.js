import React, { useContext, createContext } from 'react';
import en from './en';
import hi from './hi';
import ta from './ta';
import bn from './bn';
import te from './te';
import kn from './kn';

export const LangContext = createContext({ lang: 'en', setLang: () => {} });

const TRANSLATIONS = { en, hi, ta, bn, te, kn };

export function useTranslation() {
  const { lang } = useContext(LangContext);
  const strings = TRANSLATIONS[lang] || TRANSLATIONS.en;

  function t(key) {
    return strings[key] ?? key;
  }

  return { t, lang };
}
