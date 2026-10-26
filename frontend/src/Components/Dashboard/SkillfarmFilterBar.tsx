// React
import React from "react";

// Third Party
import { CheckCheck, Search, Sparkles } from "lucide-react";
import { Button } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/SkillfarmFilterBar.module.css";

import type { CharacterFilterParams } from "@/Api/schema";
// Utils
import { renderTooltip } from "@/Utils";

interface SkillfarmFilterBarProps {
  filters: CharacterFilterParams;
  onFilterChange: (newFilters: Partial<CharacterFilterParams>) => void;
  totalCount: number;
  activeCount: number;
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
  activeCount,
  pausedCount,
  pendingCount,
  reviewedCount,
  onBulkAcknowledge,
  isBulkAcknowledging,
}) => {
  const { t } = useTranslation();
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
      <div className="aa-tab-bar mw-100 overflow-x-auto">
        <button
          type="button"
          className={`aa-tab-btn text-nowrap flex-shrink-0 ${activeTab === "all" ? "active" : ""}`}
          onClick={() => handleTabClick("all")}
        >
          {t("All ({{count}})", { count: totalCount })}
        </button>

        <button
          type="button"
          className={`aa-tab-btn text-nowrap flex-shrink-0 ${activeTab === "training" ? "active" : ""}`}
          onClick={() => handleTabClick("training")}
        >
          {t("Active Training ({{count}})", { count: activeCount })}
        </button>

        <button
          type="button"
          className={`aa-tab-btn text-nowrap flex-shrink-0 ${activeTab === "paused" ? "active" : ""} ${pausedCount > 0 ? styles["tab-alert"] : ""}`}
          onClick={() => handleTabClick("paused")}
        >
          {t("Paused Training ({{count}})", { count: pausedCount })}
        </button>

        <button
          type="button"
          className={`aa-tab-btn text-nowrap flex-shrink-0 ${activeTab === "pending" ? "active" : ""} ${pendingCount > 0 ? styles["tab-alert"] : ""}`}
          onClick={() => handleTabClick("pending")}
        >
          {pendingCount > 0 && (
            <span className="sf-extraction-pulsing me-1">
              <Sparkles size={14} />
            </span>
          )}
          {t("Pending Extractions ({{count}})", { count: pendingCount })}
        </button>

        <button
          type="button"
          className={`aa-tab-btn text-nowrap flex-shrink-0 ${activeTab === "reviewed" ? "active" : ""}`}
          onClick={() => handleTabClick("reviewed")}
        >
          {t("Reviewed ({{count}})", { count: reviewedCount })}
        </button>
      </div>

      {/* Search & Actions */}
      <div className="d-flex align-items-center gap-2 flex-wrap">
        <div className="position-relative d-inline-flex align-items-center">
          <Search
            size={16}
            className={`${styles["search-icon"]} position-absolute`}
          />
          <input
            type="text"
            className={`sf-search-input ${styles["search-input"]}`}
            placeholder={t("Search characters or corps…")}
            value={filters.search || ""}
            onChange={(e) => onFilterChange({ search: e.target.value })}
          />
        </div>

        {pendingCount > 0 && onBulkAcknowledge && (
          renderTooltip(
            t("Mark all currently pending skill extractions as reviewed"),
            <Button variant="warning"
              onClick={onBulkAcknowledge}
              disabled={isBulkAcknowledging}
            >
              <CheckCheck size={16} />
              <span>{t("Acknowledge All ({{count}})", { count: pendingCount })}</span>
            </Button>
          )
        )}
      </div>
    </div>
  );
};
