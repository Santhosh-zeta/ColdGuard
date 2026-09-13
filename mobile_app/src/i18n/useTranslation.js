/**
 * useTranslation hook and LangContext for ColdGuard i18n.
 */

import React, { useContext, createContext } from 'react';
import en from './en';
import hi from './hi';
import ta from './ta';
import bn from './bn';

export const LangContext = createContext({ lang: 'en', setLang: () => {} });

const TRANSLATIONS = { en, hi, ta, bn };

export function useTranslation() {
  const { lang } = useContext(LangContext);
  const strings = TRANSLATIONS[lang] || TRANSLATIONS.en;

  function t(key) {
    return strings[key] ?? key;
  }

  return { t, lang };
}
