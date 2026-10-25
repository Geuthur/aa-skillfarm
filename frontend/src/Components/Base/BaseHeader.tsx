// React
import type { ReactNode } from "react";

// Third Party
import { Card } from "react-bootstrap";

export interface BaseSectionHeaderProps {
  name?: string;
  children?: ReactNode;
}

export function BaseSectionHeader({ name = "Header", children }: BaseSectionHeaderProps) {
  return (
    <Card className="border-0 shadow-sm mb-3" aria-labelledby="section-heading">
      <Card.Header className="bg-primary text-light rounded d-flex justify-content-between align-items-center">
        <h3 id="section-heading" className="mb-0 text-white">
          {name}
        </h3>
        {children && <div className="text-end d-flex align-items-center gap-2">{children}</div>}
      </Card.Header>
    </Card>
  );
}

export default BaseSectionHeader;
