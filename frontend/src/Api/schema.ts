import type { components } from "@/Api/OpenApi";

export type MenuLink = components["schemas"]["MenuLink"];
export type MenuSchema = components["schemas"]["MenuSchema"];
export type UserData = components["schemas"]["UserData"];
export type ActionResponse = components["schemas"]["ActionResponse"];
export type CharacterFilterParams = Partial<components["schemas"]["CharacterFilter"]>;
export type CharacterSummarySchema = components["schemas"]["CharacterSummarySchema"];
export type CharacterListResponse = components["schemas"]["CharacterListResponse"];
export type CharacterDetailResponse = components["schemas"]["CharacterDetailResponse"];
export type SkillQueueEntrySchema = components["schemas"]["SkillQueueEntrySchema"];
export type FarmedSkillSchema = components["schemas"]["FarmedSkillSchema"];
export type SkillSetupSchema = components["schemas"]["SkillSetupSchema"];
export type CalculatorItemSchema = components["schemas"]["CalculatorItemSchema"];
export type CalculatorResponse = components["schemas"]["CalculatorResponse"];
export type AdminStatsResponse = components["schemas"]["AdminStatsResponse"];
export type OverviewUserSchema = components["schemas"]["OverviewUserSchema"];
export type OverviewResponse = components["schemas"]["OverviewResponse"];
export type OverviewUserCharactersResponse = components["schemas"]["OverviewUserCharactersResponse"];
