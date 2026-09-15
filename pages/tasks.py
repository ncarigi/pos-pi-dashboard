from nicegui import ui
import json
import os
import datetime

TASKS_FILE = "/home/ncarigi/personal.json"

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

def load_tasks():
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, "r") as f:
                tasks = json.load(f)
                
                tasks = [{"task": t, "completed_date": None} if isinstance(t, str) else t for t in tasks]
                
                today_str = datetime.datetime.now().strftime("%Y-%m-%d")
                active_tasks = []
                needs_saving = False
                
                for t in tasks:
                    comp_date = t.get("completed_date")
                    if comp_date and comp_date < today_str:
                        needs_saving = True
                    else:
                        active_tasks.append(t)
                        
                if needs_saving:
                    save_tasks(active_tasks)
                    
                return active_tasks
        except Exception:
            return []
    return []

def router():
    @ui.page('/tasks')
    def tasks_page():
        with ui.column().classes('p-4 sm:p-8 w-full max-w-[375px] mx-auto items-center'):
            
            ui.label('Personal Tasks').classes('text-h4 font-bold mb-4')
            ui.button('Back to Home', on_click=lambda: ui.navigate.to('/')).classes('mb-4 bg-gray-500 text-white w-full')

            with ui.column().classes('w-full p-4 shadow-md rounded border border-yellow-200 bg-[#fefae0]'):
                
                tasks_container = ui.column().classes("w-full gap-1 mb-2")

                with ui.row().classes("w-full items-center gap-2 pt-3 border-t border-yellow-200/70 no-wrap"):
                    task_input = ui.input(placeholder="Jot down a task...") \
                        .props("dense outlined") \
                        .classes("flex-grow bg-white") \
                        .on("keydown.enter", lambda: add_task())
                    
                    ui.button(icon="add", on_click=lambda: add_task()) \
                        .props("dense color=purple unelevated") \
                        .classes("px-3 shadow-sm")

                def refresh_task_ui():
                    tasks_container.clear()
                    tasks = load_tasks()
                    
                    with tasks_container:
                        if not tasks:
                            ui.label("List is empty!").classes("text-gray-400 italic text-center w-full py-4")
                        
                        for idx, task in enumerate(tasks):
                            is_done = task.get("completed_date") is not None
                            
                            row_classes = "w-full items-center justify-between no-wrap py-1.5 px-2 rounded transition-all duration-300"
                            if is_done:
                                row_classes += " opacity-60 scale-[0.98]"
                                
                            with ui.row().classes(row_classes):
                                # Left side: Checkbox + Done Badge
                                with ui.row().classes("items-center no-wrap gap-2 flex-grow overflow-hidden"):
                                    cb = ui.checkbox(
                                        task["task"], 
                                        value=is_done, 
                                        on_change=lambda e, i=idx: toggle_task(i, e.value)
                                    ).classes("text-[15px] text-gray-800 font-medium transition-all duration-300")
                                    
                                    if is_done:
                                        cb.classes("line-through text-gray-500 font-normal")
                                        ui.label("Done").classes("text-[10px] font-bold text-white bg-green-400 px-2 py-0.5 rounded shadow-sm")
                                
                                # Right side: Simple grey X that turns red on hover
                                ui.icon('close') \
                                    .classes("text-gray-400 text-xl cursor-pointer transition-colors duration-200 hover:text-red-500") \
                                    .on('click', lambda e, i=idx: delete_task(i))

                def add_task():
                    text = task_input.value
                    if text and text.strip():
                        tasks = load_tasks()
                        tasks.append({"task": text.strip(), "completed_date": None})
                        save_tasks(tasks)
                        task_input.set_value("")
                        refresh_task_ui()

                def toggle_task(index, is_completed):
                    tasks = load_tasks()
                    if 0 <= index < len(tasks):
                        if is_completed:
                            tasks[index]["completed_date"] = datetime.datetime.now().strftime("%Y-%m-%d")
                        else:
                            tasks[index]["completed_date"] = None
                        save_tasks(tasks)
                        refresh_task_ui()
                        
                def delete_task(index):
                    tasks = load_tasks()
                    if 0 <= index < len(tasks):
                        tasks.pop(index)
                        save_tasks(tasks)
                        refresh_task_ui()

                refresh_task_ui()