from nicegui import ui, events
from database import database
import datetime

db = database()

def create_event(date: str):
    event = db.create_event(date)
    edit_event_dialog(event)

def edit_event_dialog(event):
    with ui.dialog() as d, ui.card():
        ui.label('Event bearbeiten')
        name_input = ui.input('Name', value=event[1])
        date_input = ui.input('Datum', value=event[2])
        kind_input = ui.select(label = 'Art', options=['open-stage', 'solo', 'sonstiges'], value=event[4]).classes("w-full")
        def save():
            db.edit_event(event[0], name_input.value, date_input.value, kind_input.value)
            d.close()
            update()
        ui.button('Speichern', on_click=lambda: save())
    d.open()
        
def get_event(date: str):
    try:
        print(date.value)
        return db.get_event(date.value)
    except:
        return None

def print_reservations(event):
    reservations.clear()
    if event is None:
        return
    reservation_entries = db.get_reservation(event[0])
    with reservations, ui.column():
        ui.button('Reservierung hinzufügen')
        if reservation_entries is None or len(reservation_entries) == 0:
            ui.label('Keine Reservierungen')
        else:
            ui.label('Reservierungen').classes('text-2xl')
            ui.table(['Name', 'Menge', 'Kommentar'], reservation_entries)

def print_event(event):
    event_details.clear()
    
    with event_details:
        if event is None:
            ui.label('Kein Event an diesem Tag')
            ui.button('Event hinzufügen', on_click=lambda: create_event(datepicker.value))
        else:
            # print all event details
            with ui.row():
                ui.label('Event Details').classes('text-2xl')
                ui.button('Event bearbeiten', on_click=lambda: edit_event_dialog(event))
            ui.label("TODO")

def update():
    date = datepicker.value
    event = get_event(date)
    print_event(event)
    print_reservations(event)

datepicker = ui.date(on_change=lambda date: update(), value=datetime.date.today().isoformat())
reservations = ui.card()
event_details = ui.card()
db.print_events()