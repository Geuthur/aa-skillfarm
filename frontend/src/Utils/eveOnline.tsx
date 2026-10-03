// Third Party
import i18n from "i18next";

/**
 * Returns the URL for the image of a given ship type.
 */
export function shipImageUrl(shipTypeId: number, size: number = 512): string {
  return `https://images.evetech.net/types/${shipTypeId}/render?size=${size}`;
}

/**
 * Returns the URL for the image of a given character.
 */
export function characterImageUrl(characterId: number, size: number = 512): string {
  return `https://images.evetech.net/characters/${characterId}/portrait?size=${size}`;
}

/**
 * Returns the URL for the image of a given corporation.
 */
export function corporationImageUrl(corporationId: number, size: number = 128): string {
  return `https://images.evetech.net/corporations/${corporationId}/logo?size=${size}`;
}

/**
 * Returns the URL for the image of a given alliance.
 */
export function allianceImageUrl(allianceId: number, size: number = 128): string {
  return `https://images.evetech.net/alliances/${allianceId}/logo?size=${size}`;
}

/**
 * Returns the URL for the image of a given item type.
 */
export function itemImageUrl(typeId: number, size: number = 32): string {
  return `https://images.evetech.net/types/${typeId}/icon?size=${size}`;
}

/**
 * Returns the appropriate CSS classes for a given security status.
 */
export const getSecColor = (sec: number) => {
  if (sec >= 0.5) return "aa-badge-hisec";
  if (sec > 0.0) return "aa-badge-lowsec";
  return "aa-badge-nullsec";
};

/**
 * Formats a Date object into EVE Online time string (HH:MM:SS EVE)
 */
export const formatEveTime = (date: Date = new Date()): string => {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(date.getUTCHours())}:${pad(date.getUTCMinutes())}:${pad(date.getUTCSeconds())} EVE`;
};

/**
 * Helper function for localized number formatting
 */
export function formatNumber(
  value: number,
  unit: string = "ISK",
  locale?: string,
  options?: Intl.NumberFormatOptions
) {
  const effectiveLocale = locale || i18n.language || "en";
  const suffix = unit ? ` ${unit}` : "";
  if (value >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(2)}B${suffix}`;
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M${suffix}`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K${suffix}`;
  const formatted = new Intl.NumberFormat(effectiveLocale, options).format(value);
  return unit ? `${formatted}${suffix}` : formatted;
}
