#TODO: section for reservations & artists
#TODO: popup editing for reservations

from nicegui import ui
import datetime
from datetime import timedelta
from dialogs import edit_reservation_dialog, confirm_dialog, loading_dialog, edit_event_dialog, edit_bookings_dialog, edit_single_booking_dialog, add_booking_dialog, input_dialog
from util import event_types, api_call, breakpoint, escape_for_url

columns = [
    {'name': 'name', 'label': 'Name', 'field': 'name', 'required': True, 'align': 'left', 'sortable': True},
    {'name': 'quantity', 'label': 'Anzahl', 'field': 'quantity', 'required': True, 'align': 'left', 'sortable': True},
    {'name': 'comment', 'label': 'Kommentar', 'field': 'comment', 'required': True, 'align': 'left', 
     'classes': breakpoint('sm', 'hidden'), 'headerClasses': breakpoint('sm', 'hidden')},
    {'name': 'buttons', 'label': '', 'field': 'buttons'},
]

def artist_chip(session, artist, event_id: int, on_change=None):
    async def remove(msg):
        d = confirm_dialog('Künstler*in löschen', 'Soll die Künstler*in wirklich gelöscht werden?')
        if await d:
            await api_call(session, "bookings/?event_id="+str(event_id)+"&artist_id="+str(artist.get('id')), "DELETE")
            await on_change()
    async def click(msg):
        d = await edit_single_booking_dialog(session, artist, event_id)
        if await d:
            await on_change()
    with ui.element('q-chip').props('clickable removable icon="person" @remove="$parent.$emit(\'remove\')" @click"$parent.$emit(\'click\') color="secondary" text-color="white"') as chip:
        ui.label(artist.get('name'))
        if artist.get('comment') is not None and artist.get('comment') != "":
            ui.label(artist.get('comment')).classes("italic").props('color="white"').style("margin-left: 0.5em")
            #ui.icon('notes', color='white')
    chip.on('remove', remove)
    chip.on('click', click)

def technician_chip(session, technician:str, event_id: int, on_change=None):
    async def click(msg):
        d =  input_dialog("Technik", "Techniker*in bearbeiten/hinzufügen", value=technician)
        await api_call(session, "technician/?event_id=" + str(event_id) + "&technician=" + escape_for_url(await d), "PUT")
        await on_change()
    with ui.element('q-chip').props('clickable icon="tune" @click"$parent.$emit(\'click\') color="accent" text-color="white"') as chip:
        if technician is None or technician == "":
            ui.label("Techniker*in hinzufügen").classes("italic")
        else:
            ui.label(technician)
    chip.on('click', click)

def bar_staff_chip(session, bar_staff_1: str, bar_staff_2: str, event: dict, on_change=None):
    async def click(msg):
        from dialogs import bar_staff_edit_dialog
        d = bar_staff_edit_dialog(bar_staff_1, bar_staff_2)
        result = await d
        if result:
            person1, person2 = result
            await api_call(session, f"bar_staff/?event_id={event.get('id')}&bar_staff_1={escape_for_url(person1)}&bar_staff_2={escape_for_url(person2)}", "PUT")
            await on_change()

    # Erstelle Label-Text
    names = []
    if bar_staff_1 is not None and bar_staff_1 != "":
        names.append(bar_staff_1)
    if bar_staff_2 is not None and bar_staff_2 != "":
        names.append(bar_staff_2)

    label_text = " & ".join(names) if len(names) > 0 else "Tresenpersonal hinzufügen"

    with ui.element('q-chip').props('clickable icon="local_bar" @click"$parent.$emit(\'click\') color="orange" text-color="white"') as chip:
        if len(names) == 0:
            ui.label(label_text).classes("italic")
        else:
            ui.label(label_text)
    chip.on('click', click)

def add_artists_chips(session, artist_list, event: dict, on_change=None):
    if artist_list is None or len(artist_list) == 0:
        with ui.element('q-chip').props('color="negative" text-color="white"'):
            ui.label("Keine Künstler*innen eingetragen")
    for a in artist_list:
        artist_chip(session, a, event.get('id'), on_change)
    technician_chip(session, event.get('technician'), event.get('id'), on_change)
    bar_staff_chip(session, event.get('bar_staff_1'), event.get('bar_staff_2'), event, on_change)

async def print_page(session, date: str):
    #TODO print next days
    date_str = datetime.date.fromisoformat(date).strftime("%A, %d.%m.%Y")
    reservations = await api_call(session, "reservations/date/" + date)
    artists = await api_call(session, "artists/event/" + date)
    events = await api_call(session, "events/" + date)
    events_full = await api_call(session, "events/?start_date=" + date + "&min_reservations=40")
    ui.label(date_str).classes("text-xl")
    if events.get('comment') is not None and events.get('comment') != "":
        ui.label(events.get('comment')).classes("text-sm italic").style("color: grey")
    with ui.column():
        for r in reservations:
            with ui.row().classes("w-full"):
                ui.label(r['name'])
                ui.label(r['comment']).classes("text-sm italic").style("color: grey")
                ui.space()
                ui.label(str(r['quantity']) + "x")
            ui.separator()
    ui.label("Insgesamt: " + str(events.get('num_reservations')) + " Reservierungen").classes("text-bold")
    ui.label("Künstler*innen:").classes("text-lg")
    with ui.row().classes("w-full"):
        for a in artists:
            ui.label(a['name'])
            if a['comment'] is not None and a['comment'] != "":
                ui.label(a['comment']).classes("text-sm italic").style("color: grey")
            ui.label(" | ")
        if events.get('technician') is not None and events.get('technician') != "":
            ui.label("Technik: " + str(events.get('technician'))).style("color: grey")
            ui.label(" | ")
        # Bar-Staff zusammen anzeigen
        bar_staff_names = []
        if events.get('bar_staff_1') is not None and events.get('bar_staff_1') != "":
            bar_staff_names.append(events.get('bar_staff_1'))
        if events.get('bar_staff_2') is not None and events.get('bar_staff_2') != "":
            bar_staff_names.append(events.get('bar_staff_2'))
        if len(bar_staff_names) > 0:
            ui.label("Tresen: " + " & ".join(bar_staff_names)).style("color: grey")
    ui.label("Veranstaltungen mit 40+ Reservierungen:").classes("text-lg")
    with ui.column().classes("w-full"):
        for e in events_full:
            ui.label(datetime.date.fromisoformat(e['date']).strftime("%A, %d.%m.%Y")+ " - " + e['moderator'] + " - " + str(e['num_reservations']) + " Reservierungen")

async def get_event_data(session, date: str):
    data = {}
    data['reservations'] = await api_call(session, "reservations/date/" + date) # session.get("http://localhost:8000/reservations/date/" + date).json()
    data['event'] = await api_call(session, "events/" + date)
    data['event']['date-str'] = datetime.date.fromisoformat(data['event']['date']).strftime("%A, %d.%m.%Y")
    data['artists'] = await api_call(session, "artists/event/" + date)
    return data

async def detail_page(session, date: str, start_dialog=False, name="", quantity=1, comment=""):
    ui.html('<iframe id="subpageFrame" style="display:none;"></iframe>').set_visibility(False)
    date_str = datetime.date.fromisoformat(date).strftime("%A, %d.%m.%Y")
    # name, quantity, comment, date
    async def generate_overview():
        data = await get_event_data(session, date)
        table.rows = data.get('reservations')
        event = data.get('event')
        comments.value = event.get('comment')
        comments.on("update:model-value", lambda: save_comment_button.set_visibility(True))
        event_label.set_text(event_types.get(event.get('event_kind')) + " - " + event.get('moderator'))
        reservation_label.set_text("Reservierungen: " + str(event.get("num_reservations")))
        # Zähle Künstler + Techniker + Bar-Staff zusammen
        total_people = event.get("num_artists")
        if event.get('technician') is not None and event.get('technician') != "":
            total_people += 1
        total_people += event.get("num_bar_staff")

        artist_label.set_text("Künstler*innen: " + str(total_people))
        artists_div.clear()
        with artists_div:
            add_artists_chips(session, data.get('artists'), event, on_change=generate_overview)

    with ui.column().style("margin: 0em; width: 100%; max-width: 50em; align-self: center;"):
        with ui.row(wrap=False).classes('w-full'):
            async def next_event():
                d = await api_call(session, "events/" + date + "/next")
                ui.open('/event/' + d.get('date'))
            async def previous_event():
                d = await api_call(session, "events/" + date + "/previous")
                ui.open('/event/' + d.get('date'))
            ui.button(icon="arrow_back", on_click=previous_event)
            with ui.column().classes('flex-grow'):
                ui.label(date_str).classes("text-xl").style("width: 100%; height: 100%; text-align: center;")
            ui.button(icon="arrow_forward", on_click=next_event)
        ui.button("Zurück zur Übersicht", on_click=lambda: ui.open('/')).classes("w-full")
        async def add_artist():
            event = await api_call(session, "events/" + date)
            d = await add_booking_dialog(session, event)
            if await d:
                await generate_overview()
        async def add_reservation():
            d = await edit_reservation_dialog(session, date=date)
            if await d:
                await generate_overview()
        async def edit_event():
            d = await edit_event_dialog(session, date=date, alow_edit_date=False)
            result = await d
            if result == 'edit':
                await generate_overview()
            if result == 'delete':
                ui.open('/')
        async def save_comment():
            event = await api_call(session, "events/" + date)
            await api_call(session, "events/" + str(date), "PUT", json = {
                'event_kind': event.get('event_kind'),
                'moderator': event.get('moderator'),
                'comment': comments.value
            })
            ui.notify("Kommentar gespeichert", color="positive")
            save_comment_button.set_visibility(False)
        async def row_update(args):
            # print(args)
            await api_call(session, "reservations/" + str(args.get("id")), "PUT", json = {
                'name': args.get("name"),
                'quantity': args.get("quantity"),
                'comment': args.get("comment"),
                'date': args.get("date")
            })
            ui.notify("Änderung gespeichert")
            await generate_overview()
        with ui.row().classes('w-full'):
            event_label = ui.label().classes("text-xl")
            ui.space()
            with ui.row(wrap=False):
                ui.button(icon="refresh", on_click=generate_overview)
                ui.button(icon="edit", on_click=edit_event)
                def print():
                    ui.run_javascript('''
                        var subpageFrame = document.getElementById('subpageFrame');
                        subpageFrame.src = '/print/{}';
                        subpageFrame.onload = function() {{
                            subpageFrame.contentWindow.print();
                        }}; '''.format(date))
                ui.button(icon="print", on_click=print, color = "accent")
        comments = ui.input(label="Kommentar").classes("w-full").props("outlined")
        save_comment_button = ui.button("Kommentar speichern", on_click=save_comment).classes("w-full")
        save_comment_button.set_visibility(False)
        with ui.row().classes('w-full'):
            artist_label = ui.label(f"Künstler*innen: ...").classes("text-xl")
            ui.space()
            ui.button(icon="person_add", on_click=add_artist, color="secondary")
        artists_div = ui.element('div').classes('w-full')
        with ui.row().classes('w-full'):
            reservation_label = ui.label(f"Reservierungen: ...").classes("text-xl")
            ui.space()
            ui.button(icon="group_add", on_click=add_reservation)
        with ui.table(columns, rows=[]).classes('w-full bordered') as table:
            table.add_slot(f'body-cell-buttons', """
                <q-td :props="props">
                    <q-btn @click="$parent.$emit('edit', props)" icon="edit" flat dense color='primary'/>
                    <q-btn @click="$parent.$emit('delete', props)" icon="delete" flat dense color='negative'/>
                </q-td>
            """)
            table.add_slot(f'body-cell-name', """
                <q-td :props="props">
                    {{ props.row.name }}
                    <q-popup-edit v-model="props.row.name" v-slot="scope" buttons 
                       @update:model-value="() => $parent.$emit('update', props.row)"
                    >
                        <q-input v-model="scope.value" dense autofocus counter @keyup.enter="scope.set"/>
                    </q-popup-edit>
                </q-td>
            """)
            table.add_slot(f'body-cell-quantity', """
                <q-td :props="props">
                    {{ props.row.quantity }}
                    <q-popup-edit v-model="props.row.quantity" v-slot="scope" buttons 
                       @update:model-value="() => $parent.$emit('update', props.row)"
                    >
                        <q-input v-model="scope.value" dense autofocus counter @keyup.enter="scope.set" type="number"/>
                    </q-popup-edit>
                </q-td>
            """)
            table.add_slot(f'body-cell-comment', """
                <q-td :props="props">
                    {{ props.row.comment }}
                    <q-popup-edit v-model="props.row.comment" v-slot="scope" buttons 
                       @update:model-value="() => $parent.$emit('update', props.row)"
                    >
                        <q-input v-model="scope.value" dense autofocus counter @keyup.enter="scope.set"/>
                    </q-popup-edit>
                </q-td>
            """)
            async def delete_reservation(id):
                dialog = confirm_dialog('Reservierung löschen', 'Soll die Reservierung wirklich gelöscht werden?')
                if await dialog:
                    await api_call(session, "reservations/" + str(id), "DELETE")
                    ui.notify('Reservierung gelöscht')
                    await generate_overview()

            async def edit_reservation(id):
                d = await edit_reservation_dialog(session, reservation_id=id)
                if await d:
                    await generate_overview()

            table.on('edit', lambda msg: edit_reservation(msg.args['row']['id']))
            table.on('delete', lambda msg: delete_reservation(msg.args['row']['id']))
            table.on('update', lambda msg: row_update(msg.args))

    ui.timer(0.1, generate_overview, once=True)
    if start_dialog:
        d = await edit_reservation_dialog(session, name=name, num=quantity, comment=comment, date=date)
        if await d:
            await generate_overview()