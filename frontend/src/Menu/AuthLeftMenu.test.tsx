// React
import { MemoryRouter } from "react-router-dom";

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
      { name: "Administration", link: "/admin/" },
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

    const adminLink = screen.getByText("Administration");
    expect(adminLink).toBeDefined();
    expect(adminLink.getAttribute("href")).toBe("/skillfarm/admin/");
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
});
