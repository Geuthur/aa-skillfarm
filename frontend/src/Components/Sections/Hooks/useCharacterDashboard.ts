// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

// AA Skillfarm
import {
  acknowledgeAllExtractions,
  acknowledgeExtractions,
  acknowledgePaused,
  fetchCharacters,
  fetchOverviewUser,
} from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
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
      ? queryKeys.OverviewUser(userId, filterParams)
      : queryKeys.Characters(filterParams),
    queryFn: () =>
      isForeignUser ? fetchOverviewUser(userId, filterParams) : fetchCharacters(filterParams),
  });
}

/** Acknowledge mutations of the dashboard (extractions, paused training, bulk extractions). */
export function useCharacterAcknowledgements() {
  const queryClient = useQueryClient();
  const invalidateCharacters = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.CharactersRoot });
    queryClient.invalidateQueries({ queryKey: queryKeys.Overview });
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
