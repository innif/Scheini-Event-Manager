from nicegui import ui
import datetime
from datetime import timedelta
from dialogs import edit_reservation_dialog

columns = [
    {'name': 'weekday', 'label': 'Wochentag', 'field': 'weekday', 'required': True, 'align': 'left', 'sortable': True},
    {'name': 'date_str', 'label': 'Datum', 'field': 'date_str', 'required': True, 'align': 'left', 'sortable': True},
    {'name': 'moderator', 'label': 'Moderation', 'field': 'moderator', 'required': True, 'align': 'left', 'sortable': True},
    {'name': 'num_reservations', 'label': 'Reservierungen', 'field': 'num_reservations', 'sortable': True, 'align': 'left'},
    {'name': 'buttons', 'label': '', 'field': 'buttons', 'sortable': False},
]
months = {
    1: "Januar",
    2: "Februar",
    3: "März",
    4: "April",
    5: "Mai",
    6: "Juni",
    7: "Juli",
    8: "August",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Dezember"
}
years = [datetime.datetime.now().year + i for i in range(-1, 3)]
month_select = None
year_select = None

def get_data(session, month, year, past_events = False):
    start = datetime.date(year, month, 1)
    if not past_events:
        start = max(start, datetime.date.today())
    start = start.isoformat()
    end = (datetime.date(year, month + 1, 1) - timedelta(days=1)).isoformat()
    res = session.get("http://localhost:8000/events/?start_date=" + start + "&end_date=" + end).json()
    for r in res:
        date = datetime.date.fromisoformat(r['date'])
        r['date_str'] = date.strftime("%d.%m.%Y")
        r['weekday'] = date.strftime("%A")
    return res

def overview_page(session):
    def on_selection_change():
        if month_select is not None and year_select is not None:
            table.rows = get_data(session, month_select.value, year_select.value, cb_past_events.value)

    async def add_reservation(date):
        d = edit_reservation_dialog(session, date=date)
        if await d:
            on_selection_change()

    with ui.column().style("margin: 0em; width: 100%; max-width: 50em; align-self: center;"):
        with ui.card().classes("w-full"), ui.row(wrap=False).classes('w-full'):
            month_select = ui.select(months, label="Monat", value = datetime.datetime.now().month, on_change=on_selection_change).style("width: 50%;")
            year_select = ui.select(years, label="Jahr", value = datetime.datetime.now().year, on_change=on_selection_change).style("width: 50%;")

        data = []
        with ui.row(wrap=False).classes('w-full'):
            ui.button(icon="refresh", on_click=on_selection_change)
            cb_past_events = ui.checkbox("Vergangene Events anzeigen", on_change=on_selection_change)
        with ui.table(columns, rows=[]).classes('w-full bordered') as table:
            table.add_slot(f'body-cell-buttons', """
                <q-td :props="props">
                    <q-btn @click="$parent.$emit('edit', props)" icon="edit" flat dense color='blue'/>
                </q-td>
            """)
            table.add_slot(f'body-cell-num_reservations', """
                <q-td :props="props">
                    <q-badge :color="props.value < 52 ? 'green' : 'red'">
                        {{ props.value }}
                    </q-badge>
                    <q-btn @click="$parent.$emit('add', props)" icon="add" flat dense color='green'/>
                </q-td>
            """)
            table.on('action', lambda msg: print(msg))
            table.on('add', lambda msg: add_reservation(msg.args['row']['date']))
            table.on('edit', lambda msg: ui.open('/event/' + msg.args['row']['date']))
    on_selection_change()