import time
import network
import socket
import machine
from machine import Pin, PWM
import ssd1306

# 初始化I2C对象，使用正确的引脚和扫描到的设备地址
i2c = machine.I2C(scl=machine.Pin(5), sda=machine.Pin(4))
oled = ssd1306.SSD1306_I2C(128, 32, i2c, addr=0x3C)  # 使用扫描到的地址
msg_pushed = False

# 使用GPIO14作为伺服电机的控制引脚
servo_pin = Pin(14)

# 初始化PWM对象
servo = PWM(servo_pin, freq=50)  # 伺服电机通常使用50Hz的频率

def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect('JoJoHome_2.4G', 'Pigeon88')  #ssid key
        while not sta_if.isconnected():
            pass
    return sta_if.config('mac')

# TCP服务器地址和端口
TCP_SERVER_IP = '192.168.0.248'  # 服务器的IP地址
TCP_SERVER_PORT = 8080  # 服务器的端口

# 伺服电机角度转换为PWM值的函数
def servo_duty(angle):
    return int(650 + (angle * 10 / 9))

# 打开门（将伺服电机设置为垂直状态）
def open_door():
    servo.duty(servo_duty(90))  # 假设90度为垂直位置
    print('Door opened')

# 关闭门（将伺服电机设置为水平状态）
def close_door():
    servo.duty(servo_duty(0))  # 假设0度为水平位置
    print('Door closed')

def turn_on_protection():
    # TODO: 实现开启保护模式的逻辑
    print('Turning on protection')
    pass

def turn_off_protection():
    # TODO: 实现关闭保护模式的逻辑
    print('Turning off protection')
    pass

# 修改send_tcp_message函数以处理不同的响应
def send_tcp_message(message):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((TCP_SERVER_IP, TCP_SERVER_PORT))
        s.send(message)
        response = s.recv(1024)
        s.close()
        response = response.decode('utf-8')
        print('Received:', response)
        oled.fill(0)  # 清屏
        oled.text('Received:', 0, 0)
        oled.text(response, 0, 10)
        oled.show()

        # 根据不同的响应执行不同的操作
        if response == "PERMIT_DOOROPEN":
            open_door()
        elif response == "TURN_ON_PROTECT":
            turn_on_protection()
        elif response == "TURN_OFF_PROTECT":
            turn_off_protection()

    except OSError as e:
        print('Error:', e)
        oled.fill(0)
        oled.text('Error:', 0, 0)
        oled.text(str(e), 0, 10)
        oled.show()

def send_open_request(p):
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
    # 发送请求打开门的命令
    send_tcp_message(b'REQUEST_DOOROPEN_HUZZAH')
    time.sleep(2)

def usr_permit_dooropen(p):
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
    send_tcp_message(b'USR_PERMIT_DOOROPEN')
    time.sleep(2)

def main():
    global msg_pushed
    mac_address = do_connect()
    print(mac_address)

    pin_2 = Pin(2, Pin.IN, Pin.PULL_UP)
    pin_2.irq(trigger=Pin.IRQ_FALLING, handler=send_open_request)
    pin_16 = Pin(0, Pin.IN, Pin.PULL_UP)
    pin_16.irq(trigger=Pin.IRQ_FALLING, handler=usr_permit_dooropen)

    while True:

        if msg_pushed:
            pass



if __name__ == '__main__':
    main()
