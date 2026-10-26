// React
import { useEffect, useMemo, useState } from "react";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, BellOff, Settings2, Users } from "lucide-react";
import { Button, Card } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/SettingsPage.module.css";

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
import { BaseOwnerSettingsSection } from "@/Components/Base/OwnerSettings";
import type { BaseMissingOwner, BaseOwner } from "@/Components/Base/OwnerSettings/types";

export const SettingsPage: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  // Cooldown & Feedback States
  const [globalCooldown, setGlobalCooldown] = useState(0);
  const [updatingCharacterId, setUpdatingCharacterId] = useState<number | null>(null);
  const [characterCooldowns, setCharacterCooldowns] = useState<Record<number, number>>({});
  const [feedbackMsg, setFeedbackMsg] = useState<{ variant: "success" | "danger"; text: string } | null>(null);

  useEffect(() => {
    if (globalCooldown <= 0) return;
    const timer = setInterval(() => {
      setGlobalCooldown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [globalCooldown]);

  useEffect(() => {
    const activeCooldowns = Object.values(characterCooldowns).some((v) => v > 0);
    if (!activeCooldowns) return;
    const timer = setInterval(() => {
      setCharacterCooldowns((prev) => {
        const next: Record<number, number> = {};
        for (const [key, val] of Object.entries(prev)) {
          if (val > 1) next[Number(key)] = val - 1;
        }
        return next;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [characterCooldowns]);

  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.UserSettings,
    queryFn: fetchUserSettings,
  });

  const {
    data: charactersData,
    isLoading: isLoadingChars,
    isError: isErrorChars,
  } = useQuery({
    queryKey: queryKeys.UserCharacterStatuses,
    queryFn: fetchUserCharacterStatuses,
  });

  const invalidateQueries = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.UserCharacterStatuses });
    queryClient.invalidateQueries({ queryKey: queryKeys.CharactersRoot });
    queryClient.invalidateQueries({ queryKey: queryKeys.Overview });
  };

  const updateMutation = useMutation({
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

  const updateAllMutation = useMutation({
    mutationFn: () => triggerUpdateAll(false),
    onSuccess: (res) => {
      setFeedbackMsg({ variant: "success", text: res.message || t("Update all task queued.") });
      setGlobalCooldown(60);
      invalidateQueries();
      setTimeout(() => setFeedbackMsg(null), 5000);
    },
    onError: (err: unknown) => {
      setFeedbackMsg({
        variant: "danger",
        text: err instanceof Error ? err.message : t("Failed to queue update all task."),
      });
      setTimeout(() => setFeedbackMsg(null), 5000);
    },
  });

  const updateCharacterMutation = useMutation({
    mutationFn: (charId: number) => triggerCharacterUpdate(charId, false),
    onSuccess: (res, charId) => {
      setFeedbackMsg({ variant: "success", text: res.message || t("Character update task queued.") });
      setCharacterCooldowns((prev) => ({ ...prev, [charId]: 60 }));
      invalidateQueries();
      setTimeout(() => setFeedbackMsg(null), 5000);
    },
    onError: (err: unknown) => {
      setFeedbackMsg({
        variant: "danger",
        text: err instanceof Error ? err.message : t("Failed to trigger character update."),
      });
      setTimeout(() => setFeedbackMsg(null), 5000);
    },
    onSettled: () => {
      setUpdatingCharacterId(null);
    },
  });

  const handleTriggerCharacterUpdate = (charId: number) => {
    setUpdatingCharacterId(charId);
    updateCharacterMutation.mutate(charId);
  };

  const toggleNotifMutation = useMutation({
    mutationFn: (charId: number) => toggleNotification(charId),
    onSuccess: () => {
      invalidateQueries();
    },
    onError: (err: unknown) => {
      setFeedbackMsg({
        variant: "danger",
        text: err instanceof Error ? err.message : t("Failed to toggle notification."),
      });
      setTimeout(() => setFeedbackMsg(null), 5000);
    },
  });

  const deleteCharMutation = useMutation({
    mutationFn: (charId: number) => deleteCharacter(charId),
    onSuccess: (res) => {
      setFeedbackMsg({ variant: "success", text: res.message || t("Character removed successfully.") });
      invalidateQueries();
      setTimeout(() => setFeedbackMsg(null), 5000);
    },
    onError: (err: unknown) => {
      setFeedbackMsg({
        variant: "danger",
        text: err instanceof Error ? err.message : t("Failed to delete character."),
      });
      setTimeout(() => setFeedbackMsg(null), 5000);
    },
  });

  const characters = charactersData?.characters;
  const missingCharacters = charactersData?.missing_characters;

  const mappedOwners: BaseOwner[] = useMemo(() => {
    if (!characters) return [];
    return characters.map((char) => ({
      id: char.character_id,
      name: char.character_name,
      owner_type: "character",
      avatar_url: char.portrait_url,
      subtitle: `[${char.corporation_ticker}]`,
      status: char.status,
      has_error: char.has_error,
      error_message: char.error_message,
      last_sync: char.last_sync,
      sections: char.sections,
    }));
  }, [characters]);

  const mappedMissing: BaseMissingOwner[] = useMemo(() => {
    if (!missingCharacters) return [];
    return missingCharacters.map((char) => ({
      id: char.character_id,
      name: char.character_name,
      avatar_url: char.portrait_url,
      subtitle: char.corporation_name,
    }));
  }, [missingCharacters]);

  if (isLoading) {
    return (
      <div className="aa-loader-container">
        <span className="spinner-border" />
        <span>{t("Loading settings…")}</span>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <Card className="bg-secondary text-light border-0 shadow-sm" role="alert">
        <Card.Body className={styles["error"]}>
          {t("Failed to load settings. Please try refreshing the page.")}
        </Card.Body>
      </Card>
    );
  }

  return (
    <Card className={`${styles["page"]} mx-auto m-0 border-0`}>
      <Card.Body className="bg-dark">
        <Card.Header className={styles["header"] + " bg-secondary"}>
          <Settings2 size={24} aria-hidden="true" />
          <div>
            <h1 className={`${styles["title"]} m-0 fw-bold`}>{t("Settings")}</h1>
            <p className={styles["description"]}>{t("Manage your Skillfarm preferences.")}</p>
          </div>
        </Card.Header>

        <Card className="bg-secondary text-light border-0 shadow-sm mb-4">
          <Card.Body className={styles["setting-row"]}>
            <div className={styles["setting-copy"]}>
              <div className={`${styles["setting-title"]} d-flex align-items-center gap-2 fw-bold`}>
                <BellOff size={18} aria-hidden="true" />
                <label htmlFor="disable-notifications">{t("Disable all notifications")}</label>
              </div>
              <p className={styles["setting-description"]}>
                {t("When enabled, Skillfarm will not send notifications to your Alliance Auth or Discord account.")}
              </p>
              {updateMutation.isError && (
                <p className={styles["error-message"]} role="alert">
                  {t("Could not save this setting. Your previous preference was restored.")}
                </p>
              )}
              {updateMutation.isPending && (
                <p className={styles["save-status"]} role="status">{t("Saving…")}</p>
              )}
            </div>
            <input
              id="disable-notifications"
              className={styles["switch"]}
              type="checkbox"
              role="switch"
              checked={data.disable_notifications}
              disabled={updateMutation.isPending}
              onChange={(event) =>
                updateMutation.mutate({ disable_notifications: event.currentTarget.checked })
              }
            />
          </Card.Body>
        </Card>

        {/* Modular BaseOwnerSettingsSection with Registered & Missing characters */}
        <BaseOwnerSettingsSection<BaseOwner, BaseMissingOwner>
          title={t("Character Update Status")}
          description={t("ESI synchronization status of your linked characters.")}
          icon={<Users size={20} aria-hidden="true" />}
          owners={mappedOwners}
          missingOwners={mappedMissing}
          isLoading={isLoadingChars}
          isError={isErrorChars}
          errorMessage={t("Failed to load character update status.")}
          emptyMessage={t("No Skillfarm characters found for your account.")}
          appName="Skillfarm"
          onUpdateAll={() => updateAllMutation.mutate()}
          isUpdatingAll={updateAllMutation.isPending}
          globalCooldown={globalCooldown}
          feedbackMessage={feedbackMsg}
          onDismissFeedback={() => setFeedbackMsg(null)}
          onTriggerSingleUpdate={handleTriggerCharacterUpdate}
          updatingOwnerId={updatingCharacterId}
          ownerCooldowns={characterCooldowns}
          onDeleteOwner={(owner) => deleteCharMutation.mutateAsync(owner.id)}
          isDeleting={deleteCharMutation.isPending}
          deleteModalTitle={t("Remove Character from Skillfarm")}
          deleteModalDescription={(owner) =>
            t(
              "Are you sure you want to remove {{name}} from Skillfarm? All skill queues and audit records for this character will be permanently deleted.",
              { name: owner.name },
            )
          }
          renderCardActions={(owner) => {
            const char = charactersData?.characters.find((c) => c.character_id === owner.id);
            const notificationEnabled = char?.notification_enabled ?? false;
            return (
              <Button
                variant="secondary"
                size="sm"
                className={`d-flex align-items-center gap-1 ${
                  notificationEnabled ? "text-success" : "text-muted"
                }`}
                onClick={() => toggleNotifMutation.mutate(owner.id)}
                disabled={toggleNotifMutation.isPending}
                title={
                  notificationEnabled
                    ? t("Disable Notifications")
                    : t("Enable Notifications")
                }
                aria-label={
                  notificationEnabled
                    ? t("Disable Notifications")
                    : t("Enable Notifications")
                }
              >
                {notificationEnabled ? <Bell size={13} /> : <BellOff size={13} />}
                <span>
                  {notificationEnabled ? t("Notifications On") : t("Notifications Off")}
                </span>
              </Button>
            );
          }}
          missingSectionTitle={t("Characters not in Skillfarm")}
          missingActionUrl="/skillfarm/characters/add/"
          missingActionLabel={t("Add Character")}
        />
      </Card.Body>
    </Card>
  );
};

export default SettingsPage;