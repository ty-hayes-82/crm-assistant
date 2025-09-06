# CRM Assistant - Multi-Agent Company Intelligence and Data Quality

A production-ready team of AI agents and tools that help you:
- Ask questions about any company in HubSpot and get a complete answer
- Pull all associated contacts and deals
- Analyze pipelines and generate insights
- Audit data quality, find gaps, and recommend fixes

## Quick Start

1) Configure your HubSpot Private App token in `.env` at repo root:
```
PRIVATE_APP_ACCESS_TOKEN=your_hubspot_token
```

2) Start the MCP server (provides HubSpot tools):
```
python mcp_wrapper/simple_hubspot_server.py
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
- `DataQualityIntelligenceAgent` – Scrutinizes data quality and highlights gaps
- Workflows: `crm_agent/agents/workflows/`
  - `crm_enrichment.py` – Full enrichment pipeline
  - `data_quality_workflow.py` – Assessment and monitoring

You can instantiate a system-level agent via `crm_agent/coordinator.py`:
```python
from crm_agent.coordinator import get_crm_agent

agent = get_crm_agent(agent_type="coordinator")
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

## Troubleshooting

- Health check: `curl http://localhost:8081/health`
- Token missing → ensure `.env` contains `PRIVATE_APP_ACCESS_TOKEN`
- Empty results → verify the company exists in your HubSpot portal and the token scopes include read access

## License
MIT
