// Third Party
import { useQuery } from "@tanstack/react-query";

// AA Skillfarm
import { calculatorQueryKeys, fetchCalculatorData } from "@/Api/calls/calculator";

/** Loads the market prices used by the profit calculator. */
export function useCalculatorData() {
  return useQuery({
    queryKey: calculatorQueryKeys.data,
    queryFn: fetchCalculatorData,
  });
}
