// Third Party
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

// AA Skillfarm
import { MissingOwnerCard } from "@/Components/Base/OwnerSettings/MissingOwnerCard";

describe("MissingOwnerCard", () => {
  it("should render the add character button as solid primary button", () => {
    // Test Data
    const missing = { id: 1, name: "Alt Character", subtitle: "Alt Corp" };

    // Test Action
    render(
      <MissingOwnerCard
        missing={missing}
        appName="Skillfarm"
        actionUrl="/skillfarm/characters/add/"
        actionLabel="Add Character"
      />,
    );

    // Expected Result
    const button = screen.getByRole("button", { name: "Add Character" });
    expect(button).toHaveClass("btn", "btn-primary");
    expect(button).not.toHaveClass("btn-outline-primary");
  });
});
