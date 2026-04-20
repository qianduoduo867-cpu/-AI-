import socket
import threading
import json
import uuid
import time

class RemoteServer:
    def __init__(self, host="0.0.0.0", port=5555):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []
        self.command_handlers = {}
        self.running = True

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[*] Server listening on {self.host}:{self.port}")
        
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                print(f"[+] Client connected: {addr}")
                self.clients.append(client_socket)
                thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                thread.daemon = True
                thread.start()
            except:
                break

    def handle_client(self, client_socket):
        while self.running:
            try:
                data = client_socket.recv(8192)
                if not data:
                    break
                message = json.loads(data.decode())
                self.handle_response(client_socket, message)
            except:
                break
        
        if client_socket in self.clients:
            self.clients.remove(client_socket)
        client_socket.close()

    def handle_response(self, client_socket, message):
        cmd_id = message.get("id", "")
        if cmd_id in self.command_handlers:
            handler = self.command_handlers[cmd_id]
            handler(message)
            del self.command_handlers[cmd_id]

    def send_command(self, command, client_socket=None, callback=None):
        cmd_id = str(uuid.uuid4())[:8]
        
        if client_socket is None:
            if not self.clients:
                print("[!] No clients connected")
                return None
            client_socket = self.clients[0]
        
        message = {
            "id": cmd_id,
            "command": command
        }
        
        if callback:
            self.command_handlers[cmd_id] = callback
        
        try:
            client_socket.send(json.dumps(message).encode())
        except Exception as e:
            print(f"[!] Send failed: {e}")
            return None
        
        return cmd_id

    def send_command_blocking(self, command, client_socket=None, timeout=60):
        result = {}
        event = threading.Event()
        
        def callback(response):
            result.update(response)
            event.set()
        
        cmd_id = self.send_command(command, client_socket, callback)
        if not cmd_id:
            return {"status": "error", "output": "No client connected"}
        
        event.wait(timeout)
        return result if result else {"status": "timeout", "output": "Command timed out"}

    def list_clients(self):
        return self.clients

    def stop(self):
        self.running = False
        for client in self.clients:
            client.close()
        if self.server_socket:
            self.server_socket.close()

def interactive_shell(server):
    print("\n=== Remote AI Control Shell ===")
    print("Commands:")
    print("  clients      - List connected clients")
    print("  exec <cmd>  - Execute command on client")
    print("  ai <msg>    - Send to AI forNatural language processing")
    print("  quit        - Exit")
    print("================================\n")
    
    while True:
        try:
            cmd = input("> ").strip()
            if not cmd:
                continue
            
            if cmd == "quit":
                break
            elif cmd == "clients":
                print(f"Connected clients: {len(server.list_clients())}")
            elif cmd.startswith("exec "):
                command = cmd[5:]
                result = server.send_command_blocking(command)
                print(f"\nStatus: {result.get('status')}")
                print(f"Output:\n{result.get('output', '')}\n")
            elif cmd == "help":
                print("Available commands: clients, exec <command>, quit")
            else:
                print("Unknown command. Type 'help' for available commands.")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    
    port = 5555
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    server = RemoteServer(port=port)
    
    import threading
    thread = threading.Thread(target=server.start)
    thread.daemon = True
    thread.start()
    
    interactive_shell(server)
    server.stop()