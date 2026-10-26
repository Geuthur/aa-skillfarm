// React
import React, { useState } from "react";

// Third Party
import { ArrowLeft, Clock, RefreshCw } from "lucide-react";
import { Alert, Badge, Button, ButtonGroup, Card, Dropdown, Nav, ProgressBar, Spinner, Table } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/Administration.module.css";

import type { CharacterDetailResponse, AdministrationAuditSchema } from "@/Api/schema";
// AA Skillfarm
import { OwnerPortrait } from "@/Components/Base/OwnerPortrait";
import { renderTooltip } from "@/Utils";
import { formatNumber } from "@/Utils/format";

interface AdministrationInspectionViewProps {
  inspectingAudit: AdministrationAuditSchema;
  detail?: CharacterDetailResponse;
  isLoading: boolean;
  isError: boolean;
  updatingCharacterId: number | null;
  taskFeedback: { variant: "success" | "danger"; message: string } | null;
  onDismissFeedback: () => void;
  onBack: () => void;
  onRefetch: () => void;
  onTriggerUpdate: (characterId: number, forceRefresh: boolean) => void;
  isSuperuser?: boolean;
}

export const AdministrationInspectionView: React.FC<AdministrationInspectionViewProps> = ({
  inspectingAudit,
  detail,
  isLoading,
  isError,
  updatingCharacterId,
  taskFeedback,
  onDismissFeedback,
  onBack,
  onTriggerUpdate,
  isSuperuser = false,
}) => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<"queue" | "skills">("queue");

  const isUpdating = updatingCharacterId === inspectingAudit.character_id;

  return (
    <Card className="bg-dark text-light border-0 shadow-sm">
      <Card.Body className="bg-secondary rounded">
        <Card.Header className="d-flex align-items-center justify-content-between mb-4 bg-dark rounded p-3">
          <div className="d-flex align-items-center gap-3">
            <Button
              variant="secondary"
              size="sm"
              onClick={onBack}
              className="d-flex align-items-center gap-1 sf-btn sf-btn-secondary aa-btn aa-btn-secondary"
            >
              <ArrowLeft size={16} />
              <span>{t("Back to Administration Overview")}</span>
            </Button>
            {inspectingAudit.portrait_url && (
              <OwnerPortrait src={inspectingAudit.portrait_url} size="md" shape="rounded" />
            )}
            <div>
              <div className="d-flex align-items-center gap-2">
                <h1 className="h4 mb-0 fw-bold">{inspectingAudit.character_name}</h1>
                {inspectingAudit.corporation_ticker && (
                  <Badge bg="secondary">[{inspectingAudit.corporation_ticker}]</Badge>
                )}
                <Badge bg="warning" text="dark">
                  {t("Administration Inspection")}
                </Badge>
              </div>
              <p className="text-muted small mb-0">
                {t("Owner:")} {inspectingAudit.user_name || t("Unknown")}
              </p>
            </div>
          </div>

          <div className="d-flex align-items-center gap-2">
            <Dropdown as={ButtonGroup} size="sm">
              {renderTooltip(
                t("Trigger character update task"),
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => onTriggerUpdate(inspectingAudit.character_id, false)}
                  disabled={isUpdating}
                  className="d-flex align-items-center gap-1 sf-btn sf-btn-danger aa-btn aa-btn-danger"
                >
                  {isUpdating ? <Spinner size="sm" animation="border" /> : <RefreshCw size={14} />}
                  <span>{t("Update Character")}</span>
                </Button>
              )}
              <Dropdown.Toggle
                split
                size="sm"
                variant="danger"
                aria-label={t("More update options")}
                disabled={isUpdating}
                className="aa-btn aa-btn-danger"
              />
              <Dropdown.Menu align="end">
                <Dropdown.Item onClick={() => onTriggerUpdate(inspectingAudit.character_id, false)}>
                  <RefreshCw size={14} className="me-2 text-primary" />
                  {t("Normal Update")}
                </Dropdown.Item>
                {isSuperuser && (
                  <Dropdown.Item onClick={() => onTriggerUpdate(inspectingAudit.character_id, true)}>
                    <RefreshCw size={14} className="me-2 text-warning" />
                    {t("Force Refresh (Bypass Cache)")}
                  </Dropdown.Item>
                )}
              </Dropdown.Menu>
            </Dropdown>
          </div>
        </Card.Header>

        {taskFeedback && (
          <Alert
            variant={taskFeedback.variant}
            dismissible
            onClose={onDismissFeedback}
            className="mb-3"
          >
            {taskFeedback.message}
          </Alert>
        )}

        {/* Character Metrics */}
        <div className="row g-3 mb-4">
          <div className="col-12 col-md-3">
            <div className="p-3 bg-dark rounded border border-secondary-subtle">
              <div className="text-muted small">{t("Total Skill Points")}</div>
              <div className="h4 mb-0 fw-bold font-monospace">
                {formatNumber(inspectingAudit.total_sp ?? 0)}
              </div>
            </div>
          </div>
          <div className="col-12 col-md-3">
            <div className="p-3 bg-dark rounded border border-secondary-subtle">
              <div className="text-muted small">{t("Training Queue")}</div>
              <div className="h5 mb-0 fw-bold">
                {inspectingAudit.is_training ? (
                  <span className="text-success">{t("Active")}</span>
                ) : (
                  <span className="text-warning">{t("Paused")}</span>
                )}
              </div>
              {inspectingAudit.queue_finish_date && (
                <div className="small text-muted">
                  {t("Finishes:")} {inspectingAudit.queue_finish_date}
                </div>
              )}
            </div>
          </div>
          <div className="col-12 col-md-3">
            <div className="p-3 bg-dark rounded border border-secondary-subtle">
              <div className="text-muted small">{t("Ready Extractions")}</div>
              <div className="h4 mb-0 fw-bold text-info">
                {inspectingAudit.extractions_ready_count}
              </div>
            </div>
          </div>
          <div className="col-12 col-md-3">
            <div className="p-3 bg-dark rounded border border-secondary-subtle">
              <div className="text-muted small">{t("ESI Status")}</div>
              <div className="h5 mb-0 fw-bold">
                <span
                  className={`badge ${
                    inspectingAudit.status === "ok"
                      ? "bg-success"
                      : inspectingAudit.status === "token_error"
                        ? "bg-warning text-dark"
                        : "bg-danger"
                  }`}
                >
                  {inspectingAudit.status}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <Nav variant="tabs" className="mb-3 border-secondary" activeKey={activeTab}>
          <Nav.Item>
            <Nav.Link
              eventKey="queue"
              onClick={() => setActiveTab("queue")}
              className={`text-light ${activeTab === "queue" ? "active bg-dark border-secondary" : ""}`}
            >
              <Clock size={16} className="me-1" />
              {t("Skill Queue")} ({detail?.skillqueue?.length ?? 0})
            </Nav.Link>
          </Nav.Item>
          <Nav.Item>
            <Nav.Link
              eventKey="skills"
              onClick={() => setActiveTab("skills")}
              className={`text-light ${activeTab === "skills" ? "active bg-dark border-secondary" : ""}`}
            >
              {t("Farmed Skills")} ({detail?.farmed_skills?.length ?? 0})
            </Nav.Link>
          </Nav.Item>
        </Nav>

        {isLoading ? (
          <div className="text-center py-5">
            <Spinner animation="border" variant="light" />
            <div className="mt-2 text-muted">{t("Loading character details…")}</div>
          </div>
        ) : isError ? (
          <Alert variant="danger">
            {t("Failed to load detailed inspection data for this character.")}
          </Alert>
        ) : activeTab === "queue" ? (
          <div className="table-responsive">
            <Table hover variant="dark" className="align-middle mb-0">
              <thead>
                <tr>
                  <th>#</th>
                  <th>{t("Skill")}</th>
                  <th>{t("Level")}</th>
                  <th>{t("Progress")}</th>
                  <th>{t("Finishes At")}</th>
                </tr>
              </thead>
              <tbody>
                {detail?.skillqueue && detail.skillqueue.length > 0 ? (
                  detail.skillqueue.map((entry) => (
                    <tr key={`${entry.skill_id}-${entry.queue_position}`}>
                      <td>{entry.queue_position + 1}</td>
                      <td>
                        <div className="fw-semibold">{entry.skill_name}</div>
                        {entry.is_active && (
                          <span className="badge bg-success-subtle text-success border border-success-subtle small">
                            {t("Training Now")}
                          </span>
                        )}
                      </td>
                      <td>{entry.finished_level_roman}</td>
                      <td className={styles.progressCol}>
                        <ProgressBar
                          now={entry.progress_percent}
                          label={`${entry.progress_percent}%`}
                          variant={entry.is_active ? "success" : "secondary"}
                        />
                      </td>
                      <td>{entry.finish_date || "-"}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="text-center py-4 text-muted">
                      {t("Skill queue is currently empty or paused.")}
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
          </div>
        ) : (
          <div className="table-responsive">
            <Table hover variant="dark" className="align-middle mb-0">
              <thead>
                <tr>
                  <th>{t("Skill")}</th>
                  <th>{t("Level")}</th>
                  <th>{t("Skill Points")}</th>
                  <th>{t("Extractable")}</th>
                </tr>
              </thead>
              <tbody>
                {detail?.farmed_skills && detail.farmed_skills.length > 0 ? (
                  detail.farmed_skills.map((skill) => (
                    <tr key={skill.skill_id}>
                      <td className="fw-semibold">{skill.skill_name}</td>
                      <td>{skill.trained_level}</td>
                      <td className="font-monospace">{formatNumber(skill.skillpoints)}</td>
                      <td>
                        {skill.is_extractable ? (
                          <span className="badge bg-info">{t("Extractable (Level 5)")}</span>
                        ) : (
                          <span className="text-muted small">{t("In Training")}</span>
                        )}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} className="text-center py-4 text-muted">
                      {t("No configured farm skills found.")}
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
          </div>
        )}
      </Card.Body>
    </Card>
  );
};
