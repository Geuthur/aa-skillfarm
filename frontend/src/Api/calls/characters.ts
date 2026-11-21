// Third Party
import { apiErrorMessage } from "aa-geuthur-react";

// AA Skillfarm
import { apiClient } from "@/Api/Api";
import type {
  ActionResponse,
  CharacterDetailResponse,
  CharacterFilterParams,
  CharacterListResponse,
  SkillSetupSchema,
} from "@/Api/schema";

const API_BASE = "/skillfarm/api";

/** Query keys of the characters area: the own character list, character details and skill setup. */
export const charactersQueryKeys = {
  root: ["characters"] as const,
  list: (filters?: unknown) => ["characters", filters] as const,
  detail: (characterId: number | null) => ["characterDetail", characterId] as const,
  skillSetup: (characterId: number | null) => ["skillSetup", characterId] as const,
};

export function buildFilterQuery(filters: CharacterFilterParams): Record<string, string | number> {
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
    throw new Error(apiErrorMessage(error, "Failed to fetch characters"));
  }
  return data as CharacterListResponse;
}

export async function fetchCharacterDetail(characterId: number): Promise<CharacterDetailResponse> {
  const { data, error } = await apiClient.GET(`${API_BASE}/characters/{character_id}/`, {
    params: { path: { character_id: characterId } },
  });
  if (error || !data) {
    throw new Error(apiErrorMessage(error, `Failed to fetch details for character ${characterId}`));
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
    throw new Error(apiErrorMessage(error, "Failed to acknowledge extractions"));
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
    throw new Error(apiErrorMessage(error, "Failed to acknowledge paused status"));
  }
  return data as ActionResponse;
}

export async function acknowledgeAllExtractions(): Promise<ActionResponse> {
  const { data, error } = await apiClient.POST(`${API_BASE}/acknowledge-all-extractions/`, {});
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to bulk acknowledge extractions"));
  }
  return data as ActionResponse;
}

export async function fetchSkillSetup(characterId: number): Promise<SkillSetupSchema> {
  const { data, error } = await apiClient.GET(`${API_BASE}/characters/{character_id}/setup/`, {
    params: { path: { character_id: characterId } },
  });
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load skill setup"));
  }
  return data as SkillSetupSchema;
}

export async function updateSkillSetup(characterId: number, selectedSkills: string[]): Promise<ActionResponse> {
  const { data, error } = await apiClient.POST(`${API_BASE}/characters/{character_id}/setup/`, {
    params: { path: { character_id: characterId } },
    body: { selected_skills: selectedSkills },
  });
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to update skill setup"));
  }
  return data as ActionResponse;
}
