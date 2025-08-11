"""
Basic MCP server implementation placeholder.
"""
import threading
import os

class MCPServer:
    def __init__(self, host='127.0.0.1', port=5000):
        import socket
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"MCP Server listening on {self.host}:{self.port}")

    def handle_client(self, conn, addr):
        import json
        print(f"Connection from {addr}")
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                try:
                    message = json.loads(data.decode())
                except Exception:
                    # Assume natural language if not JSON
                    message = self.parse_natural_language(data.decode())
                print(f"Received from {addr}: {message}")
                if message.get("command") == "create_ec2":
                    params = message.get("params", {})
                    # Generate Terraform file for EC2
                    tf_path = self.generate_ec2_terraform(params)
                    result = {"terraform_file": tf_path}
                    response = json.dumps({"status": "success", "result": result})
                else:
                    response = json.dumps({"status": "error", "message": "Unknown command"})
                conn.sendall(response.encode())
        except Exception as e:
            print(f"Error with client {addr}: {e}")
        finally:
            conn.close()

    def generate_ec2_terraform(self, params):
        from terraform_generator import generate_ec2_tf
        import subprocess
        instance_type = params.get("InstanceType", "t2.micro")
        ami = params.get("ImageId", "ami-03f4878755434977f")
        region = params.get("region", "ap-south-1")
        tf_path = generate_ec2_tf(instance_type, ami, region)
        tf_dir = os.path.dirname(tf_path)
        # Run terraform init and apply
        try:
            init_result = subprocess.run(["terraform", "init"], cwd=tf_dir, capture_output=True, text=True)
            apply_result = subprocess.run(["terraform", "apply", "-auto-approve"], cwd=tf_dir, capture_output=True, text=True)
            return {
                "terraform_file": tf_path,
                "terraform_init": init_result.stdout,
                "terraform_apply": apply_result.stdout
            }
        except Exception as e:
            return {
                "terraform_file": tf_path,
                "error": str(e)
            }

    def parse_natural_language(self, text):
        # Gemini LLM integration using API key from .env
        import os
        import requests
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Gemini API key not found in environment.")
            return {"command": "unknown", "data": text}
        # Example Gemini API call (replace URL and payload as needed)
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=" + api_key
        payload = {
            "contents": [{"parts": [{"text": text}]}]
        }
        try:
            response = requests.post(url, json=payload)
            result = response.json()
            # Parse Gemini response to extract command and params
            # This is a placeholder; adapt to actual Gemini output
            if "ec2" in text.lower() and "t2.micro" in text.lower():
                return {
                    "command": "create_ec2",
                    "params": {
                        "region": "ap-south-1",
                        "ImageId": "ami-03f4878755434977f",  # Amazon Linux 2 AMI for ap-south-1
                        "InstanceType": "t2.micro"
                    }
                }
            # Example: parse result['candidates'][0]['content']['parts'][0]['text']
            # and extract command/params
            return {"command": "unknown", "gemini_result": result}
        except Exception as e:
            print(f"Gemini API error: {e}")
            return {"command": "unknown", "error": str(e), "data": text}

    def create_ec2_instance(self, params):
        try:
            import boto3
            ec2 = boto3.resource('ec2', region_name=params.get('region', 'us-east-1'))
            instances = ec2.create_instances(
                ImageId=params.get('ImageId', 'ami-0c94855ba95c71c99'),
                MinCount=1,
                MaxCount=1,
                InstanceType=params.get('InstanceType', 't2.micro'),
            )
            instance_id = instances[0].id
            print(f"EC2 instance created: {instance_id}")
            return {"instance_id": instance_id}
        except Exception as e:
            print(f"EC2 creation error: {e}")
            return {"error": str(e)}

    def run(self):
        print("MCP Server running...")
        try:
            while True:
                conn, addr = self.server_socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                client_thread.start()
        except KeyboardInterrupt:
            print("Server shutting down.")
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.server_socket.close()
