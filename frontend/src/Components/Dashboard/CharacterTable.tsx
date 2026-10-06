// React
import React, { useMemo } from "react";

// Third Party
import type { ColumnDef } from "@tanstack/react-table";
import { Bell, BellOff, Check, Eye, PauseCircle, Settings, Trash2 } from "lucide-react";
import { useTranslation } from "react-i18next";

// Styles
import styles from "./CharacterTable.module.css";

import type { CharacterSummarySchema } from "@/Api/schema";
import { ExtractionBadge } from "@/Components/Dashboard/ExtractionBadge";
import { TrainingProgressBar } from "@/Components/Dashboard/TrainingProgressBar";
import { BaseTable } from "@/Components/Tables/BaseTable";
// Utils
import { renderTooltip } from "@/Utils";

interface CharacterTableProps {
  characters: CharacterSummarySchema[];
  onViewQueue: (characterId: number) => void;
  onOpenSetup: (characterId: number) => void;
  onAcknowledgeExtractions: (characterId: number) => void;
  onAcknowledgePaused: (characterId: number) => void;
  onToggleNotification: (characterId: number) => void;
  onDeleteCharacter: (character: CharacterSummarySchema) => void;
}

export const CharacterTable: React.FC<CharacterTableProps> = ({
  characters,
  onViewQueue,
  onOpenSetup,
  onAcknowledgeExtractions,
  onAcknowledgePaused,
  onToggleNotification,
  onDeleteCharacter,
}) => {
  const { t } = useTranslation();

  const columns = useMemo<ColumnDef<CharacterSummarySchema>[]>(
    () => [
      {
        id: "pilot",
        header: t("Pilot"),
        accessorFn: (row) => row.character_name,
        cell: ({ row }) => {
          const char = row.original;
          return (
            <div className={styles["pilot-info"]}>
              <div className="aa-portrait">
                <img src={char.portrait_url} alt={char.character_name} />
              </div>
              <div>
                <div
                  className={styles["pilot-name"]}
                  onClick={() => onViewQueue(char.character_id)}
                >
                  {char.character_name}
                </div>
                <div className={styles["pilot-corp"]}>
                  {char.corporation_name} [{char.corporation_ticker}]
                </div>
              </div>
            </div>
          );
        },
      },
      {
        id: "training_queue",
        header: t("Training Queue"),
        accessorFn: (row) => row.current_training_skill ?? "",
        meta: { className: styles["col-queue"] },
        cell: ({ row }) => {
          const char = row.original;
          return (
            <TrainingProgressBar
              isTraining={char.is_training}
              currentSkill={char.current_training_skill}
              trainingStartDate={char.training_start_date}
              trainingFinishDate={char.training_finish_date}
              queueFinishDate={char.queue_finish_date}
              queuePausedAcknowledged={char.queue_paused_acknowledged}
              progressPercent={char.progress_percent}
            />
          );
        },
      },
      {
        id: "extractions",
        header: t("Extractions"),
        accessorFn: (row) => row.extractions_ready_count,
        meta: { className: styles["col-extractions"] },
        cell: ({ row }) => {
          const char = row.original;
          return (
            <ExtractionBadge
              readyCount={char.extractions_ready_count}
              isAcknowledged={char.extraction_acknowledged}
              acknowledgedAt={char.extraction_acknowledged_at}
            />
          );
        },
      },
      {
        id: "total_sp",
        header: t("Total SP"),
        accessorFn: (row) => row.total_sp,
        cell: ({ row }) => (
          <span className={styles["total-sp"]}>
            {(row.original.total_sp / 1_000_000).toFixed(2)}M
          </span>
        ),
      },
      {
        id: "last_sync",
        header: t("Last Sync"),
        accessorFn: (row) => row.last_update ?? "",
        cell: ({ row }) => (
          <span className={styles["last-sync"]}>
            {row.original.last_update ? row.original.last_update.slice(5) : t("Pending")}
          </span>
        ),
      },
      {
        id: "actions",
        header: t("Actions"),
        enableSorting: false,
        meta: { className: styles["col-actions"], align: "right" },
        cell: ({ row }) => {
          const char = row.original;
          const hasPendingExtractions =
            char.extractions_ready_count > 0 && !char.extraction_acknowledged;
          const hasUnacknowledgedPaused =
            !char.is_training && !char.queue_paused_acknowledged;

          return (
            <div className={styles["actions-cell"]}>
              <div className={styles["actions-group"]}>
                {/* Acknowledge Extraction action */}
                {hasPendingExtractions &&
                  renderTooltip(
                    t("Mark extractions as reviewed"),
                    <button
                      type="button"
                      className="sf-btn sf-btn-warning sf-btn-sm"
                      onClick={() => onAcknowledgeExtractions(char.character_id)}
                    >
                      <Check size={14} />
                      <span>{t("Acknowledge")}</span>
                    </button>,
                  )}

                {/* Acknowledge Paused queue */}
                {hasUnacknowledgedPaused &&
                  renderTooltip(
                    t("Acknowledge paused training"),
                    <button
                      type="button"
                      className="sf-btn sf-btn-secondary sf-btn-sm"
                      onClick={() => onAcknowledgePaused(char.character_id)}
                    >
                      <PauseCircle size={14} />
                      <span>{t("Acknowledge Idle")}</span>
                    </button>,
                  )}

                {/* View Queue */}
                {renderTooltip(
                  t("Inspect Skill Queue"),
                  <button
                    type="button"
                    className="sf-btn sf-btn-secondary sf-btn-sm"
                    onClick={() => onViewQueue(char.character_id)}
                  >
                    <Eye size={14} />
                  </button>,
                )}

                {/* Skill Setup */}
                {renderTooltip(
                  t("Configure Farm Skillset"),
                  <button
                    type="button"
                    className="sf-btn sf-btn-secondary sf-btn-sm"
                    onClick={() => onOpenSetup(char.character_id)}
                  >
                    <Settings size={14} />
                  </button>,
                )}

                {/* Notifications Toggle */}
                {renderTooltip(
                  char.notification_enabled
                    ? t("Disable Notifications")
                    : t("Enable Notifications"),
                  <button
                    type="button"
                    className={`sf-btn sf-btn-secondary sf-btn-sm ${
                      char.notification_enabled ? styles["notification-on"] : ""
                    }`}
                    onClick={() => onToggleNotification(char.character_id)}
                  >
                    {char.notification_enabled ? <Bell size={14} /> : <BellOff size={14} />}
                  </button>,
                )}

                {/* Delete */}
                {renderTooltip(
                  t("Remove from Skillfarm"),
                  <button
                    type="button"
                    className="sf-btn sf-btn-danger sf-btn-sm"
                    onClick={() => onDeleteCharacter(char)}
                  >
                    <Trash2 size={14} />
                  </button>,
                )}
              </div>
            </div>
          );
        },
      },
    ],
    [
      t,
      onViewQueue,
      onOpenSetup,
      onAcknowledgeExtractions,
      onAcknowledgePaused,
      onToggleNotification,
      onDeleteCharacter,
    ],
  );

  if (characters.length === 0) {
    return (
      <div className={`aa-panel ${styles["empty-state"]}`}>
        <h4 className={styles["empty-title"]}>{t("No characters found")}</h4>
        <p className={styles["empty-text"]}>
          {t("Try clearing your filters or adding new characters to Skillfarm.")}
        </p>
      </div>
    );
  }

  return (
    <BaseTable
      data={characters}
      columns={columns}
      variant="vowra"
      itemLabel={t("Characters")}
      pageSizeOptions={[10, 25, 50, 100]}
      initialState={{
        pagination: { pageSize: 25 },
        sorting: [{ id: "pilot", desc: false }],
      }}
      getRowClassName={(row) =>
        row.original.is_training
          ? "sf-card-active"
          : row.original.queue_paused_acknowledged
            ? "sf-card-idle-acknowledged"
            : "sf-card-idle"
      }
    />
  );
};
