# populate thew database with a bunch of random reservations

import random
import requests

url = "http://localhost:8000/reservations/"
user = "user"
pswd = "password"

session = requests.Session()

names = [
    "John Doe",
    "Jane Smith",
    "Michael Johnson",
    "Emily Davis",
    "David Brown",
    "Sarah Wilson",
    "Robert Taylor",
    "Olivia Martinez",
    "William Anderson",
    "Sophia Thomas"
]

comments = [
    None,
    "I'm allergic to peanuts",
    "I'm bringing a friend",
]

textfile = open("events.txt", "r")
events = textfile.readlines()
dates = [e.split()[0] for e in events]

for i in range(1000):
    date = random.choice(dates)
    name = random.choice(names)
    quantity = random.randint(1, 5)
    comment = random.choice(comments)
    r = session.post(url, auth=(user, pswd), json={"date": date, "name": name, "quantity": quantity, "comment": comment})
    print(r.text)