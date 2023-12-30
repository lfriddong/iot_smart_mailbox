import machine
import network
import urequests
import time
import ujson

# 请根据实际情况配置以下参数
WIFI_SSID = "Columbia University"
WIFI_PASSWORD = ""
SERVER_URL = "http://35.225.150.6:5000"

# 初始化网络连接
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(WIFI_SSID, WIFI_PASSWORD)

# 等待连接成功
while not wifi.isconnected():
    pass

print("Connected to WiFi")

# 初始化伺服电机和按钮
servo_pin = 0  # 请根据实际情况配置伺服电机的引脚
button_pin = 4  # 请根据实际情况配置按钮的引脚
buzzer_pin_number = 5  # 替换为您连接蜂鸣器的实际引脚编号
light_sensor = machine.ADC(0)  # 光敏传感器连接到 ESP8266 的 A0 引脚, A0 引脚通常对应 ADC(0)

servo = machine.PWM(machine.Pin(servo_pin), freq=50)
button = machine.Pin(button_pin, machine.Pin.IN, machine.Pin.PULL_UP)
buzzer_pin = machine.Pin(buzzer_pin_number, machine.Pin.OUT)
pwm_buzzer = machine.PWM(buzzer_pin)
#ir_distance_sensor = machine.ADC(machine.Pin(ir_distance_sensor_pin))

# --- 全局变量 --------------
# 设置初始状态

# 与服务端同步字段：
door_open_permit = False
mannual_protect_on = False
mannual_protect_off = False

# huzzhah本地状态字段:
protect_mode_status = False
door_open_request = False
detect_door_open = False # 通过servo检测，代码还没实现
# --------------------------

# ------与服务器同步通信----------------
'''
def send_request(action):
    global SERVER_URL
    try:
        response = urequests.post(SERVER_URL, json={'action': action})
        return response.json()
    except Exception as e:
        print("Error sending request:", e)
        return {}
'''
# 拉取服务端状态
def get_server_status():
    global door_open_permit, mannual_protect_on,mannual_protect_off
    try:
        response = urequests.get(SERVER_URL + "/get_status")
        server_data = response.json()
        door_open_permit = server_data.get("door_open_permit", False)
        mannual_protect_on = server_data.get("mannual_protect_on", False)
        mannual_protect_off = server_data.get("mannual_protect_off", False)
    except Exception as e:
        print("Error checking server status:", e)

# 发送并更新服务端状态
def set_updated_status(status_name: str, value:bool ):
    try:
        payload = {f'{status_name}': value}
        response = urequests.post(SERVER_URL + "/set_status", json=payload)
        server_response = response.json()
        print("Server response:", server_response)
    except Exception as e:
        print("Error sending status to server:", e)


# -------------------------------------
def open_door():
    global servo
    # 设置伺服电机的duty值到75，以打开门
    servo.duty(20)
    time.sleep(1)  # 等待电机运动到指定位置


def close_door():
    global servo
    # 设置伺服电机的duty值回到20，以关闭门
    servo.duty(75)
    time.sleep(1)  # 等待电机运动回初始位置


def start_buzzer(frequency=1000):
    """
    开启蜂鸣器。
    :param frequency: 蜂鸣器发声的频率，单位为赫兹。
    """
    pwm_buzzer.freq(frequency)  # 设置蜂鸣器的频率
    pwm_buzzer.duty(512)  # 设置PWM占空比为50%


def stop_buzzer():
    """ 关闭蜂鸣器，停止发声。"""
    pwm_buzzer.deinit()  # 关闭PWM，停止发声


def alert():
    """
    在检测到非法开门时触发警报
    """
    start_buzzer()
    # 可以在这里添加其他警报逻辑，如 LED 闪烁等
    time.sleep(10)  # 警报持续时间
    stop_buzzer()


# ----------------------------------------------------

def take_photo_and_upload_delivery():
    # 触发esp32 /foto路由，进而拍照并上传服务器
    camera_url = "http://10.206.107.215"
    try:
        # 发送 GET 请求到 /foto 路由
        response = urequests.get(f"{camera_url}/foto")
        print("Server response:", response.text)
        response.close()
    except Exception as e:
        print("Error triggering photo capture:", e)

def take_photo_and_upload_unauth():
    pass

# （主动发送）处理开门请求
def button_interrupt_handler(pin):
    # 去抖
    time.sleep(0.05)  # 初始延时以过滤即时噪声
    # 再次检查按钮状态以确认是否真的被按下
    if not pin.value():
        stable_time = time.time()
        while time.time() - stable_time < 0.2:  # 在0.2秒内持续检查按钮状态
            if pin.value():  # 如果按钮状态改变，重新开始计时
                stable_time = time.time()
        # 如果按钮状态在0.2秒内保持不变，则确认为有效的按钮按下

        # 更新服务器door_open_request字段
        # set_updated_status('door_open_request',True) 弃用此字段
        take_photo_and_upload_delivery()


def main_loop():
    global door_open_request, door_open_permit, protect_mode_status, mannual_protect_on, mannual_protect_off
    button.irq(trigger=machine.Pin.IRQ_FALLING, handler=button_interrupt_handler)
    
    while True:
        # 轮询服务器状态
        get_server_status()

        # （接收通知）处理开门许可
        if door_open_permit:
            # 执行打开门的操作
            open_door()
            time.sleep(5)
            # 响应后，恢复door_open_permit为false，并同步服务端
            door_open_permit = False
            set_updated_status("door_open_permit",False)
            # 设置本地保护模式状态，并同步到服务器
            protect_mode_status = True
            set_updated_status("protect_mode_status",True)
            time.sleep(8)
            close_door()

        if mannual_protect_on:
            protect_mode_status = True
            mannual_protect_on = False
            set_updated_status('mannual_protect_on',False)

        if mannual_protect_off:
            protect_mode_status = False
            mannual_protect_off = False
            set_updated_status('mannual_protect_off',False)

        # 处理保护模式
        if protect_mode_status:
            print('protect_mode_ON')
            light_value = light_sensor.read()

            if protect_mode_status:
                if light_value > 100:
                    detect_door_open = True
                    # 在这里可以添加门打开时的其他操作，例如发出警报、拍照等
                else:
                    detect_door_open = False
                    # 在这里可以添加门关闭或无事发生时的操作

            if detect_door_open:
                # 保护模式下，检测到门被打开时触发蜂鸣器和拍照
                take_photo_and_upload_delivery()
                time.sleep(0.1)
                take_photo_and_upload_delivery()
                time.sleep(0.1)
                take_photo_and_upload_delivery()
                alert()
                set_updated_status('alarm_on',True)
                detect_door_open = False
        elif not protect_mode_status:
            print('protect_mode_OFF')

        # 延时一段时间后再次轮询
        time.sleep(3)

# 启动主循环
main_loop()
