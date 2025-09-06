# CRM Cleanup & Gap Analysis Agent 🧹

An intelligent agent that helps clean up duplicate information/contacts and identifies the biggest gaps in your HubSpot CRM data.

## Features

### 🔍 Duplicate Detection
- **Contact Duplicates**: Identifies potential duplicate contacts using:
  - Exact email matching (highest confidence)
  - Fuzzy name matching with configurable similarity threshold
  - Combined scoring for comprehensive analysis
- **Company Duplicates**: Finds duplicate companies through:
  - Exact domain matching (highest confidence) 
  - Company name similarity analysis
  - Cross-reference validation

### 📊 Gap Analysis
- **Critical Gaps**: Missing essential fields that impact business operations
- **Moderate Gaps**: Important fields that should be filled for better insights
- **Minor Gaps**: Nice-to-have fields for complete profiles
- **Smart Prioritization**: Importance scoring based on field criticality

### 🎯 Intelligent Recommendations
- **Actionable Insights**: Specific steps to improve data quality
- **Data Source Suggestions**: Where to find missing information
- **Time Estimation**: Realistic cleanup time estimates
- **Prioritized Action Plans**: Phase-based cleanup strategies

## Quick Start

### 1. Start the MCP Server
```bash
python mcp_wrapper/simple_hubspot_server.py
```

### 2. Run the Cleanup Analysis
```bash
# Full interactive analysis
python crm_cleanup_demo.py

# Quick analysis (100 records each)
python crm_cleanup_demo.py --quick

# Direct agent usage
python crm_cleanup_agent.py
```

## Usage Examples

### Interactive Demo
The demo script provides a user-friendly interface:
```bash
python crm_cleanup_demo.py
```

Features:
- Connection testing
- Configurable analysis limits
- Detailed duplicate analysis
- Gap analysis with recommendations
- Export to file
- Prioritized action plans

### Direct Agent Usage
For programmatic access:
```python
from crm_cleanup_agent import CRMCleanupAgent

# Initialize agent
agent = CRMCleanupAgent()

# Fetch data
contacts = agent.get_all_contacts(limit=500)
companies = agent.get_all_companies(limit=500)

# Generate comprehensive report
report = agent.generate_cleanup_report(contacts, companies)

# Print formatted report
agent.print_cleanup_report(report)
```

## Configuration Options

### Similarity Threshold
Adjust the similarity threshold for duplicate detection:
```python
agent.similarity_threshold = 0.8  # Default: 80% similarity
```

### Critical Fields
Customize which fields are considered critical:
```python
agent.critical_fields = {
    'contact': ['firstname', 'lastname', 'email', 'phone', 'jobtitle', 'company'],
    'company': ['name', 'domain', 'industry', 'city', 'state', 'country', 'phone', 'website']
}
```

## Report Structure

### Duplicate Analysis
- **Contact Duplicates**: Groups of similar contacts with match details
- **Company Duplicates**: Groups of similar companies with match details
- **Similarity Scores**: Confidence levels for each duplicate group
- **Recommended Actions**: Merge, review, or manual inspection

### Gap Analysis
- **Critical Gaps**: High-impact missing fields (>80% importance)
- **Moderate Gaps**: Medium-impact missing fields (50-80% importance)  
- **Minor Gaps**: Low-impact missing fields (<50% importance)
- **Data Sources**: Suggested sources for filling gaps

### Quality Metrics
- **Data Quality Score**: Overall CRM health percentage
- **Completeness Analysis**: Field-by-field completeness stats
- **Improvement Potential**: Estimated quality gains from cleanup

## Sample Output

```
🧹 CRM CLEANUP & GAP ANALYSIS REPORT
================================================================================

📊 ANALYSIS SUMMARY
   Analysis Date: 2024-01-15 14:30:25
   Contacts Analyzed: 1,250
   Companies Analyzed: 450
   Data Quality Score: 72.5%

🔍 DUPLICATE DETECTION
   Potential Duplicate Contacts: 23
   Potential Duplicate Companies: 8

👥 DUPLICATE CONTACTS (23)
   1. John Smith (john.smith@example.com)
      Duplicates: 2 records
      Match Type: email
      Similarity: 100.0%
      Action: merge_records

🏢 DUPLICATE COMPANIES (8)
   1. Acme Corporation (acme.com)
      Duplicates: 3 records
      Match Type: domain
      Similarity: 100.0%
      Action: merge_records

📋 DATA GAPS ANALYSIS
   Critical Gaps: 45
   Moderate Gaps: 120
   Minor Gaps: 230
   Total Gaps: 395

🚨 CRITICAL GAPS (45)
   1. Jane Doe (contact)
      Missing: email, company
      Importance: 85.0%
      Sources: LinkedIn, Company website

🎯 PRIORITY ACTIONS
   1. Merge 23 groups of duplicate contacts
   2. Merge 8 groups of duplicate companies
   3. Fill 45 critical data gaps

⏱️  ESTIMATED CLEANUP TIME: 3h 25m
```

## Advanced Features

### Export Recommendations
Generate detailed cleanup recommendations file:
```python
# In demo mode, choose option 3 to export
# Creates: crm_cleanup_recommendations_YYYYMMDD_HHMMSS.txt
```

### Action Plan Generation
Get a phase-based cleanup strategy:
- **Phase 1**: Quick wins (high-confidence duplicates)
- **Phase 2**: Systematic cleanup (moderate-confidence items)
- **Phase 3**: Optimization (remaining gaps and processes)

### Batch Processing
For large datasets, the agent handles:
- Automatic batching of API requests
- Memory-efficient processing
- Progress tracking and logging

## Integration

### With Existing CRM Workflows
The agent can be integrated into existing CRM workflows:
```python
# Custom workflow integration
def weekly_cleanup_check():
    agent = CRMCleanupAgent()
    report = agent.generate_cleanup_report(
        contacts=get_recent_contacts(),
        companies=get_recent_companies()
    )
    
    if report.data_quality_score < 0.8:
        send_cleanup_alert(report)
```

### With Multi-Agent Systems
Compatible with the existing CRM agent architecture:
```python
from crm_agent.agents.specialized.crm_agents import CRMDataQualityAgent
from crm_cleanup_agent import CRMCleanupAgent

# Combine with existing quality agents
quality_agent = CRMDataQualityAgent()
cleanup_agent = CRMCleanupAgent()
```

## Error Handling

The agent includes comprehensive error handling:
- **Connection Issues**: Graceful MCP server connection failures
- **API Limits**: Automatic batching and rate limiting
- **Data Validation**: Robust handling of malformed records
- **Memory Management**: Efficient processing of large datasets

## Performance

### Optimization Features
- **Batch Processing**: Efficient API usage
- **Smart Caching**: Avoid redundant calculations
- **Configurable Limits**: Balance speed vs. completeness
- **Progress Tracking**: Real-time analysis feedback

### Benchmarks
- **Small Dataset** (100 records): ~30 seconds
- **Medium Dataset** (500 records): ~2 minutes
- **Large Dataset** (1000+ records): ~5-10 minutes

## Requirements

- Python 3.7+
- HubSpot Private App Access Token
- Running MCP server (`mcp_wrapper/simple_hubspot_server.py`)
- Dependencies: `requests`, `difflib` (built-in)

## Troubleshooting

### Common Issues

1. **"Cannot connect to MCP server"**
   ```bash
   # Start the MCP server first
   python mcp_wrapper/simple_hubspot_server.py
   ```

2. **"No data retrieved"**
   - Check HubSpot access token in `.env` file
   - Verify HubSpot API permissions

3. **"Analysis taking too long"**
   - Reduce the analysis limits
   - Use `--quick` mode for initial assessment

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

The cleanup agent is designed to be extensible:
- **Custom Matching Algorithms**: Add new duplicate detection methods
- **Additional Data Sources**: Integrate external enrichment APIs
- **Custom Gap Analysis**: Define industry-specific critical fields
- **Enhanced Reporting**: Add new visualization and export formats

## License

This project follows the same license as the parent CRM assistant project.
