// React
import React from "react";

// Third Party
import { AlertTriangle, ArrowRight } from "lucide-react";
import { Button } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/InactiveTrainingAlert.module.css";

interface InactiveTrainingAlertProps {
  pausedCount: number;
  unacknowledgedCount?: number;
  currentFilter: string;
  onFilterInactive: () => void;
}

export const InactiveTrainingAlert: React.FC<InactiveTrainingAlertProps> = ({
  pausedCount,
  unacknowledgedCount,
  currentFilter,
  onFilterInactive,
}) => {
  const { t } = useTranslation();
  const effectiveCount = unacknowledgedCount !== undefined ? unacknowledgedCount : pausedCount;

  if (effectiveCount <= 0 || currentFilter === "paused") {
    return null;
  }

  return (
    <div className="sf-inactive-banner px-4 py-3 mb-4 d-flex flex-column flex-sm-row justify-content-between align-items-start align-items-sm-center gap-3" role="alert">
      <div className="d-flex align-items-center gap-3">
        <span className={`text-warning fs-3 ${styles["alert-icon"]}`} aria-hidden="true">
          <AlertTriangle size={28} />
        </span>
        <div>
          <h4 className="sf-inactive-banner-title m-0">
            {pausedCount === 1
              ? t("1 Character has no active training queue!")
              : t("{{count}} Characters have no active training queue!", { count: pausedCount })}
          </h4>
          <p className="sf-inactive-banner-subtitle mt-1 mb-0">
            {t("Training time is currently being lost. Review these characters to resume their skill queues.")}
          </p>
        </div>
      </div>
      <Button variant="warning"
        onClick={onFilterInactive}
      >
        <span>{t("View Paused Characters ({{count}})", { count: pausedCount })}</span>
        <ArrowRight size={16} />
      </Button>
    </div>
  );
};
