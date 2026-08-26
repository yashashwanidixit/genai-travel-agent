from app.llm.ollama_provider import OllamaProvider


def test_provider_sends_response_schema(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "message": {
                    "content": '{"category":"hotel_search"}'
                }
            }

    def fake_post(url, json, timeout):
        captured["payload"] = json
        return FakeResponse()

    monkeypatch.setattr(
        "app.llm.ollama_provider.requests.post",
        fake_post,
    )

    provider = OllamaProvider()

    schema = {
        "type": "object",
        "properties": {
            "category": {
                "type": "string"
            }
        },
    }

    provider.generate_structured_with_metadata(
        "system",
        "user",
        response_schema=schema,
    )

    assert captured["payload"]["format"] == schema