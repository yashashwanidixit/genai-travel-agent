"""LLM provider abstraction layer.

IntentAgent depends only on LLMProvider (see provider.py), never on a
specific backend. OllamaProvider is the Stage 1 implementation; future
stages can add other providers without touching IntentAgent.
"""