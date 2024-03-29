from nicegui import ui, app
import datetime
from datetime import timedelta
from dialogs import edit_reservation_dialog, loading_dialog, edit_event_dialog, edit_bookings_dialog
from util import api_call, breakpoint
import asyncio

#TODO limit field length

columns = [
    {'name': 'weekday', 'label': 'Wochentag', 'field': 'weekday', 'required': True, 'align': 'left', 'sortable': True, 
     'classes': breakpoint('md', 'hidden'), 'headerClasses': breakpoint('md', 'hidden')},
    {'name': 'date_str', 'label': 'Datum', 'field': 'date_str', 'required': True, 'align': 'left', 'sortable': True,
     'classes': breakpoint('md', 'hidden'), 'headerClasses': breakpoint('md', 'hidden')},
    {'name': 'date_str_short', 'label': 'Datum', 'field': 'date_str_short', 'required': True, 'align': 'left', 'sortable': True,
     'classes': breakpoint('md', 'hidden', False), 'headerClasses': breakpoint('md', 'hidden', False)},
    {'name': 'moderator', 'label': 'Moderation', 'field': 'moderator', 'required': True, 'align': 'left', 'sortable': True,
     'classes': breakpoint('md', 'hidden'), 'headerClasses': breakpoint('md', 'hidden'), 'style': 'max-width: 10em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'},
    {'name': 'comment', 'label': 'Kommentar', 'field': 'comment', 'sortable': False, 'align': 'left',
     'classes': breakpoint('sm', 'hidden'), 'headerClasses': breakpoint('sm', 'hidden'), 'style': 'max-width: 10em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'},
    {'name': 'result', 'label': 'Suchergebnis', 'field': 'result', 'sortable': True, 'align': 'left', 'classes:': 'hidden', 'headerClasses': 'hidden'},
    {'name': 'num_reservations', 'label': 'Reserv.', 'field': 'num_reservations', 'sortable': True, 'align': 'left'},
    {'name': 'num_artists', 'label': 'Künstl.', 'field': 'num_artists', 'sortable': True, 'align': 'left'},
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

highlight_text = """
    <q-td :props="props" :class="(props.row.highlight)?'bg-grey-3':'bg-white'">
        {{ props.value }}
    </q-td>
"""

years = [datetime.datetime.now().year + i for i in range(-1, 3)]
month_select = None
year_select = None
ui.colors()

def search_columns(activate: bool):
    columns[5]['classes'] = 'hidden' if not activate else ''
    columns[5]['headerClasses'] = 'hidden' if not activate else ''
    columns[6]['classes'] = 'hidden' if activate else ''
    columns[6]['headerClasses'] = 'hidden' if activate else ''

async def get_data(session, month, year, past_events: bool = False, search: str = None):
    start = datetime.date(year, month, 1)
    if not past_events:
        start = max(start, datetime.date.today())
    start = start.isoformat()
    end = None
    if month == 12:
        end = (datetime.date(year + 1, 1, 1) - timedelta(days=1)).isoformat()
    else:
        end = (datetime.date(year, month + 1, 1) - timedelta(days=1)).isoformat()
    if search:
        res = await api_call(session, "events/?start_date=" + start + "&search_query=" + search)
    else:
        res = await api_call(session, "events/?start_date=" + start + "&end_date=" + end)
    for r in res:
        date = datetime.date.fromisoformat(r['date'])
        r['date_str'] = date.strftime("%d.%m.%Y")
        r['date_str_short'] = date.strftime("%d.%m.%y (%a)")
        r['weekday'] = date.strftime("%A")
        r['highlight'] = date.isocalendar()[1] % 2 == 0
    return res

async def overview_page(session):
    #TODO Expandable Rows (for comments) https://nicegui.io/documentation/table#table_with_expandable_rows
    async def on_selection_change():
        search = search_input.value
        if search == "":
            search = None
        search_columns(search is not None)
        if month_select is not None and year_select is not None:
            table.rows = await get_data(session, month_select.value, year_select.value, cb_past_events.value, search)

    async def add_reservation(date):
        d = await edit_reservation_dialog(session, date=date)
        if await d:
            await on_selection_change()

    async def add_artist(date):
        d = await edit_bookings_dialog(session, date=date)
        await d
        await on_selection_change()

    async def add_event():
        d = await edit_event_dialog(session)
        if await d:
            await on_selection_change()
    
    async def toggle_search():
        search_row.set_visibility(not search_row.visible)
        if search_row.visible:
            search_input.run_method('focus')
        else:    
            search_input.set_value("")
            await on_selection_change()

    async def comment_update(args):
        await api_call(session, "events/" + args['date'], "PUT", json = {
            'event_kind': args['event_kind'],
            'moderator': args['moderator'],
            'comment': args['comment']
        })
        ui.notify("Kommentar gespeichert", color="positive")
        await on_selection_change()

    with ui.column().style("margin: 0em; width: 100%; max-width: 60em; align-self: center;"):
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
            ui.button(icon="arrow_back", on_click=back).classes("my-auto")
            month_select = ui.select(months, label="Monat", value = datetime.datetime.now().month, on_change=on_selection_change).style("width: 50%;")
            year_select = ui.select(years, label="Jahr", value = datetime.datetime.now().year, on_change=on_selection_change).style("width: 50%;")
            ui.button(icon="arrow_forward", on_click=forward).classes("my-auto")
        
        data = []
        with ui.row().classes('w-full'): 
            cb_past_events = ui.checkbox("Vergangene Events anzeigen", on_change=on_selection_change)
            ui.space()
            with ui.row(wrap=False):
                ui.button(icon="add", on_click=add_event, color="positive")
                ui.button(icon="refresh", on_click=on_selection_change)
                ui.button(icon="search", on_click=toggle_search)
                ui.button(on_click=lambda: (app.storage.user.clear(), ui.open('/login')), icon='logout', color = 'negative')
        with ui.row(wrap=False).classes('w-full') as search_row:
            search_input = ui.input(label="Suche", on_change=on_selection_change).classes('w-full').props("clearable outlined")
            with search_input.add_slot('prepend'):
                ui.icon('search')
            with search_input.add_slot('after'):
                ui.button(icon='arrow_upward', on_click=toggle_search).props('flat')
            search_row.set_visibility(False)
        with ui.table(columns, rows=[]).classes('w-full bordered') as table:
            table.add_slot(f'body-cell-date_str', highlight_text)
            table.add_slot(f'body-cell-date_str_short', highlight_text)
            table.add_slot(f'body-cell-weekday', highlight_text)
            table.add_slot(f'body-cell-moderator', """
                <q-td :props="props" :class="(props.row.highlight)?'bg-grey-3':'bg-white'">
                    <q-btn :icon="props.row.event_kind == 'open_stage' ? 'mic_external_on' : 'person'" flat dense/>
                    {{ props.value }}
                </q-td>
            """)
            table.add_slot(f'body-cell-buttons', """
                <q-td :props="props" :class="(props.row.highlight)?'bg-grey-3':'bg-white'">
                    <q-btn @click="$parent.$emit('edit', props)" icon="visibility" dense flat color='primary'/>
                </q-td>
            """)
            table.add_slot(f'body-cell-num_reservations', """
                <q-td :props="props" :class="(props.row.highlight)?'bg-grey-3':'bg-white'">
                    <q-badge :color="props.value < 40 ? 'primary' : (props.value < 51 ? 'warning' : 'negative')">
                        {{ props.value }}
                    </q-badge>
                    <q-btn @click="$parent.$emit('add', props)" icon="add" flat dense my-auto color='positive'/>
                </q-td>
            """)
            table.add_slot(f'body-cell-num_artists', """
                <q-td :props="props" :class="(props.row.highlight)?'bg-grey-3':'bg-white'">
                    <q-badge :color="props.value >= 7 ? 'negative' : (props.value < 4 ? 'warning' : 'positive')">
                        {{ props.value }}
                    </q-badge>
                    <q-btn @click="$parent.$emit('add_artist', props)" icon="edit" flat dense my-auto color='positive'/>
                </q-td>
            """)
            table.add_slot(f'body-cell-comment', """
                <q-td :props="props" :class="(props.row.highlight)?'bg-grey-3':'bg-white'">
                    {{ props.row.comment }}
                    <q-popup-edit v-model="props.row.comment" v-slot="scope" buttons 
                       @update:model-value="() => $parent.$emit('comment', props.row)"
                    >
                        <q-input v-model="scope.value" dense autofocus counter  @keyup.enter="scope.set"/>
                    </q-popup-edit>
                </q-td>
            """)
            table.on('action', lambda msg: print(msg))
            table.on('add', lambda msg: add_reservation(msg.args['row']['date']))
            table.on('edit', lambda msg: ui.open('/event/' + msg.args['row']['date']))
            table.on('add_artist', lambda msg: add_artist(msg.args['row']['date']))
            table.on('comment', lambda msg: comment_update(msg.args))
            #table.on('row-click', lambda msg: print(msg.args))
    ui.timer(0.1, on_selection_change, once = True)
