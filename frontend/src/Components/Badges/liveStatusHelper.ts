// React
import { useEffect, useState } from "react";

// Utils
import { formatEveTime } from "@/Utils/eveOnline";

/**
 * Formats a numeric timestamp into an EVE Online time string (HH:MM:SS EVE)
 */
export function formatLastFetch(date?: number): string {
  if (!date) return "";
  return formatEveTime(new Date(date));
}

/**
 * Hook to manage the short ping animation whenever dataUpdatedAt changes
 */
export function useLivePing(
  dataUpdatedAt?: number,
  isBusy: boolean = false,
  duration: number = 2000
): boolean {
  const [pinging, setPinging] = useState(false);

  useEffect(() => {
    if (isBusy) return;

    const startTimer = setTimeout(() => setPinging(true), 0);
    const stopTimer = setTimeout(() => setPinging(false), duration);

    return () => {
      clearTimeout(startTimer);
      clearTimeout(stopTimer);
    };
  }, [dataUpdatedAt, isBusy, duration]);

  return pinging;
}
