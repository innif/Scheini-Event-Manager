from nicegui import ui
from database import Database, OPEN_STAGE
import datetime

db = Database()
db.print_events()

def add_reservation_dialog(event_id):
    d = ui.dialog()
    d.open()
    with d, ui.card():
        name_input = ui.input("Name")
        number_input = ui.number("Anzahl")
        comment_input = ui.input("Kommentar")
        ui.button("Speichern", on_click=lambda: [db.add_reservation(event_id, name_input.value, number_input.value, comment = comment_input.value), d.close()])

def date_changed(date):
    print(date.value)
    event_card.clear()
    event = db.get_event(date.value)
    date = datetime.datetime.fromisoformat(date.value)
    with event_card:
        if event is not None:
            print(event)
            ui.label(f"{event[1]} {event[2]}").classes("text-lg")
            ui.label(f"Moderation: {event[3]}")
            ui.label(f"Technik: {event[4]}")
            artists = db.get_artists(event[0])
            if artists is not None:
                for artist in artists:
                    ui.label(f"{artist[1]}")
            ui.label("Reservierungen").classes('text-sm')
            reservations = db.get_reservations(event[0])
            if reservations is not None:
                for reservation in reservations:
                    with ui.row():
                        ui.label(f"{reservation[2]}").classes("font-semobold")
                    ui.label(f"{reservation[2]}: {reservation[3]}")
                    ui.button
            ui.button("Reservierung hinzufügen", on_click=lambda: add_reservation_dialog(event[0]))
        else:
            print("No event on this date")
            ui.label("No event on this date")
    
calendar = ui.date(on_change=date_changed)
event_card = ui.card()

ui.run(language='de')