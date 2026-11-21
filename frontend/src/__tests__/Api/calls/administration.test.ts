// Third Party
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA Skillfarm
import { apiClient } from "@/Api/Api";
import {
  administrationQueryKeys,
  deleteAdministrationAudit,
  fetchAdminStats,
  loadAdministrationAuditInspect,
  loadAdministrationAudits,
  loadAdministrationCorporations,
  loadAdministrationUnregistered,
  triggerAdministrationAuditUpdate,
  triggerUpdateAll,
  triggerUpdatePrices,
} from "@/Api/calls/administration";

describe("administrationQueryKeys", () => {
  it("should provide the administration keys", () => {
    expect(administrationQueryKeys.stats).toEqual(["adminStats"]);
    expect(administrationQueryKeys.audits).toEqual(["administrationAudits"]);
    expect(administrationQueryKeys.auditInspect(1001)).toEqual(["administrationAuditInspect", 1001]);
    expect(administrationQueryKeys.corporations).toEqual(["administrationCorporations"]);
    expect(administrationQueryKeys.unregistered(2001)).toEqual(["administrationUnregistered", 2001]);
  });
});

describe("Administration API calls", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe("loadAdministrationUnregistered", () => {
    it("should pass the corporation id as path parameter", async () => {
      // Test Data
      const response = { corporation_id: 2001, items: [] };
      vi.spyOn(apiClient, "GET").mockResolvedValueOnce({
        data: response,
        error: undefined,
        response: new Response(),
      } as never);

      // Test Action
      const result = await loadAdministrationUnregistered(2001);

      // Expected Result
      expect(result).toEqual(response);
      expect(apiClient.GET).toHaveBeenCalledWith(
        "/skillfarm/api/administration/corporations/{corporation_id}/unregistered/",
        { params: { path: { corporation_id: 2001 } } },
      );
    });
  });

  describe("triggerAdministrationAuditUpdate", () => {
    it("should pass the character id as path parameter and the force flag as body", async () => {
      // Test Data
      const response = { success: true, message: "Queued" };
      vi.spyOn(apiClient, "POST").mockResolvedValueOnce({
        data: response,
        error: undefined,
        response: new Response(),
      } as never);

      // Test Action
      const result = await triggerAdministrationAuditUpdate(1001, true);

      // Expected Result
      expect(result).toEqual(response);
      expect(apiClient.POST).toHaveBeenCalledWith(
        "/skillfarm/api/administration/audits/{character_id}/update/",
        { params: { path: { character_id: 1001 } }, body: { force_refresh: true } },
      );
    });
  });
});

type Method = "GET" | "POST" | "DELETE";

/** Every call of `Api/calls/administration.ts`: [name, HTTP method, call, fixed text]. */
const calls: [string, Method, () => Promise<unknown>, string][] = [
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
