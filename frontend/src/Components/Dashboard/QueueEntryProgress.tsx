// React
import React from "react";

// Styles
import styles from "./QueueEntryProgress.module.css";

import { useLiveProgress } from "@/Utils/liveProgress";

interface QueueEntryProgressProps {
  startDate?: string | null;
  finishDate?: string | null;
  fallbackPercent?: number;
}

export const QueueEntryProgress: React.FC<QueueEntryProgressProps> = ({
  startDate,
  finishDate,
  fallbackPercent,
}) => {
  const percent = useLiveProgress(startDate, finishDate, fallbackPercent);

  return (
    <div>
      <div className={`sf-progress-track ${styles["track"]}`}>
        <div className="sf-progress-fill" style={{ width: `${percent.toFixed(1)}%` }} />
      </div>
      <span className={styles["meta"]}>{percent.toFixed(1)}%</span>
    </div>
  );
};

export default QueueEntryProgress;
