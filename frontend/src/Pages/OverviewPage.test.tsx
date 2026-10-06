// React
import { MemoryRouter } from "react-router-dom";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA Skillfarm
import * as ApiCalls from "@/Api/ApiCalls";
import type { OverviewUserSchema } from "@/Api/schema";
import { OverviewPage } from "@/Pages/OverviewPage";

vi.mock("@/Api/ApiCalls", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/Api/ApiCalls")>();
  return { ...actual, fetchOverview: vi.fn() };
});

const buildUser = (overrides: Partial<OverviewUserSchema> = {}): OverviewUserSchema => ({
  user_id: 7,
  username: "alice",
  main_character_id: 90000001,
  main_character_name: "Alice Pilot",
  corporation_name: "Test Corp",
  corporation_ticker: "TEST",
  portrait_url: "https://images.evetech.net/characters/90000001/portrait",
  character_count: 3,
  training_count: 2,
  paused_count: 1,
  pending_extractions_count: 1,
  ...overrides,
});

const renderPage = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/skillfarm/overview/"]}>
        <OverviewPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe("OverviewPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render a row with a link to the user detail page", async () => {
    // Test Data
    vi.mocked(ApiCalls.fetchOverview).mockResolvedValueOnce({ users: [buildUser()] });

    // Test Action
    renderPage();

    // Expected Result
    expect(await screen.findByText("Alice Pilot")).toBeInTheDocument();
    expect(screen.getByText("Test Corp [TEST]")).toBeInTheDocument();
    const link = screen.getByRole("link", { name: /Characters/ });
    expect(link.getAttribute("href")).toBe("/skillfarm/overview/7/");
  });

  it("should render an empty state when no users are visible", async () => {
    // Test Data
    vi.mocked(ApiCalls.fetchOverview).mockResolvedValueOnce({ users: [] });

    // Test Action
    renderPage();

    // Expected Result
    expect(await screen.findByText("No users found")).toBeInTheDocument();
  });

  it("should render permission denied when the request fails", async () => {
    // Test Data
    vi.mocked(ApiCalls.fetchOverview).mockRejectedValueOnce(new Error("Failed"));

    // Test Action
    renderPage();

    // Expected Result
    expect(await screen.findByText("Permission Denied")).toBeInTheDocument();
  });
});
