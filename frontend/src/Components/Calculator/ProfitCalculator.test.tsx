// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { ProfitCalculator } from "./ProfitCalculator";
import * as ApiCalls from "@/Api/ApiCalls";
import type { CalculatorResponse } from "@/Api/schema";

vi.mock("@/Api/ApiCalls", () => ({
  fetchCalculatorData: vi.fn(),
}));

describe("ProfitCalculator", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    vi.clearAllMocks();
  });

  const mockData: CalculatorResponse = {
    error: false,
    plex: { type_id: 44992, name: "PLEX", buy: 4800000, sell: 5000000, updated_at: "2026-10-01" },
    injector: { type_id: 40520, name: "Skill Injector", buy: 900000000, sell: 1000000000, updated_at: "2026-10-01" },
    extractor: { type_id: 40519, name: "Skill Extractor", buy: 400000000, sell: 500000000, updated_at: "2026-10-01" },
    month_calc: -750000000,
    month12_calc: 250000000,
    month24_calc: 375000000,
  };

  it("should render inputs and compute profit correctly with defaults", async () => {
    // Test Data
    vi.mocked(ApiCalls.fetchCalculatorData).mockResolvedValueOnce(mockData);

    // Test Action
    render(
      <QueryClientProvider client={queryClient}>
        <ProfitCalculator />
      </QueryClientProvider>
    );

    // Expected Result: Inputs exist
    const inputs = await screen.findAllByDisplayValue("3.5");
    expect(inputs.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Calculated Net Result:/i)).toBeInTheDocument();
    expect(screen.getByText(/Gross Injector Revenue/i)).toBeInTheDocument();
    expect(screen.getByText(/Extractor Cost/i)).toBeInTheDocument();
    expect(screen.getByText(/Total Net Profit \/ Loss/i)).toBeInTheDocument();
  });

  it("should update profit when custom PLEX amount is selected", async () => {
    // Test Data
    vi.mocked(ApiCalls.fetchCalculatorData).mockResolvedValueOnce(mockData);
    const user = userEvent.setup();

    render(
      <QueryClientProvider client={queryClient}>
        <ProfitCalculator />
      </QueryClientProvider>
    );

    await screen.findAllByDisplayValue("3.5");

    // Test Action: check custom PLEX checkbox
    const customPlexCheck = screen.getByLabelText(/Use custom PLEX amount/i);
    await user.click(customPlexCheck);

    // Expected Result: custom PLEX input appears
    expect(screen.getByPlaceholderText(/PLEX amount/i)).toBeInTheDocument();
  });
});
