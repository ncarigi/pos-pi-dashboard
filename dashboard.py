from nicegui import ui, Client
from pages import meals, tasks, today, tomorrow

meals.router()
tasks.router()
today.router()
tomorrow.router()

@ui.page('/')
def home_page():
    ui.label('RaspberryPi Manager').classes('text-h4 font-bold mb-8 mt-4 text-center w-full')

    # max-w-sm keeps the grid constrained so it looks like a phone screen even on desktop
    # grid-cols-2 puts them in a perfect 2x2 grid
    with ui.element('div').classes('w-full max-w-sm mx-auto p-4 grid grid-cols-2 gap-6'):
        
        # MEALS APP (Blue tint)
        with ui.card().tight().classes('w-full aspect-square flex flex-col items-center justify-center cursor-pointer hover:shadow-xl hover:-translate-y-1 transition-all rounded-3xl bg-blue-50 text-blue-500').on('click', lambda: ui.navigate.to('/meals')):
            ui.icon('restaurant', size='4em')
            ui.label('Meals').classes('mt-3 text-lg font-bold text-gray-800')

        # TASKS APP (Green tint)
        with ui.card().tight().classes('w-full aspect-square flex flex-col items-center justify-center cursor-pointer hover:shadow-xl hover:-translate-y-1 transition-all rounded-3xl bg-green-50 text-green-500').on('click', lambda: ui.navigate.to('/tasks')):
            ui.icon('checklist', size='4em')
            ui.label('Tasks').classes('mt-3 text-lg font-bold text-gray-800')

        # TODAY APP (Orange tint)
        with ui.card().tight().classes('w-full aspect-square flex flex-col items-center justify-center cursor-pointer hover:shadow-xl hover:-translate-y-1 transition-all rounded-3xl bg-orange-50 text-orange-500').on('click', lambda: ui.navigate.to('/today')):
            ui.icon('wb_sunny', size='4em') 
            ui.label('Today').classes('mt-3 text-lg font-bold text-gray-800')

        # TOMORROW APP (Purple tint)
        with ui.card().tight().classes('w-full aspect-square flex flex-col items-center justify-center cursor-pointer hover:shadow-xl hover:-translate-y-1 transition-all rounded-3xl bg-purple-50 text-purple-500').on('click', lambda: ui.navigate.to('/tommorow')):
            ui.icon('calendar_month', size='4em')
            ui.label('Tomorrow').classes('mt-3 text-lg font-bold text-gray-800')

ui.run(host='0.0.0.0', port=80, title="Pi Dashboard", favicon='⚡')