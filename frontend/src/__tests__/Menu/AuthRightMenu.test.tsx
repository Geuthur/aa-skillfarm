// React
import { MemoryRouter } from "react-router-dom";

// Third Party
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

// AA Skillfarm
import AuthRightMenu from "@/Menu/AuthRightMenu";

vi.mock("react-i18next", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-i18next")>();
  return {
    ...actual,
    useTranslation: () => ({
      t: (key: string) => key,
    }),
  };
});

describe("AuthRightMenu", () => {
  it("should render action links for right menu", () => {
    // Test Data
    const testData = [
      { name: "Add Character", link: "/skillfarm/char/add/", is_external: true },
    ];

    // Test Action
    render(
      <MemoryRouter>
        <AuthRightMenu data={testData} isLoading={false} error={false} />
      </MemoryRouter>
    );

    // Expected Result
    const addCharLink = screen.getByText("Add Character");
    expect(addCharLink).toBeDefined();
    expect(addCharLink.getAttribute("href")).toBe("/skillfarm/char/add/");
  });

  it("should filter out items without links", () => {
    // Test Data
    const testData = [{ name: "Category Only" }];

    // Test Action
    const { container } = render(
      <MemoryRouter>
        <AuthRightMenu data={testData} isLoading={false} error={false} />
      </MemoryRouter>
    );

    // Expected Result
    expect(container.querySelectorAll("li")).toHaveLength(0);
  });
});
