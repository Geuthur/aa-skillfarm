// Third Party
import { useQuery } from "@tanstack/react-query";

// AA Skillfarm
import { fetchOverview } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";

/** Loads the overview of all users with their training summary. */
export function useOverview() {
  return useQuery({
    queryKey: queryKeys.Overview,
    queryFn: fetchOverview,
  });
}
