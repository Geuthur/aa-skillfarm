// React
import { MemoryRouter } from "react-router-dom";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NuqsTestingAdapter } from "nuqs/adapters/testing";
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA Skillfarm
import * as ApiCalls from "@/Api/ApiCalls";
import { SuperuserPage } from "@/Pages/SuperuserPage";

vi.mock("@/Api/ApiCalls", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/Api/ApiCalls")>();
  return {
    ...actual,
    fetchAdminStats: vi.fn(),
    loadSuperuserAudits: vi.fn(),
    triggerSuperuserAuditUpdate: vi.fn(),
    deleteSuperuserAudit: vi.fn(),
    loadSuperuserAuditInspect: vi.fn(),
    triggerUpdateAll: vi.fn(),
    triggerUpdatePrices: vi.fn(),
  };
});

const mockStats = {
  total_characters: 15,
  active_characters: 12,
  in_training_count: 10,
  paused_training_count: 2,
  total_sp: 75_000_000,
  total_pending_extractions: 6,
};

const mockAudits = [
  {
    character_id: 95000001,
    character_name: "Farmer Alpha",
    corporation_id: 98000001,
    corporation_name: "Farm Holdings",
    corporation_ticker: "FARM",
    user_id: 1,
    user_name: "admin_user",
    portrait_url: "https://images.evetech.net/characters/95000001/portrait?size=64",
    total_sp: 12_500_000,
    is_training: true,
    current_training_skill: "Biology V",
    training_finish_date: "2026-10-25 12:00",
    queue_finish_date: "2026-11-01 12:00",
    extractions_ready_count: 3,
    active: true,
    status: "ok",
    last_update: "2026-10-18 20:00",
    error_message: null,
  },
];

const mockDetail = {
  character: {
    character_id: 95000001,
    character_name: "Farmer Alpha",
    corporation_id: 98000001,
    corporation_name: "Farm Holdings",
    corporation_ticker: "FARM",
    portrait_url: "https://images.evetech.net/characters/95000001/portrait?size=64",
    total_sp: 12_500_000,
    is_training: true,
    training_start_date: "2026-10-18 10:00",
    training_finish_date: "2026-10-25 12:00",
    queue_finish_date: "2026-11-01 12:00",
    current_training_skill: "Biology V",
    progress_percent: 50.0,
    extractions_ready_count: 3,
    extraction_acknowledged: false,
    extraction_acknowledged_at: null,
    queue_paused_acknowledged: false,
    notification_enabled: false,
    update_status: "ok",
    last_update: "2026-10-18 20:00",
  },
  skillqueue: [
    {
      skill_id: 3402,
      skill_name: "Biology",
      finished_level: 5,
      finished_level_roman: "V",
      queue_position: 0,
      start_date: "2026-10-18 10:00",
      finish_date: "2026-10-25 12:00",
      start_sp: 45255,
      end_sp: 256000,
      training_start_sp: 45255,
      progress_percent: 50.0,
      is_active: true,
      is_extractable: true,
    },
  ],
  farmed_skills: [
    {
      skill_id: 3402,
      skill_name: "Biology",
      active_level: 4,
      trained_level: 4,
      skillpoints: 45255,
      is_extractable: false,
    },
  ],
  configured_skillset: ["Biology"],
};

const renderPage = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/skillfarm/superuser/"]}>
        <NuqsTestingAdapter hasMemory>
          <SuperuserPage />
        </NuqsTestingAdapter>
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe("SuperuserPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render global admin metrics and list all audits", async () => {
    // Test Data
    vi.mocked(ApiCalls.fetchAdminStats).mockResolvedValueOnce(mockStats);
    vi.mocked(ApiCalls.loadSuperuserAudits).mockResolvedValueOnce(mockAudits);

    // Test Action
    renderPage();

    // Expected Result
    expect(await screen.findByText("Superuser Administration")).toBeInTheDocument();
    expect(await screen.findByText("Farmer Alpha")).toBeInTheDocument();
    expect(screen.getByText("admin_user")).toBeInTheDocument();
    expect(screen.getByText("12,500,000")).toBeInTheDocument();
  });

  it("should trigger update task when clicking update button", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.fetchAdminStats).mockResolvedValue(mockStats);
    vi.mocked(ApiCalls.loadSuperuserAudits).mockResolvedValue(mockAudits);
    vi.mocked(ApiCalls.triggerSuperuserAuditUpdate).mockResolvedValueOnce({
      success: true,
      message: "Queued update task for Farmer Alpha",
    });

    // Test Action
    renderPage();
    expect(await screen.findByText("Farmer Alpha")).toBeInTheDocument();

    const updateBtn = screen.getByRole("button", { name: "Update" });
    await user.click(updateBtn);

    // Expected Result
    await waitFor(() => {
      expect(ApiCalls.triggerSuperuserAuditUpdate).toHaveBeenCalledWith(95000001, false);
    });
    expect(await screen.findByText("Queued update task for Farmer Alpha")).toBeInTheDocument();
  });

  it("should open inspection view when clicking inspect button and allow going back", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.fetchAdminStats).mockResolvedValue(mockStats);
    vi.mocked(ApiCalls.loadSuperuserAudits).mockResolvedValue(mockAudits);
    vi.mocked(ApiCalls.loadSuperuserAuditInspect).mockResolvedValue(mockDetail);

    // Test Action
    renderPage();
    expect(await screen.findByText("Farmer Alpha")).toBeInTheDocument();

    const inspectBtn = screen.getByRole("button", { name: "Inspect" });
    await user.click(inspectBtn);

    // Expected Result
    expect(await screen.findByText("Superuser Inspection")).toBeInTheDocument();
    expect(screen.getByText("Skill Queue (1)")).toBeInTheDocument();
    expect(await screen.findByText("Biology")).toBeInTheDocument();

    // Test Action: navigate back
    const backBtn = screen.getByRole("button", { name: "Back to Superuser Overview" });
    await user.click(backBtn);

    // Expected Result: back to overview table
    expect(await screen.findByText("All Skillfarm Character Audits")).toBeInTheDocument();
  });

  it("should open delete confirmation modal and delete character audit", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.fetchAdminStats).mockResolvedValue(mockStats);
    vi.mocked(ApiCalls.loadSuperuserAudits).mockResolvedValue(mockAudits);
    vi.mocked(ApiCalls.deleteSuperuserAudit).mockResolvedValueOnce({
      success: true,
      message: "Character audit deleted successfully.",
    });

    // Test Action
    renderPage();
    expect(await screen.findByText("Farmer Alpha")).toBeInTheDocument();

    const deleteBtn = screen.getByRole("button", { name: "Delete" });
    await user.click(deleteBtn);

    // Expected Result
    expect(await screen.findByText("Delete Character Audit")).toBeInTheDocument();
    expect(
      screen.getByText("Are you sure you want to delete character audit 'Farmer Alpha'?", {
        exact: false,
      }),
    ).toBeInTheDocument();

    const confirmBtn = screen.getByRole("button", { name: "Confirm Delete" });
    await user.click(confirmBtn);

    await waitFor(() => {
      expect(ApiCalls.deleteSuperuserAudit).toHaveBeenCalledWith(95000001);
    });
  });
});
