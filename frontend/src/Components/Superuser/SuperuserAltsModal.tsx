// React
import React, { useMemo } from "react";

// Third Party
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { Eye, RefreshCw, Trash2, User } from "lucide-react";
import { Badge, Button, ButtonGroup, Dropdown, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/Superuser.module.css";

// AA Skillfarm
import type { SuperuserAuditSchema } from "@/Api/schema";
import { BaseModal, ModalSize } from "@/Components/Base/BaseModal";
import type { ModalData } from "@/Components/Base/BaseModal";
import { BaseTable } from "@/Components/Base/BaseTable";
import type { MainCharacterGroup } from "@/Components/Superuser/SuperuserAuditsTable";
import { renderTooltip } from "@/Utils";

export interface SuperuserAltsModalProps {
  group: MainCharacterGroup | null;
  updatingCharacterId: number | null;
  onHide: () => void;
  onInspect: (audit: SuperuserAuditSchema) => void;
  onTriggerUpdate: (characterId: number, forceRefresh: boolean) => void;
  onDelete: (audit: SuperuserAuditSchema) => void;
}

export const SuperuserAltsModal: React.FC<SuperuserAltsModalProps> = ({
  group,
  updatingCharacterId,
  onHide,
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
        size: 36,
        enableSorting: false,
        cell: ({ row }) => {
          const audit = row.original;
          return audit.portrait_url ? (
            <img
              src={audit.portrait_url}
              alt=""
              width={28}
              height={28}
              className="rounded flex-shrink-0"
              loading="lazy"
            />
          ) : (
            <div className={`p-1 bg-secondary rounded text-center ${styles.avatarFallback}`}>
              <User size={14} />
            </div>
          );
        },
      }),

      columnHelper.accessor("character_name", {
        id: "character_name",
        header: t("Alt Character"),
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

      columnHelper.accessor("status", {
        id: "status",
        header: t("ESI Status"),
        cell: ({ row }) => {
          const audit = row.original;
          return (
            <div>
              <Badge
                bg={
                  audit.status === "ok"
                    ? "success"
                    : audit.status === "token_error"
                      ? "warning"
                      : "danger"
                }
                text={audit.status === "token_error" ? "dark" : undefined}
              >
                {audit.status}
              </Badge>
              {audit.error_message && (
                <div
                  className="small text-danger text-truncate"
                  style={{ maxWidth: 160 }}
                >
                  {audit.error_message}
                </div>
              )}
            </div>
          );
        },
      }),

      columnHelper.accessor("total_sp", {
        id: "total_sp",
        header: t("Total SP"),
        cell: ({ getValue }) => (
          <span className="fw-semibold font-monospace">
            {((getValue() as number) ?? 0).toLocaleString()}
          </span>
        ),
      }),

      columnHelper.accessor("is_training", {
        id: "training_status",
        header: t("Training Status"),
        cell: ({ row }) => {
          const audit = row.original;
          return audit.is_training ? (
            <div>
              <Badge bg="success" className="mb-1">
                {t("Training")}
              </Badge>
              {audit.current_training_skill && (
                <div
                  className={`small text-muted text-truncate ${styles.skillTruncate}`}
                >
                  {audit.current_training_skill}
                </div>
              )}
            </div>
          ) : (
            <Badge bg="warning" text="dark">
              {t("Paused")}
            </Badge>
          );
        },
      }),

      columnHelper.accessor("extractions_ready_count", {
        id: "extractions_ready_count",
        header: t("Ready Extractions"),
        cell: ({ getValue }) => {
          const count = (getValue() as number) ?? 0;
          return count > 0 ? (
            <Badge bg="info">{count}</Badge>
          ) : (
            <span className="text-muted small">0</span>
          );
        },
      }),

      columnHelper.display({
        id: "actions",
        header: () => <div className="text-end">{t("Actions")}</div>,
        size: 160,
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
                </Button>,
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
                  </Button>,
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
                  />,
                )}
                <Dropdown.Menu
                  align="end"
                  className={`shadow-lg ${styles.dropdownMenu}`}
                >
                  <Dropdown.Item
                    onClick={() => onTriggerUpdate(audit.character_id, false)}
                  >
                    <RefreshCw size={14} className="me-2 text-primary" />
                    {t("Normal Update")}
                  </Dropdown.Item>
                  <Dropdown.Item
                    onClick={() => onTriggerUpdate(audit.character_id, true)}
                  >
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
                </Button>,
              )}
            </div>
          );
        },
      }),
    ];
  }, [t, updatingCharacterId, onInspect, onTriggerUpdate, onDelete]);

  const modalData: ModalData = {
    modal_id: "superuser-alts-modal",
    title: group
      ? `${group.mainCharacterName} — ${group.alts.length} ${
          group.alts.length === 1 ? t("Alt") : t("Alts")
        }`
      : t("Alts"),
    url: "",
  };

  return (
    <BaseModal
      data={modalData}
      showModal={group !== null}
      setShowModal={(show) => {
        if (!show) onHide();
      }}
      size={ModalSize.extraLarge}
    >
      <div className="aa-panel p-0">
        <BaseTable
          columns={columns}
          data={group?.alts ?? []}
          emptyText={t("No alt characters found.")}
          exportFileName={`alts_${group?.mainCharacterName ?? "character"}.csv`}
        />
      </div>
    </BaseModal>
  );
};

export default SuperuserAltsModal;
