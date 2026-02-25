import socket, pyautogui, cv2, pickle, struct, numpy as np, time, platform, threading
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected = False
while not connected:
    try:
        client.connect(("127.0.0.1", 9999))
        connected = True
    except:
        time.sleep(2)

info = f"{platform.system()} ({platform.node()})"
client.send(info.encode().ljust(64))

def listen_commands():
    while True:
        try:
            data = client.recv(1024).decode()
            if data.startswith("CLICK:"):
                _, x, y = data.split(":")
                pyautogui.click(int(x), int(y))
            elif data.startswith("KEY:"):
                key = data.split(":")[1]
                if len(key) > 1: pyautogui.press(key.lower())
                else: pyautogui.write(key)
        except: break

threading.Thread(target=listen_commands, daemon=True).start()

try:
    while True:
        img = pyautogui.screenshot()
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        res, enc = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
        data = pickle.dumps(enc)
        client.sendall(struct.pack("Q", len(data)) + data)
except: pass
finally: client.close()
