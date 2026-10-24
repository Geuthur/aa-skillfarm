export const queryKeys = {
  User: ["user"] as const,
  UserSettings: ["userSettings"] as const,
  UserCharacterStatuses: ["userCharacterStatuses"] as const,
  Menu: ["menu"] as const,
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
