#!/usr/bin/env python3
"""
Test the timezone fix for the Discord bot
"""

import sys
import os
from datetime import datetime
import pytz

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from events_agent.infra.settings import settings

def test_timezone_conversion():
    """Test the timezone conversion logic we just implemented"""
    print("🔍 Testing timezone conversion fix")
    print(f"Default timezone: {settings.default_tz}")
    
    # Simulate different Google Calendar datetime formats
    test_cases = [
        {
            "name": "UTC with Z suffix (3PM UTC)",
            "input": "2025-09-26T15:00:00.000Z",
            "expected_local": "Saturday, September 27 at 01:00 AM"  # +10 hours for Melbourne
        },
        {
            "name": "UTC with Z suffix (5AM UTC)", 
            "input": "2025-09-26T05:00:00Z",
            "expected_local": "Friday, September 26 at 03:00 PM"  # +10 hours for Melbourne
        },
        {
            "name": "Already in Melbourne timezone",
            "input": "2025-09-26T15:00:00+10:00",
            "expected_local": "Friday, September 26 at 03:00 PM"  # No conversion needed
        }
    ]
    
    print("\n🔍 Testing timezone conversion:")
    local_tz = pytz.timezone(settings.default_tz)
    
    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        print(f"Input: {test_case['input']}")
        
        try:
            # Apply the fix we implemented
            dt = datetime.fromisoformat(test_case['input'].replace("Z", "+00:00"))
            dt_local = dt.astimezone(local_tz)
            formatted = dt_local.strftime('%A, %B %d at %I:%M %p')
            
            print(f"Original: {dt} ({dt.tzinfo})")
            print(f"Local: {dt_local} ({dt_local.tzinfo})")
            print(f"Formatted: {formatted}")
            print(f"Expected: {test_case['expected_local']}")
            
            # Check if it matches expected (basic check)
            if test_case['expected_local'] in formatted:
                print("✅ PASS")
            else:
                print("❌ FAIL")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_timezone_conversion()