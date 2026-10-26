// React
import React, { useMemo, useState } from "react";

// Third Party
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { Eye, RefreshCw, Trash2 } from "lucide-react";
import { Badge, Button, ButtonGroup, Card, Dropdown, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/Administration.module.css";

import type { AdministrationAuditSchema } from "@/Api/schema";
import type { MainCharacterGroup } from "@/Components/Administration/AdministrationAuditsTable";
import { AdministrationErrorModal } from "@/Components/Administration/AdministrationErrorModal";
import { BaseModal, ModalSize } from "@/Components/Base/BaseModal";
import type { ModalData } from "@/Components/Base/BaseModal";
import { BaseTable } from "@/Components/Base/BaseTable";
// AA Skillfarm
import { OwnerPortrait } from "@/Components/Base/OwnerPortrait";
import { renderTooltip } from "@/Utils";
import { formatNumber } from "@/Utils/format";

export interface AdministrationAltsModalProps {
  group: MainCharacterGroup | null;
  updatingCharacterId: number | null;
  onHide: () => void;
  onInspect: (audit: AdministrationAuditSchema) => void;
  onTriggerUpdate: (characterId: number, forceRefresh: boolean) => void;
  onDelete: (audit: AdministrationAuditSchema) => void;
  isSuperuser?: boolean;
}

export const AdministrationAltsModal: React.FC<AdministrationAltsModalProps> = ({
  group,
  updatingCharacterId,
  onHide,
  onInspect,
  onTriggerUpdate,
  onDelete,
  isSuperuser = false,
}) => {
  const { t } = useTranslation();
  // Audit whose error details are shown in the stacked error modal
  const [errorAudit, setErrorAudit] = useState<AdministrationAuditSchema | null>(null);

  const columns = useMemo<ColumnDef<AdministrationAuditSchema, unknown>[]>(() => {
    const columnHelper = createColumnHelper<AdministrationAuditSchema>();

    return [
      columnHelper.display({
        id: "avatar",
        header: () => null,
        size: 36,
        enableSorting: false,
        cell: ({ row }) => {
          const audit = row.original;
          return <OwnerPortrait src={audit.portrait_url} size="sm" shape="rounded" />;
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
          const hasIssue =
            Boolean(audit.error_message) || (audit.status && audit.status !== "ok");
          const openDetails = () => setErrorAudit(audit);
          return (
            <Badge
              bg={
                audit.status === "ok"
                  ? "success"
                  : audit.status === "token_error"
                    ? "warning"
                    : "danger"
              }
              text={audit.status === "token_error" ? "dark" : undefined}
              {...(hasIssue && {
                role: "button",
                tabIndex: 0,
                className: styles.statusBadgeButton,
                "aria-label": t("Show error details for {{name}}", {
                  name: audit.character_name,
                }),
                onClick: openDetails,
                onKeyDown: (e: React.KeyboardEvent) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    openDetails();
                  }
                },
              })}
            >
              {audit.status}
            </Badge>
          );
        },
      }),

      columnHelper.accessor("total_sp", {
        id: "total_sp",
        header: t("Total SP"),
        cell: ({ getValue }) => (
          <span className="fw-semibold font-monospace">
            {formatNumber((getValue() as number) ?? 0)}
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
                  className="d-inline-flex align-items-center gap-1"
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
                    className="d-inline-flex align-items-center gap-1"
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
                  {isSuperuser && (
                    <Dropdown.Item
                      onClick={() => onTriggerUpdate(audit.character_id, true)}
                    >
                      <RefreshCw size={14} className="me-2 text-warning" />
                      {t("Force Refresh (Bypass Cache)")}
                    </Dropdown.Item>
                  )}
                </Dropdown.Menu>
              </Dropdown>
              {isSuperuser &&
                renderTooltip(
                  t("Delete Audit"),
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => onDelete(audit)}
                    className="d-inline-flex align-items-center gap-1"
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
  }, [t, updatingCharacterId, onInspect, onTriggerUpdate, onDelete, isSuperuser]);

  const modalData: ModalData = {
    modal_id: "administration-alts-modal",
    title: group
      ? `${group.mainCharacterName} — ${group.alts.length} ${
          group.alts.length === 1 ? t("Alt") : t("Alts")
        }`
      : t("Alts"),
    url: "",
  };

  return (
    <>
    <BaseModal
      data={modalData}
      showModal={group !== null}
      setShowModal={(show) => {
        if (!show) onHide();
      }}
      size={ModalSize.extraLarge}
    >
      <Card>
        <Card.Body className="p-0">
          <BaseTable
            columns={columns}
            data={group?.alts ?? []}
            emptyText={t("No alt characters found.")}
            exportFileName={`alts_${group?.mainCharacterName ?? "character"}.csv`}
          />
        </Card.Body>
      </Card>
    </BaseModal>
    {/* Rendered after the alts modal so it stacks on top; the alts modal stays open */}
    <AdministrationErrorModal
      show={errorAudit !== null}
      onHide={() => setErrorAudit(null)}
      characterName={errorAudit?.character_name ?? ""}
      status={errorAudit?.status ?? ""}
      errorMessage={errorAudit?.error_message}
    />
    </>
  );
};

export default AdministrationAltsModal;
