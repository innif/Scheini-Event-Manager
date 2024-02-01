from nicegui import ui
import datetime
from datetime import timedelta
from dialogs import edit_reservation_dialog, confirm_dialog, loading_dialog, edit_event_dialog
from util import event_types, api_call

columns = [
    {'name': 'name', 'label': 'Name', 'field': 'name', 'required': True, 'align': 'left', 'sortable': True},
    {'name': 'quantity', 'label': 'Anzahl', 'field': 'quantity', 'required': True, 'align': 'left', 'sortable': True},
    {'name': 'comment', 'label': 'Kommentar', 'field': 'comment', 'required': True, 'align': 'left'},
    {'name': 'buttons', 'label': '', 'field': 'buttons'},
]


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

    with ui.column().style("margin: 0em; width: 100%; max-width: 50em; align-self: center;"):
        with ui.row(wrap=False).classes('w-full'):
            ui.button(icon="arrow_left")
            with ui.column().classes('flex-grow'):
                ui.label(date_str).classes("text-xl").style("width: 100%; height: 100%; text-align: center;")
            ui.button(icon="arrow_right")
        ui.button("Zurück zur Übersicht", on_click=lambda: ui.open('/')).classes("w-full")
        event_label = ui.label().style("width: 100%; height: 100%; text-align: center")
        with ui.row(wrap=False).classes('w-full'):
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
            ui.button(icon="add", on_click=add_reservation)
            ui.button(icon="refresh", on_click=generate_overview)
            ui.button(icon="edit", on_click=edit_event)
        with ui.table(columns, rows=[{'name': 'Name', 'quantity': 'Anzahl', 'comment': 'Kommentar'}]).classes('w-full bordered') as table:
            table.add_slot(f'body-cell-buttons', """
                <q-td :props="props">
                    <q-btn @click="$parent.$emit('edit', props)" icon="edit" flat dense color='blue'/>
                    <q-btn @click="$parent.$emit('delete', props)" icon="delete" flat dense color='green'/>
                </q-td>
            """)
            async def delete_reservation(id):
                dialog = confirm_dialog('Reservierung löschen', 'Soll die Reservierung wirklich gelöscht werden?')
                if await dialog:
                    d = loading_dialog('Lösche Reservierung', 'Bitte warten...')
                    d.open()
                    await api_call(session, "reservations/" + str(id), "DELETE")
                    d.close()
                    ui.notify('Reservierung gelöscht')
                    await generate_overview()

            async def edit_reservation(id):
                d = await edit_reservation_dialog(session, reservation_id=id)
                if await d:
                    await generate_overview()

            table.on('edit', lambda msg: edit_reservation(msg.args['row']['id']))
            table.on('delete', lambda msg: delete_reservation(msg.args['row']['id']))

    ui.timer(0.1, generate_overview, once=True)