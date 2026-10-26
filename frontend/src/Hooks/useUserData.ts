// Third Party
import { useQuery } from "@tanstack/react-query";

// AA Skillfarm
import { loadUserData } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";

/** Loads the current user (main character, corporation, admin and superuser flags). */
export function useUserData() {
  return useQuery({
    queryKey: queryKeys.User,
    queryFn: loadUserData,
    staleTime: 5 * 60 * 1000,
  });
}
