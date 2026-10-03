// React
import type { ReactNode } from "react";

export interface BaseSectionHeaderProps {
  name?: string;
  children?: ReactNode;
}

export function BaseSectionHeader({ name = "Header", children }: BaseSectionHeaderProps) {
  return (
    <section className="card mb-3" aria-labelledby="section-heading">
      <div className="card-header bg-primary rounded d-flex justify-content-between align-items-center">
        <h3 id="section-heading" className="mb-0 text-white">
          {name}
        </h3>
        {children && <div className="text-end d-flex align-items-center gap-2">{children}</div>}
      </div>
    </section>
  );
}

export default BaseSectionHeader;
