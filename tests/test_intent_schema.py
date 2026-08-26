from app.agents.intent_agent import _LLMIntentOutput
from app.models.intent import IntentCategory


def test_llm_intent_output_schema_contains_required_category():
    schema = _LLMIntentOutput.model_json_schema()

    assert "category" in schema["properties"]
    assert "category" in schema["required"]


def test_llm_intent_output_schema_contains_soft_preferences():
    schema = _LLMIntentOutput.model_json_schema()

    assert "target_price" in schema["properties"]
    assert "target_rating" in schema["properties"]


def test_llm_intent_output_schema_contains_hard_constraints():
    schema = _LLMIntentOutput.model_json_schema()

    assert "max_hotel_price" in schema["properties"]
    assert "minimum_hotel_rating" in schema["properties"]


def test_valid_hotel_output_passes_pydantic():
    output = _LLMIntentOutput(
        category=IntentCategory.HOTEL_SEARCH,
        target_price=4000,
        target_rating=4.5,
    )

    assert output.category == IntentCategory.HOTEL_SEARCH
    assert output.target_price == 4000
    assert output.target_rating == 4.5