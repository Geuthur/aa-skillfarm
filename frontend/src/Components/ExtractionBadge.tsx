// React
import React from "react";

// Third Party
import { CheckCircle2, Sparkles, Minus } from "lucide-react";

// Styles
import styles from "./ExtractionBadge.module.css";

interface ExtractionBadgeProps {
  readyCount: number;
  isAcknowledged: boolean;
  acknowledgedAt?: string | null;
  size?: "sm" | "md";
}

export const ExtractionBadge: React.FC<ExtractionBadgeProps> = ({
  readyCount,
  isAcknowledged,
  acknowledgedAt,
  size = "md",
}) => {
  if (readyCount <= 0) {
    return (
      <span className="sf-badge-none" title="No extractions ready">
        <Minus size={12} />
        <span>0 Ready</span>
      </span>
    );
  }

  // Ready but NOT acknowledged -> Subtle pulsing animation!
  if (!isAcknowledged) {
    return (
      <span
        className="sf-badge-extraction-pending"
        title={`${readyCount} skill extraction${readyCount > 1 ? "s" : ""} ready for extraction (Pending Review)`}
      >
        <span className="sf-extraction-pulsing" aria-hidden="true">
          <Sparkles size={size === "sm" ? 14 : 16} />
        </span>
        <span>{readyCount} Ready</span>
      </span>
    );
  }

  // Ready AND Acknowledged -> Steady green checkmark
  return (
    <span
      className="sf-badge-extraction-reviewed"
      title={`${readyCount} skill extraction${readyCount > 1 ? "s" : ""} ready (Reviewed${acknowledgedAt ? ` at ${acknowledgedAt}` : ""})`}
    >
      <CheckCircle2 size={size === "sm" ? 14 : 16} className={styles["icon-ready"]} />
      <span>{readyCount} Reviewed</span>
    </span>
  );
};
