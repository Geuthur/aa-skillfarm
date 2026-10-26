// React
import type { ReactNode } from "react";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA Skillfarm
import { loadUserData } from "@/Api/ApiCalls";
import { useUserData } from "@/Hooks/useUserData";

vi.mock("@/Api/ApiCalls", () => ({
  loadUserData: vi.fn(),
}));

const createWrapper = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe("useUserData", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should load the current user", async () => {
    // Test Data
    const response = { user: { is_admin: true, is_superuser: false } };
    vi.mocked(loadUserData).mockResolvedValue(response as never);

    // Test Action
    const { result } = renderHook(() => useUserData(), { wrapper: createWrapper() });

    // Expected Result
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(response);
    expect(loadUserData).toHaveBeenCalledTimes(1);
  });
});
