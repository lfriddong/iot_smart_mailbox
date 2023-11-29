import uasyncio as asyncio
import network
import urequests
import json
import machine
from machine import Pin, PWM
import ssd1306

# Initialize I2C and OLED
i2c = machine.I2C(scl=Pin(5), sda=Pin(4))
oled = ssd1306.SSD1306_I2C(128, 32, i2c)

# Global variables
msg_pushed = False
protection_mode = 0  # Start with protection mode off
servo_pin = PWM(Pin(14), freq=50)  # Servo motor connected to pin 14

def update_oled(message):
    """ Update the OLED display with the given message. """
    oled.fill(0)  # Clear the display
    oled.text(message, 0, 0)
    oled.show()

async def protection_mode_monitor():
    global protection_mode, servo_pin
    while True:
        if protection_mode:
            duty = servo_pin.duty()
            if duty < 30:  # Adjust this threshold as needed
                update_oled("Warning: Door open!")
            else:
                update_oled("Protection: ON")
            await asyncio.sleep(1)  # Check every second
        else:
            update_oled("Protection: OFF")
            await asyncio.sleep(1)  # Sleep longer when protection mode is off to save CPU

def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect('JoJoHome_2.4G', 'Pigeon88')  #ssid key
        while not sta_if.isconnected():
            pass
    update_oled('WiFi Connected')
    return sta_if.config('mac')

async def send_request_to_server():
    try:
        url = 'http://ntfy.sh/iotgroup8'
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({"message": "REQUEST_DOOROPEN"})
        response = urequests.post(url, data=data, headers=headers)
        print(response.text)
    except Exception as e:
        print('Error sending request:', e)
    finally:
        await asyncio.sleep(2)  # Non-blocking sleep

async def button_task():
    global msg_pushed
    pin_2 = Pin(2, Pin.IN, Pin.PULL_UP)
    while True:
        if not pin_2.value():  # Active low button
            await asyncio.sleep(0.01)  # Debounce delay
            if not pin_2.value():
                msg_pushed = True
                while not pin_2.value():
                    await asyncio.sleep(0.01)  # Wait for button release
        await asyncio.sleep(0.1)  # Polling delay

async def main():
    global msg_pushed
    # Connect to WiFi
    mac_address = do_connect()
    print(mac_address)

    # Start tasks
    asyncio.create_task(protection_mode_monitor())
    asyncio.create_task(button_task())

    while True:
        if msg_pushed:
            await send_request_to_server()
            msg_pushed = False  # Reset the flag after sending the request
        await asyncio.sleep(0.1)  # Non-blocking sleep

asyncio.run(main())
