import { useLocale } from "../i18n/LocaleContext";

/** Large listening status so the jury sees mic state during voice turns. */
export default function ListenBanner() {
  const { t } = useLocale();
  return (
    <div className="listen-banner" role="status" aria-live="assertive">
      <span className="listen-banner__pulse" aria-hidden />
      <div>
        <strong>{t("call.listening")}</strong>
        <p>{t("call.listeningHint")}</p>
      </div>
    </div>
  );
}
