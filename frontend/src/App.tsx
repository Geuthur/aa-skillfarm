// React
import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NuqsAdapter } from "nuqs/adapters/react-router/v8";
import i18n from "i18next";
import Backend from "i18next-http-backend";
import { initReactI18next } from "react-i18next";

// Styles
import "@/App.css";
import "@/index.css";

import { ErrorPage } from "@/Pages/404";
import { AdminPage } from "@/Pages/AdminPage";
import AuthPage from "@/Pages/Base";
import { CalculatorPage } from "@/Pages/CalculatorPage";
import { DashboardPage } from "@/Pages/Dashboard";
import { OverviewPage } from "@/Pages/OverviewPage";
import { OverviewUserPage } from "@/Pages/OverviewUserPage";
import { SettingsPage } from "@/Pages/SettingsPage";

export const AppName = "aa-skillfarm";
export const ProjectName = "skillfarm";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 30, // 30 seconds
      refetchOnWindowFocus: false,
    },
  },
});

// Read language directly from Django's LANGUAGE_CODE (set as lang="..." on root div)
const djangoLanguage = typeof document !== "undefined" ? document.getElementById(`${AppName}-root`)?.getAttribute("lang") ?? "en" : "en";

i18n
  .use(Backend)
  .use(initReactI18next)
  .init({
    lng: djangoLanguage,
    fallbackLng: "en",
    keySeparator: false,
    nsSeparator: false,
    interpolation: {
      escapeValue: false, // react already safes from xss => https://www.i18next.com/translation-function/interpolation#unescape
    },
    react: {
      useSuspense: false, //   <---- this will do the magic
    },
    backend: {
      loadPath: `/static/${ProjectName}/i18n/{{lng}}/{{ns}}.json`,
    },
  });

function App() {
  return (
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <NuqsAdapter>
            <Routes>
              <Route path={`/${ProjectName}/`} element={<AuthPage />}>
                <Route index element={<DashboardPage />} />
                <Route path="calculator/" element={<CalculatorPage />} />
                <Route path="admin/" element={<AdminPage />} />
                <Route path="overview/" element={<OverviewPage />} />
                <Route path="overview/:userId/" element={<OverviewUserPage />} />
                <Route path="settings/" element={<SettingsPage />} />
                <Route path="*" element={<ErrorPage />} />
              </Route>
              <Route path="*" element={<Navigate to={`/${ProjectName}/`} replace />} />
            </Routes>
          </NuqsAdapter>
        </BrowserRouter>
      </QueryClientProvider>
    </React.StrictMode>
  );
}

export default App;