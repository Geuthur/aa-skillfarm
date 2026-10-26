// React
import React, { useState } from "react";

// Third Party
import { useQueryState } from "nuqs";
import { Card } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/CharacterDashboard.module.css";

import type {
  CharacterFilterParams,
  OverviewUserSchema,
} from "@/Api/schema";
import { CharacterTable, InactiveTrainingAlert, SkillfarmFilterBar } from "@/Components/Dashboard";
import { SkillQueueModal, SkillSetupModal } from "@/Components/Modals";
import { useCharacterAcknowledgements, useCharacters } from "@/Components/Sections/Hooks";

interface CharacterDashboardProps {
  /** Show the characters of this user (overview detail) instead of the own characters. */
  userId?: number;
  renderHeader?: (user: OverviewUserSchema) => React.ReactNode;
}

export const CharacterDashboard: React.FC<CharacterDashboardProps> = ({ userId, renderHeader }) => {
  const { t } = useTranslation();
  const isForeignUser = userId !== undefined;

  // URL state via nuqs for filterable, bookmarkable, and shareable URLs
  const [search, setSearch] = useQueryState("search", { defaultValue: "" });
  const [trainingStatus, setTrainingStatus] = useQueryState("training_status", {
    defaultValue: "all",
  });
  const [extractionStatus, setExtractionStatus] = useQueryState("extraction_status", {
    defaultValue: "all",
  });
  const [notificationStatus, setNotificationStatus] = useQueryState("notification_status", {
    defaultValue: "all",
  });

  // Modal state
  const [selectedQueueCharId, setSelectedQueueCharId] = useState<number | null>(null);
  const [selectedSetupCharId, setSelectedSetupCharId] = useState<number | null>(null);

  const filterParams: CharacterFilterParams = {
    search: search || undefined,
    training_status: (trainingStatus as CharacterFilterParams["training_status"]) || "all",
    extraction_status: (extractionStatus as CharacterFilterParams["extraction_status"]) || "all",
    notification_status:
      (notificationStatus as CharacterFilterParams["notification_status"]) || "all",
  };

  const { data, isLoading, error } = useCharacters(filterParams, userId);
  const { acknowledgeExtraction, acknowledgePausedTraining, acknowledgeAll } =
    useCharacterAcknowledgements();

  const handleFilterChange = (newFilters: Partial<CharacterFilterParams>) => {
    if (newFilters.search !== undefined) setSearch(newFilters.search || null);
    if (newFilters.training_status !== undefined) setTrainingStatus(newFilters.training_status);
    if (newFilters.extraction_status !== undefined) setExtractionStatus(newFilters.extraction_status);
    if (newFilters.notification_status !== undefined) setNotificationStatus(newFilters.notification_status);
  };

  return (
    <div>
      {data?.user && renderHeader ? renderHeader(data.user) : null}

      {/* Noticeable Banner for characters with paused training */}
      <InactiveTrainingAlert
        pausedCount={data?.paused_training_count ?? 0}
        unacknowledgedCount={data?.unacknowledged_paused_count ?? 0}
        currentFilter={trainingStatus}
        onFilterInactive={() => handleFilterChange({ training_status: "paused", extraction_status: "all" })}
      />

      {/* Filter Bar with Status Pills & Search */}
      <SkillfarmFilterBar
        filters={filterParams}
        onFilterChange={handleFilterChange}
        totalCount={data?.total_count ?? 0}
        activeCount={data?.active_training_count ?? 0}
        pausedCount={data?.paused_training_count ?? 0}
        pendingCount={data?.pending_extractions_count ?? 0}
        reviewedCount={data?.acknowledged_extractions_count ?? 0}
        onBulkAcknowledge={isForeignUser ? undefined : () => acknowledgeAll.mutate()}
        isBulkAcknowledging={acknowledgeAll.isPending}
      />

      {isLoading && (
        <div className="aa-loader-container d-flex align-items-center justify-content-center w-100">
          <span className={`spinner-border ${styles["loader-spinner"]}`} />
          <span>{t("Loading characters…")}</span>
        </div>
      )}

      {error && (
        <Card>
          <Card.Body className={`${styles["error-panel"]} p-4 text-center`}>
            {t("Failed to load characters. Please try refreshing the page.")}
          </Card.Body>
        </Card>
      )}

      {data && (
        <CharacterTable
          characters={data.characters}
          onViewQueue={(id) => setSelectedQueueCharId(id)}
          onOpenSetup={(id) => setSelectedSetupCharId(id)}
          onAcknowledgeExtractions={(id) => acknowledgeExtraction.mutate(id)}
          onAcknowledgePaused={(id) => acknowledgePausedTraining.mutate(id)}
        />
      )}

      {/* Modals */}
      <SkillQueueModal characterId={selectedQueueCharId} onClose={() => setSelectedQueueCharId(null)} />

      <SkillSetupModal characterId={selectedSetupCharId} onClose={() => setSelectedSetupCharId(null)} />
    </div>
  );
};

export default CharacterDashboard;
