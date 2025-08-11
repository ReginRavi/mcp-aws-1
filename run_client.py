from mcp_client import MCPClient
import sys
import requests

if __name__ == "__main__":
    # Default values
    instance_type = "t2.micro"
    image_id = "ami-03f4878755434977f"
    region = "ap-south-1"
    # If a natural language command is provided, parse it simply
    if len(sys.argv) > 1:
        cmd = " ".join(sys.argv[1:]).lower()
        if "t2.micro" in cmd:
            instance_type = "t2.micro"
        # You can add more parsing logic here
    payload = {
        "InstanceType": instance_type,
        "ImageId": image_id,
        "region": region
    }
    response = requests.post("http://127.0.0.1:8000/create_ec2", json=payload)
    print("Response from server:", response.json())
