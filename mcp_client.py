# Modifications for mcp_client.py to add detailed logging

# Add this at the top of mcp_client.py after the existing imports:
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

# Enhanced MCPClient class with detailed logging:
class MCPClient:
    def __init__(self, host: str = '127.0.0.1', port: int = 5000, api_port: int = 8000):
        self.host = host
        self.port = port
        self.api_port = api_port
        self.api_base_url = f"http://{host}:{api_port}"
        self.client_socket = None
        logger.info(f"🔧 MCP Client initialized - API: {self.api_base_url}")

    def create_ec2_instance(self, instance_type: str = "t2.micro", 
                          image_id: str = "ami-03f4878755434977f",
                          region: str = "ap-south-1", 
                          instance_name: str = "example",
                          allowed_ssh_cidrs: str = "10.0.0.0/8") -> Dict[str, Any]:
        """Create EC2 instance via API with detailed logging"""
        logger.info(f"🚀 Starting EC2 instance creation")
        logger.debug(f"Parameters: type={instance_type}, ami={image_id}, region={region}, name={instance_name}")
        
        payload = {
            "instance_type": instance_type,
            "image_id": image_id,
            "region": region,
            "instance_name": instance_name,
            "allowed_ssh_cidrs": allowed_ssh_cidrs
        }
        
        logger.debug(f"📤 Request payload: {json.dumps(payload, indent=2)}")
        
        try:
            start_time = time.time()
            logger.info(f"📡 Sending POST request to {self.api_base_url}/create_ec2")
            
            response = requests.post(
                f"{self.api_base_url}/create_ec2", 
                json=payload, 
                timeout=300
            )
            
            elapsed_time = time.time() - start_time
            logger.info(f"⏱️  Request completed in {elapsed_time:.2f} seconds")
            logger.debug(f"📊 Response status: {response.status_code}")
            logger.debug(f"📊 Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            result = response.json()
            
            logger.debug(f"📥 Response body: {json.dumps(result, indent=2)}")
            logger.info(f"✅ EC2 creation request completed successfully")
            
            return result
            
        except requests.exceptions.Timeout:
            logger.error("⏰ Request timed out after 300 seconds")
            return {"error": "Request timed out"}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"🔌 Connection error: {str(e)}")
            return {"error": f"Connection failed: {str(e)}"}
        except requests.exceptions.HTTPError as e:
            logger.error(f"🚫 HTTP error: {response.status_code} - {str(e)}")
            try:
                error_detail = response.json()
                logger.error(f"📋 Error details: {json.dumps(error_detail, indent=2)}")
            except:
                logger.error(f"📋 Raw error response: {response.text}")
            return {"error": f"HTTP {response.status_code}: {str(e)}"}
        except Exception as e:
            logger.error(f"💥 Unexpected error: {str(e)}")
            logger.debug(f"🔍 Stack trace: {traceback.format_exc()}")
            return {"error": str(e)}

# Enhanced NaturalLanguageParser with detailed logging:
class NaturalLanguageParser:
    @staticmethod
    def parse_command(command: str) -> Dict[str, Any]:
        """Parse natural language command with detailed logging"""
        logger.info(f"🔍 Parsing command: '{command}'")
        command_lower = command.lower().strip()
        logger.debug(f"🔧 Normalized command: '{command_lower}'")
        
        # EC2 patterns
        if re.search(r'\b(create|launch|start).*ec2.*instance\b', command_lower):
            logger.debug("🎯 Matched EC2 creation pattern")
            
            instance_match = re.search(r'\b(t[0-9]\.[a-z]+)\b', command_lower)
            region_match = re.search(r'\b(us-[a-z]+-[0-9]|eu-[a-z]+-[0-9]|ap-[a-z]+-[0-9])\b', command_lower)
            name_match = re.search(r'\bname[d]?\s+["\']?([a-zA-Z0-9\-_]+)["\']?\b', command_lower)
            
            result = {
                'action': 'create_ec2',
                'instance_type': instance_match.group(1) if instance_match else 't2.micro',
                'region': region_match.group(1) if region_match else 'ap-south-1',
                'instance_name': name_match.group(1) if name_match else 'example'
            }
            
            logger.debug(f"✅ Parsed EC2 parameters: {result}")
            return result
        
        # Add similar detailed logging for other patterns...
        logger.debug("🤷 No specific pattern matched, using default")
        return {
            'action': 'generate_code',
            'service_type': 'terraform',
            'user_input': command
        }

# Enhanced main function with detailed logging:
def main():
    """Main CLI interface with detailed logging"""
    logger.info("🚀 MCP Client starting...")
    
    # ... existing argument parsing code ...
    
    client = MCPClient(host=args.host, port=args.port, api_port=args.api_port)
    command_str = " ".join(args.command)
    
    logger.info(f"🎯 Processing command: '{command_str}'")
    
    # Health check first
    logger.info("🏥 Performing health check...")
    health_start = time.time()
    health = client.health_check()
    health_time = time.time() - health_start
    
    if 'error' in health:
        logger.error(f"💔 Health check failed in {health_time:.2f}s: {health['error']}")
        logger.error("🔧 Make sure the server is running: python bootstrap.py server")
        return
    else:
        logger.info(f"💚 Health check passed in {health_time:.2f}s")
        logger.debug(f"📊 Health status: {health}")
    
    # Parse and execute command
    logger.info("🧠 Parsing natural language command...")
    parsed_command = NaturalLanguageParser.parse_command(command_str)
    logger.info(f"✅ Command parsed - Action: {parsed_command.get('action', 'unknown')}")
    
    # ... rest of the execution logic with similar detailed logging ...

if __name__ == "__main__":
    try:
        # Create logs directory
        os.makedirs("logs", exist_ok=True)
        logger.info("📁 Logs directory ready")
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Client interrupted by user")
    except Exception as e:
        logger.error(f"💥 Client crashed: {str(e)}")
        logger.debug(f"🔍 Stack trace: {traceback.format_exc()}")