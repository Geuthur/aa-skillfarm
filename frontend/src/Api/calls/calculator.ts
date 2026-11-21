// Third Party
import { apiErrorMessage } from "aa-geuthur-react";

// AA Skillfarm
import { apiClient } from "@/Api/Api";
import type {
  CalculatorResponse,
} from "@/Api/schema";

const API_BASE = "/skillfarm/api";

/** Query keys of the calculator area. */
export const calculatorQueryKeys = {
  data: ["calculatorData"] as const,
};

export async function fetchCalculatorData(): Promise<CalculatorResponse> {
  const { data, error } = await apiClient.GET(`${API_BASE}/calculator/`, {});
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load calculator data"));
  }
  return data as CalculatorResponse;
}
