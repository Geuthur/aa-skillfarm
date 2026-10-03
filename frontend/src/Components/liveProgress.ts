// React
import { useEffect, useState } from "react";

export function computeProgress(
  startDateStr: string | null | undefined,
  finishDateStr: string | null | undefined,
  fallbackPercent: number | undefined,
  now: number
): number {
  if (startDateStr && finishDateStr) {
    const start = new Date(startDateStr.replace(" ", "T")).getTime();
    const finish = new Date(finishDateStr.replace(" ", "T")).getTime();

    if (!isNaN(start) && !isNaN(finish) && finish > start) {
      if (now >= finish) return 100;
      if (now <= start) return 0;
      const calculated = ((now - start) / (finish - start)) * 100;
      return Math.min(100, Math.max(0, calculated));
    }
  }

  if (typeof fallbackPercent === "number" && !isNaN(fallbackPercent)) {
    return Math.min(100, Math.max(0, fallbackPercent));
  }

  return 0;
}

/** Progress in percent (0-100), recalculated every second while the skill is training. */
export function useLiveProgress(
  startDate: string | null | undefined,
  finishDate: string | null | undefined,
  fallbackPercent?: number,
  active: boolean = true
): number {
  const [now, setNow] = useState<number>(() => Date.now());

  useEffect(() => {
    if (!active || !finishDate) return;

    const timer = setInterval(() => setNow(Date.now()), 1000);

    return () => clearInterval(timer);
  }, [active, finishDate]);

  return computeProgress(startDate, finishDate, fallbackPercent, now);
}
