#!/usr/bin/env python3
"""
Test date parsing with more context about what's happening
"""

import sys
import os
from datetime import datetime
import pytz
import dateparser

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from events_agent.infra.date_parsing import parse_natural_range
from events_agent.infra.settings import settings

def test_detailed_parsing():
    """Test detailed parsing behavior"""
    print("🔍 DETAILED PARSING ANALYSIS")
    print("=" * 50)
    
    melb_tz = pytz.timezone(settings.default_tz)
    now_melb = datetime.now(melb_tz)
    
    print(f"Current Melbourne time: {now_melb}")
    print(f"Current date: {now_melb.strftime('%A, %B %d, %Y')}")
    print(f"Current time: {now_melb.strftime('%I:%M %p')}")
    print()
    
    # Test various interpretations
    test_cases = [
        "3PM September 26",
        "September 26 3PM", 
        "September 26th 3PM",
        "today 3PM",
        "today at 3PM",
        "September 26 15:00"
    ]
    
    for test_input in test_cases:
        print(f"Input: '{test_input}'")
        
        try:
            # Use raw dateparser to see what it's doing
            try:
                raw_result = dateparser.parse(test_input.strip().lower())
                print(f"  Raw dateparser: {raw_result}")
            except Exception as e:
                print(f"  Raw dateparser error: {e}")
            
            # Use our parsing function
            start_dt, end_dt = parse_natural_range(test_input, settings.default_tz)
            print(f"  Our parser: {start_dt.strftime('%A, %B %d at %I:%M %p')}")
            
            # Check if it's interpreting as past or future
            if start_dt < now_melb:
                print(f"  ⚠️  Parsed as PAST event (before current time)")
            else:
                print(f"  ✅ Parsed as FUTURE event")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print()

if __name__ == "__main__":
    test_detailed_parsing()