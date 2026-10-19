// React
import React, { useMemo } from "react";

// Third Party
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { Eye, RefreshCw, Trash2, User } from "lucide-react";
import { Alert, Button, ButtonGroup, Card, Dropdown, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/Superuser.module.css";

// AA Skillfarm
import type { SuperuserAuditSchema } from "@/Api/schema";
import BaseTable from "@/Components/Base/BaseTable/BaseTable";
import { renderTooltip } from "@/Utils";

interface SuperuserAuditsTableProps {
  audits?: SuperuserAuditSchema[];
  isLoading: boolean;
  isError: boolean;
  updatingCharacterId: number | null;
  taskFeedback: { variant: "success" | "danger"; message: string } | null;
  onDismissFeedback: () => void;
  onInspect: (audit: SuperuserAuditSchema) => void;
  onTriggerUpdate: (characterId: number, forceRefresh: boolean) => void;
  onDelete: (audit: SuperuserAuditSchema) => void;
}

export const SuperuserAuditsTable: React.FC<SuperuserAuditsTableProps> = ({
  audits,
  isLoading,
  isError,
  updatingCharacterId,
  taskFeedback,
  onDismissFeedback,
  onInspect,
  onTriggerUpdate,
  onDelete,
}) => {
  const { t } = useTranslation();

  const columns = useMemo<ColumnDef<SuperuserAuditSchema, unknown>[]>(() => {
    const columnHelper = createColumnHelper<SuperuserAuditSchema>();

    return [
      columnHelper.display({
        id: "avatar",
        header: () => null,
        size: 48,
        enableSorting: false,
        cell: ({ row }) => {
          const audit = row.original;
          return audit.portrait_url ? (
            <img
              src={audit.portrait_url}
              alt=""
              width={32}
              height={32}
              className="rounded"
              loading="lazy"
            />
          ) : (
            <div className={`p-1 bg-secondary rounded text-center ${styles.avatarFallback}`}>
              <User size={16} />
            </div>
          );
        },
      }),

      columnHelper.accessor("character_name", {
        id: "character_name",
        header: t("Character"),
        cell: ({ row }) => {
          const audit = row.original;
          return (
            <div>
              <div className="fw-semibold">{audit.character_name}</div>
              {audit.corporation_name && (
                <span className="text-muted small">
                  {audit.corporation_name}{" "}
                  {audit.corporation_ticker && `[${audit.corporation_ticker}]`}
                </span>
              )}
            </div>
          );
        },
      }),

      columnHelper.accessor("user_name", {
        id: "user_name",
        header: t("Owner User"),
        cell: ({ row }) => {
          const audit = row.original;
          return audit.user_name ? (
            <span className="badge bg-secondary border border-secondary-subtle">
              {audit.user_name}
            </span>
          ) : (
            <span className="text-muted small">-</span>
          );
        },
      }),

      columnHelper.accessor("status", {
        id: "status",
        header: t("ESI Status"),
        cell: ({ row }) => {
          const audit = row.original;
          return (
            <span
              className={`badge ${
                audit.status === "ok"
                  ? "bg-success"
                  : audit.status === "token_error"
                    ? "bg-warning text-dark"
                    : "bg-danger"
              }`}
            >
              {audit.status}
            </span>
          );
        },
      }),

      columnHelper.accessor("total_sp", {
        id: "total_sp",
        header: t("Total SP"),
        cell: ({ row }) => {
          const audit = row.original;
          return (
            <span className="fw-semibold font-monospace">
              {audit.total_sp?.toLocaleString() ?? "0"}
            </span>
          );
        },
      }),

      columnHelper.accessor("is_training", {
        id: "is_training",
        header: t("Training Status"),
        cell: ({ row }) => {
          const audit = row.original;
          return audit.is_training ? (
            <div>
              <span className="badge bg-success mb-1">{t("Training")}</span>
              {audit.current_training_skill && (
                <div className={`small text-muted text-truncate ${styles.skillTruncate}`}>
                  {audit.current_training_skill}
                </div>
              )}
            </div>
          ) : (
            <span className="badge bg-warning text-dark">{t("Paused")}</span>
          );
        },
      }),

      columnHelper.accessor("extractions_ready_count", {
        id: "extractions_ready_count",
        header: t("Ready Extractions"),
        cell: ({ row }) => {
          const audit = row.original;
          return audit.extractions_ready_count > 0 ? (
            <span className="badge bg-info">{audit.extractions_ready_count}</span>
          ) : (
            <span className="text-muted small">0</span>
          );
        },
      }),

      columnHelper.display({
        id: "actions",
        header: () => <div className="text-end">{t("Actions")}</div>,
        enableSorting: false,
        cell: ({ row }) => {
          const audit = row.original;
          const isUpdating = updatingCharacterId === audit.character_id;

          return (
            <div className="d-flex align-items-center justify-content-end gap-2">
              {renderTooltip(
                t("Inspect Character Details"),
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => onInspect(audit)}
                  className="d-inline-flex align-items-center gap-1 sf-btn sf-btn-primary aa-btn aa-btn-primary"
                >
                  <Eye size={13} />
                  <span>{t("Inspect")}</span>
                </Button>
              )}
              <Dropdown as={ButtonGroup} size="sm">
                {renderTooltip(
                  t("Trigger character update task"),
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => onTriggerUpdate(audit.character_id, false)}
                    disabled={isUpdating}
                    className="d-inline-flex align-items-center gap-1 sf-btn sf-btn-danger aa-btn aa-btn-danger"
                  >
                    {isUpdating ? (
                      <Spinner size="sm" animation="border" />
                    ) : (
                      <RefreshCw size={13} />
                    )}
                    <span>{t("Update")}</span>
                  </Button>
                )}
                {renderTooltip(
                  t("More update options"),
                  <Dropdown.Toggle
                    split
                    size="sm"
                    variant="danger"
                    aria-label={t("More update options")}
                    disabled={isUpdating}
                    className="aa-btn aa-btn-danger"
                  />
                )}
                <Dropdown.Menu
                  align="end"
                  className={`shadow-lg ${styles.dropdownMenu}`}
                >
                  <Dropdown.Item onClick={() => onTriggerUpdate(audit.character_id, false)}>
                    <RefreshCw size={14} className="me-2 text-primary" />
                    {t("Normal Update")}
                  </Dropdown.Item>
                  <Dropdown.Item onClick={() => onTriggerUpdate(audit.character_id, true)}>
                    <RefreshCw size={14} className="me-2 text-warning" />
                    {t("Force Refresh (Bypass Cache)")}
                  </Dropdown.Item>
                </Dropdown.Menu>
              </Dropdown>
              {renderTooltip(
                t("Delete Audit"),
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => onDelete(audit)}
                  className="d-inline-flex align-items-center gap-1 sf-btn sf-btn-danger aa-btn aa-btn-danger"
                >
                  <Trash2 size={13} />
                  <span>{t("Delete")}</span>
                </Button>
              )}
            </div>
          );
        },
      }),
    ];
  }, [t, updatingCharacterId, onInspect, onTriggerUpdate, onDelete]);

  return (
    <Card className="bg-secondary text-light border-0 shadow-sm mt-3">
      <Card.Header className="d-flex align-items-center justify-content-between bg-transparent py-3">
        <h2 className="h5 mb-0 fw-semibold">{t("All Skillfarm Character Audits")}</h2>
      </Card.Header>
      <Card.Body>
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

        <BaseTable
          data={audits}
          columns={columns}
          isFetching={isLoading}
          isError={isError}
          emptyText={t("No Skillfarm characters found.")}
        />
      </Card.Body>
    </Card>
  );
};
