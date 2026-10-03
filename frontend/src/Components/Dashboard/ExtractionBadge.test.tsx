// Third Party
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ExtractionBadge } from "./ExtractionBadge";

describe("ExtractionBadge", () => {
  it("should render none badge when ready count is 0", () => {
    // Test Data
    const count = 0;

    // Test Action
    render(<ExtractionBadge readyCount={count} isAcknowledged={false} />);

    // Expected Result
    expect(screen.getByText(/0 Ready/i)).toBeInTheDocument();
  });

  it("should render pulsing pending badge when extractions are ready and not acknowledged", () => {
    // Test Data
    const count = 3;

    // Test Action
    const { container } = render(<ExtractionBadge readyCount={count} isAcknowledged={false} />);

    // Expected Result
    expect(screen.getByText(/3 Ready/i)).toBeInTheDocument();
    expect(container.querySelector(".sf-extraction-pulsing")).toBeInTheDocument();
    expect(container.querySelector(".sf-badge-extraction-pending")).toBeInTheDocument();
  });

  it("should render steady reviewed badge when extractions are acknowledged", () => {
    // Test Data
    const count = 2;

    // Test Action
    const { container } = render(
      <ExtractionBadge readyCount={count} isAcknowledged={true} acknowledgedAt="2026-10-02 12:00" />
    );

    // Expected Result
    expect(screen.getByText(/2 Reviewed/i)).toBeInTheDocument();
    expect(container.querySelector(".sf-extraction-pulsing")).not.toBeInTheDocument();
    expect(container.querySelector(".sf-badge-extraction-reviewed")).toBeInTheDocument();
  });
});
