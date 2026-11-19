// Third Party
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA Skillfarm
import { apiClient } from "@/Api/Api";
import {
  acknowledgeAllExtractions,
  acknowledgeExtractions,
  acknowledgePaused,
  deleteAdministrationAudit,
  deleteCharacter,
  fetchAdminStats,
  fetchCalculatorData,
  fetchCharacterDetail,
  fetchCharacters,
  fetchOverview,
  fetchOverviewUser,
  fetchSkillSetup,
  fetchUserCharacterStatuses,
  loadAdministrationAuditInspect,
  loadAdministrationAudits,
  loadAdministrationCorporations,
  loadAdministrationUnregistered,
  toggleNotification,
  triggerAdministrationAuditUpdate,
  triggerCharacterUpdate,
  triggerUpdateAll,
  triggerUpdatePrices,
  updateSkillSetup,
} from "@/Api/ApiCalls";

type Method = "GET" | "POST" | "DELETE";

/** Every call of `ApiCalls.ts`: [name, HTTP method, call, fixed text]. */
const calls: [string, Method, () => Promise<unknown>, string][] = [
  ["fetchUserCharacterStatuses", "GET", () => fetchUserCharacterStatuses(), "Failed to load character update statuses"],
  ["fetchCharacters", "GET", () => fetchCharacters({}), "Failed to fetch characters"],
  ["fetchOverview", "GET", () => fetchOverview(), "Failed to load overview"],
  ["fetchOverviewUser", "GET", () => fetchOverviewUser(7, {}), "Failed to fetch characters for user 7"],
  ["fetchCharacterDetail", "GET", () => fetchCharacterDetail(1001), "Failed to fetch details for character 1001"],
  ["acknowledgeExtractions", "POST", () => acknowledgeExtractions(1001), "Failed to acknowledge extractions"],
  ["acknowledgePaused", "POST", () => acknowledgePaused(1001), "Failed to acknowledge paused status"],
  ["toggleNotification", "POST", () => toggleNotification(1001), "Failed to toggle notification"],
  ["fetchSkillSetup", "GET", () => fetchSkillSetup(1001), "Failed to load skill setup"],
  ["updateSkillSetup", "POST", () => updateSkillSetup(1001, ["Spaceship Command"]), "Failed to update skill setup"],
  ["deleteCharacter", "DELETE", () => deleteCharacter(1001), "Failed to delete character"],
  ["triggerCharacterUpdate", "POST", () => triggerCharacterUpdate(1001), "Failed to trigger character update"],
  ["acknowledgeAllExtractions", "POST", () => acknowledgeAllExtractions(), "Failed to bulk acknowledge extractions"],
  ["fetchCalculatorData", "GET", () => fetchCalculatorData(), "Failed to load calculator data"],
  ["fetchAdminStats", "GET", () => fetchAdminStats(), "Failed to load admin stats"],
  ["triggerUpdateAll", "POST", () => triggerUpdateAll(), "Failed to trigger update all"],
  ["triggerUpdatePrices", "POST", () => triggerUpdatePrices(), "Failed to trigger price update"],
  ["loadAdministrationAudits", "GET", () => loadAdministrationAudits(), "Failed to load administration audits"],
  [
    "triggerAdministrationAuditUpdate",
    "POST",
    () => triggerAdministrationAuditUpdate(1001),
    "Failed to trigger audit update",
  ],
  ["deleteAdministrationAudit", "DELETE", () => deleteAdministrationAudit(1001), "Failed to delete character audit"],
  [
    "loadAdministrationAuditInspect",
    "GET",
    () => loadAdministrationAuditInspect(1001),
    "Failed to load character inspection details",
  ],
  [
    "loadAdministrationCorporations",
    "GET",
    () => loadAdministrationCorporations(),
    "Failed to load administration corporations",
  ],
  [
    "loadAdministrationUnregistered",
    "GET",
    () => loadAdministrationUnregistered(2001),
    "Failed to load unregistered characters",
  ],
];

const failWith = (method: Method, error: unknown) =>
  vi.spyOn(apiClient, method).mockResolvedValueOnce({
    data: undefined,
    error,
    response: new Response(),
  } as never);

describe("API calls", () => {
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
