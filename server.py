from flask import Flask, request, jsonify
import threading
import time

app = Flask(__name__)

# 初始化服务端状态字段
status = {
    "door_open_permit": False,
    "mannual_protect_on": False,
    "mannual_protect_off": False,
    "request_door_open": False,
    "alarm_on": False,
    "protect_mode_status":False
}

# 用于同步状态的锁
status_lock = threading.Lock()

def check_and_reset_status():
    with status_lock:
        # 在这里添加任何需要定期重置的状态字段
        status["door_open_permit"] = False
        status["mannual_protect_on"] = False
        status["mannual_protect_off"] = False
        status["request_door_open"] = False
        status["alarm_on"] = False

def get_status():
    with status_lock:
        return status.copy()

def set_status(request_data):
    with status_lock:
        # 仅更新客户端提供的字段
        for key in request_data:
            if key in status:
                status[key] = request_data[key]
    print(status)

# -------路由----------------
@app.route('/get_status', methods=['GET'])
def get_status_route():
    return jsonify(get_status())

@app.route('/set_status', methods=['POST'])
def set_status_route():
    request_data = request.get_json()
    set_status(request_data)
    return jsonify({"success": True})

@app.route('/get_image_url', methods=['GET'])
def get_image_url():
    # app轮询url路径
    # 这个逻辑需要根据你的实际情况实现
    latest_image_url = "http://35.225.150.6/images/1.jpeg"  # 替换成实际的图片 URL
    return jsonify({"image_url": latest_image_url})    

@app.route('/upload_photo', methods=['POST'])
def upload_photo():
    try:
        # 接收照片数据
        photo_data = request.data
        
        # 保存照片到文件路径
        with open('/home/wd2375/pub_pics/1.jpeg', 'wb') as photo_file:
            photo_file.write(photo_data)

        return jsonify({"success": True, "message": "Photo uploaded successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


'''
额外功能
@app.route('/perform_action', methods=['POST'])
def perform_action_route():
    data = request.get_json()
    action = data.get('action', None)
    if action:
        # 根据 action 执行相应的操作
        if action == 'get_status':
            return jsonify(get_status())
        elif action == 'some_other_action':
            # 执行其他操作
            pass
        else:
            return jsonify({"error": "Unknown action"})
    else:
        return jsonify({"error": "No action specified"})
'''
# --------------------------------


if __name__ == '__main__':
    # 启动服务端
    threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 5000}).start()

    # 模拟服务端定期清零状态
    while True:
        check_and_reset_status()
        time.sleep(300)  # 每隔5分钟清零状态
