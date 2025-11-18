export const GENERAL_CONFIG_STORAGE_KEY = "generalSystemConfig";
export const GENERAL_CONFIG_EVENT = "systemSettings:generalUpdated";
export const DEFAULT_SYSTEM_NAME = "智慧偵測監控系統";

export type GeneralConfigEventDetail = {
  general?: {
    systemName?: string;
    [key: string]: unknown;
  };
};

export const readStoredSystemName = () => {
  if (typeof window === "undefined") {
    return DEFAULT_SYSTEM_NAME;
  }
  try {
    const raw = window.localStorage.getItem(GENERAL_CONFIG_STORAGE_KEY);
    if (!raw) {
      return DEFAULT_SYSTEM_NAME;
    }
    const parsed = JSON.parse(raw);
    const storedName = typeof parsed?.systemName === "string" ? parsed.systemName.trim() : "";
    return storedName || DEFAULT_SYSTEM_NAME;
  } catch (error) {
    console.warn("Failed to read stored system name", error);
    return DEFAULT_SYSTEM_NAME;
  }
};
