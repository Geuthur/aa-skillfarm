// React
import React from "react";

// Third Party
import { AlertCircle, Plus } from "lucide-react";
import { Button } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
// AA Base
import styles from "@/Components/Base/OwnerSettings/OwnerSettings.module.css";

import { OwnerPortrait } from "@/Components/Base/OwnerPortrait";
import type { BaseMissingOwner, MissingOwnerCardProps } from "@/Components/Base/OwnerSettings/types";

/** Card for an entity (e.g. an alt) that belongs to the user but is not registered in the app. */
export const MissingOwnerCard: React.FC<MissingOwnerCardProps<BaseMissingOwner>> = ({
  missing,
  appName = "Alliance Auth",
  actionUrl,
  actionLabel,
}) => {
  const { t } = useTranslation();

  return (
    <article className={`${styles["char-card"]} ${styles["missing-card"]}`}>
      <div className="d-flex align-items-center gap-2">
        <OwnerPortrait src={missing.avatar_url} alt={missing.name} bordered />
        <div className={`${styles["char-info"]} flex-fill`}>
          <div className="d-flex align-items-center justify-content-between gap-2">
            <h3 className={`${styles["char-name"]} m-0 fw-semibold text-nowrap overflow-hidden`}>{missing.name}</h3>
            <span className={`${styles["status-badge"]} d-inline-flex align-items-center gap-1 fw-semibold ${styles["missing-badge"]}`}>
              <AlertCircle size={11} aria-hidden="true" />
              <span>{t("Not Registered")}</span>
            </span>
          </div>
          {missing.subtitle && <p className={`${styles["char-corp"]} text-nowrap overflow-hidden`}>{missing.subtitle}</p>}
        </div>
      </div>

      <p className="small text-muted mb-0">
        {t("{{name}} is not registered in {{app}}.", { name: missing.name, app: appName })}
      </p>

      {actionUrl && (
        <div className="d-flex justify-content-end mt-auto pt-2 border-top border-secondary">
          <Button
            href={actionUrl}
            variant="primary"
            size="sm"
            className="d-flex align-items-center gap-1"
          >
            <Plus size={13} />
            <span>{actionLabel ?? t("Add to {{app}}", { app: appName })}</span>
          </Button>
        </div>
      )}
    </article>
  );
};
