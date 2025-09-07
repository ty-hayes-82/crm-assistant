#!/usr/bin/env python3
"""
Iterative Enrichment Improver
Pulls random companies, enriches them, analyzes results, and improves the process
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import requests
import json
import random
import time
from typing import Dict, Any, List, Tuple
from datetime import datetime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from web_search_agent import create_web_search_agent

# MCP server configuration
MCP_URL = "http://localhost:8081/mcp"

class EnrichmentLogger:
    """Logs enrichment attempts and analyzes results for improvements."""
    
    def __init__(self):
        self.logs = []
        self.improvements = []
        self.success_patterns = []
        self.failure_patterns = []
    
    def log_attempt(self, company_data: Dict, enrichment_results: Dict, success: bool, errors: List[str] = None):
        """Log an enrichment attempt."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "company_name": company_data.get("name", "Unknown"),
            "company_id": company_data.get("id", ""),
            "industry": company_data.get("industry", ""),
            "location": f"{company_data.get('city', '')}, {company_data.get('state', '')}",
            "enrichment_results": enrichment_results,
            "success": success,
            "errors": errors or [],
            "fields_updated": len(enrichment_results.get("updates", {})),
            "web_search_results": enrichment_results.get("web_search_success", False)
        }
        self.logs.append(log_entry)
        print(f"📝 Logged enrichment attempt for {log_entry['company_name']}")
    
    def analyze_patterns(self):
        """Analyze success and failure patterns to identify improvements."""
        print(f"\n🔍 Analyzing {len(self.logs)} enrichment attempts...")
        
        successes = [log for log in self.logs if log["success"]]
        failures = [log for log in self.logs if not log["success"]]
        
        print(f"   ✅ Successes: {len(successes)}")
        print(f"   ❌ Failures: {len(failures)}")
        
        # Analyze success patterns
        if successes:
            industries = {}
            locations = {}
            for success in successes:
                industry = success["industry"] or "Unknown"
                industries[industry] = industries.get(industry, 0) + 1
                
                location = success["location"]
                if location.strip() != ",":
                    locations[location] = locations.get(location, 0) + 1
            
            print(f"\n🎯 Success Patterns:")
            print(f"   Top Industries: {dict(sorted(industries.items(), key=lambda x: x[1], reverse=True)[:3])}")
            if locations:
                print(f"   Top Locations: {dict(sorted(locations.items(), key=lambda x: x[1], reverse=True)[:3])}")
        
        # Analyze failure patterns
        if failures:
            common_errors = {}
            for failure in failures:
                for error in failure["errors"]:
                    error_type = self.categorize_error(error)
                    common_errors[error_type] = common_errors.get(error_type, 0) + 1
            
            print(f"\n❌ Failure Patterns:")
            for error_type, count in sorted(common_errors.items(), key=lambda x: x[1], reverse=True):
                print(f"   {error_type}: {count} times")
        
        # Generate improvements
        self.generate_improvements()
    
    def categorize_error(self, error: str) -> str:
        """Categorize error messages into types."""
        error_lower = error.lower()
        
        if "read only" in error_lower or "read_only" in error_lower:
            return "Read-only field"
        elif "invalid" in error_lower and "option" in error_lower:
            return "Invalid field option"
        elif "invalid" in error_lower and ("number" in error_lower or "integer" in error_lower):
            return "Invalid number format"
        elif "not found" in error_lower:
            return "Company not found"
        elif "connection" in error_lower or "timeout" in error_lower:
            return "Connection issue"
        else:
            return "Other error"
    
    def generate_improvements(self):
        """Generate code improvements based on analysis."""
        print(f"\n💡 Generated Improvements:")
        
        # Check for read-only field issues
        readonly_errors = [log for log in self.logs if any("read only" in str(error).lower() for error in log["errors"])]
        if readonly_errors:
            improvement = "Skip known read-only fields: " + str(set(error.split('"')[1] for log in readonly_errors for error in log["errors"] if "read only" in str(error).lower()))
            self.improvements.append(improvement)
            print(f"   🔧 {improvement}")
        
        # Check for invalid option errors
        option_errors = [log for log in self.logs if any("invalid" in str(error).lower() and "option" in str(error).lower() for error in log["errors"])]
        if option_errors:
            improvement = "Add field validation for dropdown/option fields"
            if improvement not in self.improvements:
                self.improvements.append(improvement)
                print(f"   🔧 {improvement}")
        
        # Check web search success rate
        web_search_attempts = [log for log in self.logs if "web_search_results" in log]
        if web_search_attempts:
            success_rate = sum(1 for log in web_search_attempts if log["web_search_results"]) / len(web_search_attempts)
            if success_rate < 0.5:
                improvement = "Improve web search queries - current success rate: {:.1%}".format(success_rate)
                self.improvements.append(improvement)
                print(f"   🔧 {improvement}")
        
        if not self.improvements:
            print("   ✅ No major improvements identified - system working well!")

class IterativeEnricher:
    """Iterative enrichment system that improves with each attempt."""
    
    def __init__(self):
        self.logger = EnrichmentLogger()
        self.web_agent = create_web_search_agent()
        self.readonly_fields = set()  # Track fields we can't update
        self.invalid_field_values = {}  # Track invalid values for fields
        
    def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a tool via the MCP server."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "call_tool",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }
        
        try:
            response = requests.post(MCP_URL, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                return {"error": result["error"]}
            
            content = result["result"]["content"][0]["text"]
            return json.loads(content)
        
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}
    
    def get_random_company(self) -> Tuple[Dict[str, Any], bool]:
        """Get a random company from HubSpot."""
        print("🎲 Getting random company from HubSpot...")
        
        # Get a list of companies
        result = self.call_mcp_tool("get_companies", {"limit": 50})
        
        if "error" in result:
            print(f"❌ Error getting companies: {result['error']}")
            return {}, False
        
        companies = result.get("results", [])
        if not companies:
            print("❌ No companies found")
            return {}, False
        
        # Pick a random company
        company = random.choice(companies)
        company_props = company.get("properties", {})
        
        print(f"🎯 Selected: {company_props.get('name', 'Unknown')} (ID: {company['id']})")
        print(f"   Location: {company_props.get('city', '')}, {company_props.get('state', '')}")
        print(f"   Industry: {company_props.get('industry', 'Not specified')}")
        
        return company, True
    
    def analyze_company_needs(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze what enrichment the company needs."""
        props = company.get("properties", {})
        needs = {
            "missing_fields": [],
            "short_fields": [],
            "placeholder_fields": []
        }
        
        # Check for missing critical fields
        critical_fields = ["description", "industry", "website", "domain", "phone"]
        for field in critical_fields:
            if not props.get(field):
                needs["missing_fields"].append(field)
        
        # Check for short descriptions
        description = props.get("description", "")
        if description and len(description) < 50:
            needs["short_fields"].append("description")
        
        # Check for placeholder values
        placeholder_values = ["--", "Unknown", "Not specified", "TBD", "N/A"]
        for field, value in props.items():
            if str(value) in placeholder_values:
                needs["placeholder_fields"].append(field)
        
        return needs
    
    def enrich_company_intelligently(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligently enrich a company based on learned patterns."""
        company_id = company["id"]
        props = company.get("properties", {})
        company_name = props.get("name", "Unknown Company")
        
        print(f"\n🧠 Intelligently enriching: {company_name}")
        print("=" * 50)
        
        # Analyze what the company needs
        needs = self.analyze_company_needs(company)
        print(f"📊 Analysis: {len(needs['missing_fields'])} missing, {len(needs['short_fields'])} short, {len(needs['placeholder_fields'])} placeholder fields")
        
        updates = {}
        errors = []
        web_search_success = False
        
        # 1. Basic field enrichment based on industry/type
        if not props.get("industry") and "golf" in company_name.lower():
            updates["industry"] = "LEISURE_TRAVEL_TOURISM"
        
        # 2. Web search for missing domain/website
        if "domain" in needs["missing_fields"] or "website" in needs["missing_fields"]:
            print("🔍 Using web search for domain/website...")
            location = f"{props.get('city', '')}, {props.get('state', '')}"
            web_results = self.web_agent.comprehensive_company_search(company_name, location)
            
            if web_results.get("domain"):
                if "domain" in needs["missing_fields"]:
                    updates["domain"] = web_results["domain"]
                if "website" in needs["missing_fields"]:
                    updates["website"] = f"https://{web_results['domain']}"
                web_search_success = True
                print(f"   ✅ Found domain: {web_results['domain']}")
            else:
                print("   ❌ No domain found via web search")
        
        # 3. Generate description if missing
        if "description" in needs["missing_fields"]:
            industry = props.get("industry", "business")
            location = f"{props.get('city', '')}, {props.get('state', '')}"
            generated_desc = f"{company_name} is a {industry.lower().replace('_', ' ')} company"
            if location.strip() != ",":
                generated_desc += f" located in {location}"
            generated_desc += ". Additional information about the company's services and operations would enhance this profile."
            updates["description"] = generated_desc
        
        # 4. Add email pattern if domain is available
        domain = updates.get("domain") or props.get("domain")
        if domain and not props.get("email_pattern"):
            updates["email_pattern"] = f"firstname.lastname@{domain}"
        
        # 5. Filter out known problematic fields
        filtered_updates = {}
        for field, value in updates.items():
            if field not in self.readonly_fields:
                # Check if we've seen this field/value combination fail before
                if field not in self.invalid_field_values or value not in self.invalid_field_values[field]:
                    filtered_updates[field] = value
                else:
                    print(f"   ⚠️  Skipping {field} - known invalid value: {value}")
        
        # 6. Apply updates
        success = True
        if filtered_updates:
            print(f"🔄 Applying {len(filtered_updates)} updates...")
            for field, value in filtered_updates.items():
                print(f"   • {field}: {str(value)[:60]}{'...' if len(str(value)) > 60 else ''}")
            
            result = self.call_mcp_tool("update_company", {
                "company_id": company_id,
                "properties": filtered_updates
            })
            
            if "error" in result:
                error_msg = result["error"]
                errors.append(error_msg)
                success = False
                print(f"❌ Update failed: {error_msg}")
                
                # Learn from the error
                self.learn_from_error(error_msg, filtered_updates)
            else:
                print("✅ Updates applied successfully!")
        else:
            print("ℹ️  No updates needed or all updates filtered out")
        
        return {
            "updates": filtered_updates,
            "success": success,
            "errors": errors,
            "web_search_success": web_search_success,
            "needs_analysis": needs
        }
    
    def learn_from_error(self, error_msg: str, attempted_updates: Dict[str, Any]):
        """Learn from errors to avoid them in future attempts."""
        error_lower = error_msg.lower()
        
        # Track read-only fields
        if "read only" in error_lower or "read_only" in error_lower:
            # Extract field name from error message
            if '"' in error_msg:
                field_name = error_msg.split('"')[1]
                self.readonly_fields.add(field_name)
                print(f"   📝 Learned: {field_name} is read-only")
        
        # Track invalid field values
        elif "invalid" in error_lower and "option" in error_lower:
            # Extract field and value from error message
            for field, value in attempted_updates.items():
                if field in error_msg:
                    if field not in self.invalid_field_values:
                        self.invalid_field_values[field] = set()
                    self.invalid_field_values[field].add(value)
                    print(f"   📝 Learned: {field} cannot be '{value}'")
    
    def run_iteration(self, iteration_num: int) -> bool:
        """Run a single enrichment iteration."""
        print(f"\n🚀 ITERATION {iteration_num}")
        print("=" * 60)
        
        # Get random company
        company, success = self.get_random_company()
        if not success:
            return False
        
        # Enrich the company
        enrichment_results = self.enrich_company_intelligently(company)
        
        # Log the attempt
        self.logger.log_attempt(
            company.get("properties", {}),
            enrichment_results,
            enrichment_results["success"],
            enrichment_results["errors"]
        )
        
        # Show what we learned
        if self.readonly_fields:
            print(f"\n📚 Known read-only fields: {list(self.readonly_fields)}")
        if self.invalid_field_values:
            print(f"📚 Known invalid values: {dict(self.invalid_field_values)}")
        
        return True

def main():
    """Main iterative improvement process."""
    print("🔄 Iterative Enrichment Improver")
    print("=" * 50)
    print("This script will:")
    print("1. Pull random companies from HubSpot")
    print("2. Attempt to enrich them")
    print("3. Learn from successes and failures")
    print("4. Improve the enrichment process")
    print("5. Repeat 5 times total")
    print()
    
    # Check MCP server
    try:
        health_response = requests.get("http://localhost:8081/health")
        if health_response.status_code == 200:
            print("✅ MCP Server: Connected")
        else:
            print("❌ MCP Server not responding")
            return
    except Exception as e:
        print(f"❌ Cannot connect to MCP server: {e}")
        return
    
    # Initialize the iterative enricher
    enricher = IterativeEnricher()
    
    # Run 5 iterations
    successful_iterations = 0
    for i in range(1, 6):
        success = enricher.run_iteration(i)
        if success:
            successful_iterations += 1
        
        # Analyze patterns after each iteration (except the first)
        if i > 1:
            enricher.logger.analyze_patterns()
        
        # Wait between iterations
        if i < 5:
            print(f"\n⏳ Waiting 3 seconds before next iteration...")
            time.sleep(3)
    
    # Final analysis
    print(f"\n🎉 FINAL ANALYSIS")
    print("=" * 60)
    print(f"Completed {successful_iterations}/5 iterations")
    
    enricher.logger.analyze_patterns()
    
    # Summary of learnings
    print(f"\n📚 SYSTEM IMPROVEMENTS:")
    if enricher.readonly_fields:
        print(f"   🔒 Identified {len(enricher.readonly_fields)} read-only fields")
    if enricher.invalid_field_values:
        print(f"   ⚠️  Identified invalid values for {len(enricher.invalid_field_values)} fields")
    
    success_rate = successful_iterations / 5 * 100
    print(f"\n📊 SUCCESS RATE: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎯 Excellent! System is working very well.")
    elif success_rate >= 60:
        print("👍 Good performance with room for improvement.")
    else:
        print("🔧 Needs improvement - check the error patterns above.")
    
    print(f"\n✅ Iterative improvement complete!")
    print("The system has learned from each attempt and should perform better on future enrichments.")

if __name__ == "__main__":
    main()
