// Third Party
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA Skillfarm
import { apiClient } from "@/Api/Api";
import {
  calculatorQueryKeys,
  fetchCalculatorData,
} from "@/Api/calls/calculator";

describe("calculatorQueryKeys", () => {
  it("should provide the calculator keys", () => {
    expect(calculatorQueryKeys.data).toEqual(["calculatorData"]);
  });
});

describe("Calculator API calls", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe("fetchCalculatorData", () => {
    it("should return the calculator data", async () => {
      // Test Data
      const response = { month_calc: 0 };
      vi.spyOn(apiClient, "GET").mockResolvedValueOnce({
        data: response,
        error: undefined,
        response: new Response(),
      } as never);

      // Test Action
      const result = await fetchCalculatorData();

      // Expected Result
      expect(result).toEqual(response);
      expect(apiClient.GET).toHaveBeenCalledWith("/skillfarm/api/calculator/", {});
    });
  });
});

type Method = "GET";

/** Every call of `Api/calls/calculator.ts`: [name, HTTP method, call, fixed text]. */
const calls: [string, Method, () => Promise<unknown>, string][] = [
  ["fetchCalculatorData", "GET", () => fetchCalculatorData(), "Failed to load calculator data"],
];

const failWith = (method: Method, error: unknown) =>
  vi.spyOn(apiClient, method).mockResolvedValueOnce({
    data: undefined,
    error,
    response: new Response(),
  } as never);

describe("API error messages", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe.each(calls)("%s", (_name, method, call, fixedText) => {
    it("should throw the message of the API when the request fails", async () => {
      // Test Data
      failWith(method, { error: "Permission Denied" });

      // Test Action & Expected Result
      await expect(call()).rejects.toThrow("Permission Denied");
    });

    it("should throw the fixed text when the API sent no message", async () => {
      // Test Data
      failWith(method, {});

      // Test Action & Expected Result
      await expect(call()).rejects.toThrow(fixedText);
    });
  });
});
