// Third Party
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { toolTipContainer, renderTooltip } from "./bootsTrap";

describe("bootsTrap Utils", () => {
  it("should render toolTipContainer correctly", () => {
    // Test Data
    const text = "Sample Tooltip Message";

    // Test Action
    render(toolTipContainer(text));

    // Expected Result
    expect(screen.getByText(text)).toBeInTheDocument();
  });

  it("should render element wrapped with renderTooltip", () => {
    // Test Data
    const tooltipText = "Help Text";

    // Test Action
    render(
      renderTooltip(
        tooltipText,
        <button type="button">Trigger Button</button>
      )
    );

    // Expected Result
    expect(screen.getByRole("button", { name: "Trigger Button" })).toBeInTheDocument();
  });
});
