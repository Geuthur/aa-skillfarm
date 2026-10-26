// React
import React, { useMemo, useState } from "react";

// Third Party
import {
  AlertTriangle,
  Check,
  Building2,
  Clock,
  Coins,
  RefreshCw,
  Shield,
  ShieldAlert,
  Trash2,
  Users,
} from "lucide-react";
import { parseAsInteger, useQueryState } from "nuqs";
import { Badge, Button, ButtonGroup, Card, CardBody, Col, Form, Modal, Row } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/Administration.module.css";

// AA Skillfarm
import type { AdministrationAuditSchema } from "@/Api/schema";
import { AdministrationAuditsTable } from "@/Components/Administration/AdministrationAuditsTable";
import { AdministrationCollapsibleCard } from "@/Components/Administration/AdministrationCollapsibleCard";
import { AdministrationCorporationsTable } from "@/Components/Administration/AdministrationCorporationsTable";
import { AdministrationInspectionView } from "@/Components/Administration/AdministrationInspectionView";
import { AdministrationTaskCard } from "@/Components/Administration/AdministrationTaskCard";
import {
  useAdministrationAccess,
  useAdministrationAuditInspect,
  useAdministrationAudits,
  useAdministrationStats,
  useAdministrationTasks,
  useAuditActions,
} from "@/Components/Administration/Hooks";
import { formatNumber } from "@/Utils/format";

export const AdministrationPage: React.FC = () => {
  const { t } = useTranslation();

  // Filter and search states
  const [statusFilter, setStatusFilter] = useState<"all" | "training" | "paused" | "issues">("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [forceRefreshGlobal, setForceRefreshGlobal] = useState(false);
  const [auditToDelete, setAuditToDelete] = useState<AdministrationAuditSchema | null>(null);

  const { isSuperuser, isAdmin } = useAdministrationAccess();
  const { data: stats, isLoading: isLoadingStats } = useAdministrationStats(isAdmin);
  const {
    data: audits,
    isLoading: isLoadingAudits,
    isError: isErrorAudits,
  } = useAdministrationAudits(isAdmin);
  const { feedback, updateAll, updatePrices } = useAdministrationTasks();
  const { updatingCharacterId, taskFeedback, dismissFeedback, triggerUpdate, deleteAudit } =
    useAuditActions(() => setAuditToDelete(null));

  const handleConfirmDelete = () => {
    if (!auditToDelete) return;
    deleteAudit.mutate(auditToDelete.character_id);
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
  } = useAdministrationAuditInspect(inspectingAudit?.character_id ?? null);

  if (inspectingAudit) {
    return (
      <AdministrationInspectionView
        inspectingAudit={inspectingAudit}
        detail={auditDetail}
        isLoading={isLoadingDetail}
        isError={isErrorDetail}
        updatingCharacterId={updatingCharacterId}
        taskFeedback={taskFeedback}
        onDismissFeedback={dismissFeedback}
        onBack={() => setInspectCharacterId(null)}
        onRefetch={() => refetchDetail()}
        onTriggerUpdate={triggerUpdate}
        isSuperuser={isSuperuser}
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
            <h1 className="h3 mb-1 fw-bold">{t("Administration")}</h1>
            <p className="mb-0 small text-muted">
              {isAdmin
                ? t(
                    "System-wide character synchronization, extraction readiness overview, and administrative maintenance.",
                  )
                : t(
                    "Characters of your corporation that are not registered in Skillfarm yet.",
                  )}
            </p>
          </div>
        </header>

        {isAdmin ? (
          <>
        {feedback && (
          <Card className="mb-3">
            <Card.Body className={`${styles["feedback"]} d-flex align-items-center gap-2`}>
              <Check size={18} />
              <span>{feedback.text}</span>
            </Card.Body>
          </Card>
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

        {/* Global Task Administration Panel (Collapsible, superusers only) */}
        {isSuperuser && (
          <AdministrationCollapsibleCard
            title={t("Global Task Administration")}
            icon={<RefreshCw size={16} className="text-primary" />}
            toggleLabel={t("Toggle Task Administration")}
            testId="toggle-task-panel"
            bodyClassName="p-3"
          >
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
                <AdministrationTaskCard
                  title={t("Characters")}
                  description={t(
                    "Queue background tasks to synchronize skill queues, extractions, and training status for all characters.",
                  )}
                  buttonLabel={t("Update All Characters")}
                  buttonVariant="primary"
                  icon={<Users size={14} />}
                  isPending={updateAll.isPending}
                  onClick={() => updateAll.mutate(forceRefreshGlobal)}
                  testId="update-all-characters-btn"
                />
              </Col>
              <Col md={6}>
                <AdministrationTaskCard
                  title={t("Market Prices")}
                  description={t(
                    "Update market prices for skill injectors, extractors, and PLEX from EVE Online ESI.",
                  )}
                  buttonLabel={t("Update Market Prices")}
                  buttonVariant="secondary"
                  icon={<Coins size={14} />}
                  isPending={updatePrices.isPending}
                  onClick={() => updatePrices.mutate()}
                  testId="update-market-prices-btn"
                />
              </Col>
            </Row>
          </AdministrationCollapsibleCard>
        )}

        {/* Corporations */}
        <AdministrationCollapsibleCard
          title={t("Corporations")}
          icon={<Building2 size={16} className="text-primary" />}
          toggleLabel={t("Toggle Corporations")}
          testId="toggle-corporations-panel"
        >
          <AdministrationCorporationsTable />
        </AdministrationCollapsibleCard>

        {/* Filter and Search Bar */}
        <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-2 mt-4 mb-2">
          <div className="mw-100 overflow-x-auto">
            <ButtonGroup size="sm">
              <Button
                variant={statusFilter === "all" ? "primary" : "secondary"}
                onClick={() => setStatusFilter("all")}
              >
                {t("All")} <Badge bg="secondary" className="ms-1">{totalCount}</Badge>
              </Button>
              <Button
                variant={statusFilter === "training" ? "primary" : "secondary"}
                onClick={() => setStatusFilter("training")}
              >
                {t("In Training")} <Badge bg="secondary" className="ms-1">{trainingCount}</Badge>
              </Button>
              <Button
                variant={statusFilter === "paused" ? "primary" : "secondary"}
                onClick={() => setStatusFilter("paused")}
              >
                {t("Paused")} <Badge bg="secondary" className="ms-1">{pausedCount}</Badge>
              </Button>
              <Button
                variant={statusFilter === "issues" ? "primary" : "secondary"}
                onClick={() => setStatusFilter("issues")}
              >
                {t("Issues")} <Badge bg="secondary" className="ms-1">{issuesCount}</Badge>
              </Button>
            </ButtonGroup>
          </div>

          <div className={`${styles.searchContainer} w-100`}>
            <Form.Control
              type="search"
              placeholder={t("Search by character, user, or corp…")}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              size="sm"
              className="bg-dark text-light border-secondary"
              aria-label={t("Search characters")}
            />
          </div>
        </div>

        {/* All Character Audits Table */}
        <AdministrationAuditsTable
          audits={filteredAudits}
          isLoading={isLoadingAudits}
          isError={isErrorAudits}
          updatingCharacterId={updatingCharacterId}
          taskFeedback={taskFeedback}
          onDismissFeedback={dismissFeedback}
          onInspect={(audit) => setInspectCharacterId(audit.character_id)}
          onTriggerUpdate={triggerUpdate}
          onDelete={(audit) => setAuditToDelete(audit)}
          isSuperuser={isSuperuser}
        />

        {/* Delete Confirmation Modal */}
        <Modal
          show={Boolean(auditToDelete)}
          onHide={() => !deleteAudit.isPending && setAuditToDelete(null)}
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
                      <strong>{t("Total SP:")}</strong> {formatNumber(auditToDelete.total_sp ?? 0)}
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
              disabled={deleteAudit.isPending}
            >
              {t("Cancel")}
            </Button>
            <Button
              variant="danger"
              onClick={handleConfirmDelete}
              disabled={deleteAudit.isPending}
              className="d-flex align-items-center gap-1"
            >
              <Trash2 size={14} />
              <span>
                {deleteAudit.isPending ? t("Deleting…") : t("Confirm Delete")}
              </span>
            </Button>
          </Modal.Footer>
        </Modal>
          </>
        ) : (
          <AdministrationCollapsibleCard
            title={t("Corporations")}
            icon={<Building2 size={16} className="text-primary" />}
            toggleLabel={t("Toggle Corporations")}
            testId="toggle-corporations-panel"
            defaultOpen
          >
            <AdministrationCorporationsTable />
          </AdministrationCollapsibleCard>
        )}
      </CardBody>
    </Card>
  );
};

export default AdministrationPage;
