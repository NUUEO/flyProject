from flask import Flask, render_template, request, redirect, url_for, Response, jsonify
import subprocess
import os
import time
from camera import Camera

app = Flask(__name__)

# 全域變數：延遲初始化相機實例
camera_instance = None
item = 0
colorfilter = ['Init','Red','Green','Blue','Visible','None']
def get_camera():
    global camera_instance
    
    timestamp = time.localtime()
    try:
        os.mkdir("Picture")
    except FileExistsError:
        pass
    path = "Picture_{name}"
    if camera_instance is None:
        print("Lazy initializing camera ...")
        camera_instance = Camera()
        time.sleep(1)
        camera_instance.set_polarized8_format()
        time.sleep(1)
        camera_instance.open_camera()
    
    return camera_instance

@app.route('/')
def index():
    steps = request.args.get('steps', "84")
    speed = request.args.get('speed', "600")
    # 請建立一個 index.html 模板，至少包含一個顯示串流影像的 <img> 標籤，例如：
    # <img src="{{ url_for('video_feed') }}" style="width:100%;max-width:612px;">
    return render_template('index.html', steps=steps, speed=speed,colorfilter=colorfilter, item=item)

@app.route('/video_feed')
def video_feed():
    cam = get_camera()
    global colorfilter, item
    return Response(cam.http_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/motor', methods=['POST'])
def motor_control():
    global colorfilter
    global item
    data = request.get_json()
    action = data.get("action")
    steps = data.get("steps")
    speed = data.get("speed")

    if action not in ["reverse", "forward", "Previous", "Next"]:
        return jsonify({"status": "error", "message": "無效的指令"}), 400

    # 這裡可以加入控制馬達的程式碼，例如：
    print(f"執行動作: {action}, 步數: {steps}, 速度: {speed}")
    if action == 'reverse':
        direction = "1"
    elif action == 'forward':
        direction = "0"
    elif action == 'Previous':
        steps = "86"
        direction = "1"
        item = item - 1
        if item < 0:
            item = len(colorfilter) - 1
    elif action == 'Next':
        steps = "86"
        direction = "0"
        item = item + 1
        if item >= len(colorfilter):
            item = 0
    else:
        return redirect(url_for('index'))
    
    command = ["./motor", "-d", direction, "-s", steps, "-p", speed]
    
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print("馬達命令執行失敗：", e)
    return jsonify({"status": "success", "message": f"{action} 執行成功！步數: {steps}, 速度: {speed}"}),200

@app.route('/get_filter_status')
def get_filter_status():
    global colorfilter, item
    return {'current_filter': colorfilter[item]}
@app.route('/saveimg', methods=['POST'])
def saveimg():
    global colorfilter
    global item
    cam = get_camera()
    cam.save(colorfilter[item])
    print(colorfilter[item])
    return jsonify({'status': 'success', 'message': '影像已儲存'}), 200

@app.route('/sync', methods=['POST'])
def sync():
    if request.content_type != "application/json":
        return jsonify({'status': 'error', 'message': '請求格式錯誤，請使用 JSON'}), 415

    data = request.get_json()
    folder_name = data.get("folder_name", "default_backup")
    print(folder_name)
    if not folder_name:
        return jsonify({'status': 'error', 'message': '請提供資料夾名稱'}), 400
    subprocess.run(['pwd'])
    base_path = "/home/defu/Pictures" 
    local_path = "./Picture/*"  # 你的影像資料夾
    new_path = f"{base_path}/{folder_name}"

    try:
        # 先在 NAS 上建立目錄
        print("建立目錄")
        try:
            subprocess.run(["mkdir", new_path], check=True)
        except:
            pass
        # 執行 rsync 備份
        print("執行備份")
        subprocess.run(f"cp -vr {local_path} {new_path}/", shell=True, check=True)
        return jsonify({'status': 'success', 'message': f'備份成功'}), 500
    except subprocess.CalledProcessError as e:
        print("完成")
        return jsonify({'status': 'error', 'message': f'備份失敗: {e}'}), 500
@app.route('/shutdown', methods=['POST'])
def shutdown():
    subprocess.run(f"echo 'begin0927' | sudo -S poweroff", shell=True, check=True)
if __name__ == '__main__':
    try:
        # 若硬體容易受多進程存取影響，建議關閉自動重載
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        if camera_instance:
            camera_instance.close_camera()
        exit()
