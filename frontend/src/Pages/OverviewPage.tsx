// React
import React from "react";
import { Link } from "react-router-dom";

// Third Party
import { useQuery } from "@tanstack/react-query";
import { Eye, Shield } from "lucide-react";
import { useTranslation } from "react-i18next";

// Utils
import { renderTooltip } from "@/Utils";

// Styles
import styles from "./OverviewPage.module.css";

import { fetchOverview } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import { ProjectName } from "@/App";

export const OverviewPage: React.FC = () => {
  const { t } = useTranslation();
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.Overview,
    queryFn: fetchOverview,
  });

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
    <div className="sf-table-container">
      <table className="sf-table">
        <thead>
          <tr>
            <th>{t("User")}</th>
            <th>{t("Characters")}</th>
            <th>{t("Training")}</th>
            <th>{t("Paused")}</th>
            <th>{t("Pending Extractions")}</th>
            <th className={styles["col-actions"]}>{t("Actions")}</th>
          </tr>
        </thead>
        <tbody>
          {data.users.map((user) => (
            <tr key={user.user_id}>
              <td>
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
              </td>
              <td>{user.character_count}</td>
              <td>{user.training_count}</td>
              <td>{user.paused_count}</td>
              <td>{user.pending_extractions_count}</td>
              <td className={styles["actions-cell"]}>
                {renderTooltip(
                  t("Show characters of {{user}}", { user: user.main_character_name }),
                  <Link
                    to={`/${ProjectName}/overview/${user.user_id}/`}
                    className="sf-btn"
                  >
                    <Eye size={16} />
                    <span>{t("Characters")}</span>
                  </Link>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default OverviewPage;
