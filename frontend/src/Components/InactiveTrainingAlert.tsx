// React
import React from "react";

// Third Party
import { AlertTriangle, ArrowRight } from "lucide-react";

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
              ? "1 Character has no active training queue!"
              : `${pausedCount} Characters have no active training queue!`}
          </h4>
          <p className="sf-inactive-banner-subtitle">
            Training time is currently being lost. Review these characters to resume their skill queues.
          </p>
        </div>
      </div>
      <button
        type="button"
        className="sf-btn sf-btn-warning"
        onClick={onFilterInactive}
      >
        <span>View Paused Characters ({pausedCount})</span>
        <ArrowRight size={16} />
      </button>
    </div>
  );
};
