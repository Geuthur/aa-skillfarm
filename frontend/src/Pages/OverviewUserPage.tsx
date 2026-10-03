// React
import React from "react";
import { Link, useParams } from "react-router-dom";

// Third Party
import { ArrowLeft } from "lucide-react";
import { useTranslation } from "react-i18next";

// Utils
import { renderTooltip } from "@/Utils";

// Styles
import styles from "./OverviewUserPage.module.css";

import { ProjectName } from "@/App";
import { CharacterDashboard } from "@/Components/Sections/CharacterDashboard";
import { ErrorPage } from "@/Pages/404";

export const OverviewUserPage: React.FC = () => {
  const { t } = useTranslation();
  const { userId } = useParams<{ userId: string }>();
  const parsedUserId = Number(userId);

  if (!Number.isInteger(parsedUserId)) {
    return <ErrorPage />;
  }

  return (
    <CharacterDashboard
      userId={parsedUserId}
      renderHeader={(user) => (
        <div className={styles["header"]}>
          {renderTooltip(
            t("Back to overview"),
            <Link to={`/${ProjectName}/overview/`} className="sf-btn">
              <ArrowLeft size={16} />
              <span>{t("Overview")}</span>
            </Link>
          )}
          {user.portrait_url && (
            <img src={user.portrait_url} alt={user.main_character_name} width={40} height={40} className={styles["avatar"]} />
          )}
          <h3 className={styles["title"]}>
            {user.main_character_name}
          </h3>
        </div>
      )}
    />
  );
};

export default OverviewUserPage;
