// React
import React, { useEffect, useState } from "react";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  AlertTriangle,
  Bell,
  BellOff,
  CheckCircle2,
  Clock,
  RotateCw,
  Settings2,
  Trash2,
  Users,
} from "lucide-react";
import { Button, Card } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/SettingsPage.module.css";

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
import type { UserCharacterStatusSchema, UserSettingsSchema } from "@/Api/schema";
import { DeleteCharacterModal } from "@/Components/Modals/DeleteCharacterModal";
import type { DeletableCharacter } from "@/Components/Modals/DeleteCharacterModal";

export const SettingsPage: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  // Cooldown & Modal States
  const [globalCooldown, setGlobalCooldown] = useState(0);
  const [updatingCharacterId, setUpdatingCharacterId] = useState<number | null>(null);
  const [characterCooldowns, setCharacterCooldowns] = useState<Record<number, number>>({});
  const [characterToDelete, setCharacterToDelete] = useState<DeletableCharacter | null>(null);
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
    data: characters,
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
      setCharacterToDelete(null);
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

  const handleConfirmDelete = async () => {
    if (characterToDelete) {
      await deleteCharMutation.mutateAsync(characterToDelete.character_id);
    }
  };

  if (isLoading) {
    return (
      <div className="aa-loader-container">
        <span className="spinner-border" />
        <span>{t("Loading settings...")}</span>
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

  const renderStatusBadge = (char: UserCharacterStatusSchema) => {
    const status = char.status.toLowerCase();
    const isError = status === "error";
    const isTokenError = status === "token_error";
    const isOk = status === "ok";
    const isDisabled = status === "disabled";

    let badgeClass = styles["badge-incomplete"];
    let label = t("Incomplete");
    let Icon = AlertTriangle;

    if (isOk) {
      badgeClass = styles["badge-ok"];
      label = t("OK");
      Icon = CheckCircle2;
    } else if (isError) {
      badgeClass = styles["badge-error"];
      label = t("Error");
      Icon = AlertCircle;
    } else if (isTokenError) {
      badgeClass = styles["badge-token-error"];
      label = t("Token Error");
      Icon = AlertTriangle;
    } else if (isDisabled) {
      badgeClass = styles["badge-disabled"];
      label = t("Disabled");
      Icon = AlertCircle;
    }

    return (
      <span className={`${styles["status-badge"]} ${badgeClass}`}>
        {(isError || isTokenError) && (
          <span className="aa-pending-dot-container me-1" aria-hidden="true">
            <span className={isError ? "aa-danger-dot-ping" : "aa-pending-dot-ping"} />
            <span className={isError ? "aa-danger-dot-core" : "aa-pending-dot-core"} />
          </span>
        )}
        <Icon size={12} aria-hidden="true" />
        <span>{label}</span>
      </span>
    );
  };

  return (
    <Card className={`${styles["page"]} border-0`}>
      <Card.Body className="bg-dark">
        <Card.Header className={styles["header"] + " bg-secondary"}>
          <Settings2 size={24} aria-hidden="true" />
          <div>
            <h1 className={styles["title"]}>{t("Settings")}</h1>
            <p className={styles["description"]}>{t("Manage your Skillfarm preferences.")}</p>
          </div>
        </Card.Header>

        <Card className="bg-secondary text-light border-0 shadow-sm mb-4">
          <Card.Body className={styles["setting-row"]}>
            <div className={styles["setting-copy"]}>
              <div className={styles["setting-title"]}>
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
                <p className={styles["save-status"]} role="status">{t("Saving...")}</p>
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

        {/* Character Update Status & Management Section */}
        <Card className={`${styles["section"]} border-0 shadow-sm`} aria-labelledby="char-status-heading">
          <Card.Body className="bg-secondary text-light">
            <Card.Header className={`${styles["section-header"]} bg-secondary d-flex justify-content-between align-items-center flex-wrap gap-2`}>
              <div className={styles["section-title-wrap"]}>
                <Users size={20} aria-hidden="true" />
                <h2 id="char-status-heading" className={styles["section-title"]}>
                  {t("Character Update Status")}
                </h2>
                {characters && (
                  <span className={styles["section-count"]}>
                    ({characters.length})
                  </span>
                )}
              </div>

              {characters && characters.length > 0 && (
                <Button
                  variant="secondary"
                  size="sm"
                  className="aa-btn aa-btn-secondary aa-btn-sm d-flex align-items-center gap-1"
                  disabled={updateAllMutation.isPending || globalCooldown > 0}
                  onClick={() => updateAllMutation.mutate()}
                >
                  {updateAllMutation.isPending ? (
                    <span className="spinner-border spinner-border-sm" />
                  ) : (
                    <RotateCw size={14} />
                  )}
                  <span>
                    {globalCooldown > 0
                      ? t("Update All ({{seconds}}s)", { seconds: globalCooldown })
                      : t("Update All")}
                  </span>
                </Button>
              )}
            </Card.Header>

            {feedbackMsg && (
              <div
                className={`alert alert-${feedbackMsg.variant} py-2 my-3 d-flex justify-content-between align-items-center`}
                role="alert"
              >
                <span>{feedbackMsg.text}</span>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => setFeedbackMsg(null)}
                  aria-label="Close"
                />
              </div>
            )}

            {isLoadingChars && (
              <div className="aa-loader-container">
                <span className="spinner-border" />
                <span>{t("Loading character statuses...")}</span>
              </div>
            )}

            {isErrorChars && (
              <Card className="bg-secondary text-light border-0 shadow-sm" role="alert">
                <Card.Body className={styles["error"]}>
                  {t("Failed to load character update status.")}
                </Card.Body>
              </Card>
            )}

            {!isLoadingChars && !isErrorChars && characters && characters.length === 0 && (
              <Card className="bg-secondary text-light border-0 shadow-sm">
                <Card.Body className={styles["empty-state"]}>
                  {t("No Skillfarm characters found for your account.")}
                </Card.Body>
              </Card>
            )}

            {!isLoadingChars && !isErrorChars && characters && characters.length > 0 && (
              <div className={styles["characters-grid"]}>
                {characters.map((char) => {
                  const status = char.status.toLowerCase();
                  const isError = status === "error";
                  const isTokenError = status === "token_error";
                  const cardClass = isError
                    ? styles["char-card-error"]
                    : isTokenError
                      ? styles["char-card-warning"]
                      : "";

                  const charCooldown = characterCooldowns[char.character_id] ?? 0;
                  const isUpdating = updatingCharacterId === char.character_id;

                  return (
                    <Card
                      key={char.character_id}
                      className={`aa-panel ${styles["char-card"]} ${cardClass}`}
                    >
                      <div className={styles["char-header"]}>
                        <img
                          src={char.portrait_url}
                          alt={char.character_name}
                          className={styles["portrait"]}
                        />
                        <div className={styles["char-info"]}>
                          <h3 className={styles["char-name"]}>{char.character_name}</h3>
                          <p className={styles["char-corp"]}>
                            {char.corporation_name} [{char.corporation_ticker}]
                          </p>
                        </div>
                      </div>

                      {char.error_message && (
                        <div className={styles["error-banner"]} role="alert">
                          {char.error_message}
                        </div>
                      )}

                      {char.sections && char.sections.length > 0 && (
                        <div className={styles["sections-list"]}>
                          {char.sections.map((sec) => {
                            let dotClass = styles["dot-muted"];
                            if (sec.is_success === true) dotClass = styles["dot-ok"];
                            else if (sec.is_success === false) dotClass = styles["dot-error"];
                            else if (sec.has_token_error) dotClass = styles["dot-warning"];

                            return (
                              <div key={sec.section} className={styles["section-item"]}>
                                <span className="d-inline-flex align-items-center gap-2">
                                  <span
                                    className={`${styles["section-dot"]} ${dotClass}`}
                                    aria-hidden="true"
                                  />
                                  <span>{sec.section_name}</span>
                                </span>
                                <span>
                                  {sec.has_token_error
                                    ? t("Token Error")
                                    : sec.is_success === true
                                      ? t("OK")
                                      : sec.is_success === false
                                        ? t("Failed")
                                        : t("Pending")}
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      )}

                      <div className={styles["badge-row"]}>
                        {renderStatusBadge(char)}
                        <span
                          className={styles["last-sync"]}
                          title={char.last_sync ? `${t("Last sync")}: ${char.last_sync}` : undefined}
                        >
                          <Clock size={12} aria-hidden="true" />
                          <span>{char.last_sync ? char.last_sync.slice(5) : t("Never")}</span>
                        </span>
                      </div>

                      {/* Character Action Buttons: Notifications, Update, Delete */}
                      <div className="d-flex align-items-center justify-content-between mt-3 pt-2 border-top border-secondary flex-wrap gap-2">
                        <Button
                          variant="secondary"
                          size="sm"
                          className={`aa-btn aa-btn-secondary aa-btn-sm d-flex align-items-center gap-1 ${
                            char.notification_enabled ? "text-success" : "text-muted"
                          }`}
                          onClick={() => toggleNotifMutation.mutate(char.character_id)}
                          disabled={toggleNotifMutation.isPending}
                          title={
                            char.notification_enabled
                              ? t("Disable notifications")
                              : t("Enable notifications")
                          }
                          aria-label={
                            char.notification_enabled
                              ? t("Disable notifications")
                              : t("Enable notifications")
                          }
                        >
                          {char.notification_enabled ? <Bell size={13} /> : <BellOff size={13} />}
                          <span>{char.notification_enabled ? t("Notifications On") : t("Notifications Off")}</span>
                        </Button>

                        <div className="d-flex align-items-center gap-2">
                          <Button
                            variant="secondary"
                            size="sm"
                            className="aa-btn aa-btn-secondary aa-btn-sm d-flex align-items-center gap-1"
                            disabled={isUpdating || charCooldown > 0}
                            onClick={() => handleTriggerCharacterUpdate(char.character_id)}
                            title={t("Update character")}
                            aria-label={t("Update character")}
                          >
                            {isUpdating ? (
                              <span className="spinner-border spinner-border-sm" />
                            ) : (
                              <RotateCw size={13} />
                            )}
                            <span>
                              {charCooldown > 0 ? `${charCooldown}s` : t("Update")}
                            </span>
                          </Button>

                          <Button
                            variant="danger"
                            size="sm"
                            className="aa-btn aa-btn-danger aa-btn-sm d-flex align-items-center gap-1"
                            onClick={() => setCharacterToDelete(char)}
                            title={t("Remove from Skillfarm")}
                            aria-label={t("Remove from Skillfarm")}
                          >
                            <Trash2 size={13} />
                            <span>{t("Delete")}</span>
                          </Button>
                        </div>
                      </div>
                    </Card>
                  );
                })}
              </div>
            )}
          </Card.Body>
        </Card>
      </Card.Body>

      <DeleteCharacterModal
        character={characterToDelete}
        showModal={Boolean(characterToDelete)}
        setShowModal={(show) => {
          if (!show) setCharacterToDelete(null);
        }}
        isPending={deleteCharMutation.isPending}
        onConfirm={handleConfirmDelete}
      />
    </Card>
  );
};

export default SettingsPage;