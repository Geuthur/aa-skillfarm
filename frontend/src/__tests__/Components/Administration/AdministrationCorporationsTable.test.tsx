// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA Skillfarm
import * as ApiCalls from "@/Api/ApiCalls";
import { AdministrationCorporationsTable } from "@/Components/Administration/AdministrationCorporationsTable";

vi.mock("@/Api/ApiCalls", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/Api/ApiCalls")>();
  return {
    ...actual,
    loadAdministrationCorporations: vi.fn(),
    loadAdministrationUnregistered: vi.fn(),
  };
});

const corporation = {
  corporation_id: 98000001,
  corporation_name: "Farm Holdings",
  corporation_ticker: "FARM",
  logo_url: "https://images.evetech.net/corporations/98000001/logo?size=64",
  registered_count: 2,
  unregistered_count: 2,
};

const unregistered = {
  corporation_id: 98000001,
  items: [
    {
      id: 1,
      name: "Alpha Pilot",
      avatar_url: "https://images.evetech.net/characters/1/portrait?size=64",
      subtitle: "Farm Holdings",
    },
    {
      id: 2,
      name: "Zulu Pilot",
      avatar_url: "https://images.evetech.net/characters/2/portrait?size=64",
      subtitle: "Farm Holdings",
    },
  ],
};

const renderTable = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <AdministrationCorporationsTable />
    </QueryClientProvider>,
  );
};

describe("AdministrationCorporationsTable", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(ApiCalls.loadAdministrationCorporations).mockResolvedValue([corporation]);
    vi.mocked(ApiCalls.loadAdministrationUnregistered).mockResolvedValue(unregistered);
  });

  it("should show the unregistered count on the button", async () => {
    // Test Data
    // (mocks from beforeEach)

    // Test Action
    renderTable();

    // Expected Result
    const button = await screen.findByTestId("unregistered-btn-98000001");
    expect(button).toHaveTextContent("2 Unregistered");
  });

  it("should open the modal and list unregistered characters", async () => {
    // Test Data
    const user = userEvent.setup();
    renderTable();

    // Test Action
    await user.click(await screen.findByTestId("unregistered-btn-98000001"));

    // Expected Result
    expect(await screen.findByText("Alpha Pilot")).toBeInTheDocument();
    expect(screen.getByText("Zulu Pilot")).toBeInTheDocument();
    expect(ApiCalls.loadAdministrationUnregistered).toHaveBeenCalledWith(98000001);
  });

  it("should filter the unregistered characters by search", async () => {
    // Test Data
    const user = userEvent.setup();
    renderTable();
    await user.click(await screen.findByTestId("unregistered-btn-98000001"));
    await screen.findByText("Alpha Pilot");

    // Test Action
    await user.type(screen.getByRole("searchbox", { name: "Search characters" }), "zulu");

    // Expected Result
    expect(screen.queryByText("Alpha Pilot")).not.toBeInTheDocument();
    expect(screen.getByText("Zulu Pilot")).toBeInTheDocument();
  });
});
