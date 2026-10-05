// React
import React, { useMemo } from "react";
import { Link } from "react-router-dom";

// Third Party
import { useQuery } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";
import { Eye, Shield } from "lucide-react";
import { useTranslation } from "react-i18next";

// Styles
import styles from "./OverviewPage.module.css";

import { fetchOverview } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import type { OverviewUserSchema } from "@/Api/schema";
import { ProjectName } from "@/App";
import { BaseTable } from "@/Components/Tables/BaseTable";
// Utils
import { renderTooltip } from "@/Utils";

export const OverviewPage: React.FC = () => {
  const { t } = useTranslation();
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.Overview,
    queryFn: fetchOverview,
  });

  const columns = useMemo<ColumnDef<OverviewUserSchema>[]>(
    () => [
      {
        id: "user",
        header: t("User"),
        accessorFn: (row) => row.main_character_name,
        cell: ({ row }) => {
          const user = row.original;
          return (
            <div className={styles["user-info"]}>
              {user.portrait_url && (
                <img
                  src={user.portrait_url}
                  alt={user.main_character_name}
                  width={40}
                  height={40}
                  className={styles["avatar"]}
                />
              )}
              <div>
                <div className={styles["user-name"]}>{user.main_character_name}</div>
                {user.corporation_name && (
                  <div className={styles["user-corp"]}>
                    {user.corporation_name} [{user.corporation_ticker}]
                  </div>
                )}
              </div>
            </div>
          );
        },
      },
      {
        id: "characters",
        header: t("Characters"),
        accessorFn: (row) => row.character_count,
      },
      {
        id: "training",
        header: t("Training"),
        accessorFn: (row) => row.training_count,
      },
      {
        id: "paused",
        header: t("Paused"),
        accessorFn: (row) => row.paused_count,
      },
      {
        id: "pending_extractions",
        header: t("Pending Extractions"),
        accessorFn: (row) => row.pending_extractions_count,
      },
      {
        id: "actions",
        header: t("Actions"),
        enableSorting: false,
        meta: { className: styles["col-actions"], align: "right" },
        cell: ({ row }) => {
          const user = row.original;
          return (
            <div className={styles["actions-cell"]}>
              {renderTooltip(
                t("Show characters of {{user}}", { user: user.main_character_name }),
                <Link
                  to={`/${ProjectName}/overview/${user.user_id}/`}
                  className="sf-btn"
                >
                  <Eye size={16} />
                  <span>{t("Characters")}</span>
                </Link>,
              )}
            </div>
          );
        },
      },
    ],
    [t],
  );

  if (isError) {
    return (
      <div className={`aa-panel ${styles["denied-panel"]}`}>
        <Shield size={48} className={styles["denied-icon"]} />
        <h3 className={styles["denied-title"]}>{t("Permission Denied")}</h3>
        <p className={styles["denied-text"]}>
          {t("You do not have access to the overview of other users.")}
        </p>
      </div>
    );
  }

  if (isLoading || !data) {
    return (
      <div className="aa-loader-container">
        <span className={`spinner-border ${styles["loader-spinner"]}`} />
        <span>{t("Loading overview...")}</span>
      </div>
    );
  }

  if (data.users.length === 0) {
    return (
      <div className={`aa-panel ${styles["empty-state"]}`}>
        <h4 className={styles["empty-title"]}>{t("No users found")}</h4>
        <p className={styles["empty-text"]}>
          {t("There are no Skillfarm characters visible to you.")}
        </p>
      </div>
    );
  }

  return (
    <BaseTable
      data={data.users}
      columns={columns}
      variant="vowra"
      itemLabel={t("Users")}
      pageSizeOptions={[10, 25, 50, 100]}
      initialState={{
        pagination: { pageSize: 15 },
        sorting: [{ id: "user", desc: false }],
      }}
    />
  );
};

export default OverviewPage;
