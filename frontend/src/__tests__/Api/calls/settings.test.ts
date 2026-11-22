// Third Party
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA Skillfarm
import { apiClient } from "@/Api/Api";
import {
  deleteCharacter,
  fetchUserCharacterStatuses,
  settingsQueryKeys,
  toggleNotification,
  triggerCharacterUpdate,
} from "@/Api/calls/settings";

describe("settingsQueryKeys", () => {
  it("should provide the settings keys", () => {
    expect(settingsQueryKeys.statuses).toEqual(["userCharacterStatuses"]);
  });
});

describe("Settings API calls", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe("triggerCharacterUpdate", () => {
    it("should pass the character id as path parameter and the force flag as body", async () => {
      // Test Data
      const response = { success: true, message: "Queued" };
      vi.spyOn(apiClient, "POST").mockResolvedValueOnce({
        data: response,
        error: undefined,
        response: new Response(),
      } as never);

      // Test Action
      const result = await triggerCharacterUpdate(1001, true);

      // Expected Result
      expect(result).toEqual(response);
      expect(apiClient.POST).toHaveBeenCalledWith("/skillfarm/api/characters/{character_id}/update/", {
        params: { path: { character_id: 1001 } },
        body: { force_refresh: true },
      });
    });
  });
});

type Method = "GET" | "POST" | "DELETE";

/** Every call of `Api/calls/settings.ts`: [name, HTTP method, call, fixed text]. */
const calls: [string, Method, () => Promise<unknown>, string][] = [
  ["fetchUserCharacterStatuses", "GET", () => fetchUserCharacterStatuses(), "Failed to load character update statuses"],
  ["toggleNotification", "POST", () => toggleNotification(1001), "Failed to toggle notification"],
  ["deleteCharacter", "DELETE", () => deleteCharacter(1001), "Failed to delete character"],
  ["triggerCharacterUpdate", "POST", () => triggerCharacterUpdate(1001), "Failed to trigger character update"],
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
