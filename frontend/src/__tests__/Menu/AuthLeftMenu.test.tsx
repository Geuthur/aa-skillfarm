// React
import { MemoryRouter } from "react-router";

// Third Party
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

// AA Skillfarm
import AuthLeftMenu from "@/Menu/AuthLeftMenu";

vi.mock("react-i18next", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-i18next")>();
  return {
    ...actual,
    useTranslation: () => ({
      t: (key: string) => key,
    }),
  };
});

describe("AuthLeftMenu", () => {
  it("should render internal navigation links with /skillfarm/ prefix", () => {
    // Test Data
    const testData = [
      { name: "Characters", link: "/" },
      { name: "Calculator", link: "/calculator/" },
    ];

    // Test Action
    render(
      <MemoryRouter initialEntries={["/skillfarm/"]}>
        <AuthLeftMenu data={testData} isLoading={false} error={false} />
      </MemoryRouter>
    );

    // Expected Result
    const charsLink = screen.getByText("Characters");
    expect(charsLink).toBeDefined();
    expect(charsLink.getAttribute("href")).toBe("/skillfarm/");

    const calcLink = screen.getByText("Calculator");
    expect(calcLink).toBeDefined();
    expect(calcLink.getAttribute("href")).toBe("/skillfarm/calculator/");
  });

  it("should render external links with standard href", () => {
    // Test Data
    const testData = [
      { name: "External Link", link: "https://example.com", is_external: true },
    ];

    // Test Action
    render(
      <MemoryRouter>
        <AuthLeftMenu data={testData} isLoading={false} error={false} />
      </MemoryRouter>
    );

    // Expected Result
    const externalLink = screen.getByText("External Link");
    expect(externalLink).toBeDefined();
    expect(externalLink.getAttribute("href")).toBe("https://example.com");
  });

  it("should filter out items without links", () => {
    // Test Data
    const testData = [{ name: "No Link Category" }];

    // Test Action
    const { container } = render(
      <MemoryRouter>
        <AuthLeftMenu data={testData} isLoading={false} error={false} />
      </MemoryRouter>
    );

    // Expected Result
    expect(container.querySelectorAll("li")).toHaveLength(0);
  });

  it("should render pulsating error styling and badge when has_errors is true", () => {
    // Test Data
    const testData = [
      { name: "Settings", link: "/settings/", has_errors: true, badge: 2 },
    ];

    // Test Action
    render(
      <MemoryRouter initialEntries={["/skillfarm/"]}>
        <AuthLeftMenu data={testData} isLoading={false} error={false} />
      </MemoryRouter>
    );

    // Expected Result
    const settingsLink = screen.getByText("Settings");
    expect(settingsLink).toBeDefined();
    expect(screen.getByText("2")).toHaveClass("badge", "bg-danger", "aa-menu-badge-pulse");
    expect(settingsLink.closest("a")?.querySelector(".aa-pending-dot-container")).toBeNull();
  });

  it("should render the administration link with its dedicated navigation item", () => {
    // Test Data
    const testData = [{ name: "Administration", link: "/administration/" }];

    // Test Action
    render(
      <MemoryRouter initialEntries={["/skillfarm/"]}>
        <AuthLeftMenu data={testData} isLoading={false} error={false} />
      </MemoryRouter>
    );

    // Expected Result
    const navLink = screen.getByTestId("administration-nav-link");
    expect(navLink.getAttribute("href")).toBe("/skillfarm/administration/");
  });
});
