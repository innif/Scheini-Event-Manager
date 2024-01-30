from nicegui import ui
import datetime
from datetime import timedelta

columns = [
    {'name': 'name', 'label': 'Name', 'field': 'name', 'required': True, 'align': 'left', 'sortable': True},
    {'name': 'quantity', 'label': 'Anzahl', 'field': 'quantity', 'required': True, 'align': 'left', 'sortable': True},
    {'name': 'comment', 'label': 'Kommentar', 'field': 'comment', 'required': True, 'align': 'left'},
    {'name': 'buttons', 'label': '', 'field': 'buttons'},
]

def get_event_data(session, date: str):
    data = {}
    data['reservations'] = session.get("http://localhost:8000/reservations/date/" + date).json()
    data['event'] = session.get("http://localhost:8000/events/" + date).json()
    data['event']['date-str'] = datetime.date.fromisoformat(data['event']['date']).strftime("%A, %d.%m.%Y")
    return data

def detail_page(session, date: str):
    date_str = datetime.date.fromisoformat(date).strftime("%A, %d.%m.%Y")
    # name, quantity, comment, date
    def generate_overview(date):
        data = get_event_data(session, date)
        table.rows = data.get('reservations')
        event_label.set_text(data.get('event'))

    with ui.column():
        with ui.row(wrap=False).classes('w-full'):
            ui.button(icon="arrow_left")
            ui.label(date_str).classes("text-xl").style("width: 100%; height: 100%; text-align: center")
            ui.button(icon="arrow_right")
        event_label = ui.label()
        with ui.table(columns, rows=[{'name': 'Name', 'quantity': 'Anzahl', 'comment': 'Kommentar'}]).classes('w-full bordered') as table:
            table.add_slot(f'body-cell-buttons', """
                <q-td :props="props">
                    <q-btn @click="$parent.$emit('edit', props)" icon="edit" flat dense color='blue'/>
                    <q-btn @click="$parent.$emit('delete', props)" icon="delete" flat dense color='green'/>
                </q-td>
            """)
            table.on('action', lambda msg: print(msg))
            table.on('edit', lambda msg: print("edit", msg))
            table.on('delete', lambda msg: print("delete", msg))

            generate_overview(date)