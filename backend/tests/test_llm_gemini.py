from app.agent.llm_gemini import (
    _interaction_payload,
    _interaction_text,
    skip_to_next_flash,
)


def test_interaction_text_reads_model_output_steps() -> None:
    data = {
        "steps": [
            {"type": "user_input", "content": [{"type": "text", "text": "hola"}]},
            {
                "type": "model_output",
                "content": [{"type": "text", "text": "Entendido. "}, {"type": "text", "text": "Plan."}],
            },
        ]
    }
    assert _interaction_text(data) == "Entendido. Plan."


def test_interaction_text_prefers_output_text() -> None:
    assert _interaction_text({"output_text": "ok", "steps": []}) == "ok"


def test_interaction_payload_uses_minimal_thinking() -> None:
    payload = _interaction_payload(model_id="gemini-3.6-flash", system="sys", user="hola")
    config = payload["generation_config"]
    assert config["thinking_level"] == "minimal"
    assert config["thinking_summaries"] == "none"


def test_lite_payload_skips_thinking_config() -> None:
    payload = _interaction_payload(
        model_id="gemini-3.5-flash-lite", system="sys", user="hola"
    )
    config = payload["generation_config"]
    assert "thinking_level" not in config
    assert config["max_output_tokens"] == 1024


def test_skip_to_next_flash_on_quota_and_retired_models() -> None:
    assert skip_to_next_flash(429, "You exceeded your current quota") is True
    assert skip_to_next_flash(404, "This model is no longer available") is True
    assert skip_to_next_flash(500, "internal") is False
