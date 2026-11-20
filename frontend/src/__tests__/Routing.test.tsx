// Third Party
import { createQueryClient } from "aa-geuthur-react";
import { describe, expect, it, vi } from "vitest";

// The retry rule itself (network errors and 502/503/504 only) is tested in aa-geuthur-react.
vi.mock("aa-geuthur-react", async (importOriginal) => {
  const actual = await importOriginal<typeof import("aa-geuthur-react")>();
  return { ...actual, createQueryClient: vi.fn(actual.createQueryClient) };
});

describe("Routing", () => {
  it("creates the QueryClient with createQueryClient and keeps the app defaults", async () => {
    await import("@/Routing");

    expect(createQueryClient).toHaveBeenCalledOnce();
    expect(createQueryClient).toHaveBeenCalledWith({
      defaultOptions: {
        queries: {
          staleTime: 1000 * 30,
          refetchOnWindowFocus: false,
        },
      },
    });
  });
});
