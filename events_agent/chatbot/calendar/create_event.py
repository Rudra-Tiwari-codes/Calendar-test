from typing import List
from tools.tool import BaseTool, Params
from services.service import get_calendar_service

class CreateEvent(BaseTool):    
    @property
    def name(self) -> str:
        return "CreateEvent"
    
    @property
    def description(self) -> str:
        return "Creates an event in Google Calendar"
    
    @property
    def parameters(self) -> List[Params]:
        return [
            Params(
                name="summary",
                type="string",
                description="Name of the event"
            ),
            Params(
                name="description",
                type="string",
                description="Description of the event"
            ),
            Params(
                name="location",
                type="string",
                description="Location of the event"
            ),
            Params(
                name="start_datetime",
                type="string",
                description="Start date and time of the event in ISO format (e.g., 2023-10-01T10:00:00)"
            ),
            Params(
                name="end_datetime",
                type="string",
                description="End date and time of the event in ISO format (e.g., 2023-10-01T11:00:00)"
            ),
            Params(
                name="timezone",
                type="string",
                description="Timezone of the event (default is 'Australia/Sydney')",
                default="Australia/Sydney"
            )
        ]
    
    def execute(self, summary: str, description: str, location: str, start_datetime: str, end_datetime: str, timezone: str='Australia/Sydney') -> str:
        try:
            service = get_calendar_service()
            event = {
                'summary': summary,
                'location': location,
                'description': description,
                'start': {
                    'dateTime': start_datetime,
                    'timeZone': timezone,
                },
                'end': {
                    'dateTime': end_datetime,
                    'timeZone': timezone,
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 10},
                    ],
                },
            }
            event_result = service.events().insert(calendarId='primary', body=event).execute()
            return f"Event created with ID: {event_result['id']}"
            
        except Exception as e:
            return f"Error: {str(e)}" 
