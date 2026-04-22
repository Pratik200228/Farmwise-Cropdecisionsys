export type FarmGoal = "yield" | "profit" | "sustainability" | "mixed";

/** Environmental parameters fed to the Crop Suitability AI agent */
export type Environment = {
  /** average daytime temperature in °C */
  temperatureC: number;
  /** average relative humidity in % */
  humidityPct: number;
  /** average wind speed in km/h */
  windKph: number;
  /** expected rainfall this cycle in mm */
  rainfallMm: number;
  /** soil pH (0–14, typical 4.5–8.5) */
  soilPh: number;
  /** soil moisture as a percentage (0–100) */
  soilMoisturePct: number;
};

export type FarmContext = {
  region: string;
  soilType: string;
  farmSizeAcres: number;
  primaryGoal: FarmGoal;
  season: string;
  notes: string;
  env: Environment;
};

export type ChatRole = "user" | "assistant" | "system";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: number;
};

export const defaultEnvironment = (): Environment => ({
  temperatureC: 26,
  humidityPct: 65,
  windKph: 12,
  rainfallMm: 180,
  soilPh: 6.5,
  soilMoisturePct: 45,
});

export const defaultFarmContext = (): FarmContext => ({
  region: "",
  soilType: "loam",
  farmSizeAcres: 10,
  primaryGoal: "mixed",
  season: "kharif",
  notes: "",
  env: defaultEnvironment(),
});
