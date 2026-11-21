// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

// AA Skillfarm
import {
  acknowledgeAllExtractions,
  acknowledgeExtractions,
  acknowledgePaused,
  charactersQueryKeys,
  fetchCharacters,
} from "@/Api/calls/characters";
import { fetchOverviewUser, overviewQueryKeys } from "@/Api/calls/overview";
import type {
  CharacterFilterParams,
  CharacterListResponse,
  OverviewUserSchema,
} from "@/Api/schema";

/**
 * Loads the filtered character list of the own user, or of another user when `userId` is given.
 */
export function useCharacters(filterParams: CharacterFilterParams, userId?: number) {
  const isForeignUser = userId !== undefined;
  return useQuery<CharacterListResponse & { user?: OverviewUserSchema }>({
    queryKey: isForeignUser
      ? overviewQueryKeys.user(userId, filterParams)
      : charactersQueryKeys.list(filterParams),
    queryFn: () =>
      isForeignUser ? fetchOverviewUser(userId, filterParams) : fetchCharacters(filterParams),
  });
}

/** Acknowledge mutations of the dashboard (extractions, paused training, bulk extractions). */
export function useCharacterAcknowledgements() {
  const queryClient = useQueryClient();
  const invalidateCharacters = () => {
    queryClient.invalidateQueries({ queryKey: charactersQueryKeys.root });
    queryClient.invalidateQueries({ queryKey: overviewQueryKeys.all });
  };

  const acknowledgeExtraction = useMutation({
    mutationFn: (characterId: number) => acknowledgeExtractions(characterId),
    onSuccess: invalidateCharacters,
  });

  const acknowledgePausedTraining = useMutation({
    mutationFn: (characterId: number) => acknowledgePaused(characterId),
    onSuccess: invalidateCharacters,
  });

  const acknowledgeAll = useMutation({
    mutationFn: acknowledgeAllExtractions,
    onSuccess: invalidateCharacters,
  });

  return { acknowledgeExtraction, acknowledgePausedTraining, acknowledgeAll };
}
