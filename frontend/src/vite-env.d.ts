/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  /** Set to "true" to use built-in demo replies (no backend) */
  readonly VITE_USE_MOCK_AI?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
