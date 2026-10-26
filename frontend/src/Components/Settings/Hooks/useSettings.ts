// React
import { useState } from "react";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

// AA Skillfarm
import {
  deleteCharacter,
  fetchUserCharacterStatuses,
  fetchUserSettings,
  toggleNotification,
  triggerCharacterUpdate,
  triggerUpdateAll,
  updateUserSettings,
} from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import type { UserSettingsSchema } from "@/Api/schema";
import { useCooldown, useOwnerCooldowns } from "@/Hooks/useCooldown";
import { useFeedback } from "@/Hooks/useFeedback";

/** Cooldown in seconds after an update was queued. */
const UPDATE_COOLDOWN = 60;

/** Loads the settings of the current user. */
export function useUserSettings() {
  return useQuery({
    queryKey: queryKeys.UserSettings,
    queryFn: fetchUserSettings,
  });
}

/** Loads the registered and missing characters of the current user with their sync status. */
export function useUserCharacterStatuses() {
  return useQuery({
    queryKey: queryKeys.UserCharacterStatuses,
    queryFn: fetchUserCharacterStatuses,
  });
}

/** Saves the user settings optimistically and rolls back when the request fails. */
export function useUpdateUserSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateUserSettings,
    onMutate: async (settings) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.UserSettings });
      const previous = queryClient.getQueryData<UserSettingsSchema>(queryKeys.UserSettings);
      queryClient.setQueryData<UserSettingsSchema>(queryKeys.UserSettings, settings);
      return { previous };
    },
    onError: (_error, _settings, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.UserSettings, context.previous);
      }
    },
    onSuccess: (settings) => {
      queryClient.setQueryData(queryKeys.UserSettings, settings);
    },
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
    queryClient.invalidateQueries({ queryKey: queryKeys.UserCharacterStatuses });
    queryClient.invalidateQueries({ queryKey: queryKeys.CharactersRoot });
    queryClient.invalidateQueries({ queryKey: queryKeys.Overview });
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
