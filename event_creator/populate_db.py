import requests
from requests.auth import HTTPBasicAuth

textfile = open("events.txt", "r", encoding="utf-8")

url = ""
user = ""
pswd = ""

session = requests.Session()
auth = HTTPBasicAuth(user, pswd)

for line in textfile:
    date, event_kind, moderator = line.split(maxsplit=2)
    while moderator[-1] == "\n":
        moderator = moderator[:-1]
    print(date, moderator)
    res = session.post(url + "events/?date=" + date, auth=auth, json={"event_kind": event_kind, "moderator": moderator})
    print(res.text)