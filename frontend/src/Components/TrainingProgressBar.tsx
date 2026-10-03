// React
import React from "react";

// Third Party
import { PauseCircle, Clock } from "lucide-react";

// Styles
import styles from "./TrainingProgressBar.module.css";

import { useLiveProgress } from "@/Components/liveProgress";

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
  const currentProgress = useLiveProgress(trainingStartDate, trainingFinishDate, progressPercent, isTraining);

  if (!isTraining) {
    return (
      <div className={styles["idle"]}>
        <span className="sf-badge-idle">
          <PauseCircle size={14} />
          <span>Training Inactive</span>
        </span>
        {queuePausedAcknowledged && (
          <span className={styles["idle-label"]}>
            (Acknowledged)
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
          {currentSkill || "In Training"}
        </span>
        <span className={`sf-badge-training ${styles["level-badge"]}`}>
          <Clock size={11} />
          <span>Active ({displayPercent.toFixed(1)}%)</span>
        </span>
      </div>

      <div className="sf-progress-track">
        <div
          className="sf-progress-fill"
          style={{ width: `${displayPercent.toFixed(1)}%` }}
        />
      </div>

      <div className="sf-progress-labels">
        <span>Skill Finishes: {trainingFinishDate ? trainingFinishDate.slice(5) : "Unknown"}</span>
        {queueFinishDate && <span>Queue: {queueFinishDate.slice(5)}</span>}
      </div>
    </div>
  );
};

export default TrainingProgressBar;
