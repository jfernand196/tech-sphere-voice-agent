import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { LocaleProvider } from "./i18n/LocaleContext";
import { detectLocale } from "./i18n";
import "./styles.css";

document.documentElement.lang = detectLocale() === "es" ? "es" : "en";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <LocaleProvider>
      <App />
    </LocaleProvider>
  </StrictMode>,
);
