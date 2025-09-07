# Project Manager Agent

## Overview

The Project Manager Agent is an A2A (Agent-to-Agent) compliant orchestration agent built on the ADK framework that coordinates complex CRM tasks by intelligently routing work to specialized CRM agents. It acts as a high-level project coordinator that can break down complex goals into actionable tasks and manage their execution.

## Key Features

### 🎯 Intelligent Goal Decomposition
- **Natural Language Processing**: Understands complex, high-level goals in plain English
- **Task Planning**: Automatically breaks down goals into specific, actionable tasks
- **Dependency Management**: Handles task dependencies and execution order
- **Context Awareness**: Uses provided context to optimize task planning

### 🤖 A2A Agent Coordination
- **CRM Agent Integration**: Coordinates with all specialized CRM agents
- **Dynamic Agent Selection**: Chooses the right agent for each task type
- **Error Handling**: Manages failures and retries across agent interactions
- **Progress Monitoring**: Tracks execution status across all coordinated agents

### 📊 Project Management
- **Real-time Progress Tracking**: Monitors task completion and project status
- **Comprehensive Reporting**: Provides detailed execution summaries
- **Status Updates**: Real-time feedback during long-running operations
- **Result Aggregation**: Combines results from multiple agents into coherent reports

## Supported Goal Types

### 1. Geographic Company Discovery & Enrichment
```
"Find all golf clubs in Arizona and enrich their records"
```
- Searches for companies by location and type
- Enriches missing data fields
- Identifies management company relationships

### 2. Data Quality Analysis & Enrichment
```
"Review HubSpot data and enrich missing fields for top prospects"
```
- Analyzes current data quality
- Identifies enrichment opportunities
- Systematically fills missing information

### 3. Single Company Deep Analysis
```
"Analyze The Golf Club at Mansion Ridge and set up proper management company relationship"
```
- Comprehensive company intelligence gathering
- Management company identification
- Parent company relationship setup

### 4. Industry-Specific Workflows
```
"Identify management companies for all golf courses in our CRM"
```
- Industry-focused data enrichment
- Specialized relationship mapping
- Bulk processing capabilities

## Architecture

### ADK Framework Integration

The Project Manager Agent is built on the Google ADK framework, following the same patterns as the CRM Agent:

```python
# ADK-compliant agent structure
from google.adk.agents import LlmAgent

class ProjectManagerAgent(LlmAgent):
    def __init__(self, **kwargs):
        super().__init__(
            name="ProjectManagerAgent",
            model='gemini-2.5-flash',
            instruction="...",
            **kwargs
        )
```

### A2A Communication

The agent uses the CRM Agent Registry for seamless integration:

```python
from crm_agent.core.factory import crm_agent_registry

# Register available agents
self.orchestrator.register_agent("company_intelligence", 
    lambda: crm_agent_registry.create_agent("company_intelligence"))
```

## Usage

### Basic Usage

```python
from project_manager_agent import create_project_manager

# Create the agent
pm_agent = create_project_manager()

# Execute a goal
result = await pm_agent.execute_goal(
    "Find all golf clubs in Arizona and enrich their records"
)

print(f"Status: {result['status']}")
print(f"Progress: {result['progress']}%")
print(f"Tasks: {result['completed_tasks']}/{result['total_tasks']}")
```

### With Context

```python
# Provide additional context
context = {
    "company_domain": "mansionridgegc.com",
    "current_data": {
        "management_company": "",
        "description": ""
    }
}

result = await pm_agent.execute_goal(
    "Analyze The Golf Club at Mansion Ridge",
    context=context
)
```

### ADK Integration

```python
# For ADK discovery
from project_manager_agent.agent import root_agent

# The agent is automatically available to ADK
agent = root_agent
```

## Response Format

### Success Response
```json
{
    "project_id": "abc123",
    "status": "completed",
    "progress": 100.0,
    "total_tasks": 3,
    "completed_tasks": 3,
    "failed_tasks": 0,
    "task_results": {
        "search_task": {
            "companies": [...],
            "total": 5
        },
        "enrich_task": {
            "enriched_companies": 5,
            "fields_updated": ["description", "management_company"]
        }
    }
}
```

### Partial Success Response
```json
{
    "project_id": "def456", 
    "status": "failed",
    "progress": 66.7,
    "total_tasks": 3,
    "completed_tasks": 2,
    "failed_tasks": 1,
    "task_results": {
        "search_task": {"companies": [...]},
        "enrich_task": {"error": "Agent timeout"}
    }
}
```

## Coordinated Agents

The Project Manager Agent coordinates with these specialized CRM agents:

| Agent Type | Purpose | Example Usage |
|------------|---------|---------------|
| `company_intelligence` | Comprehensive company analysis | Company deep-dive research |
| `contact_intelligence` | Contact analysis and mapping | Relationship intelligence |
| `crm_enrichment` | Web-based data enrichment | Fill missing company data |
| `company_management_enrichment` | Golf course management identification | Set parent company relationships |
| `field_enrichment_manager` | Systematic field enrichment | Bulk data quality improvement |

## Testing

### Run Basic Tests
```bash
python tests/test_project_manager_mansion_ridge.py
```

### Run Demo
```bash
python demos/demo_project_manager.py
```

## Test Results - Mansion Ridge Example

Using the exact company data from your HubSpot screenshot:

```
📋 Current Company Data:
   name: The Golf Club at Mansion Ridge ✅ Present
   domain: mansionridgegc.com ✅ Present
   management_company:  ❌ Missing
   parent_company:  ❌ Missing

🎯 Goal: Complete analysis and enrichment of Mansion Ridge

📊 Project Results:
   Status: completed
   Progress: 100.0%
   Completed Tasks: 2/2

📝 Task Execution Details:
   ✅ Management Company: Troon (ID: hubspot_31895)
   ✅ CORRECT: Troon identified as expected!
```

## Integration Examples

### With CRM Workflows

```python
# Create enrichment pipeline
from project_manager_agent import create_project_manager

pm_agent = create_project_manager()

# Execute complex multi-step goal
goal = """
Find all golf clubs in Arizona, enrich their basic information,
identify management companies, and generate a summary report
"""

result = await pm_agent.execute_goal(goal)
```

### Batch Processing

```python
goals = [
    "Analyze The Golf Club at Mansion Ridge",
    "Find golf clubs in Florida and set management companies",
    "Review data quality for software companies"
]

results = []
for goal in goals:
    result = await pm_agent.execute_goal(goal)
    results.append(result)
```

## Key Advantages

### 🚀 **Simplified Complex Operations**
- Transform complex multi-step processes into simple goal statements
- No need to understand individual agent capabilities or coordination

### 🔄 **Intelligent Orchestration** 
- Automatic task dependency resolution
- Optimal agent selection for each task type
- Error recovery and retry logic

### 📊 **Comprehensive Monitoring**
- Real-time progress updates
- Detailed execution logs
- Aggregated result reporting

### 🤖 **A2A Compliance**
- Seamless integration with existing CRM agents
- Follows ADK framework patterns
- Maintains consistency with CRM Agent architecture

## Future Enhancements

### Planned Features
- [ ] **Parallel Task Execution**: Execute independent tasks simultaneously
- [ ] **Machine Learning Goal Parsing**: Improve goal-to-task mapping accuracy
- [ ] **Interactive Goal Refinement**: Ask clarifying questions for ambiguous goals
- [ ] **Custom Workflow Templates**: Pre-defined templates for common scenarios
- [ ] **Audit Trail**: Complete execution history and change tracking

### Integration Opportunities
- [ ] **Slack Integration**: Progress notifications and approvals
- [ ] **Dashboard Integration**: Visual project monitoring
- [ ] **Scheduling**: Automated goal execution on schedules
- [ ] **API Endpoints**: RESTful API for external integrations

## Example Conversations

### Goal: "Find all clubs in Arizona and enrich their records"

**Project Manager Response:**
```
🎯 I'll break this down into a 3-step project:

1. 🔍 Search HubSpot for golf clubs in Arizona
2. ✨ Enrich missing data fields for each club
3. 🏌️ Identify management companies and set parent relationships

Coordinating with:
- CRM Operations Agent (search & enrichment)
- Company Management Agent (parent company setup)

Starting execution...
```

### Goal: "Analyze The Golf Club at Mansion Ridge"

**Project Manager Response:**
```
🎯 Creating focused analysis project for Mansion Ridge:

1. 📊 Company Intelligence Analysis
2. 🏢 Management Company Identification

Expected outcome:
- Complete company profile
- Troon set as parent company
- Enriched missing fields

Executing now...
```

## Support

For questions or issues:
1. Check the test files for usage examples
2. Review the demo scripts for common patterns  
3. Examine the coordinator.py for goal parsing logic
4. Test with the provided Mansion Ridge example

The Project Manager Agent successfully demonstrates enterprise-grade A2A orchestration capabilities while maintaining the simplicity of natural language goal specification.
