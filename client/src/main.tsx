
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.tsx";
import "./index.css";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { LanguageProvider } from "./lib/language";
import { TimezoneProvider } from "./lib/timezone";

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <LanguageProvider>
        <TimezoneProvider>
          <App />
        </TimezoneProvider>
      </LanguageProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
  
