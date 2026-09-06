from gpiozero import Button
from subprocess import call
from signal import pause

def run_printer():
    print("Hardware button pressed! Triggering printer script...")
    # This calls your original printer script exactly like the desktop icon did
    call(['sudo', 'python3', '/home/ncarigi/print_manager.py'])

# Tell the Pi that our button is connected to GPIO 17
button = Button(17)

# When the button is pressed, execute our function above
button.when_pressed = run_printer

print("Listening for hardware button press... (Press Ctrl+C to stop)")
# Keep the script running forever in the background
pause()
