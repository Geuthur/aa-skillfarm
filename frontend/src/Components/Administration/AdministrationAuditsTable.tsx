// React
import React, { useMemo, useState } from "react";

// Third Party
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { AlertTriangle, RefreshCw, Shield, User, Users } from "lucide-react";
import { Alert, Badge, Button, ButtonGroup, Card, Dropdown, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/Administration.module.css";

// AA Skillfarm
import type { AdministrationAuditSchema } from "@/Api/schema";
import { AdministrationAltsModal } from "@/Components/Administration/AdministrationAltsModal";
import { BaseTable } from "@/Components/Base/BaseTable";
// Utils
import { renderTooltip } from "@/Utils";
import { formatNumber } from "@/Utils/format";

export interface MainCharacterGroup {
  id: string;
  userId: number | null;
  userName: string;
  mainCharacterId: number | null;
  mainCharacterName: string;
  mainPortraitUrl: string | null;
  corporationName: string;
  corporationTicker: string;
  alts: AdministrationAuditSchema[];
  totalSp: number;
  trainingCount: number;
  pausedCount: number;
  readyExtractionsCount: number;
  issuesCount: number;
}

interface AdministrationAuditsTableProps {
  audits?: AdministrationAuditSchema[];
  isLoading: boolean;
  isError: boolean;
  updatingCharacterId: number | null;
  taskFeedback: { variant: "success" | "danger"; message: string } | null;
  onDismissFeedback: () => void;
  onInspect: (audit: AdministrationAuditSchema) => void;
  onTriggerUpdate: (characterId: number, forceRefresh: boolean) => void;
  onDelete: (audit: AdministrationAuditSchema) => void;
  isSuperuser?: boolean;
}

export const AdministrationAuditsTable: React.FC<AdministrationAuditsTableProps> = ({
  audits,
  isLoading,
  isError,
  updatingCharacterId,
  taskFeedback,
  onDismissFeedback,
  onInspect,
  onTriggerUpdate,
  onDelete,
  isSuperuser = false,
}) => {
  const { t } = useTranslation();
  const [selectedAltsGroup, setSelectedAltsGroup] = useState<MainCharacterGroup | null>(null);

  // Group audits by User / Main Character
  const groupedData = useMemo<MainCharacterGroup[]>(() => {
    if (!audits || audits.length === 0) return [];

    const map = new Map<string, MainCharacterGroup>();

    for (const audit of audits) {
      const key = audit.user_id ? `user_${audit.user_id}` : `char_${audit.character_id}`;
      let group = map.get(key);
      if (!group) {
        group = {
          id: key,
          userId: audit.user_id ?? null,
          userName: audit.user_name || t("Unknown User"),
          mainCharacterId: audit.main_character_id ?? audit.character_id,
          mainCharacterName: audit.main_character_name || audit.character_name || audit.user_name,
          mainPortraitUrl: audit.main_portrait_url || audit.portrait_url,
          corporationName: audit.corporation_name || "",
          corporationTicker: audit.corporation_ticker || "",
          alts: [],
          totalSp: 0,
          trainingCount: 0,
          pausedCount: 0,
          readyExtractionsCount: 0,
          issuesCount: 0,
        };
        map.set(key, group);
      }
      group.alts.push(audit);
      group.totalSp += audit.total_sp ?? 0;
      if (audit.is_training) {
        group.trainingCount += 1;
      } else {
        group.pausedCount += 1;
      }
      group.readyExtractionsCount += audit.extractions_ready_count ?? 0;
      if (audit.status !== "ok" || Boolean(audit.error_message)) {
        group.issuesCount += 1;
      }
    }

    return Array.from(map.values()).sort((a, b) =>
      a.mainCharacterName.localeCompare(b.mainCharacterName),
    );
  }, [audits, t]);

  const columns = useMemo<ColumnDef<MainCharacterGroup, unknown>[]>(() => {
    const columnHelper = createColumnHelper<MainCharacterGroup>();

    return [
      columnHelper.display({
        id: "avatar",
        header: () => null,
        size: 48,
        enableSorting: false,
        cell: ({ row }) => {
          const group = row.original;
          return group.mainPortraitUrl ? (
            <img
              src={group.mainPortraitUrl}
              alt=""
              width={32}
              height={32}
              className="rounded flex-shrink-0"
              loading="lazy"
            />
          ) : (
            <div className={`p-1 bg-secondary rounded text-center ${styles.avatarFallback}`}>
              <User size={16} />
            </div>
          );
        },
      }),

      columnHelper.accessor("mainCharacterName", {
        id: "pilot",
        header: t("Pilot / Main Character"),
        cell: ({ row }) => {
          const group = row.original;
          const altCount = group.alts.length;
          return (
            <div>
              <div className="d-flex align-items-center flex-wrap gap-1">
                <span className="fw-semibold">{group.mainCharacterName}</span>
                {altCount > 0 && (
                  <Button
                    variant="secondary"
                    size="sm"
                    className="aa-btn aa-btn-secondary aa-btn-sm py-0 px-2 text-decoration-none"
                    style={{ fontSize: "0.75rem", lineHeight: 1 }}
                    onClick={() => setSelectedAltsGroup(group)}
                    data-testid={`alts-btn-${group.id}`}
                  >
                    {altCount} {altCount === 1 ? t("Alt") : t("Alts")}
                  </Button>
                )}
              </div>
              {group.corporationName && (
                <span className="text-muted small">
                  {group.corporationName}{" "}
                  {group.corporationTicker && `[${group.corporationTicker}]`}
                </span>
              )}
            </div>
          );
        },
      }),

      columnHelper.accessor("trainingCount", {
        id: "training_status",
        header: t("Training Status"),
        cell: ({ row }) => {
          const group = row.original;
          return (
            <div className="d-flex flex-wrap gap-1">
              <Badge bg="success">
                {group.trainingCount} {t("Training")}
              </Badge>
              {group.pausedCount > 0 && (
                <Badge bg="warning" text="dark">
                  {group.pausedCount} {t("Paused")}
                </Badge>
              )}
            </div>
          );
        },
      }),

      columnHelper.accessor("totalSp", {
        id: "total_sp",
        header: t("Total SP"),
        cell: ({ getValue }) => (
          <span className="fw-semibold font-monospace">
            {formatNumber((getValue() as number) ?? 0)}
          </span>
        ),
      }),

      columnHelper.accessor("readyExtractionsCount", {
        id: "ready_extractions",
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

      columnHelper.accessor("issuesCount", {
        id: "sync_status",
        header: t("Sync Status"),
        cell: ({ row }) => {
          const group = row.original;
          return group.issuesCount > 0 ? (
            <Badge bg="danger" className="d-inline-flex align-items-center gap-1">
              <AlertTriangle size={12} />
              <span>
                {group.issuesCount} {t("Issues")}
              </span>
            </Badge>
          ) : (
            <Badge bg="success" className="d-inline-flex align-items-center gap-1">
              <Shield size={12} />
              <span>{t("OK")}</span>
            </Badge>
          );
        },
      }),

      columnHelper.display({
        id: "actions",
        header: () => <div className="text-end">{t("Actions")}</div>,
        size: 180,
        enableSorting: false,
        cell: ({ row }) => {
          const group = row.original;
          const isAnyUpdating = group.alts.some(
            (a) => updatingCharacterId === a.character_id,
          );

          return (
            <div className="d-flex align-items-center justify-content-end gap-2">
              <Button
                variant="outline-secondary"
                size="sm"
                onClick={() => setSelectedAltsGroup(group)}
                className="d-inline-flex align-items-center gap-1 aa-btn"
                data-testid={`view-alts-btn-${group.id}`}
              >
                <Users size={13} />
                <span>{t("Alts")}</span>
              </Button>

              <Dropdown as={ButtonGroup} size="sm">
                {renderTooltip(
                  t("Trigger updates for all alts of this pilot"),
                  <Button
                    variant="outline-danger"
                    size="sm"
                    disabled={isAnyUpdating}
                    onClick={() =>
                      group.alts.forEach((a) => onTriggerUpdate(a.character_id, false))
                    }
                    className="d-inline-flex align-items-center gap-1 sf-btn sf-btn-danger aa-btn aa-btn-danger"
                    data-testid={`update-all-alts-${group.id}`}
                  >
                    {isAnyUpdating ? (
                      <Spinner size="sm" animation="border" />
                    ) : (
                      <RefreshCw size={13} />
                    )}
                    <span>{t("Update All Alts")}</span>
                  </Button>,
                )}
                {renderTooltip(
                  t("More update options"),
                  <Dropdown.Toggle
                    split
                    size="sm"
                    variant="outline-danger"
                    aria-label={t("More update options")}
                    disabled={isAnyUpdating}
                    className="aa-btn aa-btn-danger"
                  />,
                )}
                <Dropdown.Menu
                  align="end"
                  className={`shadow-lg ${styles.dropdownMenu}`}
                >
                  <Dropdown.Item
                    onClick={() =>
                      group.alts.forEach((a) => onTriggerUpdate(a.character_id, false))
                    }
                  >
                    <RefreshCw size={14} className="me-2 text-primary" />
                    {t("Normal Update")}
                  </Dropdown.Item>
                  {isSuperuser && (
                    <Dropdown.Item
                      onClick={() =>
                        group.alts.forEach((a) => onTriggerUpdate(a.character_id, true))
                      }
                    >
                      <RefreshCw size={14} className="me-2 text-warning" />
                      {t("Force Refresh (Bypass Cache)")}
                    </Dropdown.Item>
                  )}
                </Dropdown.Menu>
              </Dropdown>
            </div>
          );
        },
      }),
    ];
  }, [t, updatingCharacterId, onTriggerUpdate, isSuperuser]);

  return (
    <>
      <Card className="bg-secondary text-light border-0 shadow-sm mt-3">
        <Card.Header className="d-flex align-items-center justify-content-between bg-transparent py-3">
          <div className="d-flex align-items-center gap-2">
            <Users size={20} className="text-primary" />
            <h2 className="h5 mb-0 fw-semibold">{t("All Skillfarm Character Audits")}</h2>
          </div>
        </Card.Header>
        <Card.Body className="p-0">
          {taskFeedback && (
            <div className="p-3 pb-0">
              <Alert
                variant={taskFeedback.variant}
                dismissible
                onClose={onDismissFeedback}
                className="mb-0"
              >
                {taskFeedback.message}
              </Alert>
            </div>
          )}

          {isLoading ? (
            <div className="p-4 text-center text-muted">
              <Spinner animation="border" size="sm" className="me-2" />
              <span>{t("Loading Skillfarm characters…")}</span>
            </div>
          ) : isError ? (
            <div className="p-4 text-center text-danger">
              {t("Failed to load Skillfarm characters.")}
            </div>
          ) : (
            <BaseTable
              columns={columns}
              data={groupedData}
              emptyText={t("No Skillfarm characters found.")}
              exportFileName="administration_audits.csv"
            />
          )}
        </Card.Body>
      </Card>

      <AdministrationAltsModal
        group={selectedAltsGroup}
        updatingCharacterId={updatingCharacterId}
        onHide={() => setSelectedAltsGroup(null)}
        onInspect={onInspect}
        onTriggerUpdate={onTriggerUpdate}
        onDelete={onDelete}
        isSuperuser={isSuperuser}
      />
    </>
  );
};
