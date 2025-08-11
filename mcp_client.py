"""
Basic MCP client implementation placeholder.
"""
class MCPClient:
    def __init__(self, host='127.0.0.1', port=5000):
        import socket
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("MCP Client initialized.")

    def connect(self, message="Hello MCP Server!"):
        print("MCP Client connecting to server...")
        try:
            self.client_socket.connect((self.host, self.port))
            self.client_socket.sendall(message.encode())
            data = self.client_socket.recv(1024)
            print(f"Received from server: {data.decode()}")
        except Exception as e:
            print(f"Client error: {e}")
        finally:
            self.client_socket.close()

import sys
import requests
import re

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = " ".join(sys.argv[1:]).lower()
        # Natural language: "delete ec2 instance with id i-1234567890abcdef0"
        match = re.search(r"delete.*ec2.*id\s*(i-[a-zA-Z0-9]+)", cmd)
        if match:
            instance_id = match.group(1)
            payload = {"instance_id": instance_id, "region": "ap-south-1"}
            response = requests.post("http://127.0.0.1:8000/delete_ec2", json=payload)
            print("Response from server:", response.json())
        elif "delete" in cmd:
            # Fallback: python mcp_client.py delete i-1234567890abcdef0
            if len(sys.argv) > 2:
                instance_id = sys.argv[2]
                payload = {"instance_id": instance_id, "region": "ap-south-1"}
                response = requests.post("http://127.0.0.1:8000/delete_ec2", json=payload)
                print("Response from server:", response.json())
            else:
                print("Please provide the EC2 instance ID to delete.")
        else:
            print("Usage: python mcp_client.py delete <instance_id> or python mcp_client.py 'delete ec2 instance with id i-1234567890abcdef0'")
    else:
        print("Usage: python mcp_client.py delete <instance_id> or python mcp_client.py 'delete ec2 instance with id i-1234567890abcdef0'")
