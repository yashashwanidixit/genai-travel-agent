from __future__ import annotations

from app.agents.intent_agent import IntentAgent, IntentParsingError
from app.llm.ollama_provider import OllamaProvider
from app.models.intent import TravelIntent


def _print_ollama_config(provider: OllamaProvider) -> None:
    print("\n[Ollama] Connected")
    print(f"[Ollama] Model: {provider.model}")
    print(f"[Ollama] Keep alive: {provider.keep_alive}")
    print(f"[Ollama] CPU threads: {provider.num_thread}")


def _print_intent(intent: TravelIntent) -> None:
    print("\nIntent:")
    print(intent.primary_category.value)

    print("\nSlots:")
    populated = {
        key: value
        for key, value in intent.slots.model_dump().items()
        if value is not None
    }
    if populated:
        for key, value in populated.items():
            print(f"{key}: {value}")
    else:
        print("none")

    print("\nMissing:")
    if intent.missing_slots:
        for slot in intent.missing_slots:
            print(slot)
    else:
        print("none")
    print()


def main() -> None:
    print("Travel Agent — Stage 1")
    print("Type 'exit' to quit.\n")

    llm_provider = OllamaProvider()
    agent = IntentAgent(llm_provider)

    while True:
        try:
            raw_query = input("You:\n").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not raw_query:
            continue
        if raw_query.lower() in {"exit", "quit"}:
            print("Exiting.")
            break

        _print_ollama_config(llm_provider)

        try:
            intent, metrics = agent.parse_with_metrics(raw_query)
        except IntentParsingError as exc:
            print(f"\nCould not understand that request: {exc}\n")
            continue
        except RuntimeError as exc:
            print(f"\n[Ollama] ERROR")
            print(f"LLM error: {exc}\n")
            continue

        metrics.print_report()
        _print_intent(intent)


if __name__ == "__main__":
    main()