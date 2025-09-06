# 🏢 Company Intelligence System

A comprehensive company analysis system that helps you ask questions about companies and get detailed insights including all associated contacts and deals.

## 🎯 What It Does

When you ask about a company, the system will:

1. **🔍 Find the Company** - Search HubSpot by name, domain, or partial matches
2. **📊 Gather Complete Data** - Retrieve all company information, contacts, and deals
3. **🧠 Analyze Relationships** - Understand contact roles and deal pipeline
4. **📈 Generate Insights** - Provide strategic recommendations and next steps
5. **📋 Present Everything** - Give you a comprehensive report with actionable intelligence

## 🚀 Quick Start

### 1. Setup

```bash
# 1. Configure your HubSpot access token
echo "PRIVATE_APP_ACCESS_TOKEN=your_hubspot_token_here" > .env

# 2. Start the MCP server
python mcp_wrapper/simple_hubspot_server.py

# 3. Test the functionality
python test_company_intelligence.py
```

### 2. Try the Interactive Demo

```bash
python company_intelligence_demo.py
```

### 3. Example Queries

- "Tell me everything about HubSpot"
- "What do we know about microsoft.com?"
- "Find information about Salesforce"
- "Analyze our relationship with Apple Inc"

## 🔧 Available Tools

### Core Company Analysis Tools

| Tool | Purpose | Example Usage |
|------|---------|---------------|
| `search_companies` | Find companies by name/domain | Search for "HubSpot" or "hubspot.com" |
| `get_company_details` | Get comprehensive company info + contacts | Get all data for company ID 12345 |
| `generate_company_report` | Full analysis with insights | Complete report for salesforce.com |

### What Each Tool Provides

#### 🔍 `search_companies`
- Searches by company name or domain
- Returns matching companies with basic info
- Supports partial matches and fuzzy search

#### 📋 `get_company_details` 
- Complete company profile from HubSpot
- All associated contacts with roles and contact info
- All associated deals with stages and values
- Relationship mapping between entities

#### 📊 `generate_company_report`
- Everything from `get_company_details` PLUS:
- Deal analytics (pipeline value, win rates, trends)
- Data quality assessment and completeness scores
- Strategic insights and recommendations
- Contact role analysis and key decision makers
- Engagement history and activity timeline

## 📖 Usage Examples

### Using the MCP Server Directly

```bash
# 1. Search for companies
curl -X POST http://localhost:8081/mcp \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "call_tool",
    "params": {
      "name": "search_companies",
      "arguments": {"query": "HubSpot", "limit": 5}
    }
  }'

# 2. Get detailed company analysis
curl -X POST http://localhost:8081/mcp \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "call_tool",
    "params": {
      "name": "generate_company_report",
      "arguments": {"domain": "hubspot.com"}
    }
  }'
```

### Using the Python Agent

```python
from crm_agent.agents.specialized.company_intelligence_agent import create_company_intelligence_agent

# Create the agent
agent = create_company_intelligence_agent()

# The agent will use the MCP tools to provide comprehensive company analysis
# when asked questions like "Tell me about HubSpot" or "What do we know about Salesforce?"
```

## 📊 Report Structure

When you generate a company report, you get:

```
🏢 Company Analysis: [Company Name]
├── 📋 Executive Summary
├── 🏗️ Company Profile
│   ├── Basic Info (name, domain, industry)
│   ├── Location & Size
│   ├── Contact Information
│   └── Business Details
├── 👥 Key Contacts (X total)
│   ├── Decision Makers
│   ├── Contact Information
│   └── Relationship History
├── 💼 Deal Intelligence
│   ├── Active Pipeline
│   ├── Historical Performance
│   ├── Revenue Analysis
│   └── Sales Cycle Insights
├── 📊 Data Quality Assessment
│   ├── Completeness Score
│   ├── Missing Fields
│   └── Last Updated
├── 🎯 Strategic Recommendations
│   ├── Engagement Opportunities
│   ├── Next Steps
│   └── Risk Assessment
└── 🔍 Research Opportunities
    ├── Data Enrichment Suggestions
    └── External Research Needs
```

## 🛠️ Technical Architecture

### MCP Server (`mcp_wrapper/simple_hubspot_server.py`)
- Direct HubSpot API integration
- Company search and retrieval
- Contact and deal association mapping
- Report generation with analytics

### Company Intelligence Agent
- Specialized agent for company analysis
- Structured workflow for comprehensive insights
- Integration with external data sources
- Intelligent presentation of findings

### Key Features
- **Smart Search**: Handles partial matches, domains, and company names
- **Deep Analysis**: Goes beyond basic data to provide insights
- **Relationship Mapping**: Understands connections between companies, contacts, and deals
- **Data Quality**: Assesses completeness and suggests improvements
- **Strategic Insights**: Provides actionable recommendations

## 🔒 Security & Configuration

### Required HubSpot Scopes
Your HubSpot private app needs these scopes:
- `crm.objects.companies.read`
- `crm.objects.contacts.read` 
- `crm.objects.deals.read`
- `crm.associations.read`

### Environment Configuration
```bash
# .env file
PRIVATE_APP_ACCESS_TOKEN=your_hubspot_private_app_token
```

### Rate Limiting
- The system respects HubSpot API rate limits
- Implements intelligent batching for large datasets
- Limits contact/deal retrieval to prevent timeouts

## 🧪 Testing

```bash
# Test the MCP server endpoints
python test_company_intelligence.py

# Interactive testing
python company_intelligence_demo.py

# Check server health
curl http://localhost:8081/health
```

## 🔍 Troubleshooting

### Common Issues

1. **Server won't start**
   - Check if port 8081 is available
   - Verify HubSpot token in .env file

2. **No companies found**
   - Try different search terms
   - Check if companies exist in your HubSpot account
   - Verify API token has correct scopes

3. **Incomplete data**
   - This is normal - the system will highlight missing fields
   - Use the enrichment suggestions to improve data quality

### Debug Mode

```bash
# Start server with debug logging
python mcp_wrapper/simple_hubspot_server.py --debug
```

## 🚀 Next Steps

1. **Try the Demo**: Run `python company_intelligence_demo.py`
2. **Test Your Data**: Use real company names from your HubSpot account
3. **Integrate**: Use the MCP tools in your own applications
4. **Extend**: Add custom analysis logic or external data sources

## 💡 Pro Tips

- **Use specific company names** for best search results
- **Try domain-based searches** when company names are unclear  
- **Review data quality scores** to identify enrichment opportunities
- **Focus on the strategic recommendations** for actionable insights
- **Use the contact intelligence** to identify key decision makers

---

## 🤝 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify your HubSpot configuration
3. Test with the provided demo scripts
4. Review the server logs for detailed error information

**Happy company analyzing!** 🎉
