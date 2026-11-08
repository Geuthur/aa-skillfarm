// Third Party
import { queryKeys as baseQueryKeys } from "aa-geuthur-react";

// `Menu`, `User` and `UserSettings` come from the package, so its hooks and the app share them.
export const queryKeys = {
  ...baseQueryKeys,
  UserCharacterStatuses: ["userCharacterStatuses"] as const,
  CharactersRoot: ["characters"] as const,
  Characters: (filters?: unknown) => ["characters", filters] as const,
  CharacterDetail: (characterId: number | null) => ["characterDetail", characterId] as const,
  SkillSetup: (characterId: number | null) => ["skillSetup", characterId] as const,
  Calculator: ["calculatorData"] as const,
  AdminStats: ["adminStats"] as const,
  AdministrationAudits: ["administrationAudits"] as const,
  AdministrationAuditInspect: (characterId: number | null) =>
    ["administrationAuditInspect", characterId] as const,
  AdministrationCorporations: ["administrationCorporations"] as const,
  AdministrationUnregistered: (corporationId: number | null) =>
    ["administrationUnregistered", corporationId] as const,
  Overview: ["overview"] as const,
  OverviewUser: (userId: number | null, filters?: unknown) =>
    ["overview", "user", userId, filters] as const,
  CharacterUpdate: (characterId: number) => ["characterUpdate", characterId] as const,
};
