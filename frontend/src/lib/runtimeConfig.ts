export function apiBaseUrl(): string {
  const raw = import.meta.env.VITE_API_BASE_URL;
  if (raw && raw.length > 0) return raw.replace(/\/$/, "");
  return "";
}

export function isMockAiEnabled(): boolean {
  return import.meta.env.VITE_USE_MOCK_AI === "true";
}

export function buildApiUrl(path: string): string {
  const base = apiBaseUrl();
  return base ? `${base}${path}` : path;
}
