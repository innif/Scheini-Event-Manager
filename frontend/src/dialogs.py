from nicegui import ui
import datetime

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
        dialog.close()
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
            ui.button('Abbrechen', on_click=dialog.close)
            ui.button('Speichern', on_click=save)
    dialog.open()