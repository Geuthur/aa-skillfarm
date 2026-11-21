// Third Party
import { apiErrorMessage } from "aa-geuthur-react";

// AA Skillfarm
import { apiClient } from "@/Api/Api";
import type {
  ActionResponse,
  AdminStatsResponse,
  AdministrationAuditSchema,
  AdministrationCorporationSchema,
  AdministrationUnregisteredResponse,
  CharacterDetailResponse,
} from "@/Api/schema";

const API_BASE = "/skillfarm/api";

/** Query keys of the administration area: statistics, audits and corporations. */
export const administrationQueryKeys = {
  stats: ["adminStats"] as const,
  audits: ["administrationAudits"] as const,
  auditInspect: (characterId: number | null) => ["administrationAuditInspect", characterId] as const,
  corporations: ["administrationCorporations"] as const,
  unregistered: (corporationId: number | null) => ["administrationUnregistered", corporationId] as const,
};

export async function fetchAdminStats(): Promise<AdminStatsResponse> {
  const { data, error } = await apiClient.GET(`${API_BASE}/administration/stats/`, {});
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load admin stats"));
  }
  return data as AdminStatsResponse;
}

export async function triggerUpdateAll(forceRefresh: boolean = false): Promise<ActionResponse> {
  const { data, error } = await apiClient.POST(`${API_BASE}/administration/update-all/`, {
    body: { force_refresh: forceRefresh },
  });
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to trigger update all"));
  }
  return data as ActionResponse;
}

export async function triggerUpdatePrices(): Promise<ActionResponse> {
  const { data, error } = await apiClient.POST(`${API_BASE}/administration/update-prices/`, {});
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to trigger price update"));
  }
  return data as ActionResponse;
}

export async function loadAdministrationAudits(): Promise<AdministrationAuditSchema[]> {
  const { data, error } = await apiClient.GET(`${API_BASE}/administration/audits/`, {});
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load administration audits"));
  }
  return data as AdministrationAuditSchema[];
}

export async function triggerAdministrationAuditUpdate(
  characterId: number,
  forceRefresh: boolean = false,
): Promise<ActionResponse> {
  const { data, error } = await apiClient.POST(
    `${API_BASE}/administration/audits/{character_id}/update/`,
    {
      params: { path: { character_id: characterId } },
      body: { force_refresh: forceRefresh },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to trigger audit update"));
  }
  return data as ActionResponse;
}

export async function deleteAdministrationAudit(characterId: number): Promise<ActionResponse> {
  const { data, error } = await apiClient.DELETE(
    `${API_BASE}/administration/audits/{character_id}/`,
    {
      params: { path: { character_id: characterId } },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to delete character audit"));
  }
  return data as ActionResponse;
}

export async function loadAdministrationAuditInspect(
  characterId: number,
): Promise<CharacterDetailResponse> {
  const { data, error } = await apiClient.GET(
    `${API_BASE}/administration/audits/{character_id}/inspect/`,
    {
      params: { path: { character_id: characterId } },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load character inspection details"));
  }
  return data as CharacterDetailResponse;
}

export async function loadAdministrationCorporations(): Promise<AdministrationCorporationSchema[]> {
  const { data, error } = await apiClient.GET(`${API_BASE}/administration/corporations/`, {});
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load administration corporations"));
  }
  return data as AdministrationCorporationSchema[];
}

export async function loadAdministrationUnregistered(
  corporationId: number,
): Promise<AdministrationUnregisteredResponse> {
  const { data, error } = await apiClient.GET(
    `${API_BASE}/administration/corporations/{corporation_id}/unregistered/`,
    {
      params: { path: { corporation_id: corporationId } },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load unregistered characters"));
  }
  return data as AdministrationUnregisteredResponse;
}
