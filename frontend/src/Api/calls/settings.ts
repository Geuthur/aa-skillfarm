// Third Party
import { apiErrorMessage } from "aa-geuthur-react";

// AA Skillfarm
import { apiClient } from "@/Api/Api";
import type {
  ActionResponse,
  UserCharacterStatusResponse,
} from "@/Api/schema";

const API_BASE = "/skillfarm/api";

/** Query keys of the settings area. */
export const settingsQueryKeys = {
  statuses: ["userCharacterStatuses"] as const,
};

export async function fetchUserCharacterStatuses(): Promise<UserCharacterStatusResponse> {
  const { data, error } = await apiClient.GET("/skillfarm/api/user/characters/status/", {});
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load character update statuses"));
  }
  return data as UserCharacterStatusResponse;
}

export async function toggleNotification(characterId: number): Promise<ActionResponse> {
  const { data, error } = await apiClient.POST(
    `${API_BASE}/characters/{character_id}/toggle-notification/`,
    {
      params: { path: { character_id: characterId } },
    }
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to toggle notification"));
  }
  return data as ActionResponse;
}

export async function deleteCharacter(characterId: number): Promise<ActionResponse> {
  const { data, error } = await apiClient.DELETE(`${API_BASE}/characters/{character_id}/`, {
    params: { path: { character_id: characterId } },
  });
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to delete character"));
  }
  return data as ActionResponse;
}

export async function triggerCharacterUpdate(
  characterId: number,
  forceRefresh: boolean = false,
): Promise<ActionResponse> {
  const { data, error } = await apiClient.POST(
    `${API_BASE}/characters/{character_id}/update/`,
    {
      params: { path: { character_id: characterId } },
      body: { force_refresh: forceRefresh },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to trigger character update"));
  }
  return data as ActionResponse;
}
