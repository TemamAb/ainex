/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_GEMINI_API_KEY: string;
    readonly VITE_ENABLE_LIVE_MODE?: string;
    readonly VITE_LICENSE_KEY?: string;
}

interface ImportMeta {
    readonly env: ImportMetaEnv;
}
