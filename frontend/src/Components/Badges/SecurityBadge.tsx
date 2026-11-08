// Third Party
import { getSecColor } from "aa-geuthur-react";

interface SecurityBadgeProps {
  sec: number;
  className?: string;
}

export function SecurityBadge({ sec, className = "" }: SecurityBadgeProps) {
  return (
    <span className={`sec-badge ${getSecColor(sec)} ${className}`}>
      {sec.toFixed(1)}
    </span>
  );
}

export default SecurityBadge;
