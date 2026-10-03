// React
import React from "react";

// Third Party
import { AlertTriangle, ArrowRight } from "lucide-react";
import { useTranslation } from "react-i18next";

// Styles
import styles from "./InactiveTrainingAlert.module.css";

interface InactiveTrainingAlertProps {
  pausedCount: number;
  currentFilter: string;
  onFilterInactive: () => void;
}

export const InactiveTrainingAlert: React.FC<InactiveTrainingAlertProps> = ({
  pausedCount,
  currentFilter,
  onFilterInactive,
}) => {
  const { t } = useTranslation();

  if (pausedCount <= 0 || currentFilter === "paused") {
    return null;
  }

  return (
    <div className="sf-inactive-banner" role="alert">
      <div className="sf-inactive-banner-content">
        <span className={`text-warning fs-3 ${styles["alert-icon"]}`} aria-hidden="true">
          <AlertTriangle size={28} />
        </span>
        <div>
          <h4 className="sf-inactive-banner-title">
            {pausedCount === 1
              ? t("1 Character has no active training queue!")
              : t("{{count}} Characters have no active training queue!", { count: pausedCount })}
          </h4>
          <p className="sf-inactive-banner-subtitle">
            {t("Training time is currently being lost. Review these characters to resume their skill queues.")}
          </p>
        </div>
      </div>
      <button
        type="button"
        className="sf-btn sf-btn-warning"
        onClick={onFilterInactive}
      >
        <span>{t("View Paused Characters ({{count}})", { count: pausedCount })}</span>
        <ArrowRight size={16} />
      </button>
    </div>
  );
};
