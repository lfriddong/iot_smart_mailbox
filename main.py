import machine
import network
import urequests
import time
import ujson

# 请根据实际情况配置以下参数
# WIFI_SSID = "Columbia University"
# WIFI_PASSWORD = ""
WIFI_SSID = "JoJoHome_2.4G"
WIFI_PASSWORD = "Pigeon88"
SERVER_URL = "http://your_server_ip:your_server_port"
ESP32_SERVER = "192.168.0.211"
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
ir_distance_sensor_pin = 14  # 红外距离传感器的引脚配置

servo = machine.PWM(machine.Pin(servo_pin), freq=50)
button = machine.Pin(button_pin, machine.Pin.IN, machine.Pin.PULL_UP)
buzzer_pin = machine.Pin(buzzer_pin_number, machine.Pin.OUT)
pwm_buzzer = machine.PWM(buzzer_pin)
ir_distance_sensor = machine.ADC(machine.Pin(ir_distance_sensor_pin))

# --- 全局变量 --------------
# 设置初始状态

# 与服务端同步字段：
door_open_permit = False
mannual_protect_on = False
mannual_protect_off = False

# huzzhah本地状态字段:
protect_mode_status = False
door_open_request = False
detect_door_open = False  # 通过servo检测，代码还没实现


# --------------------------

def send_request(action):
    global SERVER_URL
    try:
        response = urequests.post(SERVER_URL, json={'action': action})
        return response.json()
    except Exception as e:
        print("Error sending request:", e)
        return {}


def check_server_status():
    global door_open_request, door_open_permit, protect_mode_status
    server_data = send_request("get_status")
    door_open_request = server_data.get("door_open_request", False)
    door_open_permit = server_data.get("door_open_permit", False)
    protect_mode_status = server_data.get("protect_mode_status", False)


def open_door():
    global servo
    # 设置伺服电机的duty值到75，以打开门
    servo.duty(75)
    time.sleep(1)  # 等待电机运动到指定位置


def close_door():
    global servo
    # 设置伺服电机的duty值回到20，以关闭门
    servo.duty(20)
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


def read_ir_distance():
    """
    读取红外距离传感器GP2Y0A21YK0F的值并转换为距离（单位：厘米），还需测试。
    """
    # 读取ADC值
    adc_value = ir_distance_sensor.read()

    # 将ADC值转换为电压（假设ESP8266的ADC范围为0-1V）
    voltage = adc_value * (1.0 / 1023.0)

    # 转换电压为距离
    # 这个转换公式依赖于特定传感器的特性，可能需要根据实际情况进行调整
    distance = 27.86 * (voltage ** -1.15)

    return distance


def is_door_open():
    """
    判断门是否被非法打开。
    :return: 如果门被非法打开返回 True，否则返回 False。
    """
    global protect_mode_status

    # 仅在保护模式开启时检查门是否被打开
    if protect_mode_status:
        distance = read_ir_distance()
        # 如果检测到的距离大于20厘米，则认为门被打开
        if distance > 20:
            return True

    return False


def take_photo():
    # 实现拍照和上传服务器的代码，例如使用 ESP 摄像头和相应的库
    # Take picture 
    # http://{server}/snap
    # Take picture with LED flash 
    # http://{server}/blitz

    response = urequests.get(f"http://{ESP32_SERVER}/blitz")
    print("Photo request sent, response:", response.text)


def upload_photo():
    pass


def button_interrupt_handler(pin):
    global door_open_request
    time.sleep(0.05)  # 初始延时以过滤即时噪声

    # 再次检查按钮状态以确认是否真的被按下
    if not pin.value():
        stable_time = time.time()
        while time.time() - stable_time < 0.2:  # 在0.2秒内持续检查按钮状态
            if pin.value():  # 如果按钮状态改变，重新开始计时
                stable_time = time.time()
        # 如果按钮状态在0.2秒内保持不变，则确认为有效的按钮按下
        door_open_request = True


def main_loop():
    global door_open_request, door_open_permit, protect_mode_status
    button.irq(trigger=machine.Pin.IRQ_FALLING, handler=button_interrupt_handler)

    while True:
        # 轮询服务器状态
        check_server_status()

        # 处理开门请求
        if door_open_request and not door_open_permit:
            # 向服务器发送开门请求
            send_request("request_door_open")
            # 在这里可以添加其他逻辑
            door_open_request = False

        # 处理开门许可
        if door_open_permit:
            # 执行打开门的操作
            open_door()
            # 拍照并上传到服务器,云服务器直接访问该服务器？
            take_photo()
            # 上传照片
            upload_photo()
            # 通知服务器关门确认
            send_request("door_closed_confirm")
            # 设置本地保护模式状态
            protect_mode_status = True

        if mannual_protect_on:
            protect_mode_status = True

        if mannual_protect_off:
            protect_mode_status = False

        # 处理保护模式
        if protect_mode_status:
            if is_door_open():
                alert()
                take_photo()
                upload_photo()
                door_open_request = False

        # 延时一段时间后再次轮询
        time.sleep(3)


# 启动主循环
main_loop()
