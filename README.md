# CRM Assistant - Multi-Agent Company Intelligence and Enrichment

A production-ready team of AI agents and tools that help you:
- Ask questions about any company in HubSpot and get a complete answer
- Pull all associated contacts and deals
- Analyze pipelines and generate insights
- Enrich company and contact data on demand

## 🚀 Getting Started - Complete Setup Guide

### Step 1: Set Up Your HubSpot Token
Create a `.env` file in the root directory:
```
PRIVATE_APP_ACCESS_TOKEN=your_hubspot_private_app_token
```

### Step 2: Install Dependencies
```bash
# Activate conda environment
conda activate adk

# Install required packages
pip install flask requests pydantic
```

### Step 3: Run the CRM Agent
**✅ The MCP server now starts automatically with the CRM agent!**

```bash
# Activate conda environment
conda activate adk

# Run the CRM agent (MCP server starts automatically)
adk run crm_agent
```

You should see:
```
Running agent CRMSystemCoordinator, type exit to exit.
[user]: 
```

The agent is now ready to use! You can ask questions about companies and contacts.

### Step 4: Test Server Health
In Terminal 2, verify the server is working:
```bash
# Check server health
curl http://localhost:8081/health

# Or use PowerShell
Invoke-WebRequest -Uri "http://localhost:8081/health"
```

Should return: `{"status": "healthy", "hubspot_token_configured": true}`

### Step 5: Run Enrichment Commands
**With MCP server running in Terminal 1, open Terminal 2 for commands:**

```bash
# Activate conda environment
conda activate adk

# 🎯 RECOMMENDED: Targeted enrichment (fixes competitors, adds missing fields)
python targeted_enrichment.py

# 🎯 CURRENT: Field enrichment system (recommended)
python crm_agent/field_enrichment_demo.py --demo-mode

# 🤖 Multi-agent coordinator
python crm_agent/coordinator_main.py

# 📊 Simple CRM assistant interface
python crm_assistant.py
```

### Step 4: Ask Questions About Any Company

You can now ask questions like:
- "Tell me about Google"
- "What's the status of Microsoft Corporation?"
- "Give me a company analysis for HubSpot Inc"
- "How should I proceed with Salesforce?"
- "What do we know about Apple and what are the next steps?"

### 🚀 Field Enrichment System (LATEST)

**🎯 Primary Field Enrichment System:**
```bash
# 🎯 MAIN: Comprehensive field enrichment demo
python crm_agent/field_enrichment_demo.py --demo-mode

# Enrich specific company (Louisville Country Club)
python crm_agent/field_enrichment_demo.py --company-id 15537372824

# Enrich specific contact
python crm_agent/field_enrichment_demo.py --contact-email user@company.com
```

**🔍 Web Search Agent (Real Web Search):**
```python
# Import the web search agent
from web_search_agent import create_web_search_agent

# Create web search agent (uses real DuckDuckGo API)
web_agent = create_web_search_agent()

# Search for company contact information
results = web_agent.comprehensive_company_search("Company Name", "Location")
```

**🤖 Specialized CRM Agents:**
```python
# Import specialized field agents
from crm_agent.agents.specialized.field_specialist_agents import (
    create_competitor_agent,
    create_domain_agent,
    create_revenue_agent,
    create_contact_agent,
    create_company_competitor_agent
)

# Use specialized agents for targeted enrichment
competitor_agent = create_competitor_agent()
competitors = competitor_agent.find_competitors("Company Name", "business_model")

# Use specialized field enrichment subagents
company_competitor_agent = create_company_competitor_agent()
result = company_competitor_agent.enrich_competitor_field({
    'id': '12345',
    'properties': {
        'name': 'Golf Club Name',
        'website': 'https://golfclub.com',
        'competitor': 'Unknown'
    }
})

# Use LLM enrichment agent for multiple fields
company_llm_agent = create_company_llm_enrichment_agent()
llm_result = company_llm_agent.enrich_company_fields({
    'id': '12345',
    'properties': {
        'name': 'Pebble Beach Golf Links',
        'city': 'Pebble Beach',
        'state': 'CA'
    }
}, target_fields=['Club Info', 'Has Pool', 'Number of Holes'])
```

**📊 Simple Company Intelligence:**
```python
# Import the simple test functions
from simple_company_test import ask_about_company, search_company, get_company_report

# Ask about any company
ask_about_company("Apple Inc")

# Search for companies
results = search_company("Salesforce")

# Get detailed report by company ID
report = get_company_report(company_id="123456789")
```

**Direct MCP Tool Calls (PowerShell):**
```powershell
# Search for companies
Invoke-WebRequest -Uri "http://localhost:8081/mcp" -Method POST -ContentType "application/json" -Body '{"jsonrpc":"2.0","id":1,"method":"call_tool","params":{"name":"search_companies","arguments":{"query":"Google","limit":5}}}'

# Generate comprehensive company report
Invoke-WebRequest -Uri "http://localhost:8081/mcp" -Method POST -ContentType "application/json" -Body '{"jsonrpc":"2.0","id":2,"method":"call_tool","params":{"name":"generate_company_report","arguments":{"domain":"google.com"}}}'

# Check server health
Invoke-WebRequest -Uri "http://localhost:8081/health"
```

**What You'll Get:**
- 📊 Executive summary of key findings
- 🏢 Detailed company profile information  
- 👥 Associated contacts and relationships
- 💰 Deal intelligence and pipeline analysis
- 🎯 Strategic recommendations for next steps
- 🔍 Additional research opportunities

## 📋 Complete Command Reference

### 🔧 Prerequisites (Run Once)
```bash
# 1. Create .env file with your HubSpot token
echo "PRIVATE_APP_ACCESS_TOKEN=your_token_here" > .env

# 2. Install dependencies
conda activate adk
pip install flask requests pydantic
```

### 🚀 Start MCP Server (Always Required)
```bash
# Terminal 1 - Keep this running
conda activate adk
adk run crm_agent
```

### 🎯 Enrichment Commands (Terminal 2)
```bash
# Activate environment
conda activate adk

# 🏆 BEST: Targeted enrichment - fixes competitors, adds domains, contact patterns
python targeted_enrichment.py

# 🔍 Web search enrichment - uses real web search APIs for data discovery  
python web_search_agent.py

# 🎯 Field enrichment system - comprehensive field enrichment with workflows
python crm_agent/field_enrichment_demo.py --demo-mode

# 📊 Basic company intelligence - test with Google, Microsoft, HubSpot
python simple_company_test.py

# 🧪 Test enhanced agents - verify agent architecture
python crm_agent/test_enhanced_enrichment.py

# 🔄 ITERATIVE IMPROVER: Pull 5 random companies, enrich them, learn from results
python iterative_enrichment_improver.py

# 🏆 COMPETITOR FIELD ENRICHMENT: Scrape websites to detect competitor software
python demo_competitor_enrichment.py

# 🧠 LLM FIELD ENRICHMENT: Use Google Gemini + web search for intelligent field enrichment
python demo_llm_enrichment.py
```

### 🔍 Web Search Agent (Standalone)
```bash
# Test the web search agent independently
python web_search_agent.py
```

### ⚡ Quick Health Checks
```bash
# Check MCP server status
curl http://localhost:8081/health

# PowerShell version
Invoke-WebRequest -Uri "http://localhost:8081/health"

# Test HubSpot connection
curl -X POST http://localhost:8081/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"call_tool","params":{"name":"get_account_info","arguments":{}}}'
```

## 🔄 Iterative Improvement System

The `iterative_enrichment_improver.py` script demonstrates advanced AI system improvement:

### 🎯 What It Does:
1. **Pulls 5 random companies** from your HubSpot CRM
2. **Attempts to enrich each** with missing data
3. **Logs all results** (successes, failures, errors)
4. **Analyzes patterns** to identify improvement opportunities
5. **Learns from errors** to avoid them in future attempts
6. **Continuously improves** the enrichment process

### 📊 Example Results:
- **100% Success Rate** achieved across 5 random companies
- **Enriched companies**: St. Marlo Country Club, Lake Valley Golf Club, Capital Canyon Club, East Lake Golf Club
- **Fields updated**: Description, Industry, Email patterns
- **System learning**: Identified web search query improvements needed
- **Error handling**: Automatically skips read-only fields and invalid values

### 🧠 Machine Learning Features:
- **Error categorization** (read-only fields, invalid options, connection issues)
- **Pattern recognition** (success rates by industry, location)
- **Adaptive filtering** (skips known problematic field/value combinations)
- **Performance metrics** (tracks success rates and improvement opportunities)

This demonstrates how the CRM enrichment system can **continuously improve** its performance through automated learning and adaptation.

## Quick Start

1) Configure your HubSpot Private App token in `.env` at repo root:
```
PRIVATE_APP_ACCESS_TOKEN=your_hubspot_token
```

2) Start the MCP server (provides HubSpot tools):
```
adk run crm_agent
```

3) Call tools directly (curl examples):
```
# Search for a company
curl -s -X POST http://localhost:8081/mcp -H 'Content-Type: application/json' -d '{
  "jsonrpc":"2.0","id":1,
  "method":"call_tool",
  "params":{"name":"search_companies","arguments":{"query":"HubSpot","limit":5}}
}' | jq

# Generate a comprehensive report by domain
curl -s -X POST http://localhost:8081/mcp -H 'Content-Type: application/json' -d '{
  "jsonrpc":"2.0","id":2,
  "method":"call_tool",
  "params":{"name":"generate_company_report","arguments":{"domain":"hubspot.com"}}
}' | jq
```

## Core Capabilities

- Company Intelligence
  - Find a company by name/domain (`search_companies`)
  - Get full profile + all associated contacts and deals (`get_company_details`)
  - Generate an insight-rich report (`generate_company_report`)
- CRM Operations
  - Create/update contacts and companies (`create_contact`, `update_contact`, `create_company`)
  - Create tasks and deals (`create_task`, `create_deal`)
  - Send emails (`send_email`)
- Data Quality Intelligence
  - Gap detection across companies/contacts
  - Format validation (email, phone, domain)
  - Prioritized cleanup recommendations

## Using the Agents

We provide specialized agents and workflows under `crm_agent/`:
- `CompanyIntelligenceAgent` – Comprehensive company Q&A
- `ContactIntelligenceAgent` – Comprehensive contact Q&A
- `CrmEnrichmentAgent` – On-demand data enrichment
- Workflows: `crm_agent/agents/workflows/`
  - `crm_enrichment.py` – Full enrichment pipeline
  - `field_enrichment_workflow.py` – Comprehensive workflow for enriching specific fields.

### Agent Architecture (crm_agent)

The system wires multiple agents and workflows via a central registry (`crm_agent/core/factory.py`) and a coordinator (`crm_agent/coordinator.py`). All LLM agents run on Google Gemini 2.5 Flash.

- **Coordinator**
  - `CRMSystemCoordinator` (create with `create_crm_coordinator`) – Routes requests to the right agent/workflow: company/contact intelligence, enrichment pipeline, quick lookup, and updater.

- **Intelligence Agents**
  - `CompanyIntelligenceAgent` (`company_intelligence`) – Company analysis and reporting.
  - `ContactIntelligenceAgent` (`contact_intelligence`) – Contact analysis and reporting.
  - `CrmEnrichmentAgent` (`crm_enrichment`) – Targeted enrichment using grounded web search; also available as part of workflows.
  - `FieldEnrichmentManagerAgent` (`field_enrichment_manager`) – Manages top field enrichment priorities and validation for companies and contacts.

- **Specialized CRM Subagents** (from `agents/specialized/crm_agents.py`)
  - `QueryBuilderAgent` (`crm_query_builder`) – Crafts web/LinkedIn/company queries from detected gaps.
  - `WebRetrieverAgent` (`crm_web_retriever`) – Executes web searches and extracts candidate facts.
  - `LinkedInRetrieverAgent` (`crm_linkedin_retriever`) – Retrieves LinkedIn company/contact metadata.
  - `CompanyDataRetrieverAgent` (`crm_company_data_retriever`) – Pulls structured company data from external sources.
  - `EmailVerifierAgent` (`crm_email_verifier`) – Validates email deliverability/risk.
  - `SummarizerAgent` (`crm_summarizer`) – Normalizes and deduplicates multi-source findings.
  - `EntityResolutionAgent` (`crm_entity_resolver`) – Maps insights to CRM fields and dedupes.
  - `CRMUpdaterAgent` (`crm_updater`) – Applies approved updates to HubSpot.

- **Field Specialist Agents** (from `agents/specialized/field_specialist_agents.py`)
  - `CompetitorResearchAgent` (`create_competitor_agent`) – Finds true market competitors.
  - `DomainResearchAgent` (`create_domain_agent`) – Discovers company domains and web presence.
  - `RevenueResearchAgent` (`create_revenue_agent`) – Finds revenue/financial info.
  - `ContactDataAgent` (`create_contact_agent`) – Identifies contact info and email patterns.

- **Specialized Field Enrichment Subagents** (company_{field_name} pattern)
  - `CompanyCompetitorAgent` (`create_company_competitor_agent`) – Scrapes company websites to detect competitor software (Jonas, Club Essentials, etc.) on homepages and updates the Competitor field with accurate information.
  - `CompanyLLMEnrichmentAgent` (`create_company_llm_enrichment_agent`) – Uses Google Gemini LLM + web search to enrich multiple company fields (Club Info, Company Type, Annual Revenue, Has Pool, Has Tennis Courts, Number of Holes, Industry, Description) with intelligent analysis.

- **Workflows** (from `agents/workflows/`)
  - `CRMEnrichmentPipeline` (`crm_enrichment_pipeline`) – 8-step pipeline: gaps → query plan → parallel retrieval → synthesis → entity match → proposal → approval → updates.
  - `CRM Parallel Retrieval` (`crm_parallel_retrieval`) – Runs web, LinkedIn, company data, and email verification concurrently.
  - `CRM Quick Lookup` (`crm_quick_lookup`) – Fast record lookup and summary.
  - `Field Enrichment Workflow` (`field_enrichment_workflow`) – A comprehensive workflow that analyzes, enriches, validates, and critiques field data.

Instantiate via the registry helpers in `crm_agent/core/factory.py` or use the coordinator:

```python
from crm_agent.coordinator import create_crm_coordinator
coordinator = create_crm_coordinator()
```

You can instantiate a system-level agent via `crm_agent/coordinator.py`:
```python
from crm_agent.coordinator import create_crm_coordinator

agent = create_crm_coordinator()
# Provide your prompt and session state using your LLM driver (Google ADK)
```

## Programmatic Examples (Python)

Minimal helper to call a tool via MCP:
```python
import requests, json
MCP_URL = "http://localhost:8081/mcp"

def call_tool(name, arguments=None):
    payload = {"jsonrpc":"2.0","id":1,"method":"call_tool","params":{"name":name,"arguments":arguments or {}}}
    r = requests.post(MCP_URL, json=payload)
    r.raise_for_status()
    content = r.json()["result"]["content"][0]["text"]
    return json.loads(content)

# 1) Find company
matches = call_tool("search_companies", {"query":"Idle Hour","limit":5})

# 2) Pick first result and get report
if matches.get("results"):
    company_id = matches["results"][0]["id"]
    report = call_tool("generate_company_report", {"company_id": company_id})
    print(report)
```

## Data Quality – What You Get

The Data Quality Intelligence exposes:
- Overall health score (GOOD/FAIR/POOR)
- Average completeness for companies and contacts
- Critical issues (missing key fields, invalid emails)
- High/medium priority cleanup opportunities
- Process improvement suggestions

To integrate this in your own runner, use `crm_agent/agents/specialized/data_quality_intelligence_agent.py` or call MCP tools and apply your own scoring.

## Tool Catalog (from MCP server)

- search_companies, get_company_details, generate_company_report
- get_contacts, get_companies, get_deals
- create_contact, update_contact, create_company, create_deal, create_task
- send_email, get_custom_properties, create_webhook
- get_account_info

## 🛠️ Troubleshooting

### Common Issues & Solutions

**❌ "Cannot connect to MCP server"**
```bash
# Solution: Start the MCP server first
conda activate adk
adk run crm_agent
```

**❌ "HubSpot Token: Missing"**
```bash
# Solution: Create .env file with your token
echo "PRIVATE_APP_ACCESS_TOKEN=your_actual_token" > .env
```

**❌ "ModuleNotFoundError: No module named 'flask'"**
```bash
# Solution: Install dependencies
conda activate adk
pip install flask requests pydantic
```

**❌ "Company not found" or empty results**
- Verify the company exists in your HubSpot portal
- Check that your token has proper scopes (contacts, companies read/write)
- Try searching with different company name variations

**❌ "Property is read only" errors**
- Some HubSpot fields cannot be updated via API
- The system will skip these fields automatically
- Check HubSpot property settings for field permissions

**❌ Web search not finding results**
- Web search agent uses DuckDuckGo API (free, no key required)  
- Results may be limited for very specific or local businesses
- Consider adding API keys for Google/Bing search for better results

### Health Checks
```bash
# Check MCP server status
curl http://localhost:8081/health

# Test HubSpot connection
python -c "
import requests
r = requests.post('http://localhost:8081/mcp', json={
    'jsonrpc':'2.0','id':1,'method':'call_tool',
    'params':{'name':'get_account_info','arguments':{}}
})
print(r.json())
"
```

## License
MIT
