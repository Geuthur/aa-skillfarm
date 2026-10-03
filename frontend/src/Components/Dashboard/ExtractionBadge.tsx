// React
import React from "react";

// Third Party
import { CheckCircle2, Sparkles, Minus } from "lucide-react";
import { useTranslation } from "react-i18next";

// Utils
import { renderTooltip } from "@/Utils/bootsTrap";

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
  const { t } = useTranslation();

  if (readyCount <= 0) {
    return renderTooltip(
      t("No extractions ready"),
      <span className="sf-badge-none">
        <Minus size={12} />
        <span>{t("0 Ready")}</span>
      </span>
    );
  }

  // Ready but NOT acknowledged -> Subtle pulsing animation!
  if (!isAcknowledged) {
    return renderTooltip(
      t("{{count}} skill extraction ready for extraction (Pending Review)", { count: readyCount }),
      <span className="sf-badge-extraction-pending">
        <span className="sf-extraction-pulsing" aria-hidden="true">
          <Sparkles size={size === "sm" ? 14 : 16} />
        </span>
        <span>{t("{{count}} Ready", { count: readyCount })}</span>
      </span>
    );
  }

  // Ready AND Acknowledged -> Steady green checkmark
  return renderTooltip(
    t("{{count}} skill extraction ready (Reviewed{{at}})", {
      count: readyCount,
      at: acknowledgedAt ? ` ${acknowledgedAt}` : "",
    }),
    <span className="sf-badge-extraction-reviewed">
      <CheckCircle2 size={size === "sm" ? 14 : 16} className={styles["icon-ready"]} />
      <span>{t("{{count}} Reviewed", { count: readyCount })}</span>
    </span>
  );
};
