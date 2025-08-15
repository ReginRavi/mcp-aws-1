"""
Enhanced MCP client with multi-service support and natural language processing.
"""
import socket
import sys
import requests
import re
import json
import argparse
from typing import Dict, Any, Optional
import logging
import time
import traceback

# Modify the logging configuration in mcp_client.py:
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('logs/mcp_client_debug.log')  # File output
    ]
)
logger = logging.getLogger(__name__)

class MCPClient:
    """Enhanced MCP Client with support for multiple AWS services"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 5000, api_port: int = 8000):
        self.host = host
        self.port = port
        self.api_port = api_port
        self.api_base_url = f"http://{host}:{api_port}"
        self.client_socket = None
        logger.info("MCP Client initialized")

    def connect_socket(self, message: str = "Hello MCP Server!"):
        """Connect using socket communication"""
        logger.info("Connecting to MCP server via socket...")
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            self.client_socket.sendall(message.encode())
            data = self.client_socket.recv(1024)
            logger.info(f"Received from server: {data.decode()}")
            return data.decode()
        except Exception as e:
            logger.error(f"Socket client error: {e}")
            return None
        finally:
            if self.client_socket:
                self.client_socket.close()

    def create_ec2_instance(self, instance_type: str = "t2.micro", 
                          image_id: str = "ami-03f4878755434977f",
                          region: str = "ap-south-1", 
                          instance_name: str = "example",
                          allowed_ssh_cidrs: str = "10.0.0.0/8") -> Dict[str, Any]:
        """Create EC2 instance via API"""
        payload = {
            "instance_type": instance_type,
            "image_id": image_id,
            "region": region,
            "instance_name": instance_name,
            "allowed_ssh_cidrs": allowed_ssh_cidrs
        }
        
        try:
            response = requests.post(f"{self.api_base_url}/create_ec2", json=payload, timeout=300)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating EC2 instance: {e}")
            return {"error": str(e)}

    def create_s3_bucket(self, bucket_name: str, region: str = "ap-south-1", 
                        versioning: bool = False) -> Dict[str, Any]:
        """Create S3 bucket via API"""
        payload = {
            "bucket_name": bucket_name,
            "region": region,
            "versioning": versioning
        }
        
        try:
            response = requests.post(f"{self.api_base_url}/create_s3", json=payload, timeout=300)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating S3 bucket: {e}")
            return {"error": str(e)}

    def create_rds_instance(self, db_instance_class: str = "db.t3.micro",
                          engine: str = "mysql", db_name: str = "testdb",
                          region: str = "ap-south-1") -> Dict[str, Any]:
        """Create RDS instance via API"""
        payload = {
            "db_instance_class": db_instance_class,
            "engine": engine,
            "db_name": db_name,
            "region": region
        }
        
        try:
            response = requests.post(f"{self.api_base_url}/create_rds", json=payload, timeout=600)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating RDS instance: {e}")
            return {"error": str(e)}

    def generate_code(self, user_input: str, service_type: str = "terraform", 
                     region: str = "ap-south-1") -> Dict[str, Any]:
        """Generate infrastructure code based on natural language"""
        payload = {
            "user_input": user_input,
            "service_type": service_type,
            "region": region
        }
        
        try:
            response = requests.post(f"{self.api_base_url}/generate_code", json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error generating code: {e}")
            return {"error": str(e)}

    def deploy_custom_infrastructure(self, user_input: str, region: str = "ap-south-1") -> Dict[str, Any]:
        """Deploy custom infrastructure based on natural language"""
        payload = {
            "user_input": user_input,
            "service_type": "terraform",
            "region": region
        }
        
        try:
            response = requests.post(f"{self.api_base_url}/deploy_custom", json=payload, timeout=600)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error deploying custom infrastructure: {e}")
            return {"error": str(e)}

    def delete_resource(self, resource_type: str, resource_identifier: str, 
                       region: str = "ap-south-1") -> Dict[str, Any]:
        """Delete AWS resource"""
        payload = {
            "resource_type": resource_type,
            "resource_identifier": resource_identifier,
            "region": region
        }
        
        try:
            response = requests.delete(f"{self.api_base_url}/delete_resource", json=payload, timeout=600)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error deleting resource: {e}")
            return {"error": str(e)}

    def get_terraform_state(self, resource_type: str) -> Dict[str, Any]:
        """Get Terraform state for a resource type"""
        try:
            response = requests.get(f"{self.api_base_url}/terraform_state/{resource_type}", timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting Terraform state: {e}")
            return {"error": str(e)}

    def health_check(self) -> Dict[str, Any]:
        """Check API health status"""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Health check failed: {e}")
            return {"error": str(e)}

class NaturalLanguageParser:
    """Parse natural language commands into API calls"""
    
    @staticmethod
    def parse_command(command: str) -> Dict[str, Any]:
        """Parse natural language command and return structured data"""
        command = command.lower().strip()
        
        # EC2 patterns
        if re.search(r'\b(create|launch|start).*ec2.*instance\b', command):
            instance_match = re.search(r'\b(t[0-9]\.[a-z]+)\b', command)
            region_match = re.search(r'\b(us-[a-z]+-[0-9]|eu-[a-z]+-[0-9]|ap-[a-z]+-[0-9])\b', command)
            name_match = re.search(r'\bname[d]?\s+["\']?([a-zA-Z0-9\-_]+)["\']?\b', command)
            
            return {
                'action': 'create_ec2',
                'instance_type': instance_match.group(1) if instance_match else 't2.micro',
                'region': region_match.group(1) if region_match else 'ap-south-1',
                'instance_name': name_match.group(1) if name_match else 'example'
            }
        
        # S3 patterns
        elif re.search(r'\b(create|make).*s3.*bucket\b', command):
            bucket_match = re.search(r'\bbucket\s+["\']?([a-zA-Z0-9\-._]+)["\']?\b', command)
            region_match = re.search(r'\b(us-[a-z]+-[0-9]|eu-[a-z]+-[0-9]|ap-[a-z]+-[0-9])\b', command)
            versioning_match = re.search(r'\bversioning\b', command)
            
            return {
                'action': 'create_s3',
                'bucket_name': bucket_match.group(1) if bucket_match else 'test-bucket-' + str(hash(command))[-6:],
                'region': region_match.group(1) if region_match else 'ap-south-1',
                'versioning': bool(versioning_match)
            }
        
        # RDS patterns
        elif re.search(r'\b(create|setup).*rds.*database\b', command):
            engine_match = re.search(r'\b(mysql|postgres|postgresql|mariadb|oracle|sqlserver)\b', command)
            instance_match = re.search(r'\b(db\.[a-z0-9\.]+)\b', command)
            name_match = re.search(r'\bname[d]?\s+["\']?([a-zA-Z0-9\-_]+)["\']?\b', command)
            region_match = re.search(r'\b(us-[a-z]+-[0-9]|eu-[a-z]+-[0-9]|ap-[a-z]+-[0-9])\b', command)
            
            engine = engine_match.group(1) if engine_match else 'mysql'
            if engine in ['postgres', 'postgresql']:
                engine = 'postgres'
                
            return {
                'action': 'create_rds',
                'engine': engine,
                'db_instance_class': instance_match.group(1) if instance_match else 'db.t3.micro',
                'db_name': name_match.group(1) if name_match else 'testdb',
                'region': region_match.group(1) if region_match else 'ap-south-1'
            }
        
        # Delete patterns
        elif re.search(r'\b(delete|destroy|remove)\b', command):
            if 'ec2' in command:
                id_match = re.search(r'\b(i-[a-zA-Z0-9]+)\b', command)
                return {
                    'action': 'delete_resource',
                    'resource_type': 'ec2',
                    'resource_identifier': id_match.group(1) if id_match else 'unknown'
                }
            elif 's3' in command:
                bucket_match = re.search(r'\bbucket\s+["\']?([a-zA-Z0-9\-._]+)["\']?\b', command)
                return {
                    'action': 'delete_resource',
                    'resource_type': 's3',
                    'resource_identifier': bucket_match.group(1) if bucket_match else 'unknown'
                }
            elif 'rds' in command:
                db_match = re.search(r'\bdatabase\s+["\']?([a-zA-Z0-9\-_]+)["\']?\b', command)
                return {
                    'action': 'delete_resource',
                    'resource_type': 'rds',
                    'resource_identifier': db_match.group(1) if db_match else 'unknown'
                }
        
        # Code generation patterns
        elif re.search(r'\b(generate|create|show).*code\b', command):
            service_match = re.search(r'\b(terraform|boto3|python)\b', command)
            return {
                'action': 'generate_code',
                'service_type': service_match.group(1) if service_match else 'terraform',
                'user_input': command
            }
        
        # Custom deployment patterns
        elif re.search(r'\b(deploy|build|setup)\b', command):
            return {
                'action': 'deploy_custom',
                'user_input': command
            }
        
        # State check patterns
        elif re.search(r'\b(state|status|info)\b', command):
            if 'ec2' in command:
                resource_type = 'ec2'
            elif 's3' in command:
                resource_type = 's3'
            elif 'rds' in command:
                resource_type = 'rds'
            else:
                resource_type = 'ec2'  # default
                
            return {
                'action': 'get_state',
                'resource_type': resource_type
            }
        
        # Default fallback
        return {
            'action': 'generate_code',
            'service_type': 'terraform',
            'user_input': command
        }

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='MCP Client - Multi-Cloud Infrastructure Management')
    parser.add_argument('command', nargs='*', help='Natural language command or specific action')
    parser.add_argument('--host', default='127.0.0.1', help='Server host')
    parser.add_argument('--port', type=int, default=5000, help='Socket port')
    parser.add_argument('--api-port', type=int, default=8000, help='API port')
    parser.add_argument('--region', default='ap-south-1', help='AWS region')
    parser.add_argument('--format', choices=['json', 'pretty'], default='pretty', help='Output format')
    
    args = parser.parse_args()
    
    if not args.command:
        print("Usage examples:")
        print("  python mcp_client.py create ec2 instance t2.micro in us-east-1")
        print("  python mcp_client.py create s3 bucket my-test-bucket")
        print("  python mcp_client.py create rds database mysql named mydb")
        print("  python mcp_client.py delete ec2 instance i-1234567890abcdef0")
        print("  python mcp_client.py generate terraform code for web server")
        print("  python mcp_client.py get ec2 state")
        return
    
    client = MCPClient(host=args.host, port=args.port, api_port=args.api_port)
    command_str = " ".join(args.command)
    
    # Health check first
    health = client.health_check()
    if 'error' in health:
        logger.error("API server is not available")
        return
    
    # Parse and execute command
    parsed_command = NaturalLanguageParser.parse_command(command_str)
    result = None
    
    try:
        if parsed_command['action'] == 'create_ec2':
            result = client.create_ec2_instance(
                instance_type=parsed_command.get('instance_type', 't2.micro'),
                region=parsed_command.get('region', args.region),
                instance_name=parsed_command.get('instance_name', 'example')
            )
        elif parsed_command['action'] == 'create_s3':
            result = client.create_s3_bucket(
                bucket_name=parsed_command['bucket_name'],
                region=parsed_command.get('region', args.region),
                versioning=parsed_command.get('versioning', False)
            )
        elif parsed_command['action'] == 'create_rds':
            result = client.create_rds_instance(
                db_instance_class=parsed_command.get('db_instance_class', 'db.t3.micro'),
                engine=parsed_command.get('engine', 'mysql'),
                db_name=parsed_command['db_name'],
                region=parsed_command.get('region', args.region)
            )
        elif parsed_command['action'] == 'delete_resource':
            result = client.delete_resource(
                resource_type=parsed_command['resource_type'],
                resource_identifier=parsed_command['resource_identifier'],
                region=args.region
            )
        elif parsed_command['action'] == 'generate_code':
            result = client.generate_code(
                user_input=parsed_command['user_input'],
                service_type=parsed_command.get('service_type', 'terraform'),
                region=args.region
            )
        elif parsed_command['action'] == 'deploy_custom':
            result = client.deploy_custom_infrastructure(
                user_input=parsed_command['user_input'],
                region=args.region
            )
        elif parsed_command['action'] == 'get_state':
            result = client.get_terraform_state(parsed_command['resource_type'])
        
        # Format output
        if result:
            if args.format == 'json':
                print(json.dumps(result, indent=2))
            else:
                if 'error' in result:
                    print(f"❌ Error: {result['error']}")
                elif 'generated_code' in result:
                    print("📝 Generated Code:")
                    print("-" * 50)
                    print(result['generated_code'])
                elif 'terraform_file' in result:
                    print(f"🏗️  Infrastructure operation completed")
                    print(f"📁 Terraform file: {result['terraform_file']}")
                    if result.get('apply_success'):
                        print("✅ Terraform apply successful")
                    elif result.get('terraform_apply_stderr'):
                        print(f"❌ Terraform apply failed: {result['terraform_apply_stderr']}")
                else:
                    print("✅ Operation completed successfully")
                    for key, value in result.items():
                        if key not in ['timestamp']:
                            print(f"{key}: {value}")
    
    except Exception as e:
        logger.error(f"Command execution failed: {e}")

if __name__ == "__main__":
    main()