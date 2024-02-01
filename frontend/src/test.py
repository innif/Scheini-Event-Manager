import datetime
import requests

start_date = datetime.date(2024, 1, 1)
end_date = datetime.date(2024, 7, 31)

event_type = "open_stage"
moderator = ""

current_date = start_date
while current_date <= end_date:
    if current_date.weekday() == 2:
        moderator = input("Who is the moderator on Wednesday, " + current_date.strftime("%d.%m.%Y") + "? ")
    if current_date.weekday() in [2, 3, 4, 5]:  # Wednesday, Thursday, Friday, Saturday
        request_url = f"http://localhost:8000/events/?date={current_date.isoformat()}&event_kind={event_type}&moderator={moderator}"
        # Make the request to the URL
        res = requests.post(request_url)
        print(res.text)
    current_date += datetime.timedelta(days=1)
