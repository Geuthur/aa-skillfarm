// React
import { MemoryRouter } from "react-router-dom";

// Third Party
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

// AA Skillfarm
import type { AdministrationAuditSchema } from "@/Api/schema";
import { AdministrationAltsModal } from "@/Components/Administration/AdministrationAltsModal";
import type { MainCharacterGroup } from "@/Components/Administration/AdministrationAuditsTable";

const buildAudit = (
  overrides: Partial<AdministrationAuditSchema>,
): AdministrationAuditSchema =>
  ({
    character_id: 1,
    character_name: "Farmer Alpha",
    corporation_id: 1,
    corporation_name: "Farm Holdings",
    corporation_ticker: "FARM",
    user_id: 1,
    user_name: "admin_user",
    portrait_url: null,
    total_sp: 1000,
    is_training: true,
    current_training_skill: null,
    training_finish_date: null,
    queue_finish_date: null,
    extractions_ready_count: 0,
    active: true,
    status: "ok",
    last_update: null,
    error_message: null,
    ...overrides,
  }) as AdministrationAuditSchema;

const buildGroup = (audit: AdministrationAuditSchema): MainCharacterGroup => ({
  id: "user_1",
  userId: 1,
  userName: "admin_user",
  mainCharacterId: 1,
  mainCharacterName: "Farmer Alpha",
  mainPortraitUrl: null,
  corporationName: "Farm Holdings",
  corporationTicker: "FARM",
  alts: [audit],
  totalSp: 1000,
  trainingCount: 1,
  pausedCount: 0,
  readyExtractionsCount: 0,
  issuesCount: 0,
});

const renderModal = (audit: AdministrationAuditSchema) =>
  render(
    <MemoryRouter>
      <AdministrationAltsModal
        group={buildGroup(audit)}
        updatingCharacterId={null}
        onHide={vi.fn()}
        onInspect={vi.fn()}
        onTriggerUpdate={vi.fn()}
        onDelete={vi.fn()}
      />
    </MemoryRouter>,
  );

describe("AdministrationErrorModal via status badge", () => {
  it("test_status_badge_should_be_clickable_when_error_message_exists", () => {
    // Test Data
    renderModal(buildAudit({ status: "error", error_message: "ESI exploded" }));

    // Test Action
    const badge = screen.getByRole("button", { name: /error details/i });

    // Expected Result
    expect(badge).toHaveTextContent("error");
    expect(badge).toHaveAttribute("tabindex", "0");
    expect(screen.queryByText("ESI exploded")).not.toBeInTheDocument();
  });

  it("test_status_badge_click_should_show_full_message_and_keep_alts_modal_open", async () => {
    // Test Data
    const user = userEvent.setup();
    renderModal(buildAudit({ status: "error", error_message: "ESI exploded badly" }));

    // Test Action
    await user.click(screen.getByRole("button", { name: /error details/i }));

    // Expected Result
    expect(await screen.findByTestId("administration-error-message")).toHaveTextContent(
      "ESI exploded badly",
    );
    expect(screen.getAllByRole("dialog")).toHaveLength(2);
  });

  it("test_status_badge_keyboard_enter_should_open_error_modal", async () => {
    // Test Data
    const user = userEvent.setup();
    renderModal(buildAudit({ status: "error", error_message: "Keyboard error" }));

    // Test Action
    screen.getByRole("button", { name: /error details/i }).focus();
    await user.keyboard("{Enter}");

    // Expected Result
    expect(await screen.findByTestId("administration-error-message")).toHaveTextContent(
      "Keyboard error",
    );
  });

  it("test_status_badge_should_not_be_clickable_when_status_is_ok", async () => {
    // Test Data
    const user = userEvent.setup();
    renderModal(buildAudit({ status: "ok", error_message: null }));

    // Test Action
    await user.click(screen.getByText("ok"));

    // Expected Result
    expect(screen.queryByRole("button", { name: /error details/i })).not.toBeInTheDocument();
    expect(screen.queryByTestId("administration-error-message")).not.toBeInTheDocument();
  });

  it("test_token_error_without_message_should_show_default_text", async () => {
    // Test Data
    const user = userEvent.setup();
    renderModal(buildAudit({ status: "token_error", error_message: null }));

    // Test Action
    await user.click(screen.getByRole("button", { name: /error details/i }));

    // Expected Result
    expect(await screen.findByTestId("administration-error-message")).toHaveTextContent(
      /token is invalid or expired/i,
    );
  });
});
