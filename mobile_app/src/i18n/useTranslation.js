import React, { useContext, createContext } from 'react';
import en from './en';
import hi from './hi';
import te from './te';

export const LangContext = createContext({ lang: 'en', setLang: () => {} });

const TRANSLATIONS = { en, hi, te };

export function useTranslation() {
  const { lang } = useContext(LangContext);
  const strings = TRANSLATIONS[lang] || TRANSLATIONS.en;

  function t(key) {
    return strings[key] ?? key;
  }

  return { t, lang };
}
