// React
import { useMemo } from "react";

// Third Party
import { Bell, BellOff, Settings2, Users } from "lucide-react";
import { Button, Card } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/SettingsPage.module.css";

// AA Skillfarm
import { BaseOwnerSettingsSection } from "@/Components/Base/OwnerSettings";
import type { BaseMissingOwner, BaseOwner } from "@/Components/Base/OwnerSettings/types";
import {
  useCharacterActions,
  useUpdateUserSettings,
  useUserCharacterStatuses,
  useUserSettings,
} from "@/Components/Settings/Hooks";

export const SettingsPage: React.FC = () => {
  const { t } = useTranslation();
  const { data, isLoading, isError } = useUserSettings();
  const {
    data: charactersData,
    isLoading: isLoadingChars,
    isError: isErrorChars,
  } = useUserCharacterStatuses();
  const updateMutation = useUpdateUserSettings();
  const {
    feedback,
    clearFeedback,
    globalCooldown,
    characterCooldowns,
    updatingCharacterId,
    updateAll,
    triggerCharacterUpdate,
    toggleNotification,
    deleteCharacter,
  } = useCharacterActions();

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
      <div className="aa-loader-container d-flex align-items-center justify-content-center w-100">
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
        <Card.Header className={`${styles["header"]} d-flex align-items-center gap-3 mb-4 bg-secondary`}>
          <Settings2 size={24} aria-hidden="true" />
          <div>
            <h1 className={`${styles["title"]} m-0 fw-bold`}>{t("Settings")}</h1>
            <p className={`${styles["description"]} mt-1 mb-0`}>{t("Manage your Skillfarm preferences.")}</p>
          </div>
        </Card.Header>

        <Card className="bg-secondary text-light border-0 shadow-sm mb-4">
          <Card.Body className="d-flex align-items-start align-items-sm-center justify-content-between gap-4">
            <div className={styles["setting-copy"]}>
              <div className={`${styles["setting-title"]} d-flex align-items-center gap-2 fw-bold`}>
                <BellOff size={18} aria-hidden="true" />
                <label htmlFor="disable-notifications">{t("Disable all notifications")}</label>
              </div>
              <p className={`${styles["setting-description"]} mt-2 mb-0`}>
                {t("When enabled, Skillfarm will not send notifications to your Alliance Auth or Discord account.")}
              </p>
              {updateMutation.isError && (
                <p className={`${styles["error-message"]} mt-2 mb-0`} role="alert">
                  {t("Could not save this setting. Your previous preference was restored.")}
                </p>
              )}
              {updateMutation.isPending && (
                <p className={`${styles["save-status"]} mt-2 mb-0`} role="status">{t("Saving…")}</p>
              )}
            </div>
            <input
              id="disable-notifications"
              className={`${styles["switch"]} m-0 flex-shrink-0`}
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
          onUpdateAll={() => updateAll.mutate()}
          isUpdatingAll={updateAll.isPending}
          globalCooldown={globalCooldown}
          feedbackMessage={feedback}
          onDismissFeedback={clearFeedback}
          onTriggerSingleUpdate={triggerCharacterUpdate}
          updatingOwnerId={updatingCharacterId}
          ownerCooldowns={characterCooldowns}
          onDeleteOwner={(owner) => deleteCharacter.mutateAsync(owner.id)}
          isDeleting={deleteCharacter.isPending}
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
                onClick={() => toggleNotification.mutate(owner.id)}
                disabled={toggleNotification.isPending}
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