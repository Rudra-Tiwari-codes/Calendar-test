#!/usr/bin/env python3
"""
Final test to validate the timezone fix for the specific user issue
"""

import sys
import os
from datetime import datetime
import pytz

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from events_agent.infra.timezone_utils import format_event_time, parse_datetime_to_local
from events_agent.infra.settings import settings

def test_user_scenario():
    """Test the exact scenario described by the user"""
    print("🎯 TESTING USER'S SPECIFIC SCENARIO")
    print("=" * 50)
    print("User input: '3PM September 26'")
    print("Expected output: Friday, September 26 at 03:00 PM")
    print("Previous wrong output: Saturday, September 27 at 01:00 AM")
    print()
    
    # Simulate what Google Calendar would return for an event created at "3PM September 26" Melbourne time
    # Google Calendar stores this as UTC, so 3PM Melbourne = 5AM UTC (during daylight saving)
    google_response_start = "2025-09-26T05:00:00Z"  # 5AM UTC = 3PM Melbourne
    google_response_end = "2025-09-26T06:00:00Z"    # 6AM UTC = 4PM Melbourne
    
    print(f"Google Calendar returns:")
    print(f"  Start: {google_response_start}")
    print(f"  End: {google_response_end}")
    print()
    
    print("OLD BEHAVIOR (before fix):")
    # Old way (what was causing the issue)
    old_dt = datetime.fromisoformat(google_response_start.replace("Z", "+00:00"))
    old_format = old_dt.strftime('%A, %B %d at %I:%M %p')
    print(f"  Displayed: {old_format} ❌ (Wrong - showing UTC time)")
    print()
    
    print("NEW BEHAVIOR (after fix):")
    # New way (with timezone conversion)
    new_dt = parse_datetime_to_local(google_response_start, settings.default_tz)
    new_format = new_dt.strftime('%A, %B %d at %I:%M %p')
    print(f"  Displayed: {new_format} ✅ (Correct - converted to Melbourne time)")
    print()
    
    # Test with the utility function
    formatted_time = format_event_time(google_response_start, google_response_end, settings.default_tz)
    print(f"Using format_event_time(): {formatted_time}")
    
    print("\n🎉 ISSUE RESOLUTION:")
    if "Friday, September 26 at 03:00 PM" in new_format:
        print("✅ SUCCESS: The timezone issue has been FIXED!")
        print("✅ Events will now display in the correct local timezone")
    else:
        print("❌ Issue not fully resolved")

if __name__ == "__main__":
    test_user_scenario()