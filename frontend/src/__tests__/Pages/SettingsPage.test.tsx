// React
import { MemoryRouter } from "react-router-dom";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA Skillfarm
import * as ApiCalls from "@/Api/ApiCalls";
import { SettingsPage } from "@/Pages/SettingsPage";

vi.mock("@/Api/ApiCalls", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/Api/ApiCalls")>();
  return {
    ...actual,
    fetchUserSettings: vi.fn(),
    updateUserSettings: vi.fn(),
    fetchUserCharacterStatuses: vi.fn(),
    triggerUpdateAll: vi.fn(),
    triggerCharacterUpdate: vi.fn(),
    toggleNotification: vi.fn(),
    deleteCharacter: vi.fn(),
  };
});

const renderPage = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/skillfarm/settings/"]}>
        <SettingsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe("SettingsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should load the saved global notification preference", async () => {
    // Test Data
    vi.mocked(ApiCalls.fetchUserSettings).mockResolvedValueOnce({
      disable_notifications: true,
    });
    vi.mocked(ApiCalls.fetchUserCharacterStatuses).mockResolvedValueOnce({
      characters: [],
      missing_characters: [],
    });

    // Test Action
    renderPage();

    // Expected Result
    expect(
      await screen.findByRole("switch", { name: "Disable all notifications" }),
    ).toBeChecked();
  });

  it("should save the global preference when the switch is enabled", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.fetchUserSettings).mockResolvedValue({
      disable_notifications: false,
    });
    vi.mocked(ApiCalls.fetchUserCharacterStatuses).mockResolvedValue({
      characters: [],
      missing_characters: [],
    });
    vi.mocked(ApiCalls.updateUserSettings).mockResolvedValue({
      disable_notifications: true,
    });

    // Test Action
    renderPage();
    const toggle = await screen.findByRole("switch", {
      name: "Disable all notifications",
    });
    await user.click(toggle);

    // Expected Result
    expect(ApiCalls.updateUserSettings).toHaveBeenCalledWith(
      { disable_notifications: true },
      expect.any(Object),
    );
    await waitFor(() => expect(toggle).toBeChecked());
  });

  it("should display characters with their update status and highlight errors", async () => {
    // Test Data
    vi.mocked(ApiCalls.fetchUserSettings).mockResolvedValue({
      disable_notifications: false,
    });
    vi.mocked(ApiCalls.fetchUserCharacterStatuses).mockResolvedValue({
      characters: [
        {
          character_id: 1001,
          character_name: "Farm Pilot Alpha",
          corporation_id: 2001,
          corporation_name: "Alpha Corp",
          corporation_ticker: "AC",
          portrait_url: "https://images.evetech.net/characters/1001/portrait?size=64",
          status: "ok",
          has_error: false,
          is_active: true,
          last_sync: "2026-10-11 18:00",
          error_message: null,
          notification_enabled: true,
          sections: [
            {
              section: "skills",
              section_name: "Skills",
              is_success: true,
              has_token_error: false,
              error_message: null,
              last_run_at: "2026-10-11 18:00",
              last_run_finished_at: "2026-10-11 18:00",
            },
          ],
        },
        {
          character_id: 1002,
          character_name: "Farm Pilot Bravo",
          corporation_id: 2001,
          corporation_name: "Alpha Corp",
          corporation_ticker: "AC",
          portrait_url: "https://images.evetech.net/characters/1002/portrait?size=64",
          status: "error",
          has_error: true,
          is_active: true,
          last_sync: "2026-10-10 12:00",
          error_message: "ESI connection timed out",
          notification_enabled: false,
          sections: [
            {
              section: "skills",
              section_name: "Skills",
              is_success: false,
              has_token_error: false,
              error_message: "ESI connection timed out",
              last_run_at: "2026-10-10 12:00",
              last_run_finished_at: null,
            },
          ],
        },
      ],
      missing_characters: [],
    });

    // Test Action
    renderPage();

    // Expected Result
    expect(await screen.findByText("Farm Pilot Alpha")).toBeInTheDocument();
    expect(screen.getByText("Farm Pilot Bravo")).toBeInTheDocument();
    expect(screen.getByText("ESI connection timed out")).toBeInTheDocument();
    expect(screen.getAllByText("OK").length).toBeGreaterThan(0);
    expect(screen.getByText("Error")).toBeInTheDocument();
  });

  it("should display missing characters not yet added to Skillfarm", async () => {
    // Test Data
    vi.mocked(ApiCalls.fetchUserSettings).mockResolvedValue({
      disable_notifications: false,
    });
    vi.mocked(ApiCalls.fetchUserCharacterStatuses).mockResolvedValue({
      characters: [],
      missing_characters: [
        {
          character_id: 2001,
          character_name: "Alt Character Charlie",
          corporation_id: 3001,
          corporation_name: "Charlie Corp",
          corporation_ticker: "CC",
          portrait_url: "https://images.evetech.net/characters/2001/portrait?size=64",
        },
      ],
    });

    // Test Action
    renderPage();

    // Expected Result
    expect(await screen.findByText("Alt Character Charlie")).toBeInTheDocument();
    expect(screen.getByText("Charlie Corp")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add Character" })).toHaveAttribute(
      "href",
      "/skillfarm/characters/add/",
    );
  });

  it("should trigger update all and individual character update with force_refresh false", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.fetchUserSettings).mockResolvedValue({
      disable_notifications: false,
    });
    vi.mocked(ApiCalls.fetchUserCharacterStatuses).mockResolvedValue({
      characters: [
        {
          character_id: 1001,
          character_name: "Farm Pilot Alpha",
          corporation_id: 2001,
          corporation_name: "Alpha Corp",
          corporation_ticker: "AC",
          portrait_url: "https://images.evetech.net/characters/1001/portrait?size=64",
          status: "ok",
          has_error: false,
          is_active: true,
          last_sync: "2026-10-11 18:00",
          error_message: null,
          notification_enabled: true,
          sections: [],
        },
      ],
      missing_characters: [],
    });
    vi.mocked(ApiCalls.triggerUpdateAll).mockResolvedValue({
      success: true,
      message: "Update all task queued.",
    });
    vi.mocked(ApiCalls.triggerCharacterUpdate).mockResolvedValue({
      success: true,
      message: "Character update task queued.",
    });

    // Test Action
    renderPage();

    const updateAllBtn = await screen.findByRole("button", { name: /Update All/i });
    await user.click(updateAllBtn);

    const updateCharBtn = screen.getByRole("button", { name: "Update Owner" });
    await user.click(updateCharBtn);

    // Expected Result
    expect(ApiCalls.triggerUpdateAll).toHaveBeenCalledWith(false);
    expect(ApiCalls.triggerCharacterUpdate).toHaveBeenCalledWith(1001, false);
  });

  it("should toggle character notifications and open delete modal", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.fetchUserSettings).mockResolvedValue({
      disable_notifications: false,
    });
    vi.mocked(ApiCalls.fetchUserCharacterStatuses).mockResolvedValue({
      characters: [
        {
          character_id: 1001,
          character_name: "Farm Pilot Alpha",
          corporation_id: 2001,
          corporation_name: "Alpha Corp",
          corporation_ticker: "AC",
          portrait_url: "https://images.evetech.net/characters/1001/portrait?size=64",
          status: "ok",
          has_error: false,
          is_active: true,
          last_sync: "2026-10-11 18:00",
          error_message: null,
          notification_enabled: true,
          sections: [],
        },
      ],
      missing_characters: [],
    });
    vi.mocked(ApiCalls.toggleNotification).mockResolvedValue({
      success: true,
      message: "Notification toggled",
    });
    vi.mocked(ApiCalls.deleteCharacter).mockResolvedValue({
      success: true,
      message: "Character deleted",
    });

    // Test Action
    renderPage();

    const notifBtn = await screen.findByRole("button", { name: "Disable notifications" });
    await user.click(notifBtn);

    const deleteBtn = screen.getByRole("button", { name: /Delete Owner|Delete/i });
    await user.click(deleteBtn);

    // Expected Result
    expect(ApiCalls.toggleNotification).toHaveBeenCalledWith(1001);
    expect(await screen.findByText("Remove Character from Skillfarm")).toBeInTheDocument();
  });
});