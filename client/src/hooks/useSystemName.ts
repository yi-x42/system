import { useEffect, useState } from "react";
import {
  DEFAULT_SYSTEM_NAME,
  GENERAL_CONFIG_EVENT,
  GENERAL_CONFIG_STORAGE_KEY,
  type GeneralConfigEventDetail,
  readStoredSystemName,
} from "../lib/systemBranding";

const loadSystemName = () => {
  if (typeof window === "undefined") {
    return DEFAULT_SYSTEM_NAME;
  }
  return readStoredSystemName();
};

export function useSystemName() {
  const [systemName, setSystemName] = useState<string>(() => loadSystemName());

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const handleStorage = (event: StorageEvent) => {
      if (event.key === GENERAL_CONFIG_STORAGE_KEY) {
        setSystemName(loadSystemName());
      }
    };

    const handleGeneralUpdate = (event: Event) => {
      const customEvent = event as CustomEvent<GeneralConfigEventDetail>;
      const nextName = customEvent.detail?.general?.systemName;
      if (typeof nextName === "string" && nextName.trim()) {
        setSystemName(nextName.trim());
      } else {
        setSystemName(loadSystemName());
      }
    };

    window.addEventListener("storage", handleStorage);
    window.addEventListener(GENERAL_CONFIG_EVENT, handleGeneralUpdate as EventListener);

    return () => {
      window.removeEventListener("storage", handleStorage);
      window.removeEventListener(GENERAL_CONFIG_EVENT, handleGeneralUpdate as EventListener);
    };
  }, []);

  return systemName;
}
