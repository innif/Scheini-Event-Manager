import locale
from nicegui import ui, events
from database import database
import datetime

# Set the locale to German
locale.setlocale(locale.LC_TIME, 'de_DE')

db = database()

def create_event(date: str):
    event = db.create_event(date)
    edit_event_dialog(event)

def edit_event_dialog(event):
    with ui.dialog() as d, ui.card():
        ui.label('Event bearbeiten')
        name_input = ui.input('Moderation', value=event[1])
        date_input = ui.input('Datum', value=event[2])
        kind_input = ui.select(label = 'Art', options=['open-stage', 'solo', 'sonstiges'], value=event[4]).classes("w-full")
        def save():
            db.edit_event(event[0], name_input.value, date_input.value, kind_input.value)
            d.close()
            on_data_change()
        ui.button('Speichern', on_click=lambda: save())
    d.open()
        
def get_event(date: str):
    try:
        return db.get_event(date)
    except Exception as e:
        print(e)
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
                ui.button(icon="edit", on_click=lambda: edit_event_dialog(event))
            ui.label("TODO")

def update_calendar_view():
    date = datepicker.value
    print(date)
    event = get_event(date)
    print(event)
    print_event(event)
    print_reservations(event)

def on_data_change():
    update_calendar_view()

def add_reservation_dialog(event_id: int):
    with ui.dialog() as d, ui.card():
        ui.label('Reservierung hinzufügen')
        name_input = ui.input('Name')
        quantity_input = ui.number('Menge', value=1)
        comment_input = ui.input('Kommentar')
        def save():
            db.add_reservation(name_input.value, quantity_input.value, event_id, comment_input.value)
            d.close()
            on_data_change()
        ui.button('Speichern', on_click=lambda: save())
    d.open()

def print_reservation_row(reservation):
    def save():
        db.edit_reservation(reservation[0], name_input.value, quantity_input.value, comment_input.value)
        on_data_change()
    with ui.row():
        name_input = ui.input(value = reservation[1])
        quantity_input = ui.number(value = reservation[2])
        comment_input = ui.input(value = reservation[4])

def show_reservations_dialog(event_id: int):
    with ui.dialog() as d, ui.card():
        ui.label('Reservierungen')
        reservation_entries = db.get_reservation(event_id)
        if reservation_entries is None or len(reservation_entries) == 0:
            ui.label('Keine Reservierungen')
        else:
            with ui.scroll_area():
                for reservation in reservation_entries:
                    print_reservation_row(reservation)

    d.open()

def create_list_view():
    l = db.get_future_events()
    with ui.column().classes("w-full") as grid:
        for event in l:
            create_event_card(event)

def create_event_card(event):
    date = datetime.date.fromisoformat(event[2])
    with ui.card().classes("w-full"):
        with ui.row():
            ui.label(date.strftime('%A, %d.%m.%Y')).classes('text-xl')
            ui.splitter()
            ui.label(event[1]).classes('text-lg')
        with ui.grid(columns = 2):
            ui.label("{} Reservierungen".format(db.get_reservation_count(event[0])))
            with ui.row():
                ui.button(icon="visibility", on_click=lambda: show_reservations_dialog(event[0]))
                ui.button(icon="add", on_click=lambda: add_reservation_dialog(event[0]))
            ui.label("{} Künstler".format(db.get_reservation_count(event[0])))
            with ui.row():
                ui.button(icon="visibility")
                ui.button(icon="add")
        ui.button('Event bearbeiten', on_click=lambda: edit_event_dialog(event))

with ui.tabs(value="calendar").classes("w-full") as tabs:
    ui.tab("calendar", "Kalender", icon="calendar_month").classes("w-full")
    ui.tab("list", "Liste", icon="list").classes("w-full")

with ui.tab_panels(tabs, value="calendar").classes("w-full"):
    with ui.tab_panel("calendar"):
        with ui.row().classes("w-full"):
            datepicker = ui.date(on_change=lambda date: update_calendar_view(), value=datetime.date.today().isoformat())
            reservations = ui.card()
            event_details = ui.card()
            update_calendar_view()
    with ui.tab_panel("list").classes("w-full"):
        create_list_view()
        pass
ui.run(language="de")