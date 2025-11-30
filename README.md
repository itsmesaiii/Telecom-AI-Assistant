# Telecom Customer Support AI System

A comprehensive AI-powered customer support system that unifies multiple AI frameworks (CrewAI, AutoGen, LangChain, LlamaIndex) into a single orchestrated workflow using LangGraph.

## Features

- **💰 Billing Support**: Analyze charges, detect unusual bills, suggest better plans (CrewAI)
- **📡 Network Troubleshooting**: Diagnose connectivity issues, provide step-by-step fixes (AutoGen)
- **📋 Plan Recommendations**: Compare plans, suggest upgrades/downgrades based on usage (LangChain)
- **📚 Knowledge Base**: Answer technical questions using document retrieval (LlamaIndex)

## Architecture

```
User Query
    ↓
LangGraph Orchestrator (Classification)
    ↓
┌─────────┬──────────┬────────────┬─────────────┐
│ Billing │ Network  │  Plan      │ Knowledge   │
│ (CrewAI)│ (AutoGen)│(LangChain) │(LlamaIndex) │
└─────────┴──────────┴────────────┴─────────────┘
    ↓
Final Response
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file:

```
OPENAI_API_KEY=your_api_key_here
```

### 3. Database

The system uses `data/telecom.db` (SQLite) with the following tables:
- `customers`
- `service_plans`
- `customer_usage`
- `network_incidents`
- `common_network_issues`
- `device_compatibility`

### 4. Knowledge Base

Documents are loaded from `data/documents/` and indexed in `data/chromadb/`.

## Usage

### Run the Streamlit UI

```bash
streamlit run app.py
```

### Run Tests

```bash
# Run all tests
python tests/run_all_tests.py

# Run specific test suites
python tests/test_classification.py
python tests/test_e2e.py
python tests/test_billing_flow.py
python tests/test_network_flow.py
python tests/test_plan_flow.py
python tests/test_knowledge_flow.py
```

## Project Structure

```
telecom_assistant/
├── agents/
│   ├── billing_agents.py      # CrewAI billing agent
│   ├── network_agents.py      # AutoGen network agent
│   ├── service_agents.py      # LangChain plan agent
│   └── knowledge_agents.py    # LlamaIndex knowledge agent
├── orchestration/
│   ├── graph.py               # LangGraph orchestrator
│   └── state.py               # State definition
├── ui/
│   ├── sidebar.py             # Login & Sidebar UI
│   ├── dashboard.py           # Dashboard UI
│   └── chat_interface.py      # Chat interface UI
├── services/
│   └── customer_service.py    # Customer data service
├── tests/
│   ├── run_all_tests.py       # Master test runner
│   ├── test_classification.py # Classification tests
│   └── test_e2e.py            # End-to-end tests
├── data/
│   ├── telecom.db             # SQLite database
│   ├── documents/             # Knowledge base documents
│   └── chromadb/              # Vector store
├── config/
│   └── config.py              # Configuration
├── utils/
│   └── database.py            # Database utilities
└── app.py                     # Main entry point
```

## Test Results

✅ **Classification Accuracy**: 100% (13/13 tests passed)
✅ **End-to-End Tests**: 100% (4/4 tests passed)
✅ **Overall Success Rate**: 100% (17/17 tests passed)

## Example Queries

- **Billing**: "Why is my bill so high this month?"
- **Network**: "My internet connection is very slow"
- **Plan**: "Can you recommend a better plan for me?"
- **Knowledge**: "What is VoLTE and how does it work?"

## Technologies Used

- **LangGraph**: Main orchestrator and workflow management
- **CrewAI**: Billing analysis with multi-agent reasoning
- **AutoGen (ag2)**: Network troubleshooting with agent collaboration
- **LangChain**: Plan recommendation with tools and SQL
- **LlamaIndex**: Knowledge retrieval with vector search
- **Chroma**: Vector database for document embeddings
- **Streamlit**: Web UI for chat interface
- **SQLite**: Customer and service data storage
- **OpenAI**: LLM provider (GPT-4o)

## License

MIT
