// React
import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AaReactProvider, AuthBase, ErrorPage } from "aa-geuthur-react";
import { NuqsAdapter } from "nuqs/adapters/react-router/v8";

import { AppName, ProjectName } from "@/constants";
import { AdministrationPage } from "@/Pages/AdministrationPage";
import { CalculatorPage } from "@/Pages/CalculatorPage";
import { DashboardPage } from "@/Pages/Dashboard";
import { OverviewPage } from "@/Pages/OverviewPage";
import { OverviewUserPage } from "@/Pages/OverviewUserPage";
import { SettingsPage } from "@/Pages/SettingsPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 30, // 30 seconds
      refetchOnWindowFocus: false,
    },
  },
});

function Routing() {
  return (
    <React.StrictMode>
      <AaReactProvider projectName={ProjectName} appName={AppName}>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <NuqsAdapter>
              <Routes>
                <Route path={`/${ProjectName}/`} element={<AuthBase className="d-flex flex-column gap-4" />}>
                  <Route index element={<OverviewPage />} />
                  <Route path="characters/" element={<DashboardPage />} />
                  <Route path="calculator/" element={<CalculatorPage />} />
                  <Route path="administration/" element={<AdministrationPage />} />
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
      </AaReactProvider>
    </React.StrictMode>
  );
}

export default Routing;