// Third Party
import { Badge } from "react-bootstrap";

// Styles
import styles from "@/Styles/modules/CharacterTable.module.css";

/** Props for {@link SyncStatusBadge}. */
export interface SyncStatusBadgeProps {
  /** Bootstrap background variant (`danger`, `warning`, `success`, `secondary`). */
  variant: string;
  /** Badge text. */
  label: string;
  /** Show a leading status dot. */
  dot?: boolean;
  /** Let the dot pulse (used for errors). */
  pulse?: boolean;
}

/** Small status badge with an optional (pulsing) dot, used for the sync state of a character. */
export const SyncStatusBadge = ({ variant, label, dot = true, pulse = false }: SyncStatusBadgeProps) => (
  <Badge
    bg={variant}
    text={variant === "warning" ? "dark" : undefined}
    className={`d-inline-flex align-items-center gap-1 ${styles["status-badge"]}`}
  >
    {dot && (
      <span
        className={`d-inline-block rounded-circle ${styles["status-dot"]} ${pulse ? `aa-status-dot-pulse bg-${variant}` : "bg-white"}`}
      />
    )}
    {label}
  </Badge>
);
