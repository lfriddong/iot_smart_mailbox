import time
import network
import urequests
import json
import machine
import ssd1306
from machine import Pin, PWM
import uasyncio as asyncio

# OLED setup
i2c = machine.I2C(Pin(5), Pin(4))
oled = ssd1306.SSD1306_I2C(128, 32, i2c)
msg_pushed = False
protection_mode = 0

# Servo setup
SERVO_PIN = 16
servo = PWM(Pin(SERVO_PIN), freq=50)  # 50 Hz is common for servo motors

def set_servo_angle(angle):
    # Convert angle to duty cycle
    duty = int((angle / 180) * 1023 + 26)
    servo.duty(duty)

def get_servo_state():
    # Placeholder function to determine door state based on servo angle
    if servo.duty() < 500:  # Example threshold, adjust as needed
        return "locked"
    else:
        return "open"

def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        oled.fill(0)
        oled.text('Connecting...', 0, 0)
        oled.show()
        sta_if.active(True)
        sta_if.connect('JoJoHome_2.4G', 'Pigeon88')  # ssid key
        while not sta_if.isconnected():
            pass
    oled.fill(0)
    if sta_if.isconnected():
        oled.text('Connected', 0, 0)
    else:
        oled.text('Connect failed', 0, 0)
    oled.show()
    return sta_if.config('mac')

def send(p):
    global msg_pushed
    # debounce
    active = 0
    while active < 40:
        if p.value() == 0:
            active += 1
        else:
            return
        time.sleep_ms(1)

    msg_pushed = True
    time.sleep(2)

def send_request_to_server():
    try:
        url = 'http://ntfy.sh/iotgroup8'
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({"message": "REQUEST_DOOROPEN"})
        response = urequests.post(url, data=data, headers=headers)
        oled.fill(0)
        oled.text('Msg sent', 0, 0)
        oled.show()
        print(response.text)
    except Exception as e:
        oled.fill(0)
        oled.text('Send failed', 0, 0)
        oled.show()
        print('Error sending request:', e)
    finally:
        time.sleep(2)

# Protection mode task
async def protection_task():
    global protection_mode
    prev_mode = None  # Variable to track changes in protection_mode
    while True:
        if protection_mode != prev_mode:  # Check if protection_mode has changed
            prev_mode = protection_mode
            oled.fill(0)  # Clear the OLED display
            if protection_mode == 1:
                oled.text('Mode: ON', 0, 0)
                print("Door is locked. Protection mode on.")
            else:
                oled.text('Mode: OFF', 0, 0)
                print("Door is open. Protection mode off.")
            oled.show()  # Update the OLED display

        await asyncio.sleep(0.5)  # Non-blocking sleep

# Main task
async def main_task():
    global msg_pushed
    mac_address = do_connect()
    print(mac_address)

    pin_2 = Pin(2, Pin.IN, Pin.PULL_UP)
    pin_2.irq(trigger=Pin.IRQ_FALLING, handler=send)

    while True:
        if msg_pushed:
            send_request_to_server()
            msg_pushed = False
        await asyncio.sleep(0.1)  # Yield control

# Main entry point
def main():
    # Initialize servo to locked position
    set_servo_angle(0)  # Adjust as needed for your setup

    loop = asyncio.get_event_loop()
    loop.create_task(protection_task())
    loop.create_task(main_task())
    loop.run_forever()

if __name__ == '__main__':
    main()
