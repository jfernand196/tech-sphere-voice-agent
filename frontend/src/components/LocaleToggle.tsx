import { useLocale } from "../i18n/LocaleContext";
import type { Locale } from "../i18n";

const OPTIONS: Locale[] = ["es", "en"];

export default function LocaleToggle() {
  const { locale, setLocale, t } = useLocale();

  return (
    <div className="locale-toggle" role="group" aria-label={t("locale.aria")}>
      {OPTIONS.map((code) => (
        <button
          key={code}
          type="button"
          className={locale === code ? "locale-toggle__btn active" : "locale-toggle__btn"}
          aria-pressed={locale === code}
          onClick={() => setLocale(code)}
        >
          {t(code === "es" ? "locale.es" : "locale.en")}
        </button>
      ))}
    </div>
  );
}
