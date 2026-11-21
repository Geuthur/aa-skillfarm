// Third Party
import { useQuery } from "@tanstack/react-query";

// AA Skillfarm
import { fetchOverview, overviewQueryKeys } from "@/Api/calls/overview";

/** Loads the overview of all users with their training summary. */
export function useOverview() {
  return useQuery({
    queryKey: overviewQueryKeys.all,
    queryFn: fetchOverview,
  });
}
