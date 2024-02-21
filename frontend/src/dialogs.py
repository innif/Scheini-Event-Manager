from nicegui import ui
import datetime
from util import event_types, api_call

columns_artists = [
    {'name': 'name', 'label': 'Name', 'field': 'name', 'required': True, 'align': 'left'},
    {'name': 'comment', 'label': 'Kommentar', 'field': 'comment'},
    {'name': 'buttons', 'label': '', 'field': 'buttons'},
]

def artist_input(session, value = None, label = "Künstler*in"):
    # TODO: use with enter 
    async def load_auto_complete():
        options = await api_call(session, "artists/")
        options = [o.get('name') for o in options]
        moderator_input.set_options(options)
    artist_list = [value]
    if value is None:
        artist_list = []
    storage = {"value": value} 
    def on_change(f):
        storage["value"] = f.value
    def store_val(f):
        print(f.args)
        storage["value"] = f.args[0]
    def set_val(f):
        print(f.args)
        if storage.get("value") not in moderator_input.options:
            moderator_input.options.append(storage.get("value"))
        moderator_input.value = storage.get("value")
        print(storage)
    moderator_input = ui.select(artist_list, label=label, value=value, with_input=True, on_change=on_change).props("hide-dropdown-icon")
    moderator_input.on("filter", store_val)
    moderator_input.on("blur", set_val)
    ui.timer(0.1, load_auto_complete, once=True)
    return moderator_input

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
        name_input = ui.input('Name', value=name).classes('w-full').on('keydown.enter', lambda: num_input.run_method("focus"))
        num_input = ui.number('Anzahl', value=num).classes('w-full').on('keydown.enter', lambda: comment_input.run_method("focus"))
        comment_input = ui.input('Kommentar', value=comment).classes('w-full').on('keydown.enter', save)
        name_input.run_method("focus")
        with ui.row().classes('w-full'):
            cancel_button = ui.button('Abbrechen', on_click=lambda: dialog.submit(False))
            save_button = ui.button('Speichern', on_click=save)
    return dialog

async def edit_bookings_dialog(session, date):
    #TODO use artist_input (problem with enter)
    #TODO Technician field
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
        if new_artist.value == "" or new_artist.value is None:
            ui.notify('Künstler*in eingeben', color='negative')
            return
        artist_name: str = new_artist.value
        artist_name = artist_name.strip()
        if artist_name in [r.get("name") for r in table.rows]:
            ui.notify('Künstler*in bereits eingetragen', color='negative')
            return
        await api_call(session, f'bookings/?event_id={event.get("id")}&artist={artist_name}', method="POST")
        new_artist.value = ""
        await update_artists()
    async def update_artists():
        table.rows = await api_call(session, f"artists/event/{date}")
        table.update()
    async def update_comment(msg):
        artist_id = msg.args['id']
        comment = msg.args['comment']
        if comment is None:
            comment = ""
        await api_call(session, f'bookings/?event_id={event.get("id")}&artist_id={artist_id}&comment={comment}', method="PUT")
        ui.notify("Kommentar gespeichert")
    async def load_auto_complete():
        options = await api_call(session, "artists/")
        options = [o.get('name') for o in options]
        new_artist.set_autocomplete(options)
    with ui.dialog() as dialog, ui.card():
        date_str = datetime.date.fromisoformat(event.get('date')).strftime("%A, %d.%m.%Y")
        ui.label(date_str).classes('text-xl')
        table = ui.table(columns=columns_artists, rows=artists).classes('w-full')
        table.add_slot(f'body-cell-buttons', """
                <q-td :props="props">
                    <q-btn @click="$parent.$emit('delete', props)" icon="delete" dense flat color='primary'/>
                </q-td>
            """)
        table.add_slot(f'body-cell-comment', """
                <q-td :props="props">
                    {{ props.row.comment }}
                    <q-popup-edit v-model="props.row.comment" v-slot="scope" buttons 
                       @update:model-value="() => $parent.$emit('comment', props.row)"
                    >
                        <q-input v-model="scope.value" dense autofocus counter/>
                    </q-popup-edit>
                </q-td>
            """)
        table.on('delete', delete)
        table.on('comment', update_comment)
        with ui.row().classes('w-full no-wrap'):
            new_artist = ui.input('Künstler*in hinzufügen').classes('w-full').on('keydown.enter', add_artist)
            ui.space()
            ui.button(icon="add", on_click=add_artist, color="positive").classes("rounded-full my-auto flat")
        ui.button('Schließen', on_click=dialog.submit).classes('w-full')
    ui.timer(0.1, load_auto_complete, once=True)
    ui.timer(0.1, lambda: new_artist.run_method("focus"), once=True)
    return dialog

#TODO edit comment
async def edit_event_dialog(session, date = None, moderator = "", event_kind = "open_stage", alow_edit_date = True, comment = ""):
    res = None
    if date is not None:
        res = await api_call(session, "events/" + str(date))
    if res is not None:
        event_kind = res.get('event_kind')
        moderator = res.get('moderator')
        comment = res.get('comment')
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
                'comment': comment_input.value
            })
        else:
            r = await api_call(session, "events/" + str(date), "PUT", json = {
                'event_kind': event_kind_input.value,
                'moderator': moderator_input.value,
                'comment': comment_input.value
            })
        ui.notify('Event gespeichert')
        dialog.submit('edit')
    with ui.dialog() as dialog, ui.card():
        if res is None:
            ui.label('Neues Event').classes('text-xl')
        else:
            ui.label('Event bearbeiten').classes('text-xl')
        date_input = ui.input('Datum', value=date).classes('w-full').on('keydown.enter', lambda: event_kind_input.run_method("focus")).props('type="date"')
        event_kind_input = ui.select(event_types, value=event_kind).classes('w-full').on('keydown.enter', lambda: moderator_input.run_method("focus"))
        moderator_input = artist_input(session, value=moderator, label="Moderation").classes('w-full').on('keydown.enter', lambda: comment_input.run_method("focus"))
        comment_input = ui.input('Kommentar', value=comment).classes('w-full').on('keydown.enter', save)
        if not alow_edit_date:
            date_input.props('disable')
        if res is not None:
            delete_button = ui.button('Event löschen', on_click=delete, color='red', icon = 'delete').classes('w-full')
        with ui.row().classes('w-full'):
            cancel_button = ui.button('Abbrechen', on_click=lambda: dialog.submit(None))
            save_button = ui.button('Speichern', on_click=save)
    return dialog

async def edit_single_booking_dialog(session, artist, event_id):
    async def save():
        comment = comment_input.value if comment_input.value else ""
        await api_call(session, f'bookings/?event_id={event_id}&artist_id={artist.get("id")}&comment={comment_input.value}', method="PUT")
        ui.notify("Kommentar gespeichert")
        dialog.submit(True)
    with ui.dialog() as dialog, ui.card():
        ui.label(artist.get('name')).classes('text-xl')
        comment_input = ui.input('Kommentar', value=artist.get('comment')).classes('w-full').on('keydown.enter', save)
        comment_input.run_method("focus")
        with ui.row().classes('w-full no-wrap'):
            ui.button("Abbrechen", on_click=dialog.submit).classes("w-full")
            ui.button("Speichern", on_click=save).classes("w-full")
    return dialog

async def add_booking_dialog(session, event):
    #TODO catch duplicate
    async def save():
        await api_call(session, f'bookings/?event_id={event.get("id")}&artist={name_input.value}&comment={comment_input.value}', method="POST")
        ui.notify("Künstler*in hinzugefügt")
        dialog.submit(True)
    with ui.dialog() as dialog, ui.card():
        ui.label("Künstler*in hinzufügen").classes('text-xl')
        date = datetime.date.fromisoformat(event.get('date')).strftime("%A, %d.%m.%Y")
        ui.label(date)
        name_input = artist_input(session).classes('w-full').on('keydown.enter', lambda: comment_input.run_method("focus"))
        comment_input = ui.input('Kommentar').classes('w-full').on('keydown.enter', save)
        name_input.run_method("focus")
        with ui.row().classes('w-full no-wrap'):
            ui.button("Abbrechen", on_click=dialog.submit).classes("w-full")
            ui.button("Speichern", on_click=save).classes("w-full")
    return dialog
