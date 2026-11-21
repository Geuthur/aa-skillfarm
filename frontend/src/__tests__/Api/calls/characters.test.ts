// Third Party
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA Skillfarm
import { apiClient } from "@/Api/Api";
import {
  acknowledgeAllExtractions,
  acknowledgeExtractions,
  acknowledgePaused,
  charactersQueryKeys,
  fetchCharacterDetail,
  fetchCharacters,
  fetchSkillSetup,
  updateSkillSetup,
} from "@/Api/calls/characters";

describe("charactersQueryKeys", () => {
  it("should provide the characters keys", () => {
    expect(charactersQueryKeys.root).toEqual(["characters"]);
    expect(charactersQueryKeys.list({ search: "a" })).toEqual(["characters", { search: "a" }]);
    expect(charactersQueryKeys.detail(1001)).toEqual(["characterDetail", 1001]);
    expect(charactersQueryKeys.skillSetup(1001)).toEqual(["skillSetup", 1001]);
  });
});

describe("Characters API calls", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe("fetchCharacters", () => {
    it("should pass only the set filters as query parameters", async () => {
      // Test Data
      const response = { characters: [] };
      vi.spyOn(apiClient, "GET").mockResolvedValueOnce({
        data: response,
        error: undefined,
        response: new Response(),
      } as never);

      // Test Action
      const result = await fetchCharacters({
        search: "pilot",
        training_status: "all",
        extraction_status: "pending",
        corporation_id: 98000001,
      });

      // Expected Result
      expect(result).toEqual(response);
      expect(apiClient.GET).toHaveBeenCalledWith("/skillfarm/api/characters/", {
        params: { query: { search: "pilot", extraction_status: "pending", corporation_id: 98000001 } },
      });
    });
  });

  describe("updateSkillSetup", () => {
    it("should pass the character id as path parameter and the skills as body", async () => {
      // Test Data
      const response = { success: true, message: "Saved" };
      vi.spyOn(apiClient, "POST").mockResolvedValueOnce({
        data: response,
        error: undefined,
        response: new Response(),
      } as never);

      // Test Action
      const result = await updateSkillSetup(1001, ["Spaceship Command"]);

      // Expected Result
      expect(result).toEqual(response);
      expect(apiClient.POST).toHaveBeenCalledWith("/skillfarm/api/characters/{character_id}/setup/", {
        params: { path: { character_id: 1001 } },
        body: { selected_skills: ["Spaceship Command"] },
      });
    });
  });
});

type Method = "GET" | "POST";

/** Every call of `Api/calls/characters.ts`: [name, HTTP method, call, fixed text]. */
const calls: [string, Method, () => Promise<unknown>, string][] = [
  ["fetchCharacters", "GET", () => fetchCharacters({}), "Failed to fetch characters"],
  ["fetchCharacterDetail", "GET", () => fetchCharacterDetail(1001), "Failed to fetch details for character 1001"],
  ["acknowledgeExtractions", "POST", () => acknowledgeExtractions(1001), "Failed to acknowledge extractions"],
  ["acknowledgePaused", "POST", () => acknowledgePaused(1001), "Failed to acknowledge paused status"],
  ["acknowledgeAllExtractions", "POST", () => acknowledgeAllExtractions(), "Failed to bulk acknowledge extractions"],
  ["fetchSkillSetup", "GET", () => fetchSkillSetup(1001), "Failed to load skill setup"],
  ["updateSkillSetup", "POST", () => updateSkillSetup(1001, ["Spaceship Command"]), "Failed to update skill setup"],
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
