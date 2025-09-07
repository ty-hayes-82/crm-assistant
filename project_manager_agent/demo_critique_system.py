"""
Demonstration of the Enhanced Project Manager Agent with Critique System

This script shows how the Project Manager Agent now critically evaluates
CRM agent responses and follows up with additional questions when needed.
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from project_manager_agent.coordinator import ProjectManagerAgent
from project_manager_agent.interactive_coordinator import InteractiveProjectManagerAgent


def demonstrate_critique_system():
    """Demonstrate the critique system with various response scenarios"""
    
    print("🧠 PROJECT MANAGER AGENT - CRITIQUE SYSTEM DEMONSTRATION")
    print("=" * 60)
    
    # Create enhanced project manager with critique capabilities
    pm_agent = ProjectManagerAgent()
    
    print("\n🎯 SCENARIO 1: Testing Company Intelligence Response Critique")
    print("-" * 50)
    
    # Simulate a poor quality response that should trigger follow-up
    poor_response = {
        "name": "ACME Corp",  # Missing domain, industry, description
        "status": "found"
    }
    
    # Test critique
    critique = pm_agent.critic.critique_response(
        agent_type="company_intelligence",
        task_description="Analyze ACME Corp and provide comprehensive company information",
        response=poor_response
    )
    
    print(f"📊 Response Quality: {critique.overall_quality.value.title()}")
    print(f"📈 Score: {critique.score}/100")
    print(f"🔄 Needs Follow-up: {critique.needs_follow_up}")
    
    if critique.critiques:
        print("\n🔍 Issues Identified:")
        for i, crit in enumerate(critique.critiques, 1):
            print(f"   {i}. {crit.get('issue', 'Unknown issue')}")
    
    if critique.follow_up_questions:
        print("\n❓ Follow-up Questions Generated:")
        for i, question in enumerate(critique.follow_up_questions, 1):
            print(f"   {i}. {question}")
    
    print("\n" + "=" * 60)
    print("🎯 SCENARIO 2: Testing Management Company Response Critique")
    print("-" * 50)
    
    # Simulate a good quality response
    good_response = {
        "management_company": "Troon Golf",
        "management_company_id": "hubspot_troon_123",
        "match_score": 95,
        "confidence": 95,
        "data_sources": ["company website", "golf industry database"]
    }
    
    critique2 = pm_agent.critic.critique_response(
        agent_type="company_management_enrichment",
        task_description="Identify management company for The Golf Club at Mansion Ridge",
        response=good_response
    )
    
    print(f"📊 Response Quality: {critique2.overall_quality.value.title()}")
    print(f"📈 Score: {critique2.score}/100")
    print(f"🔄 Needs Follow-up: {critique2.needs_follow_up}")
    
    print("\n" + "=" * 60)
    print("🎯 SCENARIO 3: Testing Error Response Handling")
    print("-" * 50)
    
    # Simulate an error response
    error_response = {
        "error": "Unable to connect to data source"
    }
    
    critique3 = pm_agent.critic.critique_response(
        agent_type="crm_enrichment",
        task_description="Enrich company data for ACME Corp",
        response=error_response
    )
    
    print(f"📊 Response Quality: {critique3.overall_quality.value.title()}")
    print(f"📈 Score: {critique3.score}/100")
    print(f"🔄 Needs Follow-up: {critique3.needs_follow_up}")
    
    if critique3.follow_up_questions:
        print("\n❓ Follow-up Questions for Error Recovery:")
        for i, question in enumerate(critique3.follow_up_questions, 1):
            print(f"   {i}. {question}")
    
    print("\n" + "=" * 60)
    print("🧠 SCENARIO 4: Critical Thinking Analysis")
    print("-" * 50)
    
    # Test critical thinking on project results
    sample_project_results = [
        {"agent_type": "company_intelligence", "company_name": "Golf Club A", "industry": "Recreation"},
        {"agent_type": "company_management_enrichment", "management_company": "Troon", "confidence": 85},
        {"error": "Data source unavailable"}
    ]
    
    critical_analysis = pm_agent.thinking_engine.think_critically(
        project_goal="Find and enrich golf clubs in Arizona",
        task_results=sample_project_results
    )
    
    print(f"🎯 Goal Achievement Score: {critical_analysis['goal_achievement']['score']:.1f}%")
    print(f"📊 Data Quality Grade: {critical_analysis['data_quality']['quality_grade']}")
    
    if critical_analysis['strategic_insights']:
        print("\n💡 Strategic Insights:")
        for insight in critical_analysis['strategic_insights']:
            print(f"   • {insight}")
    
    if critical_analysis['recommended_actions']:
        print("\n🚀 Recommended Next Actions:")
        for action in critical_analysis['recommended_actions']:
            print(f"   • {action}")


async def demonstrate_interactive_critique():
    """Demonstrate interactive critique with chat interface"""
    
    print("\n" + "=" * 60)
    print("🎮 INTERACTIVE CRITIQUE DEMONSTRATION")
    print("-" * 50)
    
    # Create interactive project manager
    interactive_pm = InteractiveProjectManagerAgent()
    
    # Simulate executing a goal with critique
    print("🎯 Executing goal: 'Analyze The Golf Club at Mansion Ridge'")
    print("   (This will show real-time critique and follow-up generation)")
    
    try:
        result = await interactive_pm.execute_goal_with_chat(
            "Analyze The Golf Club at Mansion Ridge and identify its management company"
        )
        
        print(f"\n📊 Final Results:")
        print(f"   Total Tasks: {result.get('total_tasks', 0)}")
        print(f"   Completed: {result.get('completed_tasks', 0)}")
        print(f"   Progress: {result.get('progress', 0):.1f}%")
        
    except Exception as e:
        print(f"⚠️ Demo error: {str(e)}")
        print("   (This is expected in demo mode without full CRM setup)")


def show_critique_capabilities():
    """Show the capabilities of the critique system"""
    
    print("\n" + "=" * 60)
    print("🔧 CRITIQUE SYSTEM CAPABILITIES")
    print("-" * 50)
    
    capabilities = [
        "✅ Validates response completeness for each agent type",
        "✅ Checks data accuracy and confidence levels", 
        "✅ Generates specific follow-up questions",
        "✅ Identifies missing critical information",
        "✅ Suggests improvements for better results",
        "✅ Handles error responses intelligently",
        "✅ Provides quality scoring (0-100)",
        "✅ Creates follow-up tasks automatically",
        "✅ Applies critical thinking to project outcomes",
        "✅ Generates strategic insights and recommendations",
        "✅ Prevents acceptance of poor quality responses",
        "✅ Iterative improvement through multiple attempts"
    ]
    
    for capability in capabilities:
        print(f"   {capability}")
    
    print("\n🎯 AGENT-SPECIFIC VALIDATION:")
    print("   • Company Intelligence: Name, domain, industry, description")
    print("   • Contact Intelligence: Name, email, title, company")
    print("   • CRM Enrichment: Enriched fields, success rate, sources")
    print("   • Management Enrichment: Company ID, confidence score")
    print("   • Field Enrichment: Mappings, validation results, statistics")
    
    print("\n🧠 CRITICAL THINKING FEATURES:")
    print("   • Goal achievement assessment")
    print("   • Data quality analysis")
    print("   • Strategic insight generation")
    print("   • Risk assessment")
    print("   • Success metrics calculation")
    print("   • Next action recommendations")


def main():
    """Main demonstration function"""
    
    print("🚀 Starting Project Manager Agent Critique System Demo...")
    
    # Show capabilities
    show_critique_capabilities()
    
    # Demonstrate critique system
    demonstrate_critique_system()
    
    # Demonstrate interactive critique (async)
    try:
        asyncio.run(demonstrate_interactive_critique())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n⚠️ Demo completed with minor issues: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ CRITIQUE SYSTEM DEMONSTRATION COMPLETE")
    print("\n🎯 KEY IMPROVEMENTS:")
    print("   • Project Manager now critically evaluates all CRM responses")
    print("   • Automatically generates follow-up questions for poor responses")
    print("   • Provides quality scoring and improvement suggestions")
    print("   • Applies strategic thinking to project outcomes")
    print("   • Prevents acceptance of incomplete or inaccurate data")
    print("\n💡 The Project Manager Agent is now much more intelligent and thorough!")


if __name__ == "__main__":
    main()
