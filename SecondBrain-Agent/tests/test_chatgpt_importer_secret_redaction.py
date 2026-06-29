from modules.chatgpt_importer.importer import (
    REDACTED_OPENAI_API_KEY,
    conversation_to_markdown,
    redact_secrets,
)


def _fake_openai_key(*, project: bool = False) -> str:
    prefix = "sk-" + ("proj-" if project else "")
    return prefix + ("a1_" * 16)


def test_redact_secrets_removes_legacy_and_project_keys() -> None:
    legacy_key = _fake_openai_key()
    project_key = _fake_openai_key(project=True)

    result = redact_secrets(f"legacy={legacy_key}\nproject={project_key}")

    assert legacy_key not in result
    assert project_key not in result
    assert result.count(REDACTED_OPENAI_API_KEY) == 2


def test_conversation_markdown_redacts_keys_from_messages() -> None:
    api_key = _fake_openai_key(project=True)
    conversation = {
        "id": "test-conversation",
        "title": "Secret handling",
        "mapping": {
            "message-1": {
                "message": {
                    "author": {"role": "user"},
                    "content": {"parts": [f"Use {api_key} for this example"]},
                    "create_time": 1,
                }
            }
        },
    }

    _, markdown = conversation_to_markdown(conversation)

    assert api_key not in markdown
    assert REDACTED_OPENAI_API_KEY in markdown
