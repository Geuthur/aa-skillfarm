// React
import { useState } from "react";
import type { ReactNode } from "react";

// Third Party
import { ChevronDown, ChevronUp } from "lucide-react";
import { Button, Card } from "react-bootstrap";

// Styles
import styles from "@/Styles/modules/Administration.module.css";

interface AdministrationCollapsibleCardProps {
  title: string;
  icon: ReactNode;
  toggleLabel: string;
  testId: string;
  defaultOpen?: boolean;
  bodyClassName?: string;
  children: ReactNode;
}

/** Card whose body is toggled by clicking the header, like the global task administration. */
export const AdministrationCollapsibleCard = ({
  title,
  icon,
  toggleLabel,
  testId,
  defaultOpen = false,
  bodyClassName = "p-2",
  children,
}: AdministrationCollapsibleCardProps) => {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <Card className="bg-dark border-secondary mb-4 shadow-sm">
      <Card.Header
        className={`border-secondary d-flex align-items-center justify-content-between py-2 ${styles.cursorPointer}`}
        onClick={() => setOpen((prev) => !prev)}
      >
        <div className="d-flex align-items-center gap-2">
          {icon}
          <span className="fw-semibold text-light">{title}</span>
        </div>
        <Button
          variant="link"
          size="sm"
          className="p-0 text-muted"
          aria-label={toggleLabel}
          aria-expanded={open}
          data-testid={testId}
          onClick={(e) => {
            e.stopPropagation();
            setOpen((prev) => !prev);
          }}
        >
          {open ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </Button>
      </Card.Header>
      {open && <Card.Body className={bodyClassName}>{children}</Card.Body>}
    </Card>
  );
};
