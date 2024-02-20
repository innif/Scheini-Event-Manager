import requests
import dialogs
from nicegui import ui, run, app
import hashlib
import json
import datetime
from requests.auth import HTTPBasicAuth

class MediaBreakpoints:
    def __init__(self):
        self.xs = 0
        self.sm = 576
        self.md = 768
        self.lg = 992
        self.xl = 1200

event_types = {
    "open_stage": "Open Stage",
    "solo": "Solo",
    "other": "Sonstiges"
}

# key = None
session = requests.Session()
url = "http://localhost:8000/"

def breakpoint(size, css_class, max=True):
    '''Returns a string that can be used in the classes attribute of a ui element to apply a css class only on a certain breakpoint
    size: str, one of "xs", "sm", "md", "lg", "xl"
    css_class: str or list of str, the css class(es) to apply
    max: bool, if True the class is applied only on screens smaller than the given breakpoint, if False only on screens larger than the given breakpoint'''
    width = getattr(MediaBreakpoints(), size)
    if type(css_class) == list:
        breakpoint = ""
        for css in css_class:
            if max:
                breakpoint += f"max-[{width}px]:{css} "
            else:
                breakpoint += f"min-[{width}px]:{css} "
    else:
        if max:
            breakpoint = f"max-[{width}px]:{css_class}"
        else:
            breakpoint = f"min-[{width}px]:{css_class}"
    return breakpoint

def get_secrets():
    try:
        return json.load(open("secrets.json"))
    except:
        print("No secrets file found")
        return {}
    
secrets = get_secrets()

async def api_call(session, path: str, method = "GET", json = None, silent = False):
    dialog = None
    if not silent:
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
    if not silent:
        dialog.close()
    return res.json()
