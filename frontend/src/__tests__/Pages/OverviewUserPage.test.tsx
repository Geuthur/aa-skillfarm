// React
import { MemoryRouter, Route, Routes } from "react-router";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { NuqsTestingAdapter } from "nuqs/adapters/testing";
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA Skillfarm
import * as ApiCalls from "@/Api/ApiCalls";
import { OverviewUserPage } from "@/Pages/OverviewUserPage";

vi.mock("@/Api/ApiCalls", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/Api/ApiCalls")>();
  return { ...actual, fetchOverviewUser: vi.fn() };
});

const renderPage = (path: string) => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[path]}>
        <NuqsTestingAdapter>
          <Routes>
            <Route path="/skillfarm/overview/:userId/" element={<OverviewUserPage />} />
          </Routes>
        </NuqsTestingAdapter>
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe("OverviewUserPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should load the characters of the user from the route and show a back link", async () => {
    // Test Data
    vi.mocked(ApiCalls.fetchOverviewUser).mockResolvedValueOnce({
      characters: [],
      total_count: 0,
      active_training_count: 0,
      paused_training_count: 0,
      unacknowledged_paused_count: 0,
      pending_extractions_count: 0,
      acknowledged_extractions_count: 0,
      user: {
        user_id: 7,
        username: "alice",
        main_character_name: "Alice Pilot",
        corporation_name: "Test Corp",
        corporation_ticker: "TEST",
        character_count: 0,
        training_count: 0,
        paused_count: 0,
        pending_extractions_count: 0,
        has_errors: false,
      },
    });

    // Test Action
    renderPage("/skillfarm/overview/7/");

    // Expected Result
    expect(await screen.findByText("Alice Pilot")).toBeInTheDocument();
    expect(vi.mocked(ApiCalls.fetchOverviewUser).mock.calls[0][0]).toBe(7);
    const back = screen.getByRole("link", { name: /Overview/ });
    expect(back.getAttribute("href")).toBe("/skillfarm/overview/");
  });
});
