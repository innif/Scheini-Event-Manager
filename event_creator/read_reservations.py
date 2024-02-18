import requests
from requests.auth import HTTPBasicAuth

textfile = open("events.txt", "r", encoding="utf-8")

url = ""
user = ""
pswd = ""

session = requests.Session()
auth = HTTPBasicAuth(user, pswd)
date = ""

for line in textfile:
    if line.startswith("#"):
        number, name = line[1:].split(maxsplit=1)
        while name[-1] == "\n":
            name = name[:-1]
        res = session.post(url + "reservations/", auth=auth, json={"name": name, "quantity": number, "date": date})
        print(res.text)
    else:
        date, _, _ = line.split(maxsplit=2)