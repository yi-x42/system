import {
  ReactNode,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

export const timezoneOptions = [
  { value: "Asia/Taipei", label: "台北 (GMT+8)" },
  { value: "Asia/Shanghai", label: "上海 (GMT+8)" },
  { value: "Asia/Tokyo", label: "東京 (GMT+9)" },
  { value: "Asia/Seoul", label: "首爾 (GMT+9)" },
  { value: "Asia/Singapore", label: "新加坡 (GMT+8)" },
  { value: "Asia/Dubai", label: "杜拜 (GMT+4)" },
  { value: "Asia/Kolkata", label: "印度 (GMT+5:30)" },
  { value: "Europe/London", label: "倫敦 (GMT+0)" },
  { value: "Europe/Berlin", label: "柏林 (GMT+1)" },
  { value: "Europe/Moscow", label: "莫斯科 (GMT+3)" },
  { value: "America/New_York", label: "紐約 (GMT-5)" },
  { value: "America/Chicago", label: "芝加哥 (GMT-6)" },
  { value: "America/Los_Angeles", label: "洛杉磯 (GMT-8)" },
  { value: "America/Sao_Paulo", label: "聖保羅 (GMT-3)" },
  { value: "Australia/Sydney", label: "雪梨 (GMT+10)" },
  { value: "Pacific/Auckland", label: "奧克蘭 (GMT+12)" },
] as const;

export type TimezoneValue = (typeof timezoneOptions)[number]["value"];

const DEFAULT_TIMEZONE: TimezoneValue = "Asia/Taipei";
const STORAGE_KEY = "systemTimezone";

type TimezoneContextValue = {
  timezone: TimezoneValue;
  setTimezone: (timezone: TimezoneValue) => void;
  timezoneLabel: string;
};

const TimezoneContext = createContext<TimezoneContextValue>({
  timezone: DEFAULT_TIMEZONE,
  setTimezone: () => undefined,
  timezoneLabel: DEFAULT_TIMEZONE,
});

const getInitialTimezone = (): TimezoneValue => {
  if (typeof window === "undefined") {
    return DEFAULT_TIMEZONE;
  }
  const stored = localStorage.getItem(STORAGE_KEY) as TimezoneValue | null;
  return stored ?? DEFAULT_TIMEZONE;
};

export const TimezoneProvider = ({ children }: { children: ReactNode }) => {
  const [timezone, setTimezoneState] = useState<TimezoneValue>(getInitialTimezone);

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEY, timezone);
    }
  }, [timezone]);

  const setTimezone = useCallback((value: TimezoneValue) => {
    setTimezoneState(value);
  }, []);

  const timezoneLabel = useMemo(() => {
    const option = timezoneOptions.find((item) => item.value === timezone);
    return option?.label ?? timezone;
  }, [timezone]);

  return (
    <TimezoneContext.Provider value={{ timezone, setTimezone, timezoneLabel }}>
      {children}
    </TimezoneContext.Provider>
  );
};

export const useTimezone = () => useContext(TimezoneContext);
