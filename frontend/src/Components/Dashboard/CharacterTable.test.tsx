// React
import { MemoryRouter } from "react-router-dom";

// Third Party
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

// AA Skillfarm
import type { CharacterSummarySchema } from "@/Api/schema";
import { CharacterTable } from "@/Components/Dashboard/CharacterTable";

const buildCharacter = (overrides: Partial<CharacterSummarySchema> = {}): CharacterSummarySchema => ({
  character_id: 1001,
  character_name: "Test Pilot",
  corporation_id: 2001,
  corporation_name: "Test Corp",
  corporation_ticker: "TC",
  portrait_url: "https://images.evetech.net/characters/1001/portrait",
  total_sp: 5500000,
  is_training: true,
  current_training_skill: "Biology V",
  training_start_date: "2026-10-01T10:00:00Z",
  training_finish_date: "2026-10-10T10:00:00Z",
  queue_finish_date: "2026-10-15T10:00:00Z",
  queue_paused_acknowledged: false,
  progress_percent: 45,
  extractions_ready_count: 1,
  extraction_acknowledged: false,
  extraction_acknowledged_at: null,
  notification_enabled: true,
  last_update: "2026-10-05 12:00:00",
  update_status: "ok",
  ...overrides,
});

describe("CharacterTable", () => {
  it("should render characters table with headers and data", () => {
    // Test Data
    const characters = [buildCharacter()];

    // Test Action
    render(
      <MemoryRouter>
        <CharacterTable
          characters={characters}
          onViewQueue={vi.fn()}
          onOpenSetup={vi.fn()}
          onAcknowledgeExtractions={vi.fn()}
          onAcknowledgePaused={vi.fn()}
          onToggleNotification={vi.fn()}
          onDeleteCharacter={vi.fn()}
        />
      </MemoryRouter>,
    );

    // Expected Result
    expect(screen.getByText("Test Pilot")).toBeInTheDocument();
    expect(screen.getByText("Test Corp [TC]")).toBeInTheDocument();
    expect(screen.getByText("5.50M")).toBeInTheDocument();
    expect(screen.getByText("10-05 12:00:00")).toBeInTheDocument();
  });

  it("should render empty state when characters list is empty", () => {
    // Test Data
    const characters: CharacterSummarySchema[] = [];

    // Test Action
    render(
      <MemoryRouter>
        <CharacterTable
          characters={characters}
          onViewQueue={vi.fn()}
          onOpenSetup={vi.fn()}
          onAcknowledgeExtractions={vi.fn()}
          onAcknowledgePaused={vi.fn()}
          onToggleNotification={vi.fn()}
          onDeleteCharacter={vi.fn()}
        />
      </MemoryRouter>,
    );

    // Expected Result
    expect(screen.getByText("No characters found")).toBeInTheDocument();
  });

  it("should call callbacks on action button clicks", async () => {
    // Test Data
    const user = userEvent.setup();
    const onViewQueue = vi.fn();
    const onOpenSetup = vi.fn();
    const onAcknowledgeExtractions = vi.fn();
    const onAcknowledgePaused = vi.fn();
    const onToggleNotification = vi.fn();
    const onDeleteCharacter = vi.fn();

    const char = buildCharacter({
      is_training: false,
      queue_paused_acknowledged: false,
      extractions_ready_count: 2,
      extraction_acknowledged: false,
    });

    // Test Action
    render(
      <MemoryRouter>
        <CharacterTable
          characters={[char]}
          onViewQueue={onViewQueue}
          onOpenSetup={onOpenSetup}
          onAcknowledgeExtractions={onAcknowledgeExtractions}
          onAcknowledgePaused={onAcknowledgePaused}
          onToggleNotification={onToggleNotification}
          onDeleteCharacter={onDeleteCharacter}
        />
      </MemoryRouter>,
    );

    const ackBtn = screen.getByRole("button", { name: /^Acknowledge$/i });
    await user.click(ackBtn);

    const idleBtn = screen.getByRole("button", { name: /Acknowledge Idle/i });
    await user.click(idleBtn);

    const pilotName = screen.getByText("Test Pilot");
    await user.click(pilotName);

    // Expected Result
    expect(onAcknowledgeExtractions).toHaveBeenCalledWith(1001);
    expect(onAcknowledgePaused).toHaveBeenCalledWith(1001);
    expect(onViewQueue).toHaveBeenCalledWith(1001);
  });
});
