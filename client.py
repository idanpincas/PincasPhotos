import socket
import os
import sys

# ------------------- CONFIG -------------------
SERVER_IP = "127.0.0.1"
PORT = 12345
BUFFER_SIZE = 4096  # גודל החתיכות לשליחה

# ------------------- HELPER FUNCTIONS -------------------
def send_file(sock: socket.socket, file_path: str):
    """שולח קובץ לשרת"""
    try:
        filename = os.path.basename(file_path)
        filesize = os.path.getsize(file_path)

        # שליחת שם הקובץ
        sock.send(f"{filename}\n".encode())
        sock.recv(1024)  # המתנה לאישור

        # שליחת גודל הקובץssss
        sock.send(f"{filesize}\n".encode())
        sock.recv(1024)  # המתנה לאישור

        # שליחת תוכן הקובץ
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(BUFFER_SIZE)
                if not chunk:
                    break
                sock.sendall(chunk)

        print(f"[SENT] {filename}")

    except FileNotFoundError:
        print(f"[ERROR] File not found: {file_path}")
    except PermissionError:
        print(f"[ERROR] Permission denied: {file_path}")
    except Exception as e:
        print(f"[ERROR] Failed to send {file_path}: {e}")

# ------------------- MAIN CLIENT -------------------
def run_client():
    path = input("Enter file or folder path: ").strip()

    if not os.path.exists(path):
        print("[ERROR] Path does not exist.")
        return

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((SERVER_IP, PORT))
            print(f"Connected to {SERVER_IP}:{PORT}")

            # שליחת קובץ בודד
            if os.path.isfile(path):
                send_file(client_socket, path)

            # שליחת תיקייה
            elif os.path.isdir(path):
                for item in os.listdir(path):
                    full_path = os.path.join(path, item)
                    if os.path.isfile(full_path):
                        send_file(client_socket, full_path)

            print("All files sent. Connection closing.")

    except ConnectionRefusedError:
        print(f"[ERROR] Cannot connect to server {SERVER_IP}:{PORT}")
    except Exception as e:
        print(f"[ERROR] Client failed: {e}")

# ------------------- ENTRY POINT -------------------
if __name__ == "__main__":
    run_client()
