// Third Party
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SecurityBadge } from "./SecurityBadge";

describe("SecurityBadge", () => {
  it("should render security value and hisec badge class", () => {
    // Test Data
    const sec = 0.9;

    // Test Action
    render(<SecurityBadge sec={sec} />);

    // Expected Result
    const badge = screen.getByText("0.9");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("aa-badge-hisec");
  });

  it("should render nullsec badge class for negative sec status", () => {
    // Test Data
    const sec = -0.5;

    // Test Action
    render(<SecurityBadge sec={sec} />);

    // Expected Result
    const badge = screen.getByText("-0.5");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("aa-badge-nullsec");
  });
});
