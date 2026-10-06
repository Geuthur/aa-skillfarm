// Third Party
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { DeleteCharacterModal } from "./DeleteCharacterModal";
import type { CharacterSummarySchema } from "@/Api/schema";

describe("DeleteCharacterModal", () => {
  const mockChar: CharacterSummarySchema = {
    character_id: 12345,
    character_name: "Test Pilot",
    corporation_id: 98000001,
    corporation_name: "Test Corp",
    corporation_ticker: "TC",
    portrait_url: "https://images.evetech.net/characters/12345/portrait?size=64",
    total_sp: 25000000,
    is_training: true,
    progress_percent: 0,
    extractions_ready_count: 2,
    extraction_acknowledged: false,
    queue_paused_acknowledged: false,
    notification_enabled: true,
    update_status: "ok",
  };

  it("should not render modal content when character is null", () => {
    // Test Data
    const { container } = render(
      <DeleteCharacterModal
        character={null}
        showModal={false}
        setShowModal={vi.fn()}
        onConfirm={vi.fn()}
      />
    );

    // Expected Result
    expect(container).toBeEmptyDOMElement();
  });

  it("should display character details and call onConfirm when approved", async () => {
    // Test Data
    const onConfirmMock = vi.fn();
    const setShowModalMock = vi.fn();
    const user = userEvent.setup();

    render(
      <DeleteCharacterModal
        character={mockChar}
        showModal={true}
        setShowModal={setShowModalMock}
        onConfirm={onConfirmMock}
      />
    );

    // Expected Result (dialog content)
    expect(screen.getByText("Test Pilot")).toBeInTheDocument();
    expect(screen.getByText(/Test Corp \[TC\]/)).toBeInTheDocument();
    expect(
      screen.getByText(/Are you sure you want to delete this character\?/i)
    ).toBeInTheDocument();

    // Test Action: click confirm button
    const deleteButtons = screen.getAllByRole("button", { name: /Delete Character/i });
    // The confirm button in footer
    await user.click(deleteButtons[deleteButtons.length - 1]);

    // Expected Result
    expect(onConfirmMock).toHaveBeenCalledTimes(1);
  });
});
