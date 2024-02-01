import requests
import datetime
from nicegui import ui
import requests
import locale
from overview import overview_page
from event_detail import detail_page

locale.setlocale(locale.LC_ALL, 'de_DE')

session = requests.Session()

@ui.page('/')
async def index_page():
    await overview_page(session)

@ui.page('/event/{date}')
async def event_page(date: str):
    await detail_page(session, date)

ui.run()