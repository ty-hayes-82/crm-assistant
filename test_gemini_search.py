#!/usr/bin/env python3
"""
Test Gemini with Google Search grounding
"""

import os
from pathlib import Path

# Try the new Gemini API
try:
    from google import genai
    from google.genai import types
    
    # Get API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        # Try .env file
        env_path = Path(".env")
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.strip().startswith("GOOGLE_API_KEY="):
                        api_key = line.split("=", 1)[1].strip()
                        break
    
    if not api_key:
        print("❌ GOOGLE_API_KEY not found!")
        exit(1)
    
    print(f"✅ API key found: {api_key[:10]}...")
    
    # Configure the client
    client = genai.Client(api_key=api_key)
    
    # Define the grounding tool
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )
    
    # Configure generation settings
    config = types.GenerateContentConfig(
        tools=[grounding_tool]
    )
    
    print("✅ Gemini client configured with search grounding")
    
    # Test with a simple search
    test_prompt = """
    Research Houston National Golf Club in Houston, Texas and provide:
    1. The exact website URL
    2. Phone number
    3. Whether it's private, public, or semi-private
    4. Main amenities (pool, tennis courts)
    5. Course details
    
    Please search for current, accurate information about this golf club.
    """
    
    print("🔍 Testing Gemini search grounding...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=test_prompt,
        config=config
    )
    
    print(f"📊 GEMINI SEARCH RESULTS:")
    print("=" * 50)
    print(response.text)
    
    # Check for grounding metadata
    if hasattr(response, 'candidates') and response.candidates:
        candidate = response.candidates[0]
        if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
            metadata = candidate.grounding_metadata
            print(f"\n📋 GROUNDING METADATA:")
            
            if hasattr(metadata, 'web_search_queries'):
                print(f"   Search queries used: {metadata.web_search_queries}")
            
            if hasattr(metadata, 'grounding_chunks'):
                print(f"   Sources found: {len(metadata.grounding_chunks)}")
                for i, chunk in enumerate(metadata.grounding_chunks[:3]):
                    if hasattr(chunk, 'web'):
                        print(f"   [{i+1}] {chunk.web.title}: {chunk.web.uri}")
        else:
            print(f"\n⚠️  No grounding metadata found")
    
    print(f"\n✅ Gemini search grounding test completed!")

except ImportError as e:
    print(f"❌ Gemini import failed: {e}")
    
    # Try legacy API
    try:
        import google.generativeai as genai
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            env_path = Path(".env")
            if env_path.exists():
                with open(env_path) as f:
                    for line in f:
                        if line.strip().startswith("GOOGLE_API_KEY="):
                            api_key = line.split("=", 1)[1].strip()
                            break
        
        if not api_key:
            print("❌ GOOGLE_API_KEY not found!")
            exit(1)
        
        genai.configure(api_key=api_key)
        
        # Try with search grounding
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            tools=["google_search_retrieval"]
        )
        
        print("✅ Legacy Gemini configured with search grounding")
        
        test_prompt = """
        Research Houston National Golf Club in Houston, Texas and provide:
        1. The exact website URL
        2. Phone number  
        3. Whether it's private, public, or semi-private
        4. Main amenities (pool, tennis courts)
        5. Course details
        
        Please search for current, accurate information about this golf club.
        """
        
        print("🔍 Testing legacy Gemini search grounding...")
        response = model.generate_content(test_prompt)
        
        print(f"📊 LEGACY GEMINI SEARCH RESULTS:")
        print("=" * 50)
        print(response.text)
        
        print(f"\n✅ Legacy Gemini search grounding test completed!")
        
    except Exception as e2:
        print(f"❌ Legacy Gemini also failed: {e2}")

except Exception as e:
    print(f"❌ Gemini test failed: {e}")
    import traceback
    traceback.print_exc()
