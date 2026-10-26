// React
import React from "react";
import { Link, useParams } from "react-router-dom";

// Third Party
import { ArrowLeft } from "lucide-react";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/OverviewUserPage.module.css";

import { OwnerPortrait } from "@/Components/Base/OwnerPortrait";
import { CharacterDashboard } from "@/Components/Sections/CharacterDashboard";
import { ProjectName } from "@/constants";
import { ErrorPage } from "@/Pages/404";
// Utils
import { renderTooltip } from "@/Utils";

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
            <Link to={`/${ProjectName}/overview/`} className="btn btn-secondary">
              <ArrowLeft size={16} />
              <span>{t("Overview")}</span>
            </Link>
          )}
          {user.portrait_url && (
            <OwnerPortrait src={user.portrait_url} alt={user.main_character_name} size="md" />
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
