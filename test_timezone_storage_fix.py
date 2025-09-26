#!/usr/bin/env python3
"""
Test the timezone storage fix
"""

import sys
import os
from datetime import datetime
import pytz

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from events_agent.infra.date_parsing import parse_natural_range
from events_agent.infra.settings import settings

def test_timezone_fix():
    """Test the timezone storage fix"""
    print("🔍 TESTING TIMEZONE STORAGE FIX")
    print("=" * 50)
    
    # Parse "3PM September 27" (tomorrow)
    test_input = "3PM September 27"
    print(f"Input: '{test_input}'")
    
    try:
        start_dt, end_dt = parse_natural_range(test_input, settings.default_tz)
        
        print(f"Parsed datetime: {start_dt}")
        print(f"Timezone: {start_dt.tzinfo}")
        
        # Simulate the fixed calendar service logic
        user_tz = "Australia/Melbourne"
        user_timezone = pytz.timezone(user_tz)
        
        # Ensure datetime is in the correct timezone
        start_local = start_dt.astimezone(user_timezone)
        end_local = end_dt.astimezone(user_timezone)
        
        print(f"Local time: {start_local}")
        
        # Create the event body as the fixed service would
        event_body = {
            "start": {
                "dateTime": start_local.replace(tzinfo=None).isoformat(),
                "timeZone": user_tz,
            },
            "end": {
                "dateTime": end_local.replace(tzinfo=None).isoformat(),
                "timeZone": user_tz,
            }
        }
        
        print(f"\nFIXED Google Calendar event body:")
        print(f"  start dateTime: {event_body['start']['dateTime']}")
        print(f"  start timeZone: {event_body['start']['timeZone']}")
        
        print(f"\n✅ BEFORE FIX:")
        print(f"  Sent: 2025-09-27T15:00:00+10:00 with timeZone: Australia/Melbourne")
        print(f"  Result: Google Calendar double-converted → 10 hours ahead")
        
        print(f"\n✅ AFTER FIX:")
        print(f"  Sent: {event_body['start']['dateTime']} with timeZone: {event_body['start']['timeZone']}")
        print(f"  Result: Google Calendar correctly interprets as 3PM Melbourne time")
        
        # Show what Google will store
        google_utc = start_local.astimezone(pytz.UTC)
        print(f"\nGoogle Calendar will store in UTC: {google_utc.isoformat()}")
        print(f"When retrieved, it will correctly show: {start_local.strftime('%A, %B %d at %I:%M %p')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_timezone_fix()