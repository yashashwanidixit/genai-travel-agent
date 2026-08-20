# GenAI Travel Agent

An intelligent, multi-agent travel planning and booking system with autonomous recommendation, multi-layer memory, and multi-provider automation (Mock, REST API, and Appium for mobile apps).

## Architecture Overview

```
genai-travel-agent/
├── app/
│   ├── main.py                  # FastAPI Application Entrypoint
│   ├── api/
│   │   └── routes/              # REST Endpoints (trips, hotels, rides, users)
│   ├── agents/                  # Multi-Agent Layer (Intent, Memory, Reasoning)
│   ├── orchestration/           # State Machine & Orchestrator
│   ├── recommendation/          # Scoring & Ranking Pipeline
│   ├── memory/                  # Episodic, Semantic, Preferences, Workspace
│   ├── providers/               # Hotel & Ride Providers (Mock, API, Appium)
│   ├── automation/              # Appium Client & Device Manager
│   ├── models/                  # Pydantic & Data Domain Models
│   └── database/                # SQLAlchemy DB Engine & Models
├── data/                        # Sample Mock Data
├── scripts/                     # Utility and Seeding Scripts
├── tests/                       # Unit & Integration Tests
├── README.md
└── requirements.txt
```

## Features

- **Multi-Agent Architecture**:
  - `IntentAgent`: Extracts structured travel intents from natural language queries.
  - `MemoryAgent`: Ingests and recalls episodic and semantic user context and preferences.
  - `ReasoningAgent`: Generates optimized, trade-off-aware itineraries combining hotels and rides.
- **Dynamic Recommendation Engine**:
  - Feature extraction, normalizer (min-max / z-score), multi-criteria weighted scoring, and constrained ranking.
- **Provider Abstraction Layer**:
  - Pluggable interfaces for Hotel and Ride providers supporting Mock simulations, direct REST APIs, and Appium UI automation.
- **Comprehensive Memory System**:
  - Episodic chat history, semantic embedding tags, structured user preferences, and a transient workspace scratchpad.

## Quickstart

### 1. Installation
```bash
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

### 2. Run Database Seeding
```bash
python scripts/seed_data.py
```

### 3. Start Development Server
```bash
python scripts/run_dev.py
```
Or directly with uvicorn:
```bash
uvicorn app.main:app --reload --port 8000
```
Interactive API docs are available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 4. Running Tests
```bash
pytest tests/
```
