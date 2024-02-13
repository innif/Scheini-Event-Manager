from nicegui import ui, app
import datetime
from datetime import timedelta
from dialogs import edit_reservation_dialog, loading_dialog, edit_event_dialog
from util import api_call
import asyncio

columns = [
    {'name': 'event_kind', 'label': 'Art', 'field': 'event_kind', 'required': True, 'align': 'left', 'sortable': True},
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
ui.colors()

async def get_data(session, month, year, past_events = False):
    start = datetime.date(year, month, 1)
    if not past_events:
        start = max(start, datetime.date.today())
    start = start.isoformat()
    end = (datetime.date(year, month + 1, 1) - timedelta(days=1)).isoformat()
    res = await api_call(session, "events/?start_date=" + start + "&end_date=" + end)
    for r in res:
        date = datetime.date.fromisoformat(r['date'])
        r['date_str'] = date.strftime("%d.%m.%Y")
        r['weekday'] = date.strftime("%A")
    return res

async def overview_page(session):
    async def on_selection_change():
        if month_select is not None and year_select is not None:
            table.rows = await get_data(session, month_select.value, year_select.value, cb_past_events.value)

    async def add_reservation(date):
        d = await edit_reservation_dialog(session, date=date)
        if await d:
            await on_selection_change()

    async def add_event():
        d = await edit_event_dialog(session)
        if await d:
            await on_selection_change()

    with ui.column().style("margin: 0em; width: 100%; max-width: 50em; align-self: center;"):
        with ui.card().classes("w-full"), ui.row(wrap=False).classes('w-full'):
            def back():
                month_select.set_value(month_select.value - 1)
                if month_select.value is None:
                    month_select.set_value(12)
                    year_select.set_value(year_select.value - 1)
            def forward():
                month_select.set_value(month_select.value + 1)
                if month_select.value is None:
                    month_select.set_value(1)
                    year_select.set_value(year_select.value + 1)
            ui.button(icon="arrow_back", on_click=back).classes("my-auto rounded-full")
            month_select = ui.select(months, label="Monat", value = datetime.datetime.now().month, on_change=on_selection_change).style("width: 50%;")
            year_select = ui.select(years, label="Jahr", value = datetime.datetime.now().year, on_change=on_selection_change).style("width: 50%;")
            ui.button(icon="arrow_forward", on_click=forward).classes("my-auto rounded-full")
            # TODO: forward and backward buttons to change months
        
        data = []
        with ui.row(wrap=False).classes('w-full'): 
            cb_past_events = ui.checkbox("Vergangene Events anzeigen", on_change=on_selection_change)
            ui.space()
            ui.button(icon="add", on_click=add_event, color="positive")
            ui.button(icon="refresh", on_click=on_selection_change)
            ui.button(on_click=lambda: (app.storage.user.clear(), ui.open('/login')), icon='logout', color = 'negative')
        with ui.table(columns, rows=[]).classes('w-full bordered') as table:
            table.add_slot(f'body-cell-event_kind', """
                <q-td :props="props">
                    <q-btn :icon="props.value == 'open_stage' ? 'mic_external_on' : 'person'" flat dense/>
                </q-td>
            """)
            table.add_slot(f'body-cell-buttons', """
                <q-td :props="props">
                    <q-btn @click="$parent.$emit('edit', props)" icon="edit" dense flat color='primary'/>
                </q-td>
            """)
            table.add_slot(f'body-cell-num_reservations', """
                <q-td :props="props">
                    <q-badge :color="props.value < 40 ? 'positive' : (props.value < 52 ? 'warning' : 'negative')">
                        {{ props.value }}
                    </q-badge>
                    <q-btn @click="$parent.$emit('add', props)" icon="add" flat dense my-auto color='positive'/>
                </q-td>
            """)
            table.on('action', lambda msg: print(msg))
            table.on('add', lambda msg: add_reservation(msg.args['row']['date']))
            table.on('edit', lambda msg: ui.open('/event/' + msg.args['row']['date']))
    ui.timer(0.1, on_selection_change, once = True)
