from nicegui import ui
import datetime
from util import event_types, api_call

columns_artists = [
    {'name': 'name', 'label': 'Name', 'field': 'name', 'required': True, 'align': 'left'},
    {'name': 'comment', 'label': 'Kommentar', 'field': 'comment'},
    {'name': 'buttons', 'label': '', 'field': 'buttons'},
]

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

async def edit_reservation_dialog(session, reservation_id = None, date = None, name = "", num = 1, comment = ""):
    if reservation_id is None and date is None:
        return
    if reservation_id is not None:
        res = await api_call(session, "reservations/" + str(reservation_id))
        name = res['name']
        num = res['quantity']
        comment = res['comment']
        date = res['date']
    async def save():
        if reservation_id is None:
            await api_call(session, "reservations/", "POST", json = {
                'name': name_input.value,
                'quantity': num_input.value,
                'comment': comment_input.value,
                'date': date
            })
        else:
            await api_call(session, "reservations/" + str(reservation_id), "PUT", json = {
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

async def edit_bookings_dialog(session, date):
    event = await api_call(session, f"events/{date}")
    artists = await api_call(session, f"artists/event/{date}")
    async def delete(msg):
        artist_id = msg.args['row']['id']
        d = confirm_dialog('Künstler*in löschen', 'Soll die Künstler*in wirklich gelöscht werden?')
        if await d:
            print("bookings/?event_id={"+str(event.get("id"))+"}&artist_id="+str(artist_id))
            await api_call(session, "bookings/?event_id="+str(event.get("id"))+"&artist_id="+str(artist_id), "DELETE")
            await update_artists()
    async def add_artist():
        await api_call(session, f'bookings/?event_id={event.get("id")}&artist={new_artist.value}', method="POST")
        new_artist.value = ""
        await update_artists()
    async def update_artists():
        table.rows = await api_call(session, f"artists/event/{date}")
        table.update()
    with ui.dialog() as dialog, ui.card():
        table = ui.table(columns=columns_artists, rows=artists).classes('w-full')
        table.add_slot(f'body-cell-buttons', """
                <q-td :props="props">
                    <q-btn @click="$parent.$emit('delete', props)" icon="delete" dense flat color='primary'/>
                </q-td>
            """)
        table.on('delete', delete)
        with ui.row().classes('w-full no-wrap'):
            new_artist = ui.input('Künstler*in hinzufügen').classes('w-full')
            ui.space()
            ui.button(icon="add", on_click=add_artist, color="positive").classes("rounded-full my-auto flat")
        ui.button('Schließen', on_click=dialog.submit).classes('w-full')
    return dialog

async def edit_event_dialog(session, date = None, moderator = "", event_kind = "open_stage"):
    res = None
    if date is not None:
        res = await api_call(session, "events/" + str(date))
    if res is not None:
        event_kind = res.get('event_kind')
        moderator = res.get('moderator')
    async def delete():
        d = confirm_dialog('Event löschen', 'Soll das Event wirklich gelöscht werden?')
        if await d:
            await api_call(session, "events/" + str(date), "DELETE")
            dialog.submit('delete')
    async def save():
        try:
            date = datetime.date.fromisoformat(date_input.value)
        except:
            ui.notify('Ungültiges Datum', color='negative')
            return
        if res is None:
            r = await api_call(session, "events/?date=" + date_input.value, "POST", json = {
                'event_kind': event_kind_input.value,
                'moderator': moderator_input.value,
            })
        else:
            r = await api_call(session, "events/" + str(date), "PUT", json = {
                'event_kind': event_kind_input.value,
                'moderator': moderator_input.value,
            })
        ui.notify('Event gespeichert')
        dialog.submit('edit')
    with ui.dialog() as dialog, ui.card():
        if res is None:
            ui.label('Neues Event').classes('text-xl')
        else:
            ui.label('Event bearbeiten').classes('text-xl')
        date_input = ui.input('Datum (YYYY-MM-DD)', value=date).classes('w-full')
        event_kind_input = ui.select(event_types, value=event_kind).classes('w-full')
        moderator_input = ui.input('Moderator', value=moderator).classes('w-full')
        if res is not None:
            delete_button = ui.button('Event löschen', on_click=delete, color='red', icon = 'delete').classes('w-full')
        with ui.row().classes('w-full'):
            cancel_button = ui.button('Abbrechen', on_click=lambda: dialog.submit(None))
            save_button = ui.button('Speichern', on_click=save)
    return dialog