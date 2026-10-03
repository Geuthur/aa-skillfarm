// React
import React, { useState } from "react";

// Third Party
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useQueryState } from "nuqs";
import { useTranslation } from "react-i18next";

// Styles
import styles from "./CharacterDashboard.module.css";

import {
  acknowledgeAllExtractions,
  acknowledgeExtractions,
  acknowledgePaused,
  deleteCharacter,
  fetchCharacters,
  fetchOverviewUser,
  toggleNotification,
} from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import type {
  CharacterFilterParams,
  CharacterListResponse,
  CharacterSummarySchema,
  OverviewUserSchema,
} from "@/Api/schema";
import { CharacterTable } from "@/Components/Dashboard/CharacterTable";
import { InactiveTrainingAlert } from "@/Components/Dashboard/InactiveTrainingAlert";
import { DeleteCharacterModal } from "@/Components/Modals/DeleteCharacterModal";
import { SkillQueueModal } from "@/Components/Modals/SkillQueueModal";
import { SkillSetupModal } from "@/Components/Modals/SkillSetupModal";
import { SkillfarmFilterBar } from "@/Components/Dashboard/SkillfarmFilterBar";

interface CharacterDashboardProps {
  /** Show the characters of this user (overview detail) instead of the own characters. */
  userId?: number;
  renderHeader?: (user: OverviewUserSchema) => React.ReactNode;
}

export const CharacterDashboard: React.FC<CharacterDashboardProps> = ({ userId, renderHeader }) => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
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
  const [characterToDelete, setCharacterToDelete] = useState<CharacterSummarySchema | null>(null);

  const filterParams: CharacterFilterParams = {
    search: search || undefined,
    training_status: (trainingStatus as CharacterFilterParams["training_status"]) || "all",
    extraction_status: (extractionStatus as CharacterFilterParams["extraction_status"]) || "all",
    notification_status:
      (notificationStatus as CharacterFilterParams["notification_status"]) || "all",
  };

  const { data, isLoading, error } = useQuery<CharacterListResponse & { user?: OverviewUserSchema }>({
    queryKey: isForeignUser
      ? queryKeys.OverviewUser(userId, filterParams)
      : queryKeys.Characters(filterParams),
    queryFn: () => (isForeignUser ? fetchOverviewUser(userId, filterParams) : fetchCharacters(filterParams)),
  });

  const invalidateCharacters = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.CharactersRoot });
    queryClient.invalidateQueries({ queryKey: queryKeys.Overview });
  };

  // Mutations
  const ackExtractionMutation = useMutation({
    mutationFn: (charId: number) => acknowledgeExtractions(charId),
    onSuccess: invalidateCharacters,
  });

  const ackPausedMutation = useMutation({
    mutationFn: (charId: number) => acknowledgePaused(charId),
    onSuccess: invalidateCharacters,
  });

  const toggleNotifMutation = useMutation({
    mutationFn: (charId: number) => toggleNotification(charId),
    onSuccess: invalidateCharacters,
  });

  const deleteCharMutation = useMutation({
    mutationFn: (charId: number) => deleteCharacter(charId),
    onSuccess: invalidateCharacters,
  });

  const bulkAckMutation = useMutation({
    mutationFn: acknowledgeAllExtractions,
    onSuccess: invalidateCharacters,
  });

  const handleFilterChange = (newFilters: Partial<CharacterFilterParams>) => {
    if (newFilters.search !== undefined) setSearch(newFilters.search || null);
    if (newFilters.training_status !== undefined) setTrainingStatus(newFilters.training_status);
    if (newFilters.extraction_status !== undefined) setExtractionStatus(newFilters.extraction_status);
    if (newFilters.notification_status !== undefined) setNotificationStatus(newFilters.notification_status);
  };

  const handleConfirmDelete = async () => {
    if (characterToDelete) {
      await deleteCharMutation.mutateAsync(characterToDelete.character_id);
      setCharacterToDelete(null);
    }
  };

  return (
    <div>
      {data?.user && renderHeader?.(data.user)}

      {/* Noticeable Banner for characters with paused training */}
      <InactiveTrainingAlert
        pausedCount={data?.paused_training_count ?? 0}
        currentFilter={trainingStatus}
        onFilterInactive={() => handleFilterChange({ training_status: "paused", extraction_status: "all" })}
      />

      {/* Filter Bar with Status Pills & Search */}
      <SkillfarmFilterBar
        filters={filterParams}
        onFilterChange={handleFilterChange}
        totalCount={data?.total_count ?? 0}
        pausedCount={data?.paused_training_count ?? 0}
        pendingCount={data?.pending_extractions_count ?? 0}
        reviewedCount={data?.acknowledged_extractions_count ?? 0}
        onBulkAcknowledge={isForeignUser ? undefined : () => bulkAckMutation.mutate()}
        isBulkAcknowledging={bulkAckMutation.isPending}
      />

      {isLoading && (
        <div className="aa-loader-container">
          <span className={`spinner-border ${styles["loader-spinner"]}`} />
          <span>{t("Loading characters...")}</span>
        </div>
      )}

      {error && (
        <div className={`aa-panel ${styles["error-panel"]}`}>
          {t("Failed to load characters. Please try refreshing the page.")}
        </div>
      )}

      {data && (
        <CharacterTable
          characters={data.characters}
          onViewQueue={(id) => setSelectedQueueCharId(id)}
          onOpenSetup={(id) => setSelectedSetupCharId(id)}
          onAcknowledgeExtractions={(id) => ackExtractionMutation.mutate(id)}
          onAcknowledgePaused={(id) => ackPausedMutation.mutate(id)}
          onToggleNotification={(id) => toggleNotifMutation.mutate(id)}
          onDeleteCharacter={(char) => setCharacterToDelete(char)}
        />
      )}

      {/* Modals */}
      <SkillQueueModal characterId={selectedQueueCharId} onClose={() => setSelectedQueueCharId(null)} />

      <SkillSetupModal characterId={selectedSetupCharId} onClose={() => setSelectedSetupCharId(null)} />

      <DeleteCharacterModal
        character={characterToDelete}
        showModal={Boolean(characterToDelete)}
        setShowModal={(show) => {
          if (!show) setCharacterToDelete(null);
        }}
        isPending={deleteCharMutation.isPending}
        onConfirm={handleConfirmDelete}
      />
    </div>
  );
};

export default CharacterDashboard;
