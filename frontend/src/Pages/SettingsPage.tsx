// React
import React from "react";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertCircle, AlertTriangle, BellOff, CheckCircle2, Clock, Settings2, Users } from "lucide-react";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Pages/SettingsPage.module.css";

import { fetchUserCharacterStatuses, fetchUserSettings, updateUserSettings } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import type { UserCharacterStatusSchema, UserSettingsSchema } from "@/Api/schema";

export const SettingsPage: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

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
      <div className={`aa-panel ${styles["error"]}`} role="alert">
        {t("Failed to load settings. Please try refreshing the page.")}
      </div>
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
    <main className={`aa-panel-light ${styles["page"]}`}>
      <header className={styles["header"]}>
        <Settings2 size={24} aria-hidden="true" />
        <div>
          <h1 className={styles["title"]}>{t("Settings")}</h1>
          <p className={styles["description"]}>{t("Manage your Skillfarm preferences.")}</p>
        </div>
      </header>

      <section className={`aa-panel ${styles["setting-row"]}`}>
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
      </section>

      {/* Character Update Status Section */}
      <section className={styles["section"]} aria-labelledby="char-status-heading">
        <header className={styles["section-header"]}>
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
        </header>

        {isLoadingChars && (
          <div className="aa-loader-container">
            <span className="spinner-border" />
            <span>{t("Loading character statuses...")}</span>
          </div>
        )}

        {isErrorChars && (
          <div className={`aa-panel ${styles["error"]}`} role="alert">
            {t("Failed to load character update status.")}
          </div>
        )}

        {!isLoadingChars && !isErrorChars && characters && characters.length === 0 && (
          <div className={`aa-panel ${styles["empty-state"]}`}>
            {t("No Skillfarm characters found for your account.")}
          </div>
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

              return (
                <article
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
                </article>
              );
            })}
          </div>
        )}
      </section>
    </main>
  );
};

export default SettingsPage;