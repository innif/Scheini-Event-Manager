import requests
import datetime
from nicegui import ui
import requests
import locale
from overview import overview_page

locale.setlocale(locale.LC_ALL, 'de_DE')

session = requests.Session()
session.get("http://localhost:8000/")

overview_page(session)

ui.run()