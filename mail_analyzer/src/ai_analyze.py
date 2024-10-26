from openai import OpenAI
from configparser import ConfigParser
import datetime
import json
import requests

# Read config.ini file
config_object = ConfigParser()
config_object.read("config.ini")
openai_conf = config_object["OPENAI"]
server_conf = config_object["SERVER"]

prompt = open("prompt_short.txt", "r", encoding="utf-8").read()
prompt_response = open("prompt_resp.txt", "r", encoding="utf-8").read()

client = OpenAI(api_key=openai_conf["api_key"])

def get_event_details(date):
    event_details = requests.get(
            "{}/events/{}".format(server_conf["host"], date), 
            auth=(server_conf["user"], server_conf["password"])
        ).json()
    return event_details

def analyze_mail(mail_content):
    prompt_copy = prompt + "\n"
    # prompt_copy += "\n\nHeute ist " + datetime.datetime.now().strftime("%a %Y-%m-%d")

    completion = client.chat.completions.create(
        model="gpt-4o-mini",	
        messages=[
            {"role": "system", "content": prompt_copy},
            {"role": "user", "content": mail_content},
            {"role": "user", "content": "Analysiere die Mail und extrahiere die Reservierungen."}
        ]
    )

    text = completion.choices[0].message.content
 
    return json.loads(text)

def analyze_mail_response(mail_content, msg):
    prompt_copy = prompt_response + "\n"
    
    bookings_info = json.dumps(msg.get("details", {}).get("res", {}).get("bookings", []), indent=4)

    dates = [b.get("date") for b in msg.get("details", {}).get("res", {}).get("bookings", [])]
    dates += [b for b in msg.get("details", {}).get("res", {}).get("modify", [])]
    reservations_info = ""
    for d in dates:
        event_details = requests.get(
            "{}/events/{}".format(server_conf["host"], d), 
            auth=(server_conf["user"], server_conf["password"])
        ).json()
        assert isinstance(event_details, dict)
        event_details.pop("technician", None)
        event_details.pop("num_artists", None)
        reservations_info += json.dumps(event_details, indent=4) + "\n"

    prompt_copy = prompt_copy.replace("insert_reservations", reservations_info)
    prompt_copy = prompt_copy.replace("insert_actions", bookings_info)

    prompt_copy += "\n\nHeute ist " + datetime.datetime.now().strftime("%a %Y-%m-%d")

    print(prompt_copy)
    completion = client.chat.completions.create(
        model="gpt-4o-mini",	
        messages=[
            {"role": "system", "content": prompt_copy},
            {"role": "user", "content": mail_content},
            {"role": "user", "content": "Analysiere die Mail und verfasse eine Antwort."}
        ]
    )

    text = completion.choices[0].message.content
 
    return text