# CRM Assistant - Multi-Agent Data Enrichment & Cleanup

A comprehensive multi-agent system for automating CRM data enrichment and cleanup using Google's Agent Development Kit (ADK). This system implements advanced multi-agent patterns including Coordinator/Dispatcher, Sequential Pipeline, and Parallel Fan-Out/Gather for intelligent HubSpot CRM data management.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Conda environment management
- Google ADK framework
- HubSpot account with API access
- Optional: Slack workspace for approvals

### Installation

1. **Setup Environment**
   ```bash
   conda activate adk
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**
   ```bash
   # HubSpot Configuration
   export HUBSPOT_CLIENT_ID="your-hubspot-client-id"
   export HUBSPOT_CLIENT_SECRET="your-hubspot-client-secret"
   export HUBSPOT_ACCESS_TOKEN="your-oauth-access-token"
   export HUBSPOT_REFRESH_TOKEN="your-oauth-refresh-token"
   
   # Optional: External Services
   export SEARCH_API_KEY="your-serp-api-key"
   export SLACK_BOT_TOKEN="your-slack-bot-token"
   export EMAIL_VERIFY_API_KEY="your-email-verification-key"
   ```

3. **Run the CRM Assistant**
   ```bash
   # Simple CRM agent (recommended for beginners)
   adk run crm_agent
   
   # Full multi-agent coordinator (advanced features)
   adk run crm_agent.coordinator_main
   
   # Web interface
   adk web crm_agent
   ```

## 🎯 What You Can Do

### Immediate Capabilities
- **📊 Contact Enrichment**: Find missing contact information (industry, company size, phone, etc.)
- **🏢 Company Data**: Enrich company records with industry, employee count, headquarters, technology stack
- **🔍 Data Quality**: Identify missing fields, validate email addresses, detect inconsistencies
- **🤖 Automated Updates**: Apply enriched data to HubSpot with human approval
- **📈 Quality Reports**: Generate comprehensive data quality assessments
- **💬 Slack Integration**: Natural language queries and approval workflows

### Example Queries
```bash
# After running adk run crm_agent:
"Enrich the contact john@acme.com"
"What do we know about ACME Corp?"
"Check our CRM data quality"
"Find missing industry fields"
"Update company size for acme.com"
"Generate a data quality report"
```

## 🏗️ Architecture Overview

This system implements a sophisticated multi-agent architecture with three main layers:

### 1. **Coordinator Layer**
- **CRMSystemCoordinator**: Central routing agent that delegates tasks to specialized agents
- **ClarificationAgent**: Handles ambiguous requests by asking clarifying questions

### 2. **Specialized Agents**
- **QueryBuilderAgent**: Crafts precise search queries from detected CRM gaps
- **WebRetrieverAgent**: Executes web searches and extracts candidate facts
- **LinkedInRetrieverAgent**: Retrieves LinkedIn company/contact metadata
- **CompanyDataRetrieverAgent**: Gets structured data from business directories
- **EmailVerifierAgent**: Validates email deliverability and risk assessment
- **SummarizerAgent**: Normalizes and deduplicates findings from multiple sources
- **EntityResolutionAgent**: Maps findings to CRM fields with deduplication
- **CRMUpdaterAgent**: Prepares and applies updates to HubSpot with approval
- **CRMDataQualityAgent**: Validates data quality and proposes improvements

### 3. **Workflow Agents** (Advanced)
- **CRMEnrichmentPipeline**: 8-step sequential workflow for complete enrichment
- **CRMParallelRetrieval**: Concurrent data gathering from multiple sources
- **CRMQuickLookup**: Fast summary generation for existing records
- **CRMDataQualityWorkflow**: Comprehensive quality assessment and improvement

## 🛠️ Key Features

### ✨ HubSpot Official Integration
- **Native MCP Server**: Direct integration with HubSpot's official MCP server at `https://mcp.hubspot.com/`
- **OAuth 2.1 Support**: Secure authentication with PKCE and refresh token rotation
- **Granular Permissions**: Respects HubSpot app scopes and user permissions
- **Natural Language Queries**: Query HubSpot data using plain English

### 🧠 Intelligent Multi-Source Enrichment
- **Parallel Processing**: Concurrent data gathering from web, LinkedIn, and business directories
- **Confidence Scoring**: AI-powered confidence assessment for all enriched data
- **Source Attribution**: Complete audit trail of data sources and extraction methods
- **Conflict Resolution**: Smart handling of conflicting information from multiple sources

### 🔧 Advanced Workflow Orchestration
- **Sequential Pipelines**: 8-step enrichment process with state management
- **Parallel Fan-Out**: Concurrent execution for maximum efficiency
- **Human-in-the-Loop**: Slack-based approval workflows for all CRM updates
- **Error Recovery**: Graceful handling of failures with retry mechanisms

### 🎨 Clean Integration
- **Slack Bot**: Natural language queries and approval workflows
- **Type Safety**: Pydantic models for robust state management
- **Professional Output**: Executive-ready reports and summaries
- **Audit Trail**: Complete tracking of all changes and decisions

## 📁 Project Structure

```
crm_assistant/
├── crm_agent/                     # CRM agent entry points
│   ├── __init__.py               # Main CRM module
│   ├── main.py                   # Simple CRM agent
│   └── coordinator_main.py       # Full coordinator agent
├── crm_fastmcp_server/           # CRM MCP server
│   ├── __init__.py
│   ├── server.py                 # FastMCP server with CRM tools
│   └── __main__.py               # Server entry point
├── jira_agent/                   # Extended agent framework
│   ├── core/
│   │   ├── state_models.py       # CRM session state models
│   │   └── factory.py            # Agent registry with CRM agents
│   ├── agents/
│   │   ├── specialized/
│   │   │   └── crm_agents.py     # CRM-specific agents
│   │   └── workflows/
│   │       └── crm_enrichment.py # CRM workflow implementations
│   └── coordination/
│       └── crm_coordinator.py    # CRM coordinator agent
├── tests/
│   └── test_crm_system.py        # CRM system tests
├── docs/
│   └── CRM_CONVERSION.md         # Detailed conversion guide
├── requirements.txt              # Updated with CRM dependencies
└── CRM_README.md                 # This file
```

## 🔍 Available Tools & Capabilities

### HubSpot Integration (Official MCP Server)
- `query_hubspot_crm()` - Natural language queries to HubSpot
- `get_hubspot_contact()` - Retrieve contact details
- `get_hubspot_company()` - Retrieve company information

### Web & External Data
- `web_search()` - General web search using SERP APIs
- `fetch_url()` - Content extraction from websites
- `linkedin_company_lookup()` - LinkedIn company metadata
- `get_company_metadata()` - Structured business directory data
- `verify_email()` - Email deliverability validation

### Slack Integration
- `notify_slack()` - Send notifications to Slack channels
- `await_human_approval()` - Interactive approval workflows

## 🎭 Agent Personalities & Specializations

### Simple CRM Agent (Default)
**Best for**: First-time users, basic enrichment, general exploration
- Automatically handles common CRM tasks
- Provides helpful suggestions and guidance
- Handles basic enrichment operations

### CRM System Coordinator (Advanced)
**Best for**: Complex workflows, multi-step operations, enterprise use
- Intelligent request routing to specialized agents
- Orchestrates complex multi-agent workflows
- Handles ambiguous requests with clarification

### Specialized Agents
Each agent has deep expertise in their domain:
- **QueryBuilderAgent**: Expert in crafting targeted search strategies
- **WebRetrieverAgent**: Specialized in web content extraction and analysis
- **SummarizerAgent**: Expert in data normalization and conflict resolution
- **CRMUpdaterAgent**: Specialized in safe CRM updates with approval workflows

## 📊 Example Use Cases

### 1. Contact Enrichment
```
User: "Enrich john@acme.com"
→ Coordinator routes to CRMEnrichmentPipeline
→ 8-step process: Gap detection → Query planning → Parallel retrieval → 
   Synthesis → Entity mapping → Proposal → Approval → Updates
→ Result: Enriched contact with industry, company size, phone, etc.
```

### 2. Company Data Enhancement
```
User: "What can we learn about acme.com?"
→ Coordinator routes to CRMQuickLookup + CRMEnrichmentPipeline
→ Loads existing data → Identifies gaps → Enriches from multiple sources
→ Result: Complete company profile with industry, size, technology, competitors
```

### 3. Data Quality Assessment
```
User: "Check our CRM data quality"
→ Coordinator routes to CRMDataQualityWorkflow
→ Analyzes all records → Identifies systematic issues → Provides recommendations
→ Result: Quality report with specific improvement actions
```

## 🚦 Getting Started Guide

### Step 1: Basic Setup
1. Configure HubSpot app and OAuth tokens
2. Run `adk run crm_agent`
3. Try: `"What do we know about [contact-email]?"`

### Step 2: Enrichment Operations
1. Try: `"Enrich the contact john@example.com"`
2. Try: `"Find missing company information for acme.com"`
3. Review proposed changes in Slack

### Step 3: Advanced Workflows
1. Switch to: `adk run crm_agent.coordinator_main`
2. Try: `"Perform a comprehensive data quality assessment"`
3. Try: `"Enrich all contacts missing industry information"`

## 🔧 Configuration

### HubSpot App Setup
Create a HubSpot app with these settings:
- **Distribution**: Marketplace
- **User Level**: True
- **Required Scopes**: `oauth`, `crm.objects.contacts.read`, `crm.objects.companies.read`
- **Optional Scopes**: `crm.objects.deals.read`, `crm.objects.products.read`, etc.

### Environment Configuration
```bash
# Required
HUBSPOT_CLIENT_ID=your-client-id
HUBSPOT_ACCESS_TOKEN=your-access-token

# Optional but recommended
SEARCH_API_KEY=your-serp-api-key
SLACK_BOT_TOKEN=your-slack-token
EMAIL_VERIFY_API_KEY=your-email-verification-key
PRIVACY_MODE=true
```

## 🧪 Testing

```bash
# Run CRM-specific tests
python -m pytest tests/test_crm_system.py -v

# Test individual components
python -m pytest tests/test_crm_system.py::TestCRMSessionState -v

# Integration tests
python -m pytest tests/test_crm_system.py::TestCRMIntegration -v
```

## 🤝 Contributing

This system is designed to be extensible:

1. **New Data Sources**: Add retrieval agents in `jira_agent/agents/specialized/crm_agents.py`
2. **New Workflows**: Create workflows in `jira_agent/agents/workflows/crm_enrichment.py`
3. **New Tools**: Add MCP tools in `crm_fastmcp_server/server.py`
4. **Register**: Add to factory in `jira_agent/core/factory.py`

## 📚 Documentation

- **[CRM Conversion Guide](docs/CRM_CONVERSION.md)** - Complete implementation details
- **[Multi-Agent Architecture](docs/MULTI_AGENT_ARCHITECTURE.md)** - Core architectural patterns
- **[HubSpot MCP Integration](https://developers.hubspot.com/docs/api/mcp-server)** - Official HubSpot documentation

## 🐛 Troubleshooting

### Common Issues

**HubSpot authentication errors?**
- Verify OAuth tokens are current and have required scopes
- Check HubSpot app configuration matches requirements
- Ensure user has proper permissions in HubSpot

**Enrichment not finding data?**
- Configure SEARCH_API_KEY for web search functionality
- Check rate limits on external APIs
- Verify company domains and contact emails are valid

**Slack approvals not working?**
- Configure SLACK_BOT_TOKEN and app permissions
- Ensure bot is added to the target channel
- Check Slack app has necessary OAuth scopes

### Getting Help

1. **Check the logs**: ADK provides detailed logging
2. **Try the simple agent first**: `adk run crm_agent` for basic functionality
3. **Use built-in help**: Ask agents "what can you do?" or "help me get started"

## 🎯 Next Steps

After getting familiar with basic functionality:

1. **Explore Advanced Workflows**: Try the coordinator for complex operations
2. **Customize for Your Data**: Modify tools and agents for your specific needs
3. **Build Custom Integrations**: Extend the MCP server for additional data sources
4. **Scale Operations**: Use batch processing for large-scale data enrichment

## 📄 License

This project demonstrates advanced multi-agent patterns using Google ADK. Refer to individual component licenses for specific terms.

---

**Built with ❤️ using Google ADK, HubSpot MCP Server, and the power of multi-agent collaboration**

*Ready to transform your CRM data management? Start with `adk run crm_agent` and discover what your customer data has been trying to tell you!*
