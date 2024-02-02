import requests
import dialogs
from nicegui import ui, run

event_types = {
    "open_stage": "Open Stage",
    "solo": "Solo",
    "other": "Sonstiges"
}

session = requests.Session()
url = "http://localhost:8000/"

async def api_call(session, path: str, method = "GET", json = None):
    print("api-call")
    dialog = dialogs.loading_dialog()
    res = None
    if method == "GET":
        res = await run.io_bound(session.get, url + path, json = json)
    elif method == "POST":
        res = await run.io_bound(session.post, url + path, json = json)
    elif method == "PUT":
        res = await run.io_bound(session.put, url + path, json = json)
    elif method == "DELETE":
        res = await run.io_bound(session.delete, url + path, json = json)
    if res.status_code != 200:
        ui.notify("Fehler bei der Anfrage", color="negative")
        ui.notify(res.text, color="negative")
    dialog.close()
    return res.json()