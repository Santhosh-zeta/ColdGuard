import { useState, createContext, useContext } from 'react';
import en from './en';
import hi from './hi';

const translations = { en, hi };

const LangContext = createContext({ lang: 'en', setLang: () => {} });

export function useLang() {
  return useContext(LangContext);
}

export function useTranslation() {
  const { lang } = useLang();
  const dict = translations[lang] || translations.en;
  return {
    t: (key) => dict[key] || en[key] || key,
  };
}

export { LangContext };
