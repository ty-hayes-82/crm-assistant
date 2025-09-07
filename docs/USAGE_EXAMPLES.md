# CRM Assistant Usage Examples

## 🤖 How to Use Your CRM Assistant

### 🚀 Quick Start
```bash
# 1. Start MCP server (Terminal 1)
conda activate adk
python mcp_wrapper/simple_hubspot_server.py

# 2. Start CRM Assistant (Terminal 2)  
conda activate adk
python crm_assistant.py
```

## 💬 Request Types & Examples

### 🏢 Company Intelligence Requests

Ask comprehensive questions about any company in your HubSpot CRM:

**📋 Example Requests:**
```
Tell me about Google
What do you know about Microsoft?
Analyze Salesforce
Give me intelligence on HubSpot Inc
Tell me about Austin Golf Club
What do you know about Purgatory Golf Club?
```

**📊 What You'll Get:**
- Complete company profile (industry, location, website, phone)
- Business description and overview
- Associated contacts with titles and emails
- Deal pipeline analysis with values and stages
- Data completeness assessment
- Strategic next steps and recommendations

**💬 Sample Conversation:**
```
🤖 How can I help you? Tell me about Google

📊 **Google LLC** Analysis

🏢 **Company Overview:**
   • Industry: COMPUTER_SOFTWARE
   • Location: Mountain View, CA, United States
   • Website: sites.google.com
   • Phone: +1 650-253-0000
   • Description: Google LLC is an American multinational technology company...

👥 **Associated Contacts** (1 total):
   • Google Team - team@google.com
     Title: Technology Team

📈 **Key Insights:**
   • Data Completeness: 100.0%
   • Total Deal Value: $0.00
   • Open Deals: 0

🎯 **Next Steps:**
   • Review company profile for accuracy
   • Consider enriching missing data fields
   • Engage with key contacts for opportunities
```

---

### 🔍 Company Search Requests

Search your CRM to find companies by name, domain, or keywords:

**📋 Example Requests:**
```
Search for Apple
Find Microsoft
Look for golf companies
Search for companies with "tech" in the name
Find all companies in California
```

**📊 What You'll Get:**
- List of matching companies with key details
- Company domains and industries
- Location information
- Suggestions for detailed analysis

**💬 Sample Conversation:**
```
🤖 How can I help you? Search for golf companies

🔍 **Search Results for 'golf companies'** (5 found)

**1. Austin Golf Club**
   • Domain: austingolfclub.com
   • Industry: LEISURE_TRAVEL_TOURISM
   • Location: Spicewood, TX

**2. Purgatory Golf Club**
   • Domain: purgatorygolf.com
   • Industry: LEISURE_TRAVEL_TOURISM
   • Location: Noblesville, IN

💡 **To get detailed information, ask:** 'Tell me about [company name]'
```

---

### 🌐 Data Enrichment Requests

Enhance company profiles with additional web-researched information:

**📋 Example Requests:**
```
Enrich Google
Update Microsoft with web data
Improve Austin Golf Club profile
Enhance Salesforce information
Enrich missing data for HubSpot
Find more information about [company] online
```

**📊 What You'll Get:**
- Automatic identification of missing/incomplete fields
- Web search for additional company information
- Smart field updates (only updates empty/short fields)
- Real-time HubSpot record updates
- Summary of improvements made

**💬 Sample Conversation:**
```
🤖 How can I help you? Enrich Austin Golf Club

🌐 Enriching: Austin Golf Club
----------------------------------------

✅ **Austin Golf Club Enriched Successfully!**

Updated 3 fields:
   • domain: austingolfclub.com
   • website: https://austingolfclub.com
   • email_pattern: firstname.lastname@austingolfclub.com

🎯 Check your HubSpot record to see the improvements!
```

---

## 🎯 Advanced Request Examples

### 🔄 Complex Intelligence Requests
```
What's the current status of our relationship with Microsoft?
How should I proceed with the Google opportunity?
Give me a complete analysis of Salesforce including next steps
What do we know about HubSpot and what are the recommended actions?
```

### 🏆 Competitive Analysis
```
Tell me about Google and their competitors
What companies compete with Microsoft?
Who are Salesforce's main competitors?
```

### 📊 Data Quality Requests
```
What companies need data enrichment?
Show me companies with incomplete profiles
Which companies are missing contact information?
```

## 💡 Pro Tips

### 🎯 Getting Better Results
- **Be specific**: "Tell me about Google LLC" vs "Google"
- **Use full company names**: "Microsoft Corporation" vs "MS"
- **Include context**: "Austin Golf Club in Texas" vs "Austin Golf Club"

### 🔍 When Companies Aren't Found
- Try different name variations
- Search first: "Search for [partial name]"
- Check if the company exists in your HubSpot portal
- Use domain names: "Tell me about companies with domain google.com"

### 🌐 Maximizing Enrichment
- Start with companies that have minimal data
- Enrich companies before important meetings or outreach
- Use enrichment to fill gaps before reporting
- Regular enrichment keeps your CRM data fresh and complete

## 🆘 Need Help?

**Type any of these for assistance:**
- `help` - Show available commands
- `what can you do` - See capabilities
- `examples` - Get usage examples

**Common Issues:**
- **"Company not found"** → Try searching first or check spelling
- **"MCP server not responding"** → Start the MCP server first
- **"No enrichment needed"** → Company already has complete data

Your CRM Assistant is designed to understand natural language, so feel free to ask questions in your own words!
