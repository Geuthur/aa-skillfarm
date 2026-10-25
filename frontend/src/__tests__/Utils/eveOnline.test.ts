// Third Party
import { describe, expect, it } from "vitest";

import {
  characterImageUrl,
  corporationImageUrl,
  allianceImageUrl,
  itemImageUrl,
  getSecColor,
} from "@/Utils/eveOnline";

describe("eveOnline Utils", () => {
  it("should return valid image URLs", () => {
    // Test Data
    const charId = 90000001;
    const corpId = 98000001;
    const allianceId = 99000001;
    const typeId = 40520;

    // Test Action & Expected Result
    expect(characterImageUrl(charId, 128)).toBe(
      "https://images.evetech.net/characters/90000001/portrait?size=128"
    );
    expect(corporationImageUrl(corpId, 64)).toBe(
      "https://images.evetech.net/corporations/98000001/logo?size=64"
    );
    expect(allianceImageUrl(allianceId, 64)).toBe(
      "https://images.evetech.net/alliances/99000001/logo?size=64"
    );
    expect(itemImageUrl(typeId, 32)).toBe(
      "https://images.evetech.net/types/40520/icon?size=32"
    );
  });

  it("should return correct security status badge class", () => {
    // Test Data & Test Action & Expected Result
    expect(getSecColor(1.0)).toBe("aa-badge-hisec");
    expect(getSecColor(0.4)).toBe("aa-badge-lowsec");
    expect(getSecColor(-0.1)).toBe("aa-badge-nullsec");
  });
});
