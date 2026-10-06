// Third Party
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { InactiveTrainingAlert } from "./InactiveTrainingAlert";

describe("InactiveTrainingAlert", () => {
  it("should not render when pausedCount is 0", () => {
    // Test Data
    const pausedCount = 0;
    const mockFilter = vi.fn();

    // Test Action
    const { container } = render(
      <InactiveTrainingAlert pausedCount={pausedCount} currentFilter="all" onFilterInactive={mockFilter} />
    );

    // Expected Result
    expect(container).toBeEmptyDOMElement();
  });

  it("should not render when currentFilter is already paused", () => {
    // Test Data
    const pausedCount = 3;
    const mockFilter = vi.fn();

    // Test Action
    const { container } = render(
      <InactiveTrainingAlert pausedCount={pausedCount} currentFilter="paused" onFilterInactive={mockFilter} />
    );

    // Expected Result
    expect(container).toBeEmptyDOMElement();
  });

  it("should render alert banner and trigger filter on click when pausedCount > 0", async () => {
    // Test Data
    const pausedCount = 2;
    const mockFilter = vi.fn();
    const user = userEvent.setup();

    // Test Action
    render(
      <InactiveTrainingAlert pausedCount={pausedCount} currentFilter="all" onFilterInactive={mockFilter} />
    );
    const filterBtn = screen.getByRole("button", { name: /View Paused Characters/i });
    await user.click(filterBtn);

    // Expected Result
    expect(screen.getByText(/2 Characters have no active training queue!/i)).toBeInTheDocument();
    expect(mockFilter).toHaveBeenCalledTimes(1);
  });
});
