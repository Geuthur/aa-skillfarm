// React
import React from "react";

// Styles
import styles from "@/Styles/modules/QueueEntryProgress.module.css";

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
      <div className={`sf-progress-track w-100 overflow-hidden ${styles["track"]}`}>
        {/* Inline style: width is a runtime percentage */}
        <div className="sf-progress-fill" style={{ width: `${percent.toFixed(1)}%` }} />
      </div>
      <span className={styles["meta"]}>{percent.toFixed(1)}%</span>
    </div>
  );
};

export default QueueEntryProgress;
