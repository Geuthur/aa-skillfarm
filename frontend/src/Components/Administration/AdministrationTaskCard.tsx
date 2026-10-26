// React
import type { ReactNode } from "react";

// Third Party
import { Button, Card, Spinner } from "react-bootstrap";

interface AdministrationTaskCardProps {
  title: string;
  description: string;
  buttonLabel: string;
  buttonVariant: "primary" | "secondary";
  icon: ReactNode;
  isPending: boolean;
  onClick: () => void;
  testId: string;
}

/** Card with a description and one button that queues a background task. */
export const AdministrationTaskCard = ({
  title,
  description,
  buttonLabel,
  buttonVariant,
  icon,
  isPending,
  onClick,
  testId,
}: AdministrationTaskCardProps) => (
  <Card className="bg-dark border-secondary h-100">
    <Card.Header className="border-secondary py-2">
      <h6 className="mb-0 text-light">{title}</h6>
    </Card.Header>
    <Card.Body className="d-flex flex-column justify-content-between p-3">
      <p className="text-muted small">{description}</p>
      <Button
        variant={buttonVariant}
        size="sm"
        disabled={isPending}
        onClick={onClick}
        className="w-100 d-flex align-items-center justify-content-center gap-1"
        data-testid={testId}
      >
        {isPending ? <Spinner size="sm" animation="border" /> : icon}
        {buttonLabel}
      </Button>
    </Card.Body>
  </Card>
);
