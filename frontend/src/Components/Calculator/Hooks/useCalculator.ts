// Third Party
import { useQuery } from "@tanstack/react-query";

// AA Skillfarm
import { fetchCalculatorData } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";

/** Loads the market prices used by the profit calculator. */
export function useCalculatorData() {
  return useQuery({
    queryKey: queryKeys.Calculator,
    queryFn: fetchCalculatorData,
  });
}
