// Third Party
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AdministrationTaskCard } from "@/Components/Administration/AdministrationTaskCard";

const renderCard = (props: Partial<React.ComponentProps<typeof AdministrationTaskCard>> = {}) =>
  render(
    <AdministrationTaskCard
      title="Characters"
      description="Queue background tasks."
      buttonLabel="Update All Characters"
      buttonVariant="primary"
      icon={<span data-testid="task-icon" />}
      isPending={false}
      onClick={vi.fn()}
      testId="task-btn"
      {...props}
    />,
  );

describe("AdministrationTaskCard", () => {
  it("test_click_should_call_on_click", async () => {
    // Test Data
    const user = userEvent.setup();
    const onClick = vi.fn();
    renderCard({ onClick });

    // Test Action
    await user.click(screen.getByTestId("task-btn"));

    // Expected Result
    expect(onClick).toHaveBeenCalledTimes(1);
    expect(screen.getByText("Characters")).toBeInTheDocument();
    expect(screen.getByTestId("task-icon")).toBeInTheDocument();
  });

  it("test_pending_should_disable_button_and_show_spinner_instead_of_icon", () => {
    // Test Data & Test Action
    renderCard({ isPending: true });

    // Expected Result
    expect(screen.getByTestId("task-btn")).toBeDisabled();
    expect(screen.queryByTestId("task-icon")).not.toBeInTheDocument();
  });
});
