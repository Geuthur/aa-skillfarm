// Third Party
import { describe, expect, it } from "vitest";

import {
    hasRequiredFields,
} from "@/Components/Forms/validation";

describe("validation functions", () => {
    describe("hasRequiredFields", () => {
        const validator = hasRequiredFields("foo", "bar");

        it("returns true when all required fields are present and non-empty", () => {
            // Test Data & Action
            const result = validator({ foo: "val1", bar: "val2" });

            // Expected Result
            expect(result).toBe(true);
        });

        it("returns false when a required field is missing", () => {
            // Test Data & Action
            const result = validator({ foo: "val1" });

            // Expected Result
            expect(result).toBe(false);
        });

        it("returns false when a required field is an empty string or only whitespace", () => {
            // Test Data & Action & Expected Result
            expect(validator({ foo: "val1", bar: "   " })).toBe(false);
            expect(validator({ foo: "", bar: "val2" })).toBe(false);
        });

        it("returns false when a required field is not a string", () => {
            // Test Data & Action & Expected Result
            expect(validator({ foo: 123, bar: "val2" } as unknown as Record<string, unknown>)).toBe(false);
        });
    });
});
