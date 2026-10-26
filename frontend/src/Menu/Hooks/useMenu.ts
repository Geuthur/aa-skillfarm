// Third Party
import { useQuery } from "@tanstack/react-query";

// AA Skillfarm
import { loadMenu } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";

/** Loads the navigation menu links, shared by the left and the right menu. */
export function useMenu() {
  return useQuery({
    queryKey: queryKeys.Menu,
    queryFn: () => loadMenu(),
    staleTime: 5 * 60 * 1000,
    retry: 1,
    refetchOnWindowFocus: false,
  });
}
