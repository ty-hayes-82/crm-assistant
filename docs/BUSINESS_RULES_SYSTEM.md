# Swoop Golf CRM Business Rules System

## Overview

The Business Rules System provides intelligent field enrichment for Swoop Golf's CRM by understanding the business purpose and context behind each data field. This ensures that our agents don't just populate data, but populate it with strategic business intelligence.

## Key Components

### 1. Field Enrichment Rules (`crm_agent/configs/field_enrichment_rules.json`)

Central configuration file that defines:
- **Business purpose** for each field
- **Sales implications** and strategic value
- **Validation rules** and data quality standards
- **Competitive intelligence** context
- **Enrichment priorities** based on business impact

### 2. Enhanced Field Mapping Agent

The `FieldMappingAgent` now includes:
- **Business context retrieval** for any field
- **Value validation** against business rules
- **Enrichment strategy generation** based on priorities
- **Competitive analysis** for sales intelligence

### 3. Business-Aware Enrichment

All enrichment agents now understand:
- **Why** each field matters to Swoop Golf
- **How** to prioritize enrichment efforts
- **What** the data means for sales strategy

## Critical Business Fields

### 🏆 Competitor Field
**Purpose**: Track if golf clubs use Swoop Golf competitors
**Business Value**: Critical for sales strategy and competitive positioning

**Sales Priority Matrix**:
- `"Unknown"` → **HIGH PRIORITY** (Greenfield opportunity)
- `"In-House App"` → **MEDIUM PRIORITY** (May be dissatisfied)
- `"Club Essentials"`, `"Jonas"`, etc. → **LOW-MEDIUM PRIORITY** (Competitive approach needed)

**Swoop Competitors**:
- Club Essentials
- Jonas
- ForeTees
- Lightspeed Golf
- ClubProphet
- Supreme Golf
- Northstar
- Club Systems International
- Golf Genius
- Callus
- Pacesetter
- Club App

### 📧 Email Pattern Field
**Purpose**: Enable accurate email prospecting for sales outreach
**Business Value**: Critical for contact discovery and lead generation

**Pattern Examples**:
- `@clubname.com`
- `firstname.lastname@domain.com`
- `firstinitiallastname@domain.com`

**Usage**: Sales team uses patterns to guess email addresses of key contacts (GM, Director of Golf, F&B Manager)

### 🏢 Management Company Field
**Purpose**: Identify decision-making hierarchy
**Business Value**: Management companies often make technology decisions for multiple properties

**Key Management Companies**:
- Troon
- ClubCorp
- Kemper Sports
- JC Golf
- Billy Casper Golf

### 🏷️ Company Type Field
**Purpose**: Classify facility type for targeted sales approach
**Business Value**: Different facility types have different needs and budgets

**Sales Implications**:
- **Country Club**: Higher budget, member-focused, premium expectations
- **Daily Fee Course**: Revenue-focused, high volume, cost-conscious
- **Resort**: Guest experience focused, seasonal considerations
- **Municipal Course**: Budget constraints, public accountability

### 📊 NGF Category Field
**Purpose**: National Golf Foundation classification for market segmentation
**Business Value**: Industry-standard classification for competitive analysis

## Enrichment Priorities

### Critical Fields (Immediate Action Required)
1. **competitor** - Essential for sales strategy
2. **management_company** - Key for decision-making hierarchy
3. **company_type** - Critical for targeting approach
4. **email_pattern** - Essential for prospecting

### High Value Fields (High Priority)
1. **ngf_category** - Important for market analysis
2. **description** - Provides sales context
3. **club_info** - Reveals revenue opportunities

### Supplementary Fields (Nice to Have)
1. **has_pool** - Additional revenue streams
2. **has_tennis_courts** - Multi-sport opportunities
3. **state** - Territory management

## Usage Examples

### 1. Competitor Analysis
```python
agent = FieldMappingAgent()
validation = agent.validate_field_value("competitor", "Club Essentials")

# Returns:
# {
#   "status": "valid",
#   "warnings": ["'Club Essentials' is a Swoop Golf competitor - requires competitive sales approach"],
#   "sales_priority": "Low-Medium"
# }
```

### 2. Enrichment Strategy
```python
company_data = {"name": "Sample Golf Club", "city": "Phoenix"}
strategy = agent.get_enrichment_strategy(company_data)

# Returns prioritized list of missing fields with business impact
```

### 3. Business Context
```python
context = agent.get_field_business_context("competitor")

# Returns:
# {
#   "purpose": "Track if this golf club uses a competitor of Swoop Golf's technology solutions",
#   "business_value": "Critical for sales strategy - identifies prospects already using competing solutions vs. greenfield opportunities"
# }
```

## Sales Team Benefits

### 🎯 **Intelligent Lead Scoring**
- Automatically prioritize prospects based on competitor analysis
- Identify greenfield opportunities vs. competitive situations

### 📈 **Strategic Prospecting**
- Use email patterns for accurate contact discovery
- Understand facility scope and revenue potential

### 🏢 **Decision Maker Identification**
- Know who makes technology decisions (management company vs. individual club)
- Tailor approach based on facility type and structure

### 💰 **Revenue Opportunity Assessment**
- Understand facility complexity and revenue streams
- Identify clubs with multiple service points (F&B, pro shop, events)

## Data Quality Standards

### Competitor Field
- **Validation**: Cross-reference with known technology vendors
- **Quality Threshold**: If >90% show "Unknown", prioritize competitive research

### Email Pattern Field
- **Format**: Must start with "@" symbol
- **Validation**: Should match known employee emails when available

### Management Company Field
- **Confidence**: 85% fuzzy match minimum
- **Source**: Internal management company database

## Integration with Existing Agents

### Company Management Agent
- Now includes business context in results
- Explains strategic value of management company identification

### Field Mapping Agent
- Validates all field values against business rules
- Provides enrichment recommendations based on business priorities

### Future Enhancements
- **Competitive Intelligence Agent**: Automated competitor research
- **Email Discovery Agent**: Automated email pattern validation
- **Sales Priority Scoring**: Automated lead scoring based on enriched data

## Conclusion

The Business Rules System transforms our CRM from a simple data repository into a strategic sales intelligence platform. Every field enrichment now serves a specific business purpose, helping our sales team:

1. **Prioritize prospects** based on competitive landscape
2. **Tailor approaches** based on facility type and structure  
3. **Discover contacts** using validated email patterns
4. **Understand decision-making** through management company identification

This system ensures that our enrichment efforts directly support sales success and revenue growth.
