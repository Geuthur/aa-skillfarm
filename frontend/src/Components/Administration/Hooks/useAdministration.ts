// React
import { useState } from "react";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

// AA Skillfarm
import {
  deleteAdministrationAudit,
  fetchAdminStats,
  loadAdministrationAuditInspect,
  loadAdministrationAudits,
  loadAdministrationCorporations,
  loadAdministrationUnregistered,
  triggerAdministrationAuditUpdate,
  triggerUpdateAll,
  triggerUpdatePrices,
} from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import { useFeedback } from "@/Hooks/useFeedback";
import { useUserData } from "@/Hooks/useUserData";

/** Feedback of a single audit action (update or delete) that stays until it is dismissed. */
export interface TaskFeedback {
  variant: "success" | "danger";
  message: string;
}

/**
 * Access flags of the current user.
 * Global update tasks, force refresh and audit deletion are reserved for superusers.
 * Audits, statistics and tasks require admin access; corp access only sees the corporations section.
 */
export function useAdministrationAccess() {
  const { data } = useUserData();
  return {
    isSuperuser: Boolean(data?.user.is_superuser),
    isAdmin: Boolean(data?.user.is_admin),
  };
}

/** Loads the system-wide character statistics. */
export function useAdministrationStats(enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.AdminStats,
    queryFn: fetchAdminStats,
    enabled,
  });
}

/** Loads all character audits. */
export function useAdministrationAudits(enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.AdministrationAudits,
    queryFn: loadAdministrationAudits,
    enabled,
  });
}

/** Loads the detail data of the audit that is currently inspected. */
export function useAdministrationAuditInspect(characterId: number | null) {
  return useQuery({
    queryKey: queryKeys.AdministrationAuditInspect(characterId),
    queryFn: () =>
      characterId ? loadAdministrationAuditInspect(characterId) : Promise.reject(new Error("No audit")),
    enabled: characterId !== null,
  });
}

/** Loads the corporations with their registered and unregistered character counts. */
export function useAdministrationCorporations() {
  return useQuery({
    queryKey: queryKeys.AdministrationCorporations,
    queryFn: loadAdministrationCorporations,
  });
}

/** Loads the unregistered characters of a corporation, once one is selected. */
export function useAdministrationUnregistered(corporationId: number | null) {
  return useQuery({
    queryKey: queryKeys.AdministrationUnregistered(corporationId),
    queryFn: () => loadAdministrationUnregistered(corporationId as number),
    enabled: corporationId !== null,
  });
}

/** Global sync tasks (update all characters, update prices) with a self-clearing feedback message. */
export function useAdministrationTasks() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { feedback, showFeedback } = useFeedback();

  const updateAll = useMutation({
    mutationFn: (force: boolean) => triggerUpdateAll(force),
    onSuccess: (res) => {
      showFeedback("success", res.message);
      queryClient.invalidateQueries({ queryKey: queryKeys.AdministrationAudits });
    },
    onError: () => showFeedback("danger", t("Failed to queue character update task.")),
  });

  const updatePrices = useMutation({
    mutationFn: triggerUpdatePrices,
    onSuccess: (res) => showFeedback("success", res.message),
    onError: () => showFeedback("danger", t("Failed to queue price update task.")),
  });

  return { feedback, updateAll, updatePrices };
}

/**
 * Update and delete actions for a single audit.
 * @param onDeleteSettled Called after the delete finished, successfully or not
 */
export function useAuditActions(onDeleteSettled: () => void) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [updatingCharacterId, setUpdatingCharacterId] = useState<number | null>(null);
  const [taskFeedback, setTaskFeedback] = useState<TaskFeedback | null>(null);

  const updateMutation = useMutation({
    mutationFn: ({ characterId, forceRefresh }: { characterId: number; forceRefresh: boolean }) =>
      triggerAdministrationAuditUpdate(characterId, forceRefresh),
    onSuccess: (res) => {
      setTaskFeedback({
        variant: "success",
        message: res.message || t("Update task queued successfully."),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.AdministrationAudits });
    },
    onError: (err: unknown) => {
      setTaskFeedback({
        variant: "danger",
        message:
          err instanceof Error ? err.message : t("Failed to trigger update task for character."),
      });
    },
    onSettled: () => setUpdatingCharacterId(null),
  });

  const deleteAudit = useMutation({
    mutationFn: (characterId: number) => deleteAdministrationAudit(characterId),
    onSuccess: (res) => {
      setTaskFeedback({
        variant: "success",
        message: res.message || t("Character audit deleted successfully."),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.AdministrationAudits });
    },
    onError: (err: unknown) => {
      setTaskFeedback({
        variant: "danger",
        message: err instanceof Error ? err.message : t("Failed to delete character audit."),
      });
    },
    onSettled: onDeleteSettled,
  });

  const triggerUpdate = (characterId: number, forceRefresh: boolean) => {
    setUpdatingCharacterId(characterId);
    setTaskFeedback(null);
    updateMutation.mutate({ characterId, forceRefresh });
  };

  return {
    updatingCharacterId,
    taskFeedback,
    dismissFeedback: () => setTaskFeedback(null),
    triggerUpdate,
    deleteAudit,
  };
}
