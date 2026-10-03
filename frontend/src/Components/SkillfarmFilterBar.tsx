// React
import React from "react";

// Third Party
import { CheckCheck, Search, Sparkles } from "lucide-react";

// Styles
import styles from "./SkillfarmFilterBar.module.css";

import type { CharacterFilterParams } from "@/Api/schema";

interface SkillfarmFilterBarProps {
  filters: CharacterFilterParams;
  onFilterChange: (newFilters: Partial<CharacterFilterParams>) => void;
  totalCount: number;
  pausedCount: number;
  pendingCount: number;
  reviewedCount: number;
  onBulkAcknowledge?: () => void;
  isBulkAcknowledging?: boolean;
}

export const SkillfarmFilterBar: React.FC<SkillfarmFilterBarProps> = ({
  filters,
  onFilterChange,
  totalCount,
  pausedCount,
  pendingCount,
  reviewedCount,
  onBulkAcknowledge,
  isBulkAcknowledging,
}) => {
  const currentTab = () => {
    if (filters.training_status === "paused") return "paused";
    if (filters.training_status === "training") return "training";
    if (filters.extraction_status === "pending") return "pending";
    if (filters.extraction_status === "acknowledged") return "reviewed";
    return "all";
  };

  const handleTabClick = (tab: "all" | "training" | "paused" | "pending" | "reviewed") => {
    switch (tab) {
      case "training":
        onFilterChange({ training_status: "training", extraction_status: "all" });
        break;
      case "paused":
        onFilterChange({ training_status: "paused", extraction_status: "all" });
        break;
      case "pending":
        onFilterChange({ extraction_status: "pending", training_status: "all" });
        break;
      case "reviewed":
        onFilterChange({ extraction_status: "acknowledged", training_status: "all" });
        break;
      default:
        onFilterChange({ training_status: "all", extraction_status: "all" });
        break;
    }
  };

  const activeTab = currentTab();

  return (
    <div className="sf-filter-bar">
      {/* Tab filter buttons matching AA CSS Framework */}
      <div className="aa-tab-bar">
        <button
          type="button"
          className={`aa-tab-btn ${activeTab === "all" ? "active" : ""}`}
          onClick={() => handleTabClick("all")}
        >
          All ({totalCount})
        </button>

        <button
          type="button"
          className={`aa-tab-btn ${activeTab === "training" ? "active" : ""}`}
          onClick={() => handleTabClick("training")}
        >
          Active Training
        </button>

        <button
          type="button"
          className={`aa-tab-btn ${activeTab === "paused" ? "active" : ""} ${pausedCount > 0 ? styles["tab-alert"] : ""}`}
          onClick={() => handleTabClick("paused")}
        >
          Paused Training ({pausedCount})
        </button>

        <button
          type="button"
          className={`aa-tab-btn ${activeTab === "pending" ? "active" : ""} ${pendingCount > 0 ? styles["tab-alert"] : ""}`}
          onClick={() => handleTabClick("pending")}
        >
          {pendingCount > 0 && (
            <span className={`sf-extraction-pulsing ${styles["pulse-icon"]}`}>
              <Sparkles size={14} />
            </span>
          )}
          Pending Extractions ({pendingCount})
        </button>

        <button
          type="button"
          className={`aa-tab-btn ${activeTab === "reviewed" ? "active" : ""}`}
          onClick={() => handleTabClick("reviewed")}
        >
          Reviewed ({reviewedCount})
        </button>
      </div>

      {/* Search & Actions */}
      <div className={styles["actions"]}>
        <div className={styles["search-wrapper"]}>
          <Search
            size={16}
            className={styles["search-icon"]}
          />
          <input
            type="text"
            className={`sf-search-input ${styles["search-input"]}`}
            placeholder="Search characters or corps..."
            value={filters.search || ""}
            onChange={(e) => onFilterChange({ search: e.target.value })}
          />
        </div>

        {pendingCount > 0 && onBulkAcknowledge && (
          <button
            type="button"
            className="sf-btn sf-btn-warning"
            onClick={onBulkAcknowledge}
            disabled={isBulkAcknowledging}
            title="Mark all currently pending skill extractions as reviewed"
          >
            <CheckCheck size={16} />
            <span>Acknowledge All ({pendingCount})</span>
          </button>
        )}
      </div>
    </div>
  );
};
