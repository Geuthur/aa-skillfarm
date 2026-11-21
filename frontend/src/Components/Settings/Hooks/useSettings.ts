// React
import { useState } from "react";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCooldown, useFeedback, useOwnerCooldowns } from "aa-geuthur-react";
import { useTranslation } from "react-i18next";

// AA Skillfarm
import { triggerUpdateAll } from "@/Api/calls/administration";
import { charactersQueryKeys } from "@/Api/calls/characters";
import { overviewQueryKeys } from "@/Api/calls/overview";
import {
  deleteCharacter,
  fetchUserCharacterStatuses,
  settingsQueryKeys,
  toggleNotification,
  triggerCharacterUpdate,
} from "@/Api/calls/settings";

/** Cooldown in seconds after an update was queued. */
const UPDATE_COOLDOWN = 60;

/** Loads the registered and missing characters of the current user with their sync status. */
export function useUserCharacterStatuses() {
  return useQuery({
    queryKey: settingsQueryKeys.statuses,
    queryFn: fetchUserCharacterStatuses,
  });
}

/**
 * Character actions of the settings page (update all, update one, notifications, delete)
 * with their feedback message and cooldowns.
 */
export function useCharacterActions() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { feedback, showFeedback, clearFeedback } = useFeedback();
  const globalCooldown = useCooldown();
  const characterCooldowns = useOwnerCooldowns();
  const [updatingCharacterId, setUpdatingCharacterId] = useState<number | null>(null);

  const invalidateQueries = () => {
    queryClient.invalidateQueries({ queryKey: settingsQueryKeys.statuses });
    queryClient.invalidateQueries({ queryKey: charactersQueryKeys.root });
    queryClient.invalidateQueries({ queryKey: overviewQueryKeys.all });
  };

  const errorMessage = (err: unknown, fallback: string) =>
    err instanceof Error ? err.message : fallback;

  const updateAll = useMutation({
    mutationFn: () => triggerUpdateAll(false),
    onSuccess: (res) => {
      showFeedback("success", res.message || t("Update all task queued."));
      globalCooldown.start(UPDATE_COOLDOWN);
      invalidateQueries();
    },
    onError: (err: unknown) =>
      showFeedback("danger", errorMessage(err, t("Failed to queue update all task."))),
  });

  const updateCharacter = useMutation({
    mutationFn: (characterId: number) => triggerCharacterUpdate(characterId, false),
    onSuccess: (res, characterId) => {
      showFeedback("success", res.message || t("Character update task queued."));
      characterCooldowns.start(characterId, UPDATE_COOLDOWN);
      invalidateQueries();
    },
    onError: (err: unknown) =>
      showFeedback("danger", errorMessage(err, t("Failed to trigger character update."))),
    onSettled: () => setUpdatingCharacterId(null),
  });

  const toggleNotificationMutation = useMutation({
    mutationFn: (characterId: number) => toggleNotification(characterId),
    onSuccess: invalidateQueries,
    onError: (err: unknown) =>
      showFeedback("danger", errorMessage(err, t("Failed to toggle notification."))),
  });

  const deleteCharacterMutation = useMutation({
    mutationFn: (characterId: number) => deleteCharacter(characterId),
    onSuccess: (res) => {
      showFeedback("success", res.message || t("Character removed successfully."));
      invalidateQueries();
    },
    onError: (err: unknown) =>
      showFeedback("danger", errorMessage(err, t("Failed to delete character."))),
  });

  const triggerCharacterUpdateFor = (characterId: number) => {
    setUpdatingCharacterId(characterId);
    updateCharacter.mutate(characterId);
  };

  return {
    feedback,
    clearFeedback,
    globalCooldown: globalCooldown.seconds,
    characterCooldowns: characterCooldowns.cooldowns,
    updatingCharacterId,
    updateAll,
    triggerCharacterUpdate: triggerCharacterUpdateFor,
    toggleNotification: toggleNotificationMutation,
    deleteCharacter: deleteCharacterMutation,
  };
}
