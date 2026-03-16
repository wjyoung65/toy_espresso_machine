from microbit import *
import music
import random
import log

# Uses buttons from micro:bit basic kit and
room_temp = 21
temperature = room_temp
target_temp = 90

arduino_pin = pin0

WATER_SIGNAL = 512
STEAM_SIGNAL = 768
COFFEE_SIGNAL = 1023
RESET_SIGNAL = 0

GRIND_PULSE = 50
WATER_PULSE = 100
MILK_PULSE = 150
STEAM_PULSE = 200
COFFEE_PULSE = 250
END_PULSE = 300

@run_every(s=5)
def reduce_temp():
    global temperature
    if temperature > room_temp:
        temperature = temperature - 1

def animate_grind(step=200):
    reset_displays()
    send_pulse(GRIND_PULSE)
    i = 0
    frames = [Image('90909:'
                    '09990:'
                    '99999:'
                    '09990:'
                    '90909'),
              Image('09090:'
                    '99999:'
                    '09990:'
                    '99999:'
                    '09090')]
    frame_len = len(frames)
    while True:
        x = pin1.read_analog()
        if x > 600: # no buttons pressed
            break
        display.show(frames[i])
        sleep(step)
        i = (i + 1) % frame_len
    send_pulse(END_PULSE)

def animate_water(step=200):
    global temperature
    reset_displays()
    try:
        uart.init(tx=pin2)
        uart.write('%3dC,' % temperature)
        for i in range(temperature, target_temp + 1):
            temperature = i
            uart.write(' ')
            uart.write('%3dC,' % i)
            sleep(step)
        send_pulse(WATER_PULSE)
        animate_fill(500)
    finally:
        uart.init(baudrate=115200)
        send_pulse(END_PULSE)

def animate_milk():
    reset_displays()
    send_pulse(MILK_PULSE)
    animate_fill()
    send_pulse(END_PULSE)

def send_pulse(duration_ms, pin=arduino_pin):
    pin.write_digital(1)
    sleep(duration_ms)
    pin.write_digital(0)

def animate_coffee(step=400):
    reset_displays()
    send_pulse(COFFEE_PULSE)
    display.show(Image('00000:'
                       '90009:'
                       '90009:'
                       '90009:'
                       '99999'))
    sleep(step)
    display.show(Image('00900:'
                       '90009:'
                       '90009:'
                       '90009:'
                       '99999'))
    sleep(step)
    display.show(Image('00900:'
                       '90909:'
                       '90009:'
                       '90009:'
                       '99999'))
    sleep(step)
    display.show(Image('00900:'
                       '90909:'
                       '90009:'
                       '90009:'
                       '99999'))
    sleep(step)
    display.show(Image('00900:'
                       '90909:'
                       '90909:'
                       '90009:'
                       '99999'))
    sleep(step)
    display.show(Image('00900:'
                       '90909:'
                       '90909:'
                       '90909:'
                       '99999'))
    sleep(step)
    display.show(Image('00900:'
                       '90909:'
                       '90909:'
                       '92929:'
                       '99999'))
    sleep(step)
    display.show(Image('00900:'
                       '90909:'
                       '92929:'
                       '96669:'
                       '99999'))

    sleep(step)
    display.show(Image('00000:'
                       '90909:'
                       '96669:'
                       '96669:'
                       '99999'))

    sleep(step)
    display.show(Image('00000:'
                       '90009:'
                       '96669:'
                       '96669:'
                       '99999'))
    send_pulse(END_PULSE)

def animate(frames, step=200):
    for i in range(0, len(frames)):
        display.show(frames[i])
        sleep(step)

def animate_while_button_pressed(frames, step=200):
    i = 0
    frame_len = len(frames)
    while True:
        x = pin1.read_analog()
        if x > 600: # no buttons pressed
            break
        display.show(frames[i])
        sleep(step)
        i = (i + 1) % frame_len
    display.clear()


def animate_steam(step=200):
    reset_displays()
    send_pulse(STEAM_PULSE)
    frames = [Image('00500:'
                    '00500:'
                    '00500:'
                    '00500:'
                    '00000'),
              Image('00500:'
                    '00500:'
                    '00500:'
                    '50505:'
                    '05050')]
    animate_while_button_pressed(frames, step)
    send_pulse(END_PULSE)
    reset_displays()

def clear_7seg():
    try:
        uart.init(tx=pin2)
        uart.write('    ,')
    finally:
        uart.init(baudrate=115200)

def reset_displays():
    display.show(Image('00000:'
                       '00000:'
                       '00900:'
                       '00000:'
                       '00000'))
    clear_7seg()

def display_7seg(s):
    try:
        uart.init(tx=pin2)
        uart.write(s)
    finally:
        uart.init(baudrate=115200)


def animate_fill(step=100):
    animate([Image("00009:"
                   "00000:"
                   "90009:"
                   "90009:"
                   "99999"),
             Image("00009:"
                   "00090:"
                   "90009:"
                   "90009:"
                   "99999"),
             Image("00009:"
                   "00090:"
                   "90909:"
                   "90009:"
                   "99999"),
             Image("00009:"
                   "00090:"
                   "90909:"
                   "90909:"
                   "99999"),
             Image("00000:"
                   "00090:"
                   "90909:"
                   "99999:"
                   "99999"),
             Image("00000:"
                   "00000:"
                   "90909:"
                   "99999:"
                   "99999"),
             Image("00000:"
                   "00000:"
                   "90009:"
                   "99999:"
                   "99999")], step)

reset_displays()
display_7seg('%3dC,' % temperature)

state = None
stable_state = None
debounce_count = 0
DEBOUNCE_THRESHOLD = 3

while True:
    x = pin1.read_analog()

    if x < 10: # A
        state = 'grind'
    elif x < 80: # B
        state = 'water'
    elif x < 130: # C - milk
        state = 'milk'
    elif x < 160: # D
        state = 'steam'
    elif x < 600: # E
        state = 'coffee'
    else:
        state = 'waiting'

    if state == stable_state:
        debounce_count = 0
    else:
        debounce_count += 1
        if debounce_count >= DEBOUNCE_THRESHOLD:
            stable_state = state
            debounce_count = 0
            if stable_state == 'grind': animate_grind()
            elif stable_state == 'water': animate_water()
            elif stable_state == 'milk': animate_milk()
            elif stable_state == 'steam': animate_steam()
            elif stable_state == 'coffee': animate_coffee()
