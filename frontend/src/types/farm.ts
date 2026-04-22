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

export const deriveEnvironment = (season: string, region: string): Environment => {
  const s = (season || "kharif").toLowerCase();
  const r = (region || "").toLowerCase();
  
  let temp = 26;
  let rain = 180;
  let hum = 65;

  if (s.includes("rabi") || s.includes("winter") || s.includes("dry")) {
    temp = 16;
    rain = 50;
    hum = 45;
  } else if (s.includes("zaid") || s.includes("summer")) {
    temp = 34;
    rain = 60;
    hum = 50;
  } else {
    // Kharif / monsoon / wet
    temp = 29;
    rain = 300;
    hum = 85;
  }
  
  if (r.includes("nepal") || r.includes("mountain") || r.includes("hill")) {
    temp = Math.max(10, temp - 8);
  } else if (r.includes("desert") || r.includes("arid") || r.includes("rajasthan")) {
    temp += 6;
    rain = Math.max(0, rain - 120);
    hum = Math.max(20, hum - 25);
  }

  return {
    temperatureC: temp,
    humidityPct: hum,
    windKph: 12,
    rainfallMm: rain,
    soilPh: 6.5,
    soilMoisturePct: rain > 100 ? 70 : 30,
  };
};

export const defaultEnvironment = (): Environment => deriveEnvironment("Spring", "");

export const defaultFarmContext = (): FarmContext => ({
  region: "Global",
  soilType: "loam",
  farmSizeAcres: 10,
  primaryGoal: "mixed",
  season: "Spring",
  notes: "",
  env: defaultEnvironment(),
});
