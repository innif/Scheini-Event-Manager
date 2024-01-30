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

def get_data(session, month, year):
    start = datetime.date(year, month, 1).isoformat()
    end = (datetime.date(year, month + 1, 1) - timedelta(days=1)).isoformat()
    res = session.get("http://localhost:8000/events/?start_date=" + start + "&end_date=" + end).json()
    print(res)
    for r in res:
        date = datetime.date.fromisoformat(r['date'])
        r['date_str'] = date.strftime("%d.%m.%Y")
        r['weekday'] = date.strftime("%A")
    return res

def overview_page(session):
    def generate_overview(month, year):
        table.rows = get_data(session, month, year)

    def on_selection_change():
        if month_select is not None and year_select is not None:
            generate_overview(month_select.value, year_select.value)

    with ui.column():
        with ui.card().classes("w-full"), ui.row():
            year_select = ui.select(years, label="Year", value = datetime.datetime.now().year, on_change=on_selection_change)
            month_select = ui.select(months, label="Month", value = datetime.datetime.now().month, on_change=on_selection_change)

        data = []
        with ui.table(columns, rows=[]).classes('w-full bordered') as table:
            table.add_slot(f'body-cell-buttons', """
                <q-td :props="props">
                    <q-btn @click="$parent.$emit('add', props)" icon="add" flat dense color='green'/>
                    <q-btn @click="$parent.$emit('edit', props)" icon="edit" flat dense color='blue'/>
                </q-td>
            """)
            table.on('action', lambda msg: print(msg))
            table.on('add', lambda msg: edit_reservation_dialog(session, date=msg.args['row']['date']))
            table.on('edit', lambda msg: print("edit", msg))

    generate_overview(datetime.datetime.now().month, datetime.datetime.now().year)