from typing import List, Dict, Any
from tools.tool import BaseTool, Params
from services.service import get_calendar_service

class UpdateEvent(BaseTool):
    @property
    def name(self) -> str:
        return "UpdateEvent"
    
    @property
    def description(self) -> str:
        return "Updates an existing Google Calendar event by its event ID and specified fields."
    
    @property
    def parameters(self) -> List[Params]:
        return [
            Params(
                name="event_id",
                type="string",
                description="The ID of the event to update"
            ),
            Params(
                name="summary",
                type="string",
                description="Name of the event. Leave empty to keep unchanged."
            ),
            Params(
                name="description",
                type="string",
                description="Description of the event. Leave empty to keep unchanged."
            ),
            Params(
                name="location",
                type="string",
                description="Location of the event. Leave empty to keep unchanged."
            ),
            Params(
                name="start_datetime",
                type="string",
                description="Start date and time of the event in ISO format (e.g., 202  3-10-01T10:00:00). Leave empty to keep unchanged."
            ),
            Params(
                name="end_datetime",
                type="string",
                description="End date and time of the event in ISO format (e.g., 2023-10-01T11:00:00). Leave empty to keep unchanged."
            ),
            Params(
                name="timezone",
                type="string",
                description="Timezone of the event (default is 'Australia/Sydney'). Leave empty to keep unchanged.",
                default="Australia/Sydney"
            )
        ]
    
    def execute(self, event_id: str, summary: str = "", description: str = "", location: str = "", start_datetime: str = "", end_datetime: str = "", timezone: str = 'Australia/Sydney') -> str:
        try:
            service = get_calendar_service()
            event = service.events().get(calendarId='primary', eventId=event_id).execute()

            if summary:
                event['summary'] = summary
            if description:
                event['description'] = description
            if location:
                event['location'] = location
            if start_datetime:
                event['start'] = {
                    'dateTime': start_datetime,
                    'timeZone': timezone
                }
            if end_datetime:
                event['end'] = {
                    'dateTime': end_datetime,
                    'timeZone': timezone
                }

            event['reminders'] = {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            }

            updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
            return f"Event updated: {updated_event.get('htmlLink')}"
        except Exception as e:
            return f"Error: {str(e)}"

