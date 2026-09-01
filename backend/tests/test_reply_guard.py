from app.agent.reply_guard import (
    SPOKEN_ALERT_SENTENCE,
    SPOKEN_WATCH_PLAN,
    ensure_spoken_alert,
    reply_already_speaks_alert,
)


def test_ensure_spoken_alert_appends_when_model_stayed_silent() -> None:
    out = ensure_spoken_alert(
        "Ana, entiendo la fiebre. ¿Has notado náuseas?",
        escalate=True,
    )
    assert SPOKEN_ALERT_SENTENCE in out
    assert SPOKEN_WATCH_PLAN in out
    assert out.startswith("Ana, entiendo la fiebre")


def test_ensure_spoken_alert_adds_plan_if_model_only_mentioned_human() -> None:
    reply = "Eso es urgente; voy a alertar a personal capacitado ahora mismo."
    out = ensure_spoken_alert(reply, escalate=True)
    assert out.startswith(reply)
    assert SPOKEN_WATCH_PLAN in out


def test_ensure_spoken_alert_noop_when_not_escalating() -> None:
    reply = "La herida se ve bien. Manténla limpia y seca."
    assert ensure_spoken_alert(reply, escalate=False) == reply


def test_ensure_spoken_alert_does_not_duplicate_gemini_handoff() -> None:
    reply = (
        "Me alegra saber que no tiene esos síntomas. "
        "Voy a comunicar su situación de inmediato con un profesional de salud. "
        "Si se siente peor, acuda a urgencias."
    )
    out = ensure_spoken_alert(reply, escalate=True)
    assert out.count("Voy a marcar una alerta") == 0
    assert SPOKEN_WATCH_PLAN not in out or "acuda a urgencias" in out.lower()


def test_drop_unwarranted_alert_keeps_empathy_sentence() -> None:
    from app.agent.reply_guard import HOME_WATCH_WITHOUT_ALERT, drop_unwarranted_alert_close

    reply = (
        "Me alegra saber que no tiene esos síntomas en sus heridas ni vómito, Manuel. "
        "Como presenta una temperatura de 37.4 y dolor moderado, voy a comunicar "
        "su situación de inmediato con un profesional de salud para que lo valore. "
        "Por favor, vigile esta noche y si se siente peor, acuda a urgencias."
    )
    out = drop_unwarranted_alert_close(reply)
    assert "Me alegra saber" in out
    assert "profesional de salud" not in out.lower()
    assert "Voy a marcar una alerta" not in out
    assert HOME_WATCH_WITHOUT_ALERT in out


def test_ensure_spoken_alert_does_not_treat_ood_limit_as_alert() -> None:
    reply = "No tengo esa indicación en mis protocolos; confírmalo con tu equipo médico."
    assert not reply_already_speaks_alert(reply)
    assert SPOKEN_ALERT_SENTENCE not in ensure_spoken_alert(reply, escalate=False)
