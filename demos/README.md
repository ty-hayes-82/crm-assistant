# CRM Assistant Demos

This directory contains comprehensive demonstrations of the CRM Assistant system, organized by functionality.

## 📁 Directory Structure

### 🤖 [agents/](./agents/)
Demonstrations of individual CRM agents and their capabilities.

- **Company Management Agent** - Golf course management company identification
- **Competitor Analysis Agent** - Swoop Golf competitive intelligence  
- **LLM Enrichment Agent** - AI-powered data enrichment
- **Interactive Agent** - Real-time agent interaction demos

### 📊 [enrichment/](./enrichment/)
Data enrichment processes and business rule demonstrations.

- **Business Rules Demo** - Field validation and sales intelligence
- **Field Enrichment** - Specific field enrichment examples
- **Contact Enrichment** - Contact data enhancement processes
- **Iterative Improvement** - Continuous data quality improvement

### 🎯 [project_manager/](./project_manager/)
Project Manager Agent and Agent-to-Agent (A2A) communication demos.

- **Interactive Project Manager** - A2A orchestration with chat interface
- **Mansion Ridge Demo** - Complete enrichment workflow with A2A communication
- **Project Manager Basics** - Core PM functionality

## 🚀 Quick Start

### Run the Business Rules Demo
```bash
python demos/enrichment/business_rules_enrichment_demo.py
```

### Test Company Management Agent
```bash
python demos/agents/demo_company_management_enrichment.py
```

### Experience A2A Communication
```bash
python demos/project_manager/interactive_project_manager.py
```

## 🎯 Key Features Demonstrated

### 🏆 **Intelligent Competitor Analysis**
- Identifies Swoop Golf competitors (Club Essentials, Jonas, ForeTees, etc.)
- Provides sales priority scoring based on competitive landscape
- Distinguishes between greenfield opportunities and competitive situations

### 📧 **Smart Email Pattern Discovery**
- Validates email formats for accurate prospecting
- Enables contact discovery for key roles (GM, Director of Golf, F&B Manager)
- Supports multiple email pattern formats

### 🏢 **Management Company Intelligence**
- Identifies decision-making hierarchy (Troon, ClubCorp, etc.)
- Understands multi-property management structures
- Provides partnership opportunity insights

### 📋 **Business Rules Validation**
- Every field enrichment serves a specific business purpose
- Automated data quality validation against business standards
- Strategic enrichment prioritization based on sales impact

### 🤝 **Agent-to-Agent Communication**
- Real-time orchestration between specialized agents
- Chat-like interface showing agent communication
- Task decomposition and dependency management

## 💼 Business Value

Each demo showcases how the CRM Assistant transforms raw data into strategic sales intelligence:

- **🎯 Lead Prioritization** - Automatically score prospects based on competitive analysis
- **📈 Sales Efficiency** - Accurate contact discovery and facility understanding  
- **🏢 Decision Maker ID** - Know who makes technology decisions at each facility
- **💰 Revenue Assessment** - Understand facility scope and revenue opportunities

## 🧪 Testing

All demos include comprehensive testing. See the [tests/](../tests/) directory for:

- **Unit Tests** - Individual agent functionality
- **Integration Tests** - End-to-end workflow validation
- **Business Rule Tests** - Field validation and business logic

## 📚 Documentation

For detailed information about the system architecture and business rules:

- **[Business Rules System](../docs/BUSINESS_RULES_SYSTEM.md)** - Complete field enrichment rules
- **[Agent Capabilities](../docs/AGENT_CAPABILITIES.md)** - Individual agent documentation
- **[Usage Examples](../docs/USAGE_EXAMPLES.md)** - Real-world usage scenarios

## 🎉 Success Stories

### The Golf Club at Mansion Ridge
Complete enrichment success story demonstrating:
- ✅ Management Company: Troon (identified via fuzzy matching)
- ✅ Company Type: Golf Club (validated against HubSpot options)
- ✅ Competitor: ClubCorp (competitive analysis)
- ✅ Email Pattern: @mansionridgegc.com (prospecting enablement)
- ✅ All Primary Fields: Comprehensive facility information

**Result**: Transformed empty HubSpot record into complete sales intelligence profile.

---

*The CRM Assistant Demo Suite - Transforming CRM data into strategic sales intelligence.*
