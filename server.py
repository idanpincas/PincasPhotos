import socket
import os
import threading

# ------------------- CONFIG -------------------
HOST = "0.0.0.0"
PORT = 12345
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp")
BUFFER_SIZE = 4096

# ------------------- GLOBALS -------------------
client_counter = 0
client_counter_lock = threading.Lock()  # כדי להבטיח שהמספרים של לקוחות ייחודיים

# ------------------- HELPER FUNCTIONS -------------------
def is_image_file(filename: str) -> bool:
    """בדיקה אם קובץ הוא תמונה לפי סיומת"""
    return filename.lower().endswith(IMAGE_EXTENSIONS)

def receive_file(sock: socket.socket, filename: str, filesize: int, save_dir: str):
    """
    מקבלת קובץ מהלקוח ושומרת אותו בתיקייה שהוקצתה לו.
    """
    save_path = os.path.join(save_dir, os.path.basename(filename))
    remaining = filesize

    try:
        if is_image_file(filename):
            with open(save_path, "wb") as f:
                while remaining > 0:
                    chunk = sock.recv(min(BUFFER_SIZE, remaining))
                    if not chunk:
                        break
                    f.write(chunk)
                    remaining -= len(chunk)
            print(f"[SAVED] {filename} in {save_dir}")
        else:
            # קובץ לא תמונה – קריאה בלבד כדי לא לאבד נתונים
            while remaining > 0:
                chunk = sock.recv(min(BUFFER_SIZE, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
            print(f"[IGNORED] {filename}")
    except Exception as e:
        print(f"[ERROR] Failed to receive {filename}: {e}")

# ------------------- CLIENT HANDLER -------------------
def handle_client(client_socket: socket.socket, client_id: int):
    """טיפול בכל לקוח בנפרד"""
    save_dir = f"client_{client_id}_photos"
    os.makedirs(save_dir, exist_ok=True)
    print(f"[INFO] Client {client_id} directory created: {save_dir}")

    try:
        conn_file = client_socket.makefile("rb")

        while True:
            # קריאת שם קובץ
            filename_line = conn_file.readline()
            if not filename_line:
                break
            filename = filename_line.decode().strip()
            client_socket.send(b"OK")

            # קריאת גודל הקובץ
            filesize_line = conn_file.readline()
            if not filesize_line:
                break
            try:
                filesize = int(filesize_line.decode().strip())
            except ValueError:
                print(f"[ERROR] Invalid filesize from client {client_id}: {filename}")
                break
            client_socket.send(b"OK")

            # קבלת הקובץ ושמירה
            receive_file(client_socket, filename, filesize, save_dir)

    except Exception as e:
        print(f"[ERROR] Client {client_id} connection issue: {e}")
    finally:
        client_socket.close()
        print(f"[INFO] Client {client_id} disconnected")

# ------------------- MAIN SERVER -------------------
def run_server():
    global client_counter

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((HOST, PORT))
            server_socket.listen()
            print(f"Server running on {HOST}:{PORT}")

            while True:
                try:
                    client_socket, addr = server_socket.accept()
                except Exception as e:
                    print(f"[ERROR] Accept failed: {e}")
                    continue

                # קביעת מספר ייחודי ללקוח
                with client_counter_lock:
                    client_counter += 1
                    client_id = client_counter

                print(f"[INFO] Client {client_id} connected from {addr}")

                # פתיחת thread לטיפול בלקוח
                client_thread = threading.Thread(target=handle_client, args=(client_socket, client_id))
                client_thread.daemon = True
                client_thread.start()

    except Exception as e:
        print(f"[ERROR] Server failed: {e}")

# ------------------- ENTRY POINT -------------------
if __name__ == "__main__":
    run_server()
