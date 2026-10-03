import { apiClient } from "@/Api/Api";
import type {
  ActionResponse,
  AdminStatsResponse,
  CalculatorResponse,
  CharacterDetailResponse,
  CharacterFilterParams,
  CharacterListResponse,
  MenuSchema,
  OverviewResponse,
  OverviewUserCharactersResponse,
  SkillSetupSchema,
  UserData,
  UserSettingsSchema,
  UserSettingsUpdateRequest,
} from "@/Api/schema";

const API_BASE = "/skillfarm/api";

export async function loadUserData(): Promise<{ user: UserData }> {
  const { data, error } = await apiClient.GET(`${API_BASE}/user/`, {});
  if (error || !data) {
    throw new Error("Failed to load user data");
  }
  return { user: data as UserData };
}

export async function loadMenu(): Promise<MenuSchema> {
  const { data, error } = await apiClient.GET(`${API_BASE}/menu/`, {});
  if (error || !data) {
    throw new Error("Failed to load menu");
  }
  return data as MenuSchema;
}

export async function fetchUserSettings(): Promise<UserSettingsSchema> {
  const { data, error } = await apiClient.GET("/skillfarm/api/settings/", {});
  if (error || !data) {
    throw new Error("Failed to load user settings");
  }
  return data;
}

export async function updateUserSettings(
  settings: UserSettingsUpdateRequest,
): Promise<UserSettingsSchema> {
  const { data, error } = await apiClient.PUT("/skillfarm/api/settings/", {
    body: settings,
  });
  if (error || !data) {
    throw new Error("Failed to update user settings");
  }
  return data;
}

function buildFilterQuery(filters: CharacterFilterParams): Record<string, string | number> {
  const queryParams: Record<string, string | number> = {};
  if (filters.search) queryParams.search = filters.search;
  if (filters.training_status && filters.training_status !== "all") queryParams.training_status = filters.training_status;
  if (filters.extraction_status && filters.extraction_status !== "all") queryParams.extraction_status = filters.extraction_status;
  if (filters.notification_status && filters.notification_status !== "all") queryParams.notification_status = filters.notification_status;
  if (filters.corporation_id) queryParams.corporation_id = filters.corporation_id;
  return queryParams;
}

export async function fetchCharacters(filters: CharacterFilterParams): Promise<CharacterListResponse> {
  const queryParams = buildFilterQuery(filters);

  const { data, error } = await apiClient.GET(`${API_BASE}/characters/`, {
    params: { query: queryParams },
  });
  if (error || !data) {
    throw new Error("Failed to fetch characters");
  }
  return data as CharacterListResponse;
}

export async function fetchOverview(): Promise<OverviewResponse> {
  const { data, error } = await apiClient.GET(`${API_BASE}/overview/`, {});
  if (error || !data) {
    throw new Error("Failed to load overview");
  }
  return data as OverviewResponse;
}

export async function fetchOverviewUser(
  userId: number,
  filters: CharacterFilterParams,
): Promise<OverviewUserCharactersResponse> {
  const { data, error } = await apiClient.GET(`${API_BASE}/overview/{user_id}/`, {
    params: { path: { user_id: userId }, query: buildFilterQuery(filters) },
  });
  if (error || !data) {
    throw new Error(`Failed to fetch characters for user ${userId}`);
  }
  return data as OverviewUserCharactersResponse;
}

export async function fetchCharacterDetail(characterId: number): Promise<CharacterDetailResponse> {
  const { data, error } = await apiClient.GET(`${API_BASE}/characters/{character_id}/`, {
    params: { path: { character_id: characterId } },
  });
  if (error || !data) {
    throw new Error(`Failed to fetch details for character ${characterId}`);
  }
  return data as CharacterDetailResponse;
}

export async function acknowledgeExtractions(characterId: number): Promise<ActionResponse> {
  const { data, error } = await apiClient.POST(
    `${API_BASE}/characters/{character_id}/acknowledge-extractions/`,
    {
      params: { path: { character_id: characterId } },
    }
  );
  if (error || !data) {
    throw new Error("Failed to acknowledge extractions");
  }
  return data as ActionResponse;
}

export async function acknowledgePaused(characterId: number): Promise<ActionResponse> {
  const { data, error } = await apiClient.POST(
    `${API_BASE}/characters/{character_id}/acknowledge-paused/`,
    {
      params: { path: { character_id: characterId } },
    }
  );
  if (error || !data) {
    throw new Error("Failed to acknowledge paused status");
  }
  return data as ActionResponse;
}

export async function toggleNotification(characterId: number): Promise<ActionResponse> {
  const { data, error } = await apiClient.POST(
    `${API_BASE}/characters/{character_id}/toggle-notification/`,
    {
      params: { path: { character_id: characterId } },
    }
  );
  if (error || !data) {
    throw new Error("Failed to toggle notification");
  }
  return data as ActionResponse;
}

export async function fetchSkillSetup(characterId: number): Promise<SkillSetupSchema> {
  const { data, error } = await apiClient.GET(`${API_BASE}/characters/{character_id}/setup/`, {
    params: { path: { character_id: characterId } },
  });
  if (error || !data) {
    throw new Error("Failed to load skill setup");
  }
  return data as SkillSetupSchema;
}

export async function updateSkillSetup(characterId: number, selectedSkills: string[]): Promise<ActionResponse> {
  const { data, error } = await apiClient.POST(`${API_BASE}/characters/{character_id}/setup/`, {
    params: { path: { character_id: characterId } },
    body: { selected_skills: selectedSkills },
  });
  if (error || !data) {
    throw new Error("Failed to update skill setup");
  }
  return data as ActionResponse;
}

export async function deleteCharacter(characterId: number): Promise<ActionResponse> {
  const { data, error } = await apiClient.DELETE(`${API_BASE}/characters/{character_id}/`, {
    params: { path: { character_id: characterId } },
  });
  if (error || !data) {
    throw new Error("Failed to delete character");
  }
  return data as ActionResponse;
}

export async function acknowledgeAllExtractions(): Promise<ActionResponse> {
  const { data, error } = await apiClient.POST(`${API_BASE}/acknowledge-all-extractions/`, {});
  if (error || !data) {
    throw new Error("Failed to bulk acknowledge extractions");
  }
  return data as ActionResponse;
}

export async function fetchCalculatorData(): Promise<CalculatorResponse> {
  const { data, error } = await apiClient.GET(`${API_BASE}/calculator/`, {});
  if (error || !data) {
    throw new Error("Failed to load calculator data");
  }
  return data as CalculatorResponse;
}

export async function fetchAdminStats(): Promise<AdminStatsResponse> {
  const { data, error } = await apiClient.GET(`${API_BASE}/admin/stats/`, {});
  if (error || !data) {
    throw new Error("Failed to load admin stats");
  }
  return data as AdminStatsResponse;
}

export async function triggerUpdateAll(forceRefresh: boolean = false): Promise<ActionResponse> {
  const { data, error } = await apiClient.POST(`${API_BASE}/admin/update-all/`, {
    body: { force_refresh: forceRefresh },
  });
  if (error || !data) {
    throw new Error("Failed to trigger update all");
  }
  return data as ActionResponse;
}

export async function triggerUpdatePrices(): Promise<ActionResponse> {
  const { data, error } = await apiClient.POST(`${API_BASE}/admin/update-prices/`, {});
  if (error || !data) {
    throw new Error("Failed to trigger price update");
  }
  return data as ActionResponse;
}
