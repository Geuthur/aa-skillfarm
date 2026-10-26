// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

// AA Skillfarm
import { fetchCharacterDetail, fetchSkillSetup, updateSkillSetup } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";

/** Loads the skill queue of a character. */
export function useCharacterDetail(characterId: number | null) {
  return useQuery({
    queryKey: queryKeys.CharacterDetail(characterId),
    queryFn: () => (characterId ? fetchCharacterDetail(characterId) : Promise.reject("No ID")),
    enabled: !!characterId,
  });
}

/** Loads the farm skillset and the selectable skills of a character. */
export function useSkillSetup(characterId: number | null) {
  return useQuery({
    queryKey: queryKeys.SkillSetup(characterId),
    queryFn: () => (characterId ? fetchSkillSetup(characterId) : Promise.reject("No ID")),
    enabled: !!characterId,
  });
}

/**
 * Saves the farm skillset of a character.
 * @param onSaved Called after the skillset was saved and the caches were invalidated
 */
export function useSaveSkillSetup(characterId: number | null, onSaved: () => void) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (skills: string[]) => {
      if (!characterId) throw new Error("No character selected");
      return updateSkillSetup(characterId, skills);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.CharactersRoot });
      queryClient.invalidateQueries({ queryKey: queryKeys.Overview });
      queryClient.invalidateQueries({ queryKey: queryKeys.CharacterDetail(characterId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.SkillSetup(characterId) });
      onSaved();
    },
  });
}
