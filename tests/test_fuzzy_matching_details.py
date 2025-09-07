"""
Detailed test to understand fuzzy matching behavior
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from thefuzz import process
import json
from pathlib import Path

def test_fuzzy_matching_details():
    """Test fuzzy matching in detail to understand the behavior."""
    
    # Load the courses data
    file_path = Path(__file__).parent.parent / "docs" / "courses_under_management.json"
    with open(file_path, 'r') as f:
        courses_data = json.load(f)
    
    # Create list of all courses with their managers
    all_courses = []
    for manager, courses in courses_data.items():
        for course in courses:
            all_courses.append({"manager": manager, "name": course["name"]})
    
    course_names = [course["name"] for course in all_courses]
    
    # Test the problematic case
    test_name = "Cross Creek Golf Course"
    
    print(f"🔍 Analyzing fuzzy matches for: '{test_name}'")
    print("=" * 60)
    
    # Get top 10 matches
    matches = process.extract(test_name, course_names, limit=10)
    
    for i, (match_name, score) in enumerate(matches, 1):
        # Find the manager for this course
        matched_course = next((c for c in all_courses if c["name"] == match_name), None)
        manager = matched_course["manager"] if matched_course else "Unknown"
        
        print(f"{i:2d}. {match_name:<50} | Score: {score:3d} | Manager: {manager}")
    
    print()
    print("🎯 Analysis:")
    print(f"   Best match: '{matches[0][0]}' with score {matches[0][1]}")
    
    # Find the exact "Cross Creek" match
    exact_match = next((c for c in all_courses if "Cross Creek" in c["name"] and c["manager"] == "JC Golf"), None)
    if exact_match:
        exact_score = process.extractOne(test_name, [exact_match["name"]])[1]
        print(f"   JC Golf 'Cross Creek' score: {exact_score}")
    
    print()
    print("💡 Recommendation:")
    if matches[0][1] > 90:
        print("   Current threshold (85) would accept this match")
    else:
        print("   Current threshold (85) would reject this match")

if __name__ == "__main__":
    test_fuzzy_matching_details()
