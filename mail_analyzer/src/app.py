import fastapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request, HTTPException, Depends, status
import secrets
import json
from ai_analyze import analyze_mail, get_event_details, analyze_mail_response
import datetime
import locale
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from configparser import ConfigParser

# datetime locale
locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")

app = fastapi.FastAPI()
security = HTTPBasic()
config_object = ConfigParser()
config_object.read("config.ini")
secrets_object = config_object["API"]

origins = [
    "http://localhost:*",
    "http://127.0.0.1:*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, secrets_object.get("user"))
    correct_password = secrets.compare_digest(credentials.password, secrets_object.get("password"))
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

def display_html(output):
    text = ""
    reservations = output["bookings"]
    for r in reservations:
        date = r["date"]
        name = r["name"]
        quantity = r["quantity"]
        comment = r["comment"]
        event_details = get_event_details(date)
        print(event_details)
        if len(comment) > 0:
            comment = "({}) ".format(comment)
        date_pretty = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%a %d.%m.%Y")
        text += "{} ({} Reservierungen) - {} - {}x {}- ".format(date_pretty, event_details.get("num_reservations"), name, quantity, comment)
        link = "http://rotes-buch.scheinbar.de/event/{}/add?name={}&quantity={}&comment={}".format(date, name, quantity, comment)
        #include link as html
        text += "<a href='{}'>Reservierung hinzufügen</a><br>".format(link)
    for date in output["modify"]:
        event_details = get_event_details(date)
        date_pretty = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%a %d.%m.%Y")
        text += "Änderungswunsch: {} ({} Reservierungen) - ".format(date_pretty, event_details.get("num_reservations"), event_details.get("name"))
        link = "http://rotes-buch.scheinbar.de/event/{}/".format(date)
        text += "<a href='{}'>Tag Anzeigen</a><br>".format(link)
    if len(reservations) == 0 and len(output["modify"]) == 0:
        text += "Keine Reservierungen in der Mail gefunden."
    return text

def msg_to_string(msg):
    out = ""
    headers = msg.get("headers", {})
    out += "From: {}\n".format(headers.get("from", [""])[0])
    out += "To: {}\n".format(headers.get("to", [""])[0])
    out += "Subject: {}\n".format(headers.get("subject", [""])[0])
    out += "Date: {}\n".format(headers.get("date", [""])[0])
    out += "---\n"
    out += combine_parts(msg)
    return out

def combine_parts(msg):
    out = ""
    if "body" in msg:
        content_type = msg.get("contentType", "")
        body_content = msg.get("body", "").replace("=\n", "")  # Entfernt quoted-printable breaks

        # Teil als HTML rendern, wenn es sich um HTML handelt, andernfalls als Text
        if content_type == "text/html":
            out += body_content
        elif content_type == "text/plain":
            out += body_content

        return msg["body"]
    if "parts" in msg:
        for part in msg["parts"]:
            out += combine_parts(part)
    return out

@app.post("/analyze")
async def analyze(request: Request, username: str = Depends(get_current_username)):
    # get json body
    try:
        msg = await request.json()
        parts = msg.get("content", {})
        msg_string = msg_to_string(parts)
    except Exception as e:
        return {"text": "Error: Unable to read message content", "res": None}
    if len(msg_string) > 10000:
        return {"text": "Message too long", "res": None}
    try:
        res = analyze_mail(msg_string)
    except Exception as e:
        return {"text": "Error: Unable to analyze message content", "res": None}
    try:
        text = display_html(res)
    except Exception as e:
        return {"text": "Error: Unable to display message content", "res": None}
    # return as json
    return {"text": text, "res": res}

@app.post("/gen_response")
async def gen_response(request: Request, username: str = Depends(get_current_username)):
    # get json body
    try:
        msg = await request.json()
        parts = msg.get("content", {})
        msg_string = msg_to_string(parts)
    except Exception as e:
        return {"text": "Error: Unable to read message content", "res": None}
    if len(msg_string) > 10000:
        return {"text": "Message too long", "res": None}
    try:
        text = analyze_mail_response(msg_string, msg)
    except Exception as e:
        print(e)
        return {"text": "Error: Unable to analyze message content", "res": None}
    # return as json
    return {"text": text}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)