// React
import React, { useState } from "react";

// Third Party
import { useQuery, useMutation } from "@tanstack/react-query";
import { Shield, RefreshCw, Users, Coins, Check } from "lucide-react";

// Styles
import styles from "./AdminPage.module.css";

import { fetchAdminStats, triggerUpdateAll, triggerUpdatePrices } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";

export const AdminPage: React.FC = () => {
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);

  const { data: stats, isLoading, isError } = useQuery({
    queryKey: queryKeys.AdminStats,
    queryFn: fetchAdminStats,
  });

  const updateAllMutation = useMutation({
    mutationFn: (force: boolean) => triggerUpdateAll(force),
    onSuccess: (res) => {
      setFeedbackMsg(res.message);
      setTimeout(() => setFeedbackMsg(null), 5000);
    },
    onError: () => {
      setFeedbackMsg("Failed to queue character update task.");
      setTimeout(() => setFeedbackMsg(null), 5000);
    },
  });

  const updatePricesMutation = useMutation({
    mutationFn: triggerUpdatePrices,
    onSuccess: (res) => {
      setFeedbackMsg(res.message);
      setTimeout(() => setFeedbackMsg(null), 5000);
    },
    onError: () => {
      setFeedbackMsg("Failed to queue price update task.");
      setTimeout(() => setFeedbackMsg(null), 5000);
    },
  });

  if (isError) {
    return (
      <div className={`aa-panel ${styles["denied-panel"]}`}>
        <Shield size={48} className={styles["denied-icon"]} />
        <h3 className={styles["denied-title"]}>Permission Denied</h3>
        <p className={styles["denied-text"]}>
          You do not have administrative access to this page.
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className={styles["header"]}>
        <Shield size={28} className={styles["header-icon"]} />
        <div>
          <h3 className={styles["title"]}>
            Skillfarm Administration
          </h3>
          <p className={styles["subtitle"]}>
            Global character synchronization and market price tasks
          </p>
        </div>
      </div>

      {feedbackMsg && (
        <div
          className={`aa-panel ${styles["feedback"]}`}
        >
          <Check size={18} />
          <span>{feedbackMsg}</span>
        </div>
      )}

      {/* Global Metrics */}
      <div
        className={styles["metrics-grid"]}
      >
        <div className="aa-panel">
          <div className={styles["metric-label"]}>Total Characters</div>
          <div className={styles["metric-value"]}>
            {isLoading ? "..." : stats?.total_characters}
          </div>
        </div>

        <div className="aa-panel">
          <div className={styles["metric-label"]}>Active in Skillfarm</div>
          <div className={styles["metric-value-emerald"]}>
            {isLoading ? "..." : stats?.active_characters}
          </div>
        </div>

        <div className="aa-panel">
          <div className={styles["metric-label"]}>Paused Training</div>
          <div className={styles["metric-value-amber"]}>
            {isLoading ? "..." : stats?.paused_training_count}
          </div>
        </div>

        <div className="aa-panel">
          <div className={styles["metric-label"]}>Pending Extractions</div>
          <div className={styles["metric-value-amber"]}>
            {isLoading ? "..." : stats?.total_pending_extractions}
          </div>
        </div>
      </div>

      {/* Task Execution Panel */}
      <div className={`aa-panel-lg ${styles["actions-panel"]}`}>
        <div>
          <h4 className={styles["section-title"]}>
            Character ESI Sync Tasks
          </h4>
          <p className={styles["section-text"]}>
            Queue asynchronous background tasks to refresh skills and skill queues from ESI.
          </p>
          <div className={styles["button-row"]}>
            <button
              type="button"
              className="sf-btn sf-btn-primary"
              onClick={() => updateAllMutation.mutate(false)}
              disabled={updateAllMutation.isPending}
            >
              <Users size={16} />
              <span>Update Stale Characters</span>
            </button>
            <button
              type="button"
              className="sf-btn sf-btn-secondary"
              onClick={() => updateAllMutation.mutate(true)}
              disabled={updateAllMutation.isPending}
            >
              <RefreshCw size={16} />
              <span>Force Refresh All Characters</span>
            </button>
          </div>
        </div>

        <hr className={styles["divider"]} />

        <div>
          <h4 className={styles["section-title"]}>
            Market Prices Sync
          </h4>
          <p className={styles["section-text"]}>
            Fetch latest Jita market aggregates from Fuzzwork for PLEX, Extractors, and Injectors.
          </p>
          <button
            type="button"
            className="sf-btn sf-btn-secondary"
            onClick={() => updatePricesMutation.mutate()}
            disabled={updatePricesMutation.isPending}
          >
            <Coins size={16} />
            <span>Update Market Prices</span>
          </button>
        </div>
      </div>
    </div>
  );
};
