from nicegui import ui, Client
import subprocess
import asyncio

def router():
    @ui.page('/tommorow')
    def tomorrow_page():
        pass  # Route registration placeholder

    @ui.page('/tomorrow')
    async def tomorrow_summary(client: Client):
        with ui.column().classes('p-4 sm:p-8 w-full max-w-[375px] mx-auto items-center'):
            ui.label('Tomorrow Summary').classes('text-h4 font-bold mb-4')

            async def print_to_hardware(e):
                e.sender.disable()
                e.sender.text = 'Printing...'
                ui.notify("Sending tomorrow's receipt to printer...", type='info')
                await asyncio.sleep(0.2)
                
                try:
                    # Added --tomorrow and --real flags
                    physical_result = await asyncio.to_thread(
                        subprocess.run,
                        ['python3', '/home/ncarigi/print_manager.py', '--tomorrow', '--real'],
                        capture_output=True,
                        text=True
                    )
                    if physical_result.returncode == 0:
                        ui.notify("Printed successfully!", type='positive')
                    else:
                        ui.notify(f"Print failed: {physical_result.stderr}", type='negative', timeout=5000)
                except Exception as err:
                    ui.notify(f"System Error: {err}", type='negative')

                e.sender.enable()
                e.sender.text = '🖨️ Print'

            # Navigation & Actions
            ui.button('Back to Home', on_click=lambda: ui.navigate.to('/')).classes('mb-4 bg-gray-500 text-white')
            ui.button('🖨️ Print Tomorrow', on_click=print_to_hardware, color='purple').classes('w-full max-w-sm mt-4 font-bold py-3 shadow-md')

            receipt_container = ui.column().classes('w-full max-w-sm items-center mt-4')
            with receipt_container:
                ui.spinner('dots', size='lg', color='purple')
                ui.label('Fetching APIs for tomorrow...').classes('mt-2 text-gray-500')

            await client.connected()

            # Generate preview without --real flag
            try:
                result = await asyncio.to_thread(
                    subprocess.run,
                    ['python3', '/home/ncarigi/print_manager.py', '--tomorrow'],
                    capture_output=True,
                    text=True
                )
                output_text = result.stdout if result.stdout else "No output detected from print_manager.py."
                if result.stderr:
                    output_text += f"\n\n[ERRORS]:\n{result.stderr}"
            except Exception as e:
                output_text = f"Failed to run script: {e}"

            receipt_container.clear()
            with receipt_container:
                ui.label(output_text).classes(
                    'w-full bg-gray-100 text-black border-2 border-gray-400 font-mono text-sm p-3 shadow-lg whitespace-pre-wrap break-words'
                )