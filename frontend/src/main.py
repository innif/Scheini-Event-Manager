import requests
import datetime
from typing import Optional

from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from nicegui import Client, app, ui
import requests
import locale
from overview import overview_page
from event_detail import detail_page
import json
from util import get_secrets

locale.setlocale(locale.LC_ALL, 'de_DE')

session = requests.Session()

unrestricted_page_routes = {'/login'}

secrets = get_secrets()

class AuthMiddleware(BaseHTTPMiddleware):
    """This middleware restricts access to all NiceGUI pages.

    It redirects the user to the login page if they are not authenticated.
    """
    async def dispatch(self, request: Request, call_next):
        if not app.storage.user.get('authenticated', False):
            if request.url.path in Client.page_routes.values() and request.url.path not in unrestricted_page_routes:
                app.storage.user['referrer_path'] = request.url.path  # remember where the user wanted to go
                return RedirectResponse('/login')
        return await call_next(request)


app.add_middleware(AuthMiddleware)

@ui.page('/')
async def index_page():
    await overview_page(session)

@ui.page('/event/{date}')
async def event_page(date: str):
    await detail_page(session, date)

@ui.page('/login')
def login() -> Optional[RedirectResponse]:
    def try_login() -> None:  # local function to avoid passing username and password as arguments
        if secrets.get("logins").get(username.value) == password.value:
            app.storage.user.update({'username': username.value, 'authenticated': True})
            api_login = secrets.get('api-login')
            app.storage.user.update({'api-user': api_login.get("username"), 'api-pswd': api_login.get("password")})
            ui.open(app.storage.user.get('referrer_path', '/'))  # go back to where the user wanted to go
        else:
            ui.notify('Wrong username or password', color='negative')

    if app.storage.user.get('authenticated', False):
        return RedirectResponse('/')
    with ui.card().classes('absolute-center'):
        username = ui.input('Username').on('keydown.enter', try_login).classes('w-full')
        password = ui.input('Password', password=True, password_toggle_button=True).on('keydown.enter', try_login).classes('w-full')
        ui.button('Log in', on_click=try_login).classes('w-full')
    return None

ui.run(storage_secret=secrets.get('storage-secret'))