# Jira Multi-Agent System

A comprehensive multi-agent system for analyzing Jira data using Google's Agent Development Kit (ADK). This system implements advanced multi-agent patterns including Coordinator/Dispatcher, Sequential Pipeline, and Parallel Fan-Out/Gather for intelligent Jira data analysis and management.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Conda environment management
- Google ADK framework
- Jira CSV export files

### Installation

1. **Clone and Setup Environment**
   ```bash
   git clone <repository-url>
   cd yaml
   conda create -n adk python=3.9
   conda activate adk
   pip install -r requirements.txt
   ```

2. **Place Jira Data**
   ```bash
   # Export your Jira data as CSV and place in:
   docs/jira_exports/Jira_YYYY-MM-DD_HH_MM_SS-TZ.csv
   
   # The system automatically finds and loads the most recent CSV file
   ```

3. **Run the Agent**
   ```bash
   # Simple agent (recommended for beginners)
   adk run jira_agent
   
   # Multi-agent coordinator (advanced features)
   adk run jira_agent.coordinator_main
   
   # Web interface
   adk web jira_agent
   ```

## 🎯 What You Can Do

### Immediate Capabilities
- **📊 Data Analysis**: Status breakdowns, assignee workloads, priority distributions
- **🔍 Smart Search**: Find issues by keywords, status, assignee, or custom criteria
- **📈 Project Health**: Risk assessments, stale issue detection, blocked item analysis
- **🔧 Data Quality**: Missing field detection, automated fix suggestions
- **📋 Professional Reports**: Executive summaries, team dashboards, comprehensive overviews

### Example Queries
```bash
# After running adk run jira_agent:
"Show me all unassigned issues"
"Generate a project health report"
"Find issues that haven't been updated in 30 days"
"What's the status breakdown for this project?"
"Create an executive summary report"
"Find all blocked issues"
"Analyze data quality issues"
```

## 🏗️ Architecture Overview

This system implements a sophisticated multi-agent architecture with three main layers:

### 1. **Coordinator Layer**
- **JiraCoordinator**: Central routing agent that delegates tasks to specialized agents
- **ClarificationAgent**: Handles ambiguous requests by asking clarifying questions

### 2. **Specialized Agents**
- **QueryAgent**: Data queries, searches, and issue lookups
- **AnalysisAgent**: Metrics calculation, breakdowns, and insights
- **ReportingAgent**: Professional reports and summaries
- **DataQualityAgent**: Data validation and cleanup operations

### 3. **Workflow Agents** (Advanced)
- **RiskAssessmentPipeline**: Sequential workflow for comprehensive risk analysis
- **DataQualityWorkflow**: Multi-step data improvement with human approval
- **ProjectHealthDashboard**: Parallel data gathering with comprehensive reporting

## 🛠️ Key Features

### ✨ Automatic Data Loading
- **Smart Discovery**: Automatically finds and loads the most recent Jira CSV file
- **Caching**: Uses Parquet files for fast subsequent loads
- **Zero Configuration**: No need to specify file paths manually

### 🧠 Intelligent Agent Routing
- **Context-Aware**: Understands user intent and routes to the best agent
- **Fallback Handling**: Uses ClarificationAgent for ambiguous requests
- **State Management**: Agents share data through typed session state

### 🔧 Advanced Capabilities
- **Multi-Step Workflows**: Complex operations using Sequential and Parallel agents
- **Human-in-the-Loop**: Approval workflows for data modifications
- **Error Recovery**: Graceful handling of failures with helpful suggestions

### 🎨 Clean Output
- **Warning Suppression**: Clean interface without experimental feature warnings
- **Professional Formatting**: Well-structured reports and analysis
- **Actionable Insights**: Clear recommendations and next steps

## 📁 Project Structure

```
jira_agent/                 # Main agent system
├── core/                   # Base classes and factories
│   ├── base_agents.py     # Common agent base classes
│   ├── factory.py         # Agent registry and creation
│   └── state_models.py    # Typed state management
├── agents/                 # Specialized agent implementations
│   ├── specialized/       # Domain-specific agents
│   └── workflows/         # Multi-step workflow agents
├── coordination/           # Main coordination layer
│   ├── coordinator.py     # Central coordinator agent
│   └── main.py           # Simple agent entry point
├── utils/                  # Utilities and helpers
│   ├── warning_suppression.py  # Clean output management
│   └── startup.py         # Initialization utilities
└── configs/               # Configuration files

jira_fastmcp_server/       # MCP server with enhanced tools
├── server.py             # FastMCP server setup
└── tools.py              # 15+ specialized Jira analysis tools

docs/                      # Documentation and data
├── jira_exports/         # Place your Jira CSV files here
├── PHASED_DEVELOPMENT_STRATEGY.md  # Development roadmap
└── MULTI_AGENT_ARCHITECTURE.md     # Detailed architecture guide

tests/                     # Test suite
└── test_enhanced_system.py  # System validation tests
```

## 🔍 Available Tools & Capabilities

### Core Data Operations
- `load_jira_csv()` - Auto-load most recent CSV file
- `list_jira_issues()` - Browse issues with pagination
- `get_issue_details()` - Detailed issue information
- `search_issues()` - Flexible search across fields

### Analysis & Reporting
- `summarize_jira_csv()` - High-level project overview
- `get_jira_status_breakdown()` - Status distribution analysis
- `get_jira_assignee_workload()` - Team workload analysis
- `get_status_summary()` - Quick status counts
- `get_assignee_summary()` - Assignee distribution

### Risk & Quality Management
- `find_stale_issues_in_project()` - Identify neglected issues
- `find_blocked_issues_in_project()` - Detect blocked work
- `find_due_soon_issues_in_project()` - Upcoming deadlines
- `find_unassigned_issues_in_project()` - Work without owners
- `find_issues_with_missing_fields()` - Data quality audit
- `suggest_data_fixes()` - Automated improvement recommendations
- `apply_bulk_jira_updates()` - Batch data modifications (with approval)

## 🎭 Agent Personalities & Specializations

### Simple Agent (Default)
**Best for**: First-time users, basic queries, general exploration
- Automatically loads data on startup
- Provides helpful suggestions
- Handles all basic operations

### QueryAgent
**Best for**: Finding specific issues, complex searches
- Optimized for data retrieval
- Advanced search capabilities
- Saves results for other agents

### AnalysisAgent  
**Best for**: Understanding project metrics, identifying trends
- Statistical analysis
- Breakdown reports
- Pattern identification

### ReportingAgent
**Best for**: Professional presentations, executive summaries
- Executive-ready formatting
- Comprehensive overviews
- Actionable insights

### Coordinator (Advanced)
**Best for**: Complex workflows, multi-step operations
- Intelligent request routing
- Orchestrates multiple agents
- Handles ambiguous requests

## 📊 Example Use Cases

### 1. Project Health Check
```
User: "How is the project doing?"
→ Coordinator routes to AnalysisAgent
→ Generates comprehensive health metrics
→ Provides risk assessment and recommendations
```

### 2. Risk Assessment
```
User: "Show me project risks"
→ Coordinator routes to RiskAssessmentPipeline
→ Sequential agents find: stale issues → blocked issues → due soon
→ Synthesizes comprehensive risk report with priorities
```

### 3. Data Quality Audit
```
User: "Clean up our data"
→ Coordinator routes to DataQualityWorkflow
→ Identifies issues → suggests fixes → awaits approval → applies changes
→ Provides before/after quality metrics
```

## 🚦 Getting Started Guide

### Step 1: Basic Exploration
1. Run `adk run jira_agent`
2. Try: `"list the first 10 issues"`
3. Try: `"show me a project summary"`

### Step 2: Analysis & Insights
1. Try: `"what's the status breakdown?"`
2. Try: `"show me assignee workloads"`
3. Try: `"find all unassigned issues"`

### Step 3: Advanced Operations
1. Switch to: `adk run jira_agent.coordinator_main`
2. Try: `"perform a risk assessment"`
3. Try: `"generate an executive report"`

## 🔧 Configuration

### Environment Variables
```bash
# Optional: Customize default behavior
export JIRA_CSV_PATH="path/to/your/csv"
export ADK_LOG_LEVEL="INFO"
```

### Agent Configuration
Agents can be customized through the factory pattern in `jira_agent/core/factory.py`. The system uses programmatic configuration (Python) rather than YAML for better IDE support and type safety.

## 🧪 Testing

```bash
# Run the test suite
python -m pytest tests/

# Validate system components
python tests/test_enhanced_system.py

# Test specific agents
adk run jira_agent.coordination.main
# Then try the example queries from the development strategy
```

## 🤝 Contributing

This system is designed to be extensible. To add new capabilities:

1. **New Tools**: Add functions to `jira_fastmcp_server/tools.py`
2. **New Agents**: Create specialized agents in `jira_agent/agents/specialized/`
3. **New Workflows**: Build multi-step processes in `jira_agent/agents/workflows/`
4. **Register**: Add to the factory in `jira_agent/core/factory.py`

See `docs/MULTI_AGENT_ARCHITECTURE.md` for detailed implementation patterns.

## 📚 Documentation

- **[Architecture Guide](docs/MULTI_AGENT_ARCHITECTURE.md)** - Detailed system design and patterns
- **[Development Strategy](docs/PHASED_DEVELOPMENT_STRATEGY.md)** - Implementation roadmap and phases
- **[API Reference](jira_fastmcp_server/tools.py)** - All available tools and functions

## 🐛 Troubleshooting

### Common Issues

**Data not loading?**
- Ensure CSV files are in `docs/jira_exports/`
- Check file naming: `Jira_YYYY-MM-DD_*.csv`
- Try: `list_available_jira_csvs()` to see available files

**Agent not responding?**
- Check ADK environment: `conda activate adk`
- Verify installation: `pip install -r requirements.txt`
- Check logs in temp directory (path shown at startup)

**Warnings appearing?**
- Should be automatically suppressed
- If persisting, check `jira_agent/utils/warning_suppression.py`

### Getting Help

1. **Check the logs**: ADK provides detailed logging (path shown at startup)
2. **Try the simple agent first**: `adk run jira_agent` for basic functionality
3. **Use built-in help**: Ask agents "what can you do?" or "help me get started"

## 🎯 Next Steps

After getting familiar with the basic functionality:

1. **Explore Advanced Agents**: Try the coordinator for complex workflows
2. **Customize for Your Data**: Modify tools in `jira_fastmcp_server/tools.py`
3. **Build New Workflows**: Create domain-specific multi-agent processes
4. **Integrate with Your Systems**: Extend the MCP server for your tools

## 📄 License

This project demonstrates advanced multi-agent patterns using Google ADK. Refer to individual component licenses for specific terms.

---

**Built with ❤️ using Google ADK and the power of multi-agent collaboration**

*Ready to transform your Jira data analysis? Start with `adk run jira_agent` and discover what your data has been trying to tell you!*
