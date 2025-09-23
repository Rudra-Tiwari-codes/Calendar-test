#!/usr/bin/env python3
"""
Debug script to test Google Calendar datetime format handling
"""

from datetime import datetime
import pytz

def test_google_datetime_parsing():
    """Test how we're parsing Google Calendar datetime strings"""
    
    # Simulate what Google Calendar might return
    test_cases = [
        "2025-09-26T15:00:00+10:00",  # With timezone offset
        "2025-09-26T15:00:00.000Z",   # UTC with Z suffix
        "2025-09-26T05:00:00Z",       # UTC with Z suffix (different time)
        "2025-09-26",                 # Date only
    ]
    
    print("🔍 Testing Google Calendar datetime parsing:")
    
    for test_case in test_cases:
        print(f"\nTesting: '{test_case}'")
        
        # Current parsing method (what's in the bot)
        if "T" in test_case:
            try:
                # This is what the bot currently does
                start_dt = datetime.fromisoformat(test_case.replace("Z", "+00:00"))
                print(f"Current method result: {start_dt}")
                print(f"Timezone: {start_dt.tzinfo}")
                print(f"Formatted: {start_dt.strftime('%A, %B %d at %I:%M %p')}")
                
                # Convert to Melbourne timezone for display
                melb_tz = pytz.timezone('Australia/Melbourne')
                melb_dt = start_dt.astimezone(melb_tz)
                print(f"In Melbourne time: {melb_dt.strftime('%A, %B %d at %I:%M %p')}")
                
            except Exception as e:
                print(f"❌ Current method failed: {e}")
        else:
            print("Date only format - no time conversion needed")

if __name__ == "__main__":
    test_google_datetime_parsing()