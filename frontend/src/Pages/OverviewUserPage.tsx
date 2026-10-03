// React
import React from "react";
import { Link, useParams } from "react-router-dom";

// Third Party
import { ArrowLeft } from "lucide-react";

// Styles
import styles from "./OverviewUserPage.module.css";

import { ProjectName } from "@/App";
import { CharacterDashboard } from "@/Components/CharacterDashboard";
import { ErrorPage } from "@/Pages/404";

export const OverviewUserPage: React.FC = () => {
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
          <Link to={`/${ProjectName}/overview/`} className="sf-btn" title="Back to overview">
            <ArrowLeft size={16} />
            <span>Overview</span>
          </Link>
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
