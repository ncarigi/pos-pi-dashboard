from nicegui import ui
import json
import os

TASKS_FILE = "/home/ncarigi/personal.json"

def load_tasks():
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

def router():
    @ui.page('/tasks')
    def tasks_page():
        with ui.column().classes('p-8'):
            ui.label('Tasks Dashboard').classes('text-h3 font-bold mb-4')
            ui.button('Back to Home', icon='arrow_back', on_click=lambda: ui.navigate.to('/')).classes('mb-6 bg-gray-500 text-white')

            tasks_container = ui.column().classes("w-full max-w-md")

            def refresh_task_ui():
                tasks_container.clear()
                tasks = load_tasks()
                with tasks_container:
                    if not tasks:
                        ui.label("No active tasks!").classes("text-gray-400 italic")
                    for idx, task in enumerate(tasks):
                        with ui.row().classes("w-full items-center justify-between no-wrap py-1 border-b border-gray-100"):
                            ui.checkbox(
                                task, 
                                value=False, 
                                on_change=lambda _, i=idx: complete_task(i)
                            ).classes("text-sm")

            def add_task():
                text = task_input.value.strip()
                if text:
                    tasks = load_tasks()
                    tasks.append(text)
                    save_tasks(tasks)
                    task_input.set_value("")
                    refresh_task_ui()

            def complete_task(index):
                tasks = load_tasks()
                if 0 <= index < len(tasks):
                    tasks.pop(index)
                    save_tasks(tasks)
                    refresh_task_ui()

            with ui.row().classes("w-full max-w-md items-center gap-2 mb-4"):
                task_input = ui.input(placeholder="Type task & press Enter...") \
                    .props("dense outlined") \
                    .classes("flex-grow") \
                    .on("keydown.enter", add_task)
                ui.button("Add", on_click=add_task).props("dense unelevated color=primary")

            refresh_task_ui()