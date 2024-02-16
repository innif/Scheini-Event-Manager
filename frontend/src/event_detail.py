#TODO: section for reservations & artists
#TODO: popup editing for reservations

from nicegui import ui
import datetime
from datetime import timedelta
from dialogs import edit_reservation_dialog, confirm_dialog, loading_dialog, edit_event_dialog, edit_bookings_dialog
from util import event_types, api_call

columns = [
    {'name': 'name', 'label': 'Name', 'field': 'name', 'required': True, 'align': 'left', 'sortable': True},
    {'name': 'quantity', 'label': 'Anzahl', 'field': 'quantity', 'required': True, 'align': 'left', 'sortable': True},
    {'name': 'comment', 'label': 'Kommentar', 'field': 'comment', 'required': True, 'align': 'left'},
    {'name': 'buttons', 'label': '', 'field': 'buttons'},
]

async def print_page(session, date: str):
    date_str = datetime.date.fromisoformat(date).strftime("%A, %d.%m.%Y")
    reservations = await api_call(session, "reservations/date/" + date)
    artists = await api_call(session, "artists/event/" + date)
    ui.label(date_str).classes("text-xl")
    with ui.column():
        for r in reservations:
            with ui.row().classes("w-full"):
                ui.label(r['name'])
                ui.label(r['comment']).classes("text-sm italic").style("color: grey")
                ui.space()
                ui.label(str(r['quantity']) + "x")
            ui.separator()
    ui.label("Künstler*innen:").classes("text-lg")
    with ui.row().classes("w-full"):
        for a in artists:
            ui.label(a['name'])
            if a['comment'] is not None and a['comment'] != "":
                ui.label(a['comment']).classes("text-sm italic").style("color: grey")
            ui.label(" | ")
    ui.run_javascript("window.print()")
    ui.timer(0.5, lambda: ui.run_javascript("window.close()"), once=True)

async def get_event_data(session, date: str):
    data = {}
    data['reservations'] = await api_call(session, "reservations/date/" + date) # session.get("http://localhost:8000/reservations/date/" + date).json()
    data['event'] = await api_call(session, "events/" + date)
    data['event']['date-str'] = datetime.date.fromisoformat(data['event']['date']).strftime("%A, %d.%m.%Y")
    return data

async def detail_page(session, date: str):
    date_str = datetime.date.fromisoformat(date).strftime("%A, %d.%m.%Y")
    # name, quantity, comment, date
    async def generate_overview():
        data = await get_event_data(session, date)
        table.rows = data.get('reservations')
        event = data.get('event')
        event_label.set_text(event_types.get(event.get('event_kind')) + " - " + event.get('moderator'))
        reservation_label.set_text("Reservierungen: " + str(event.get("num_reservations")))
        artist_label.set_text("Künstler*innen: " + str(event.get("num_artists")))

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
        async def edit_artists():
            d = await edit_bookings_dialog(session, date=date)
            await d
            await generate_overview()
        async def add_reservation():
            d = await edit_reservation_dialog(session, date=date)
            if await d:
                await generate_overview()
        async def edit_event():
            d = await edit_event_dialog(session, date=date)
            result = await d
            if result == 'edit':
                await generate_overview()
            if result == 'delete':
                ui.open('/')
        with ui.row().classes('w-full'):
            event_label = ui.label().classes("text-xl")
            ui.space()
            with ui.row(wrap=False):
                ui.button(icon="refresh", on_click=generate_overview)
                ui.button(icon="edit", on_click=edit_event)
                ui.button(icon="print", on_click=lambda: ui.open("/print/" + date, new_tab=True), color = "accent")
        with ui.row().classes('w-full'):
            artist_label = ui.label(f"Künstler*innen: ...").classes("text-xl")
            ui.space()
            ui.button(icon="edit", on_click=edit_artists)
            #TODO table for artists
        with ui.row().classes('w-full'):
            reservation_label = ui.label(f"Reservierungen: ...").classes("text-xl")
            ui.space()
            ui.button(icon="add", on_click=add_reservation, color="positive")
        with ui.table(columns, rows=[{'name': 'Name', 'quantity': 'Anzahl', 'comment': 'Kommentar'}]).classes('w-full bordered') as table:
            table.add_slot(f'body-cell-buttons', """
                <q-td :props="props">
                    <q-btn @click="$parent.$emit('edit', props)" icon="edit" flat dense color='primary'/>
                    <q-btn @click="$parent.$emit('delete', props)" icon="delete" flat dense color='negative'/>
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

    ui.timer(0.1, generate_overview, once=True)