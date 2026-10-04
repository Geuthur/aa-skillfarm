// React
import React from "react";

// Third Party
import { PauseCircle, Clock } from "lucide-react";
import { useTranslation } from "react-i18next";

// Styles
import styles from "./TrainingProgressBar.module.css";

import { useLiveProgress } from "@/Utils/liveProgress";

interface TrainingProgressBarProps {
  isTraining: boolean;
  currentSkill?: string | null;
  trainingStartDate?: string | null;
  trainingFinishDate?: string | null;
  queueFinishDate?: string | null;
  queuePausedAcknowledged?: boolean;
  progressPercent?: number;
}

export const TrainingProgressBar: React.FC<TrainingProgressBarProps> = ({
  isTraining,
  currentSkill,
  trainingStartDate,
  trainingFinishDate,
  queueFinishDate,
  queuePausedAcknowledged,
  progressPercent,
}) => {
  const { t } = useTranslation();
  const currentProgress = useLiveProgress(trainingStartDate, trainingFinishDate, progressPercent, isTraining);

  if (!isTraining) {
    const badgeClass = queuePausedAcknowledged
      ? "sf-badge-idle-acknowledged"
      : "sf-badge-idle";

    return (
      <div className={styles["idle"]}>
        <span className={badgeClass}>
          <PauseCircle size={14} />
          <span>{t("Training Inactive")}</span>
        </span>
        {queuePausedAcknowledged && (
          <span className={styles["idle-label"]}>
            {t("(Acknowledged)")}
          </span>
        )}
      </div>
    );
  }

  const displayPercent = Math.min(100, Math.max(0, currentProgress));

  return (
    <div className="sf-progress-container">
      <div className={styles["progress-header"]}>
        <span className={styles["skill-name"]}>
          {currentSkill || t("In Training")}
        </span>
        <span className={`sf-badge-training ${styles["level-badge"]}`}>
          <Clock size={11} />
          <span>{t("Active ({{percent}}%)", { percent: displayPercent.toFixed(1) })}</span>
        </span>
      </div>

      <div className="sf-progress-track">
        <div
          className="sf-progress-fill"
          style={{ width: `${displayPercent.toFixed(1)}%` }}
        />
      </div>

      <div className="sf-progress-labels">
        <span>{t("Skill Finishes: {{date}}", { date: trainingFinishDate ? trainingFinishDate.slice(5) : t("Unknown") })}</span>
        {queueFinishDate && <span>{t("Queue: {{date}}", { date: queueFinishDate.slice(5) })}</span>}
      </div>
    </div>
  );
};

export default TrainingProgressBar;
