// React
import React, { useMemo, useState } from "react";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  Check,
  ChevronDown,
  ChevronUp,
  Clock,
  Coins,
  RefreshCw,
  Shield,
  ShieldAlert,
  Trash2,
  Users,
} from "lucide-react";
import { parseAsInteger, useQueryState } from "nuqs";
import {
  Badge,
  Button,
  ButtonGroup,
  Card,
  CardBody,
  Col,
  Form,
  Modal,
  Row,
  Spinner,
} from "react-bootstrap";
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

  // Filter and search states
  const [statusFilter, setStatusFilter] = useState<"all" | "training" | "paused" | "issues">("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [showTaskPanel, setShowTaskPanel] = useState(false);
  const [forceRefreshGlobal, setForceRefreshGlobal] = useState(false);

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

  // Filter metrics
  const totalCount = audits?.length ?? 0;
  const trainingCount = audits?.filter((a) => a.is_training).length ?? 0;
  const pausedCount = audits?.filter((a) => !a.is_training).length ?? 0;
  const issuesCount =
    audits?.filter(
      (a) => a.status === "error" || a.status === "token_error" || Boolean(a.error_message),
    ).length ?? 0;

  // Filtered audits
  const filteredAudits = useMemo(() => {
    if (!audits) return [];

    let matchingOwnerKeys: Set<string> | null = null;
    if (searchTerm.trim()) {
      const query = searchTerm.toLowerCase();
      matchingOwnerKeys = new Set(
        audits
          .filter((a) => {
            const matchesMain = a.main_character_name?.toLowerCase().includes(query);
            const matchesChar = a.character_name?.toLowerCase().includes(query);
            const matchesCorp = a.corporation_name?.toLowerCase().includes(query);
            const matchesTicker = a.corporation_ticker?.toLowerCase().includes(query);
            const matchesUser = a.user_name?.toLowerCase().includes(query);
            const matchesSkill = a.current_training_skill?.toLowerCase().includes(query);
            return Boolean(
              matchesMain || matchesChar || matchesCorp || matchesTicker || matchesUser || matchesSkill,
            );
          })
          .map((a) => (a.user_id ? `user_${a.user_id}` : `char_${a.character_id}`)),
      );
    }

    return audits.filter((audit) => {
      const ownerKey = audit.user_id ? `user_${audit.user_id}` : `char_${audit.character_id}`;
      if (matchingOwnerKeys && !matchingOwnerKeys.has(ownerKey)) {
        return false;
      }
      if (statusFilter === "training" && !audit.is_training) {
        return false;
      }
      if (statusFilter === "paused" && audit.is_training) {
        return false;
      }
      if (
        statusFilter === "issues" &&
        audit.status === "ok" &&
        !audit.error_message
      ) {
        return false;
      }
      return true;
    });
  }, [audits, statusFilter, searchTerm]);

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
        <Row className="g-3 mt-1 mb-3">
          <Col xs={12} sm={6} md={3}>
            <Card className="bg-body border-secondary h-100 shadow-sm">
              <Card.Body className="p-3 d-flex align-items-center justify-content-between">
                <div>
                  <span className="text-muted small fw-semibold">{t("Total Characters")}</span>
                  <h4 className="mb-0 text-light fw-bold">
                    {isLoadingStats ? "..." : (stats?.total_characters ?? 0)}
                  </h4>
                </div>
                <div className="p-2 rounded-3 bg-secondary bg-opacity-25 text-light">
                  <Users size={24} />
                </div>
              </Card.Body>
            </Card>
          </Col>

          <Col xs={12} sm={6} md={3}>
            <Card className="bg-body border-secondary h-100 shadow-sm">
              <Card.Body className="p-3 d-flex align-items-center justify-content-between">
                <div>
                  <span className="text-muted small fw-semibold">{t("Active in Skillfarm")}</span>
                  <h4 className="mb-0 text-primary fw-bold">
                    {isLoadingStats ? "..." : (stats?.active_characters ?? 0)}
                  </h4>
                </div>
                <div className="p-2 rounded-3 bg-primary bg-opacity-10 text-primary">
                  <Shield size={24} />
                </div>
              </Card.Body>
            </Card>
          </Col>

          <Col xs={12} sm={6} md={3}>
            <Card className="bg-body border-secondary h-100 shadow-sm">
              <Card.Body className="p-3 d-flex align-items-center justify-content-between">
                <div>
                  <span className="text-muted small fw-semibold">{t("Paused Training")}</span>
                  <h4 className="mb-0 text-warning fw-bold">
                    {isLoadingStats ? "..." : (stats?.paused_training_count ?? 0)}
                  </h4>
                </div>
                <div className="p-2 rounded-3 bg-warning bg-opacity-10 text-warning">
                  <Clock size={24} />
                </div>
              </Card.Body>
            </Card>
          </Col>

          <Col xs={12} sm={6} md={3}>
            <Card className="bg-body border-secondary h-100 shadow-sm">
              <Card.Body className="p-3 d-flex align-items-center justify-content-between">
                <div>
                  <span className="text-muted small fw-semibold">{t("Sync Issues")}</span>
                  <h4 className={`mb-0 fw-bold ${issuesCount > 0 ? "text-danger" : "text-success"}`}>
                    {issuesCount}
                  </h4>
                </div>
                <div
                  className={`p-2 rounded-3 ${
                    issuesCount > 0
                      ? "bg-danger bg-opacity-10 text-danger"
                      : "bg-success bg-opacity-10 text-success"
                  }`}
                >
                  {issuesCount > 0 ? <AlertTriangle size={24} /> : <Shield size={24} />}
                </div>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* Global Task Administration Panel (Collapsible) */}
        <Card className="bg-dark border-secondary mb-4 shadow-sm">
          <Card.Header
            className={`border-secondary d-flex align-items-center justify-content-between py-2 ${styles.cursorPointer}`}
            onClick={() => setShowTaskPanel((prev) => !prev)}
          >
            <div className="d-flex align-items-center gap-2">
              <RefreshCw size={16} className="text-primary" />
              <span className="fw-semibold text-light">{t("Global Task Administration")}</span>
            </div>
            <Button
              variant="link"
              size="sm"
              className="p-0 text-muted"
              aria-label={t("Toggle Task Administration")}
              data-testid="toggle-task-panel"
              onClick={(e) => {
                e.stopPropagation();
                setShowTaskPanel((prev) => !prev);
              }}
            >
              {showTaskPanel ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </Button>
          </Card.Header>

          {showTaskPanel && (
            <Card.Body className="p-3">
              <Form.Group className="mb-3">
                <Form.Check
                  type="switch"
                  id="global-force-refresh"
                  label={<span className="small text-muted">{t("Force Refresh ESI")}</span>}
                  checked={forceRefreshGlobal}
                  onChange={(e) => setForceRefreshGlobal(e.target.checked)}
                />
              </Form.Group>

              <Row className="g-3">
                <Col md={6}>
                  <Card className="bg-dark border-secondary h-100">
                    <Card.Header className="border-secondary py-2">
                      <h6 className="mb-0 text-light">{t("Characters")}</h6>
                    </Card.Header>
                    <Card.Body className="d-flex flex-column justify-content-between p-3">
                      <p className="text-muted small">
                        {t(
                          "Queue background tasks to synchronize skill queues, extractions, and training status for all characters.",
                        )}
                      </p>
                      <Button
                        variant="primary"
                        size="sm"
                        disabled={updateAllMutation.isPending}
                        onClick={() => updateAllMutation.mutate(forceRefreshGlobal)}
                        className="w-100 d-flex align-items-center justify-content-center gap-1 aa-btn aa-btn-primary"
                        data-testid="update-all-characters-btn"
                      >
                        {updateAllMutation.isPending ? (
                          <Spinner size="sm" animation="border" />
                        ) : (
                          <Users size={14} />
                        )}
                        {t("Update All Characters")}
                      </Button>
                    </Card.Body>
                  </Card>
                </Col>

                <Col md={6}>
                  <Card className="bg-dark border-secondary h-100">
                    <Card.Header className="border-secondary py-2">
                      <h6 className="mb-0 text-light">{t("Market Prices")}</h6>
                    </Card.Header>
                    <Card.Body className="d-flex flex-column justify-content-between p-3">
                      <p className="text-muted small">
                        {t(
                          "Update market prices for skill injectors, extractors, and PLEX from EVE Online ESI.",
                        )}
                      </p>
                      <Button
                        variant="secondary"
                        size="sm"
                        disabled={updatePricesMutation.isPending}
                        onClick={() => updatePricesMutation.mutate()}
                        className="w-100 d-flex align-items-center justify-content-center gap-1 aa-btn aa-btn-secondary"
                        data-testid="update-market-prices-btn"
                      >
                        {updatePricesMutation.isPending ? (
                          <Spinner size="sm" animation="border" />
                        ) : (
                          <Coins size={14} />
                        )}
                        {t("Update Market Prices")}
                      </Button>
                    </Card.Body>
                  </Card>
                </Col>
              </Row>
            </Card.Body>
          )}
        </Card>

        {/* Filter and Search Bar */}
        <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-2 mt-4 mb-2">
          <ButtonGroup size="sm">
            <Button
              variant={statusFilter === "all" ? "primary" : "secondary"}
              onClick={() => setStatusFilter("all")}
              className={`aa-btn ${statusFilter === "all" ? "aa-btn-primary" : "aa-btn-secondary"}`}
            >
              {t("All")} <Badge bg="secondary" className="ms-1">{totalCount}</Badge>
            </Button>
            <Button
              variant={statusFilter === "training" ? "primary" : "secondary"}
              onClick={() => setStatusFilter("training")}
              className={`aa-btn ${statusFilter === "training" ? "aa-btn-primary" : "aa-btn-secondary"}`}
            >
              {t("In Training")} <Badge bg="secondary" className="ms-1">{trainingCount}</Badge>
            </Button>
            <Button
              variant={statusFilter === "paused" ? "primary" : "secondary"}
              onClick={() => setStatusFilter("paused")}
              className={`aa-btn ${statusFilter === "paused" ? "aa-btn-primary" : "aa-btn-secondary"}`}
            >
              {t("Paused")} <Badge bg="secondary" className="ms-1">{pausedCount}</Badge>
            </Button>
            <Button
              variant={statusFilter === "issues" ? "primary" : "secondary"}
              onClick={() => setStatusFilter("issues")}
              className={`aa-btn ${statusFilter === "issues" ? "aa-btn-primary" : "aa-btn-secondary"}`}
            >
              {t("Issues")} <Badge bg="secondary" className="ms-1">{issuesCount}</Badge>
            </Button>
          </ButtonGroup>

          <div className={styles.searchContainer}>
            <Form.Control
              type="search"
              placeholder={t("Search by character, user, or corp...")}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              size="sm"
              className="bg-dark text-light border-secondary"
              aria-label={t("Search characters")}
            />
          </div>
        </div>

        {/* All Character Audits Table */}
        <SuperuserAuditsTable
          audits={filteredAudits}
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
