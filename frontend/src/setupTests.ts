// Third Party
import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { I18N_NAMESPACE } from "aa-geuthur-react";
import packageTranslations from "aa-geuthur-react/i18n/en/aa-geuthur-react.json";
import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import { afterEach } from "vitest";

import enTranslations from "../i18n/en/translation.json";

i18n.use(initReactI18next).init({
  lng: "en",
  fallbackLng: "en",
  ns: ["translation", I18N_NAMESPACE],
  defaultNS: "translation",
  keySeparator: false,
  nsSeparator: false,
  interpolation: {
    escapeValue: false,
  },
  react: {
    useSuspense: false,
  },
  resources: {
    en: {
      translation: enTranslations,
      [I18N_NAMESPACE]: packageTranslations,
    },
  },
});

afterEach(() => {
  cleanup();
});

