from nicegui import ui
import datetime
from util import event_types

def loading_dialog():
    with ui.dialog() as dialog, ui.card():
        #ui.label("Bitte warten...").classes('text-xl')
        ui.spinner(size = "3em")
    dialog.props('persistent')
    dialog.open()
    return dialog

def confirm_dialog(title, text):
    with ui.dialog() as dialog, ui.card():
        ui.label(title).classes('text-xl')
        ui.label(text).classes('text')
        with ui.row().classes('w-full'):
            ui.button('Abbrechen', on_click=lambda: dialog.submit(False))
            ui.button('Bestätigen', on_click=lambda: dialog.submit(True))
    return dialog

def edit_reservation_dialog(session, reservation_id = None, date = None, name = "", num = 1, comment = ""):
    if reservation_id is None and date is None:
        return
    if reservation_id is not None:
        res = session.get("http://localhost:8000/reservations/" + str(reservation_id)).json()
        name = res['name']
        num = res['quantity']
        comment = res['comment']
        date = res['date']
    def save():
        if reservation_id is None:
            session.post("http://localhost:8000/reservations/", json = {
                'name': name_input.value,
                'quantity': num_input.value,
                'comment': comment_input.value,
                'date': date
            })
        else:
            session.put("http://localhost:8000/reservations/" + str(reservation_id), json = {
                'name': name_input.value,
                'quantity': num_input.value,
                'comment': comment_input.value,
                'date': date
            })
        ui.notify('Reservierung gespeichert')
        dialog.submit(True)
    with ui.dialog() as dialog, ui.card():
        if reservation_id is None:
            ui.label('Neue Reservierung').classes('text-xl')
        else:
            ui.label('Reservierung bearbeiten').classes('text-xl')
        ui.label('Datum: ' + datetime.date.fromisoformat(date).strftime("%d.%m.%y")).classes('text')
        name_input = ui.input('Name', value=name).classes('w-full')
        num_input = ui.number('Anzahl', value=num).classes('w-full')
        comment_input = ui.input('Kommentar', value=comment).classes('w-full')
        with ui.row().classes('w-full'):
            cancel_button = ui.button('Abbrechen', on_click=lambda: dialog.submit(False))
            save_button = ui.button('Speichern', on_click=save)
    return dialog

def edit_event_dialog(session, date, moderator = "", event_kind = "open_stage"):
    res = session.get("http://localhost:8000/events/" + str(date)).json()
    if res is not None:
        event_kind = res.get('event_kind')
        moderator = res.get('moderator')
    async def delete():
        d = confirm_dialog('Event löschen', 'Soll das Event wirklich gelöscht werden?')
        if await d:
            session.delete("http://localhost:8000/events/" + str(date))
            dialog.submit('delete')
    def save():
        if res is None:
            r = session.post("http://localhost:8000/events/", json = {
                'date': date_input.value,
                'event_kind': event_kind_input.value,
                'moderator': moderator_input.value,
            })
            print(r)
        else:
            r = session.put("http://localhost:8000/events/" + str(date), json = {
                'event_kind': event_kind_input.value,
                'moderator': moderator_input.value,
            })
            print(r)
        ui.notify('Reservierung gespeichert')
        dialog.submit('saved')
    with ui.dialog() as dialog, ui.card():
        if res is None:
            ui.label('Neues Event').classes('text-xl')
            ui.label('Datum: ' + datetime.date.fromisoformat(date).strftime("%d.%m.%y"))
        else:
            ui.label('Event bearbeiten').classes('text-xl')
            date_input = ui.input('Date', value=date).classes('w-full')
        event_kind_input = ui.select(event_types, value=event_kind).classes('w-full')
        moderator_input = ui.input('Moderator', value=moderator).classes('w-full')
        if res is not None:
            delete_button = ui.button('Event löschen', on_click=delete)
        with ui.row().classes('w-full'):
            cancel_button = ui.button('Abbrechen', on_click=lambda: dialog.submit(None))
            save_button = ui.button('Speichern', on_click=save)
    return dialog