import requests
import dialogs
from nicegui import ui, run, app
import hashlib
import json
import datetime
from requests.auth import HTTPBasicAuth

event_types = {
    "open_stage": "Open Stage",
    "solo": "Solo",
    "other": "Sonstiges"
}


# key = None
session = requests.Session()
url = "http://localhost:8000/"

def get_secrets():
    try:
        return json.load(open("secrets.json"))
    except:
        print("No secrets file found")
        return {}
    
secrets = get_secrets()

async def api_call(session, path: str, method = "GET", json = None):
    dialog = dialogs.loading_dialog()
    auth = HTTPBasicAuth(app.storage.user.get("api-user"), app.storage.user.get("api-pswd"))
    res = None
    if method == "GET":
        res = await run.io_bound(session.get, url + path, json = json, auth = auth)
    elif method == "POST":
        res = await run.io_bound(session.post, url + path, json = json, auth = auth)
    elif method == "PUT":
        res = await run.io_bound(session.put, url + path, json = json, auth = auth)
    elif method == "DELETE":
        res = await run.io_bound(session.delete, url + path, json = json, auth = auth)
    if res.status_code != 200:
        ui.notify("Fehler bei der Anfrage", color="negative")
        ui.notify(res.text, color="negative")
    dialog.close()
    return res.json()
