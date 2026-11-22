// React
import { MemoryRouter, Route, Routes } from "react-router-dom";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { useUserData } from "aa-geuthur-react";
import { NuqsTestingAdapter } from "nuqs/adapters/testing";
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA Skillfarm
import * as overviewCalls from "@/Api/calls/overview";
import { OverviewUserPage } from "@/Pages/OverviewUserPage";

vi.mock("aa-geuthur-react", async (importOriginal) => ({
  ...(await importOriginal<typeof import("aa-geuthur-react")>()),
  useUserData: vi.fn(),
}));

vi.mock("@/Api/calls/overview", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/Api/calls/overview")>();
  return { ...actual, fetchOverviewUser: vi.fn() };
});

const mockUser = (isAdmin: boolean) =>
  vi.mocked(useUserData).mockReturnValue({
    data: {
      user: {
        user_id: 1,
        character_id: 95000001,
        character_name: "Viewer",
        corporation_id: 98000001,
        corporation_name: "Test Corp",
        is_admin: isAdmin,
        is_superuser: false,
        has_corp_access: !isAdmin,
      },
    },
  } as unknown as ReturnType<typeof useUserData>);

const overviewUser = {
  user_id: 7,
  username: "alice",
  main_character_name: "Alice Pilot",
  corporation_name: "Test Corp",
  corporation_ticker: "TEST",
  character_count: 1,
  training_count: 0,
  paused_count: 1,
  pending_extractions_count: 1,
  has_errors: false,
};

/** One character that offers every write action: pending extractions and an idle queue. */
const mockCharacters = () =>
  vi.mocked(overviewCalls.fetchOverviewUser).mockResolvedValueOnce({
    characters: [
      {
        character_id: 1001,
        character_name: "Alice Alt",
        corporation_id: 2001,
        corporation_name: "Test Corp",
        corporation_ticker: "TEST",
        portrait_url: "https://images.evetech.net/characters/1001/portrait",
        total_sp: 5500000,
        is_training: false,
        current_training_skill: null,
        training_start_date: null,
        training_finish_date: null,
        queue_finish_date: null,
        queue_paused_acknowledged: false,
        progress_percent: 0,
        extractions_ready_count: 2,
        extraction_acknowledged: false,
        extraction_acknowledged_at: null,
        notification_enabled: true,
        last_update: "2026-10-05 12:00:00",
        update_status: "ok",
      },
    ],
    total_count: 1,
    active_training_count: 0,
    paused_training_count: 1,
    unacknowledged_paused_count: 1,
    pending_extractions_count: 1,
    acknowledged_extractions_count: 0,
    user: overviewUser,
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
    mockUser(false);
  });

  it("should load the characters of the user from the route and show a back link", async () => {
    // Test Data
    vi.mocked(overviewCalls.fetchOverviewUser).mockResolvedValueOnce({
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
    expect(vi.mocked(overviewCalls.fetchOverviewUser).mock.calls[0][0]).toBe(7);
    const back = screen.getByRole("link", { name: /Overview/ });
    expect(back.getAttribute("href")).toBe("/skillfarm/overview/");
  });

  it("should hide the write actions for a user who may only see the characters", async () => {
    // Test Data
    mockUser(false);
    mockCharacters();

    // Test Action
    renderPage("/skillfarm/overview/7/");

    // Expected Result
    expect(await screen.findByText("Alice Alt")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Acknowledge$/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Acknowledge Idle/ })).not.toBeInTheDocument();
  });

  it("should show the write actions for an admin", async () => {
    // Test Data
    mockUser(true);
    mockCharacters();

    // Test Action
    renderPage("/skillfarm/overview/7/");

    // Expected Result
    expect(await screen.findByText("Alice Alt")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Acknowledge$/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Acknowledge Idle/ })).toBeInTheDocument();
  });
});
