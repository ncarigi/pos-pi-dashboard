from nicegui import ui

def router():
    @ui.page('/tomorrow')
    def tommorow_summary():
        with ui.column().classes('p-8'):
            ui.label('Tomorrow').classes('text-h3 font-bold mb-4')
            ui.button('Back to Home', icon='arrow_back', on_click=lambda: ui.navigate.to('/')).classes('mt-8 bg-gray-500 text-white')