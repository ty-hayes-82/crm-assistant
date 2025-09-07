# CRM Assistant - Project Structure

This document outlines the organized structure of the CRM Assistant codebase.

## 📁 Directory Structure

```
crm_assistant/
├── 🤖 crm_agent/                    # Main CRM agent system
│   ├── agents/                      # Agent implementations
│   │   ├── specialized/             # Specialized agents
│   │   │   ├── company_competitor_agent.py
│   │   │   ├── company_intelligence_agent.py
│   │   │   ├── company_llm_enrichment_agent.py
│   │   │   ├── contact_intelligence_agent.py
│   │   │   ├── crm_agents.py
│   │   │   ├── crm_enrichment_agent.py
│   │   │   ├── field_enrichment_manager_agent.py
│   │   │   └── field_specialist_agents.py
│   │   └── workflows/               # Workflow agents
│   │       ├── crm_enrichment.py
│   │       └── field_enrichment_workflow.py
│   ├── auth/                        # Authentication
│   │   └── hubspot_oauth.py
│   ├── configs/                     # Configuration files
│   │   └── hubspot_app.json
│   ├── core/                        # Core framework
│   │   ├── base_agents.py
│   │   ├── factory.py
│   │   └── state_models.py
│   ├── docs/                        # Internal documentation
│   ├── utils/                       # Utilities
│   │   └── warning_suppression.py
│   ├── coordinator.py               # Main coordinator
│   ├── coordinator_main.py          # Coordinator entry point
│   └── main.py                      # Main entry point
├── 🔧 crm_fastmcp_server/           # MCP server implementation
│   ├── __main__.py
│   └── stdio_server.py
├── 🧪 tests/                        # Test files
│   ├── test_available_tools.py
│   ├── test_louisville_competitor.py
│   ├── test_louisville_llm_enrichment.py
│   └── test_mcp_tools.py
├── 🎮 demos/                        # Demo and example scripts
│   ├── demo_competitor_enrichment.py
│   ├── demo_llm_enrichment.py
│   ├── enhanced_contact_enrichment.py
│   ├── field_enrichment_demo.py
│   ├── interactive_agent.py
│   ├── iterative_enrichment_improver.py
│   └── simple_company_test.py
├── 📜 scripts/                      # Utility scripts
│   ├── crm_assistant.py
│   ├── targeted_enrichment.py
│   └── web_search_agent.py
├── 📚 docs/                         # Documentation
│   ├── AGENT_CAPABILITIES.md
│   ├── COMPANY_INTELLIGENCE_README.md
│   ├── CRM_AGENT_SYSTEM_FINAL.md
│   ├── CRM_ENRICHMENT.md
│   ├── CRM_README.md
│   ├── FIELD_ENRICHMENT_SYSTEM_SUMMARY.md
│   ├── SWOOP_FIELD_ENRICHMENT_VALIDATION.md
│   ├── USAGE_EXAMPLES.md
│   ├── all-companies.csv
│   ├── all-contacts.csv
│   ├── companies_field_profiles.json
│   └── contacts_field_profiles.json
├── README.md                        # Main README
├── requirements.txt                 # Dependencies
└── STRUCTURE.md                     # This file
```

## 🎯 Quick Start Commands

### Run the Main CRM Agent
```bash
conda activate adk
adk run crm_agent
```

### Run Tests
```bash
# Test competitor detection
python tests/test_louisville_competitor.py

# Test LLM enrichment
python tests/test_louisville_llm_enrichment.py

# Test MCP tools
python tests/test_mcp_tools.py
```

### Run Demos
```bash
# Field enrichment demo
python demos/field_enrichment_demo.py --demo-mode

# Competitor enrichment demo
python demos/demo_competitor_enrichment.py

# LLM enrichment demo
python demos/demo_llm_enrichment.py
```

### Run Utility Scripts
```bash
# Targeted enrichment
python scripts/targeted_enrichment.py

# CRM assistant interface
python scripts/crm_assistant.py
```

## 📋 Key Components

### 🤖 CRM Agent System (`crm_agent/`)
- **Main Entry**: `main.py` - Creates the default CRM agent
- **Coordinator**: `coordinator.py` - Routes requests to specialized agents
- **Specialized Agents**: Handle specific tasks (competitor detection, LLM enrichment, etc.)
- **Workflows**: Complex multi-step processes

### 🔧 MCP Server (`crm_fastmcp_server/`)
- **stdio_server.py**: HubSpot MCP server implementation
- Provides tools for searching companies, contacts, and updating CRM data

### 🧪 Tests (`tests/`)
- Unit tests and integration tests
- Specific tests for competitor detection and LLM enrichment
- MCP server functionality tests

### 🎮 Demos (`demos/`)
- Example scripts showing system capabilities
- Interactive demonstrations
- Field enrichment examples

### 📜 Scripts (`scripts/`)
- Standalone utility scripts
- Web search functionality
- Targeted enrichment operations

## 🔄 Typical Workflow

1. **Start MCP Server**: `adk run crm_agent` (starts automatically)
2. **Ask Questions**: "Does Louisville Country Club use Jonas?"
3. **Coordinator Routes**: To appropriate specialized agent
4. **Agent Processes**: Searches HubSpot, provides analysis
5. **Results Delivered**: Direct answers + comprehensive analysis

## 🛠️ Development

- **Add new agents**: `crm_agent/agents/specialized/`
- **Add new workflows**: `crm_agent/agents/workflows/`
- **Add new tests**: `tests/`
- **Add new demos**: `demos/`
- **Add new scripts**: `scripts/`

## 📖 Documentation

See `docs/` directory for detailed documentation on:
- Agent capabilities
- CRM enrichment processes
- Field enrichment systems
- Usage examples
- System architecture
