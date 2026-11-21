// Third Party
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA Skillfarm
import { apiClient } from "@/Api/Api";
import {
  fetchOverview,
  fetchOverviewUser,
  overviewQueryKeys,
} from "@/Api/calls/overview";

describe("overviewQueryKeys", () => {
  it("should provide the overview keys", () => {
    expect(overviewQueryKeys.all).toEqual(["overview"]);
    expect(overviewQueryKeys.user(7, { search: "a" })).toEqual(["overview", "user", 7, { search: "a" }]);
  });
});

describe("Overview API calls", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe("fetchOverviewUser", () => {
    it("should pass the user id as path parameter and the filters as query", async () => {
      // Test Data
      const response = { characters: [] };
      vi.spyOn(apiClient, "GET").mockResolvedValueOnce({
        data: response,
        error: undefined,
        response: new Response(),
      } as never);

      // Test Action
      const result = await fetchOverviewUser(7, { search: "pilot", training_status: "training" });

      // Expected Result
      expect(result).toEqual(response);
      expect(apiClient.GET).toHaveBeenCalledWith("/skillfarm/api/overview/{user_id}/", {
        params: { path: { user_id: 7 }, query: { search: "pilot", training_status: "training" } },
      });
    });
  });
});

type Method = "GET";

/** Every call of `Api/calls/overview.ts`: [name, HTTP method, call, fixed text]. */
const calls: [string, Method, () => Promise<unknown>, string][] = [
  ["fetchOverview", "GET", () => fetchOverview(), "Failed to load overview"],
  ["fetchOverviewUser", "GET", () => fetchOverviewUser(7, {}), "Failed to fetch characters for user 7"],
];

const failWith = (method: Method, error: unknown) =>
  vi.spyOn(apiClient, method).mockResolvedValueOnce({
    data: undefined,
    error,
    response: new Response(),
  } as never);

describe("API error messages", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe.each(calls)("%s", (_name, method, call, fixedText) => {
    it("should throw the message of the API when the request fails", async () => {
      // Test Data
      failWith(method, { error: "Permission Denied" });

      // Test Action & Expected Result
      await expect(call()).rejects.toThrow("Permission Denied");
    });

    it("should throw the fixed text when the API sent no message", async () => {
      // Test Data
      failWith(method, {});

      // Test Action & Expected Result
      await expect(call()).rejects.toThrow(fixedText);
    });
  });
});
