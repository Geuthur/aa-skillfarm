// React
import React from "react";

// Third Party
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/LiveStatusIndicator.module.css";

// AA Skillfarm
import { formatLastFetch, useLivePing } from "@/Components/Badges/liveStatusHelper";
import { renderTooltip } from "@/Utils/bootsTrap";

export interface LiveStatusProps {
  isError?: boolean;
  error?: unknown;
  isLoading?: boolean;
  isFetching?: boolean;
  dataUpdatedAt?: number;
  showTimestamp?: boolean;
  timestampPrefix?: string;
  pingDuration?: number;
  className?: string;
  children?: React.ReactNode;
}

export function LiveStatusIndicator({
  isError = false,
  error,
  isLoading = false,
  isFetching = false,
  dataUpdatedAt,
  showTimestamp = false,
  timestampPrefix = "↻",
  pingDuration = 2000,
  className = "",
  children,
}: LiveStatusProps) {
  const { t } = useTranslation();
  const isBusy = isLoading || isFetching;
  const pinging = useLivePing(dataUpdatedAt, isBusy || isError, pingDuration);

  const errorMessage =
    error instanceof Error
      ? error.message
      : typeof error === "string"
      ? error
      : t("Failed to load");

  const tooltipText = isError
    ? errorMessage
    : isBusy
    ? t("Loading…")
    : dataUpdatedAt
    ? `${t("Last Fetch")}: ${formatLastFetch(dataUpdatedAt)}`
    : t("No Fetch");

  const getDotClass = () => {
    if (isError) return styles["dot-error"];
    if (isBusy) return styles["dot-busy"];
    return styles["dot-ok"];
  };

  return (
    <>
      {renderTooltip(
        tooltipText,
        <span
          className={`${className} d-inline-flex align-items-center gap-1`}
        >
          {/* Status Dot */}
          <span
            className={`${styles["dot-wrapper"]} position-relative d-inline-flex flex-shrink-0`}
          >
            {pinging && !isBusy && !isError && (
              <span
                className={`${styles["dot-ping"]} position-absolute rounded-circle`}
              />
            )}
            <span className={`${styles["dot"]} position-relative d-inline-block rounded-circle ${getDotClass()}`} />
          </span>

          {/* Optional Children */}
          {children}

          {/* Optional Timestamp */}
          {showTimestamp && dataUpdatedAt && !isBusy && !isError && (
            <span
              className={styles["label"]}
            >
              {timestampPrefix} {formatLastFetch(dataUpdatedAt)}
            </span>
          )}
        </span>
      )}
    </>
  );
}

export default LiveStatusIndicator;
