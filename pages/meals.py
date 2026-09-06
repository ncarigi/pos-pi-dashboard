from nicegui import ui

def router():
    @ui.page('/meals')
    def meals_page():
        with ui.column().classes('p-8'):
            ui.label('Meals Dashboard').classes('text-h3 font-bold mb-4')
            ui.label('This is where you can add your meal printing logic.')
            ui.button('Back to Home', icon='arrow_back', on_click=lambda: ui.navigate.to('/')).classes('mt-8 bg-gray-500 text-white')