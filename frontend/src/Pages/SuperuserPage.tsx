// React
import React, { useMemo, useState } from "react";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Check, Coins, RefreshCw, ShieldAlert, Trash2, Users } from "lucide-react";
import { parseAsInteger, useQueryState } from "nuqs";
import { Button, Card, CardBody, Modal } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/Superuser.module.css";

// AA Skillfarm
import {
  deleteSuperuserAudit,
  fetchAdminStats,
  loadSuperuserAuditInspect,
  loadSuperuserAudits,
  triggerSuperuserAuditUpdate,
  triggerUpdateAll,
  triggerUpdatePrices,
} from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import type { SuperuserAuditSchema } from "@/Api/schema";
import { SuperuserAuditsTable } from "@/Components/Superuser/SuperuserAuditsTable";
import { SuperuserInspectionView } from "@/Components/Superuser/SuperuserInspectionView";

export const SuperuserPage: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);

  // Queries
  const { data: stats, isLoading: isLoadingStats } = useQuery({
    queryKey: queryKeys.AdminStats,
    queryFn: fetchAdminStats,
  });

  const {
    data: audits,
    isLoading: isLoadingAudits,
    isError: isErrorAudits,
  } = useQuery({
    queryKey: queryKeys.SuperuserAudits,
    queryFn: loadSuperuserAudits,
  });

  // Global Sync Mutations
  const updateAllMutation = useMutation({
    mutationFn: (force: boolean) => triggerUpdateAll(force),
    onSuccess: (res) => {
      setFeedbackMsg(res.message);
      queryClient.invalidateQueries({ queryKey: queryKeys.SuperuserAudits });
      setTimeout(() => setFeedbackMsg(null), 5000);
    },
    onError: () => {
      setFeedbackMsg(t("Failed to queue character update task."));
      setTimeout(() => setFeedbackMsg(null), 5000);
    },
  });

  const updatePricesMutation = useMutation({
    mutationFn: triggerUpdatePrices,
    onSuccess: (res) => {
      setFeedbackMsg(res.message);
      setTimeout(() => setFeedbackMsg(null), 5000);
    },
    onError: () => {
      setFeedbackMsg(t("Failed to queue price update task."));
      setTimeout(() => setFeedbackMsg(null), 5000);
    },
  });

  // Single Audit Update Mutation
  const [updatingCharacterId, setUpdatingCharacterId] = useState<number | null>(null);
  const [taskFeedback, setTaskFeedback] = useState<{
    variant: "success" | "danger";
    message: string;
  } | null>(null);

  const auditUpdateMutation = useMutation({
    mutationFn: ({ characterId, forceRefresh }: { characterId: number; forceRefresh: boolean }) =>
      triggerSuperuserAuditUpdate(characterId, forceRefresh),
    onSuccess: (res) => {
      setTaskFeedback({
        variant: "success",
        message: res.message || t("Update task queued successfully."),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.SuperuserAudits });
    },
    onError: (err: unknown) => {
      setTaskFeedback({
        variant: "danger",
        message:
          err instanceof Error
            ? err.message
            : t("Failed to trigger update task for character."),
      });
    },
    onSettled: () => {
      setUpdatingCharacterId(null);
    },
  });

  const handleTriggerAuditUpdate = (characterId: number, forceRefresh: boolean) => {
    setUpdatingCharacterId(characterId);
    setTaskFeedback(null);
    auditUpdateMutation.mutate({ characterId, forceRefresh });
  };

  // Audit Deletion Mutation
  const [auditToDelete, setAuditToDelete] = useState<SuperuserAuditSchema | null>(null);

  const deleteAuditMutation = useMutation({
    mutationFn: (characterId: number) => deleteSuperuserAudit(characterId),
    onSuccess: (res) => {
      setTaskFeedback({
        variant: "success",
        message: res.message || t("Character audit deleted successfully."),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.SuperuserAudits });
      setAuditToDelete(null);
    },
    onError: (err: unknown) => {
      setTaskFeedback({
        variant: "danger",
        message:
          err instanceof Error ? err.message : t("Failed to delete character audit."),
      });
      setAuditToDelete(null);
    },
  });

  const handleConfirmDelete = () => {
    if (!auditToDelete) return;
    deleteAuditMutation.mutate(auditToDelete.character_id);
  };

  // Inspect state via nuqs URL parameter
  const [inspectCharacterId, setInspectCharacterId] = useQueryState("inspect", parseAsInteger);
  const inspectingAudit = useMemo(
    () =>
      inspectCharacterId
        ? audits?.find((a) => a.character_id === inspectCharacterId) ?? null
        : null,
    [inspectCharacterId, audits],
  );

  const {
    data: auditDetail,
    isLoading: isLoadingDetail,
    isError: isErrorDetail,
    refetch: refetchDetail,
  } = useQuery({
    queryKey: inspectingAudit
      ? queryKeys.SuperuserAuditInspect(inspectingAudit.character_id)
      : ["none"],
    queryFn: () =>
      inspectingAudit
        ? loadSuperuserAuditInspect(inspectingAudit.character_id)
        : Promise.reject(new Error("No audit")),
    enabled: Boolean(inspectingAudit),
  });

  if (inspectingAudit) {
    return (
      <SuperuserInspectionView
        inspectingAudit={inspectingAudit}
        detail={auditDetail}
        isLoading={isLoadingDetail}
        isError={isErrorDetail}
        updatingCharacterId={updatingCharacterId}
        taskFeedback={taskFeedback}
        onDismissFeedback={() => setTaskFeedback(null)}
        onBack={() => setInspectCharacterId(null)}
        onRefetch={() => refetchDetail()}
        onTriggerUpdate={handleTriggerAuditUpdate}
      />
    );
  }

  return (
    <Card className="bg-dark d-flex flex-column gap-3">
      <CardBody>
        <header className="d-flex align-items-center gap-3 mb-4">
          <div className="p-2 rounded bg-danger-subtle text-danger border border-danger-subtle">
            <ShieldAlert size={28} />
          </div>
          <div>
            <h1 className="h3 mb-1 fw-bold">{t("Superuser Administration")}</h1>
            <p className="mb-0 small text-muted">
              {t(
                "System-wide character synchronization, extraction readiness overview, and administrative maintenance.",
              )}
            </p>
          </div>
        </header>

        {feedbackMsg && (
          <div className={`aa-panel ${styles["feedback"]} mb-3`}>
            <Check size={18} />
            <span>{feedbackMsg}</span>
          </div>
        )}

        {/* Global Metrics */}
        <div className={styles["metrics-grid"]}>
          <div className="aa-panel">
            <div className={styles["metric-label"]}>{t("Total Characters")}</div>
            <div className={styles["metric-value"]}>
              {isLoadingStats ? "..." : stats?.total_characters}
            </div>
          </div>

          <div className="aa-panel">
            <div className={styles["metric-label"]}>{t("Active in Skillfarm")}</div>
            <div className={styles["metric-value-emerald"]}>
              {isLoadingStats ? "..." : stats?.active_characters}
            </div>
          </div>

          <div className="aa-panel">
            <div className={styles["metric-label"]}>{t("Paused Training")}</div>
            <div className={styles["metric-value-amber"]}>
              {isLoadingStats ? "..." : stats?.paused_training_count}
            </div>
          </div>

          <div className="aa-panel">
            <div className={styles["metric-label"]}>{t("Pending Extractions")}</div>
            <div className={styles["metric-value-amber"]}>
              {isLoadingStats ? "..." : stats?.total_pending_extractions}
            </div>
          </div>
        </div>

        {/* Global Task Execution Panel */}
        <div className={`aa-panel-lg ${styles["actions-panel"]} mt-3`}>
          <div>
            <h4 className={styles["section-title"]}>{t("Character ESI Sync Tasks")}</h4>
            <p className={styles["section-text"]}>
              {t("Queue asynchronous background tasks to refresh skills and skill queues from ESI.")}
            </p>
            <div className={styles["button-row"]}>
              <button
                type="button"
                className="sf-btn sf-btn-primary aa-btn aa-btn-primary"
                onClick={() => updateAllMutation.mutate(false)}
                disabled={updateAllMutation.isPending}
              >
                <Users size={16} />
                <span>{t("Update Stale Characters")}</span>
              </button>
              <button
                type="button"
                className="sf-btn sf-btn-secondary aa-btn aa-btn-secondary"
                onClick={() => updateAllMutation.mutate(true)}
                disabled={updateAllMutation.isPending}
              >
                <RefreshCw size={16} />
                <span>{t("Force Refresh All Characters")}</span>
              </button>
            </div>
          </div>

          <hr className={styles["divider"]} />

          <div>
            <h4 className={styles["section-title"]}>{t("Market Prices Sync")}</h4>
            <p className={styles["section-text"]}>
              {t(
                "Fetch latest Jita market aggregates from Fuzzwork for PLEX, Extractors, and Injectors.",
              )}
            </p>
            <button
              type="button"
              className="sf-btn sf-btn-secondary aa-btn aa-btn-secondary"
              onClick={() => updatePricesMutation.mutate()}
              disabled={updatePricesMutation.isPending}
            >
              <Coins size={16} />
              <span>{t("Update Market Prices")}</span>
            </button>
          </div>
        </div>

        {/* All Character Audits Table */}
        <SuperuserAuditsTable
          audits={audits}
          isLoading={isLoadingAudits}
          isError={isErrorAudits}
          updatingCharacterId={updatingCharacterId}
          taskFeedback={taskFeedback}
          onDismissFeedback={() => setTaskFeedback(null)}
          onInspect={(audit) => setInspectCharacterId(audit.character_id)}
          onTriggerUpdate={handleTriggerAuditUpdate}
          onDelete={(audit) => setAuditToDelete(audit)}
        />

        {/* Delete Confirmation Modal */}
        <Modal
          show={Boolean(auditToDelete)}
          onHide={() => !deleteAuditMutation.isPending && setAuditToDelete(null)}
          centered
        >
          <Modal.Header closeButton className="border-secondary bg-dark text-light">
            <Modal.Title className="d-flex align-items-center gap-2 text-danger">
              <Trash2 size={20} />
              <span>{t("Delete Character Audit")}</span>
            </Modal.Title>
          </Modal.Header>
          <Modal.Body className="bg-dark text-light">
            <div className="d-flex align-items-start gap-3">
              <AlertTriangle className="text-danger flex-shrink-0 mt-1" size={24} />
              <div>
                <p className="fw-semibold mb-1">
                  {t("Are you sure you want to delete character audit '{{name}}'?", {
                    name: auditToDelete?.character_name,
                  })}
                </p>
                <p className="small text-muted mb-2">
                  {t(
                    "This will permanently delete this character from Skillfarm, removing all tracked skills, queues, and configuration. This action cannot be undone.",
                  )}
                </p>
                {auditToDelete && (
                  <div className="p-2 rounded border border-secondary-subtle small bg-body">
                    <div>
                      <strong>{t("Character ID:")}</strong> {auditToDelete.character_id}
                    </div>
                    <div>
                      <strong>{t("Owner User:")}</strong> {auditToDelete.user_name || t("Unknown")}
                    </div>
                    <div>
                      <strong>{t("Total SP:")}</strong> {auditToDelete.total_sp?.toLocaleString()}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </Modal.Body>
          <Modal.Footer className="border-secondary bg-dark">
            <Button
              variant="secondary"
              onClick={() => setAuditToDelete(null)}
              disabled={deleteAuditMutation.isPending}
              className="sf-btn sf-btn-secondary aa-btn aa-btn-secondary"
            >
              {t("Cancel")}
            </Button>
            <Button
              variant="danger"
              onClick={handleConfirmDelete}
              disabled={deleteAuditMutation.isPending}
              className="d-flex align-items-center gap-1 aa-btn aa-btn-danger"
            >
              <Trash2 size={14} />
              <span>
                {deleteAuditMutation.isPending ? t("Deleting...") : t("Confirm Delete")}
              </span>
            </Button>
          </Modal.Footer>
        </Modal>
      </CardBody>
    </Card>
  );
};

export default SuperuserPage;
