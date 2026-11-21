// Third Party
import { apiErrorMessage } from "aa-geuthur-react";

// AA Skillfarm
import { apiClient } from "@/Api/Api";
import { buildFilterQuery } from "@/Api/calls/characters";
import type {
  CharacterFilterParams,
  OverviewResponse,
  OverviewUserCharactersResponse,
} from "@/Api/schema";

const API_BASE = "/skillfarm/api";

/** Query keys of the overview area: all users and the characters of a single user. */
export const overviewQueryKeys = {
  all: ["overview"] as const,
  user: (userId: number | null, filters?: unknown) => ["overview", "user", userId, filters] as const,
};

export async function fetchOverview(): Promise<OverviewResponse> {
  const { data, error } = await apiClient.GET(`${API_BASE}/overview/`, {});
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load overview"));
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
    throw new Error(apiErrorMessage(error, `Failed to fetch characters for user ${userId}`));
  }
  return data as OverviewUserCharactersResponse;
}
