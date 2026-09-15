from nicegui import ui
import json
import os
import datetime
from zoneinfo import ZoneInfo

MEALS_FILE = "/home/ncarigi/meals.json"
dragged_item = None 
LOCAL_TZ = ZoneInfo("America/Toronto") # Enforce Montreal Timezone

def load_meals():
    if os.path.exists(MEALS_FILE):
        try:
            with open(MEALS_FILE, "r") as f:
                data = json.load(f)
                for d_str, d_meals in list(data.get('schedule', {}).items()):
                    if isinstance(d_meals, list):
                        data['schedule'] = {}
                        break
                return data
        except Exception:
            pass
            
    return {
        "bank": {},
        "schedule": {}
    }

def save_meals(data):
    with open(MEALS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_meal_colors(meal_name):
    palettes = [
        ('bg-red-50', 'text-red-700', 'border-red-200'),
        ('bg-orange-50', 'text-orange-700', 'border-orange-200'),
        ('bg-amber-50', 'text-amber-700', 'border-amber-200'),
        ('bg-green-50', 'text-green-700', 'border-green-200'),
        ('bg-emerald-50', 'text-emerald-700', 'border-emerald-200'),
        ('bg-teal-50', 'text-teal-700', 'border-teal-200'),
        ('bg-cyan-50', 'text-cyan-700', 'border-cyan-200'),
        ('bg-blue-50', 'text-blue-700', 'border-blue-200'),
        ('bg-indigo-50', 'text-indigo-700', 'border-indigo-200'),
        ('bg-violet-50', 'text-violet-700', 'border-violet-200'),
        ('bg-purple-50', 'text-purple-700', 'border-purple-200'),
        ('bg-fuchsia-50', 'text-fuchsia-700', 'border-fuchsia-200'),
        ('bg-pink-50', 'text-pink-700', 'border-pink-200'),
        ('bg-rose-50', 'text-rose-700', 'border-rose-200')
    ]
    idx = sum(ord(c) for c in meal_name) % len(palettes)
    return palettes[idx]


def router():
    @ui.page('/meals')
    def meals_page():
        data = load_meals()

        # --- MOBILE TAP-TO-SCHEDULE DIALOG ---
        active_meal_for_dialog = {"name": ""}

        with ui.dialog() as mobile_schedule_dialog, ui.card().classes('w-full max-w-[320px] p-0 rounded-xl shadow-2xl'):
            dialog_title = ui.label('').classes('font-bold text-base p-3 bg-gray-50 w-full border-b border-gray-200 text-center text-gray-800')
            dialog_content = ui.column().classes('w-full p-0 gap-0 max-h-[50vh] overflow-y-auto')
            
            with ui.row().classes('w-full p-2 bg-gray-50 border-t border-gray-200'):
                ui.button('Close', on_click=mobile_schedule_dialog.close).props('flat text-gray-500').classes('w-full min-h-0 py-1')

        def open_mobile_dialog(meal):
            active_meal_for_dialog['name'] = meal
            dialog_title.set_text(f'Schedule {meal}')
            
            dialog_content.clear()
            today_date = datetime.datetime.now(tz=LOCAL_TZ).date()
            current_meal = active_meal_for_dialog['name']
            
            with dialog_content:
                for i in range(7):
                    t_date = today_date + datetime.timedelta(days=i)
                    t_str = t_date.strftime("%Y-%m-%d")
                    d_name = "Today" if i == 0 else "Tomorrow" if i == 1 else t_date.strftime("%A")
                    
                    day_schedule = data['schedule'].get(t_str, {"Lunch": [], "Dinner": []})
                    has_lunch = current_meal in day_schedule.get("Lunch", [])
                    has_dinner = current_meal in day_schedule.get("Dinner", [])
                    
                    with ui.row().classes('w-full justify-between items-center p-3 border-b border-gray-100 last:border-0'):
                        ui.label(d_name).classes('font-medium text-gray-700 text-sm')
                        with ui.row().classes('gap-2 no-wrap'):
                            
                            lunch_icon = 'check_circle' if has_lunch else 'radio_button_unchecked'
                            lunch_color = 'green' if has_lunch else 'amber-8'
                            ui.button('Lunch', icon=lunch_icon, on_click=lambda e, d=t_str: schedule_from_dialog(d, 'Lunch')) \
                                .props(f'outline size=sm color={lunch_color}').classes('px-2 py-0.5 rounded')
                            
                            dinner_icon = 'check_circle' if has_dinner else 'radio_button_unchecked'
                            dinner_color = 'green' if has_dinner else 'indigo-8'
                            ui.button('Dinner', icon=dinner_icon, on_click=lambda e, d=t_str: schedule_from_dialog(d, 'Dinner')) \
                                .props(f'outline size=sm color={dinner_color}').classes('px-2 py-0.5 rounded')
                                
            mobile_schedule_dialog.open()

        def schedule_from_dialog(date_str, meal_type):
            add_to_schedule(date_str, meal_type, active_meal_for_dialog['name'])
            open_mobile_dialog(active_meal_for_dialog['name'])

        # --- MAIN LAYOUT ---
        with ui.column().classes('w-full max-w-5xl mx-auto p-2 sm:p-4 min-h-screen pb-[45vh] md:pb-4'):
            
            with ui.row().classes('w-full items-center justify-between mb-4 no-wrap'):
                ui.label('Meal Planner').classes('text-h4 font-bold text-gray-800')
                ui.button('Back to Home', on_click=lambda: ui.navigate.to('/')).classes('bg-gray-500 text-white py-1 px-4')

            with ui.row().classes('w-full gap-6 items-start flex-col md:flex-row no-wrap'):
                
                # LEFT: Vertical Sliding Week
                with ui.column().classes('w-full md:w-2/3 gap-3'):
                    ui.label('🗓️ 7-Day Plan').classes('text-xl font-bold text-gray-700 px-1')
                    schedule_container = ui.column().classes('w-full gap-4')

                # RIGHT: Meal Bank & Progress Grid
                with ui.column().classes(
                    'w-full md:w-1/3 bg-white md:bg-gray-50 border-t md:border border-gray-200 '
                    'md:rounded-xl shadow-[0_-8px_20px_-5px_rgba(0,0,0,0.15)] md:shadow-inner '
                    'p-4 fixed bottom-0 left-0 md:sticky md:top-8 z-40 md:z-10 '
                    'max-h-[45vh] md:max-h-[90vh] overflow-y-auto transition-all'
                ):
                    ui.label('🍲 Prep Inventory').classes('text-xl font-bold text-gray-700 mb-2 hidden md:block')
                    
                    progress_container = ui.column().classes('w-full mb-2')
                    
                    with ui.row().classes('w-full items-center gap-2 mb-4 no-wrap'):
                        new_meal_input = ui.input(placeholder='New meal...') \
                            .props('dense outlined') \
                            .classes('flex-grow bg-white text-base') \
                            .on('keydown.enter', lambda: add_new_meal())
                        ui.button(icon='add', on_click=lambda: add_new_meal()).props('dense unelevated color=purple').classes('px-3 shadow-sm')
                        
                    bank_container = ui.column().classes('w-full gap-2 pb-2')

        # --- LOGIC FUNCTIONS ---
        def handle_dragstart(meal, source_date=None, source_type=None, source_idx=None):
            global dragged_item
            dragged_item = {
                'meal': meal,
                'source_date': source_date,
                'source_type': source_type,
                'idx': source_idx
            }

        def handle_drop(target_date_str, target_meal_type):
            global dragged_item
            if not dragged_item: return
            
            meal = dragged_item['meal']
            src_date = dragged_item['source_date']
            src_type = dragged_item['source_type']
            src_idx = dragged_item['idx']
            
            if src_date is None:
                if data['bank'].get(meal, 0) > 0:
                    data['bank'][meal] -= 1
            else:
                try:
                    data['schedule'][src_date][src_type].pop(src_idx)
                except Exception:
                    pass
                if not data['schedule'][src_date].get("Lunch") and not data['schedule'][src_date].get("Dinner"):
                    del data['schedule'][src_date]

            if target_date_str not in data['schedule']:
                data['schedule'][target_date_str] = {"Lunch": [], "Dinner": []}
            if target_meal_type not in data['schedule'][target_date_str]:
                data['schedule'][target_date_str][target_meal_type] = []
                
            data['schedule'][target_date_str][target_meal_type].append(meal)
            
            dragged_item = None
            save_meals(data)
            refresh_ui()

        def add_to_schedule(date_str, meal_type, meal):
            if date_str not in data['schedule']:
                data['schedule'][date_str] = {"Lunch": [], "Dinner": []}
            if meal_type not in data['schedule'][date_str]:
                data['schedule'][date_str][meal_type] = []
                
            data['schedule'][date_str][meal_type].append(meal)
            
            if data['bank'].get(meal, 0) > 0:
                data['bank'][meal] -= 1
                
            save_meals(data)
            refresh_ui()

        def remove_scheduled(date_str, meal_type, idx, meal):
            data['schedule'][date_str][meal_type].pop(idx)
            if not data['schedule'][date_str]["Lunch"] and not data['schedule'][date_str]["Dinner"]:
                del data['schedule'][date_str]
            data['bank'][meal] = data['bank'].get(meal, 0) + 1
            save_meals(data)
            refresh_ui()

        def change_bank(meal, delta):
            data['bank'][meal] = max(0, data['bank'].get(meal, 0) + delta)
            save_meals(data)
            refresh_ui()

        def add_new_meal():
            name = new_meal_input.value
            if name and name.strip():
                name = name.strip()
                if name not in data['bank']:
                    data['bank'][name] = 1
                    save_meals(data)
                new_meal_input.set_value('')
                refresh_ui()
                
        def delete_meal_from_bank(meal):
            del data['bank'][meal]
            save_meals(data)
            refresh_ui()

        # --- RENDER UI ---
        def render_meal_pills(t_str, meal_type):
            scheduled_meals = data['schedule'].get(t_str, {}).get(meal_type, [])
            if not scheduled_meals:
                ui.label('Drop here').classes('text-[10px] text-gray-400 font-medium italic hidden md:block')
            else:
                for idx, meal in enumerate(scheduled_meals):
                    bg_color, text_color, border_color = get_meal_colors(meal)
                    with ui.row().classes(f'items-center {bg_color} {text_color} border {border_color} px-2 py-1 rounded shadow-sm gap-1 no-wrap cursor-grab active:cursor-grabbing pointer-events-auto') \
                        .props('draggable="true"') \
                        .on('dragstart', lambda e, d=t_str, mt=meal_type, i=idx, ml=meal: handle_dragstart(ml, d, mt, i)):
                        
                        ui.label(meal).classes('font-bold text-sm')
                        ui.icon('close').classes('text-xs cursor-pointer hover:text-black opacity-60 hover:opacity-100 transition-all ml-1') \
                            .on('click', lambda e, d=t_str, mt=meal_type, i=idx, ml=meal: remove_scheduled(d, mt, i, ml))

        def refresh_ui():
            today_date = datetime.datetime.now(tz=LOCAL_TZ).date()
            today_str = today_date.strftime("%Y-%m-%d")
            
            old_dates = [d for d in data['schedule'].keys() if d < today_str]
            for d in old_dates:
                del data['schedule'][d]
            if old_dates:
                save_meals(data)

            schedule_container.clear()
            bank_container.clear()
            progress_container.clear()
            
            with progress_container:
                with ui.column().classes('w-full bg-white p-3 rounded-lg shadow-sm border border-gray-200'):
                    ui.label('WEEKLY COVERAGE').classes('text-[10px] font-bold text-gray-400 mb-2')
                    
                    with ui.row().classes('w-full items-center no-wrap'):
                        ui.label('').classes('w-12 flex-shrink-0') 
                        with ui.grid(columns=7).classes('flex-grow gap-0'):
                            for i in range(7):
                                t_date = today_date + datetime.timedelta(days=i)
                                ui.label(t_date.strftime("%a")[0]).classes('text-[10px] font-bold text-gray-500 place-self-center')

                    with ui.row().classes('w-full items-center no-wrap mt-2'):
                        ui.label('LUNCH').classes('text-[9px] font-extrabold text-amber-500 w-12 flex-shrink-0')
                        with ui.grid(columns=7).classes('flex-grow gap-0'):
                            for i in range(7):
                                t_str = (today_date + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
                                has_lunch = bool(data['schedule'].get(t_str, {}).get("Lunch", []))
                                icon_name = 'check_circle' if has_lunch else 'radio_button_unchecked'
                                color_class = 'text-green-500' if has_lunch else 'text-gray-200'
                                ui.icon(icon_name).classes(f'{color_class} text-sm place-self-center transition-colors')

                    with ui.row().classes('w-full items-center no-wrap mt-2'):
                        ui.label('DINNER').classes('text-[9px] font-extrabold text-indigo-500 w-12 flex-shrink-0')
                        with ui.grid(columns=7).classes('flex-grow gap-0'):
                            for i in range(7):
                                t_str = (today_date + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
                                has_dinner = bool(data['schedule'].get(t_str, {}).get("Dinner", []))
                                icon_name = 'check_circle' if has_dinner else 'radio_button_unchecked'
                                color_class = 'text-green-500' if has_dinner else 'text-gray-200'
                                ui.icon(icon_name).classes(f'{color_class} text-sm place-self-center transition-colors')


            with schedule_container:
                for i in range(7):
                    target_date = today_date + datetime.timedelta(days=i)
                    t_str = target_date.strftime("%Y-%m-%d")
                    display_date = "Today" if i == 0 else "Tomorrow" if i == 1 else target_date.strftime("%A")
                    full_date = target_date.strftime("%b %d")
                    
                    with ui.card().classes('w-full p-0 shadow-sm border border-gray-200 bg-white overflow-hidden h-max'):
                        with ui.row().classes('w-full bg-gray-50 px-3 py-2 border-b border-gray-200 justify-between items-center'):
                            ui.label(display_date).classes('font-bold text-base text-gray-800')
                            ui.label(full_date).classes('text-xs text-gray-500 font-medium')

                        with ui.column().classes('w-full gap-0'):
                            with ui.column().classes('w-full p-2 border-b border-gray-100 min-h-[45px] transition-colors hover:bg-amber-50/50') \
                                .on('dragover.prevent', lambda: None) \
                                .on('drop', lambda e, d=t_str: handle_drop(d, 'Lunch')):
                                
                                ui.label('LUNCH').classes('text-[10px] font-extrabold text-amber-500 uppercase tracking-widest mb-1 pointer-events-none')
                                with ui.row().classes('w-full gap-1.5 pointer-events-none flex-wrap'):
                                    render_meal_pills(t_str, 'Lunch')

                            with ui.column().classes('w-full p-2 min-h-[45px] transition-colors hover:bg-indigo-50/50') \
                                .on('dragover.prevent', lambda: None) \
                                .on('drop', lambda e, d=t_str: handle_drop(d, 'Dinner')):
                                
                                ui.label('DINNER').classes('text-[10px] font-extrabold text-indigo-500 uppercase tracking-widest mb-1 pointer-events-none')
                                with ui.row().classes('w-full gap-1.5 pointer-events-none flex-wrap'):
                                    render_meal_pills(t_str, 'Dinner')

            with bank_container:
                if not data['bank']:
                    ui.label('Your inventory is empty. Add a meal above!').classes('text-sm text-gray-400 italic py-2')
                
                for meal, count in data['bank'].items():
                    with ui.row().classes('w-full items-center justify-between p-2 bg-white rounded shadow-sm border border-gray-100 cursor-grab active:cursor-grabbing hover:border-purple-300 transition-all') \
                        .props('draggable="true"') \
                        .on('dragstart', lambda e, m=meal: handle_dragstart(m)):
                        
                        with ui.row().classes('items-center gap-2 no-wrap'):
                            ui.icon('drag_indicator').classes('text-gray-300 text-base hidden md:block pointer-events-none')
                            
                            with ui.column().classes('gap-0 cursor-pointer') as meal_text_col:
                                ui.label(meal).classes('font-bold text-gray-800 leading-tight text-sm')
                                
                                # --- NEW INVENTORY LOGIC ---
                                scheduled_count = sum(
                                    day_data.get("Lunch", []).count(meal) + day_data.get("Dinner", []).count(meal)
                                    for day_data in data['schedule'].values()
                                )
                                total_count = count + scheduled_count
                                
                                if total_count == 0:
                                    ui.label('OUT OF STOCK').classes('text-[9px] text-red-400 font-bold uppercase tracking-wider')
                                elif count == 0:
                                    ui.label(f'ALL {total_count} SCHEDULED').classes('text-[9px] text-amber-500 font-bold uppercase tracking-wider')
                                elif scheduled_count == 0:
                                    ui.label(f'{count} IN FRIDGE').classes('text-[9px] text-gray-500 font-bold uppercase tracking-wider')
                                else:
                                    ui.label(f'{count} AVAIL OF {total_count}').classes('text-[9px] text-gray-500 font-bold uppercase tracking-wider')
                                        
                            meal_text_col.on('click', lambda e, m=meal: open_mobile_dialog(m))
                        
                        with ui.row().classes('items-center gap-1 no-wrap'):
                            ui.button(icon='remove', on_click=lambda e, m=meal: change_bank(m, -1)) \
                                .props('flat round size=sm').classes('text-gray-500 hover:bg-gray-100 min-w-[28px] min-h-[28px]')
                            
                            ui.label(str(count)).classes('font-mono font-bold w-4 text-center text-sm')
                            
                            ui.button(icon='add', on_click=lambda e, m=meal: change_bank(m, 1)) \
                                .props('flat round size=sm').classes('text-gray-500 hover:bg-gray-100 min-w-[28px] min-h-[28px]')
                                
                            ui.button(icon='delete', on_click=lambda e, m=meal: delete_meal_from_bank(m)) \
                                .props('flat round size=sm').classes('text-red-400 hover:bg-red-50 transition-colors ml-1 min-w-[28px] min-h-[28px]')

        refresh_ui()