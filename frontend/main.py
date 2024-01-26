import requests

res = requests.get("http://localhost:5000/reservation", json = {"id": 500})
print(res.text)

res = requests.get("http://localhost:5000/reservations", json={"date": "2024-01-25"})
print(res.text)