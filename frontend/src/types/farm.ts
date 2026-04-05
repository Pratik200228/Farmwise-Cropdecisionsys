export type FarmGoal = "yield" | "profit" | "sustainability" | "mixed";

export type FarmContext = {
  region: string;
  soilType: string;
  farmSizeAcres: number;
  primaryGoal: FarmGoal;
  season: string;
  notes: string;
};

export type ChatRole = "user" | "assistant" | "system";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: number;
};

export const defaultFarmContext = (): FarmContext => ({
  region: "",
  soilType: "loam",
  farmSizeAcres: 10,
  primaryGoal: "mixed",
  season: "kharif",
  notes: "",
});
