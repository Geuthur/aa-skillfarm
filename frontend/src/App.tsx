// React
import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NuqsAdapter } from "nuqs/adapters/react-router/v8";

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
