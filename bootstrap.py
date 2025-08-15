"""
Enhanced bootstrap file to initialize and run the MCP infrastructure management system.
"""
import asyncio
import uvicorn
import subprocess
import sys
import os
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MCPBootstrap:
    """Bootstrap class for MCP infrastructure management system"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.setup_directories()
        self.check_dependencies()
    
    def setup_directories(self):
        """Create necessary directories for Terraform configurations"""
        directories = [
            "terraform",
            "terraform/terraform_ec2",
            "terraform/terraform_s3", 
            "terraform/terraform_rds",
            "terraform/terraform_custom",
            "logs"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Directory created/verified: {directory}")
    
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        dependencies = {
            'terraform': 'Terraform CLI',
            'aws': 'AWS CLI (optional)',
        }
        
        missing_deps = []
        
        for cmd, name in dependencies.items():
            try:
                result = subprocess.run([cmd, '--version'], 
                                     capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version = result.stdout.split('\n')[0]
                    logger.info(f"✅ {name}: {version}")
                else:
                    missing_deps.append(name)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                missing_deps.append(name)
                logger.warning(f"⚠️  {name} not found")
        
        if missing_deps:
            logger.warning("Missing dependencies detected. Some features may not work.")
            logger.info("To install missing dependencies:")
            if 'Terraform CLI' in missing_deps:
                logger.info("  - Terraform: https://developer.hashicorp.com/terraform/downloads")
            if 'AWS CLI (optional)' in missing_deps:
                logger.info("  - AWS CLI: pip install awscli")
        else:
            logger.info("✅ All dependencies are available")
    
    def setup_terraform_providers(self):
        """Initialize Terraform providers in base directory"""
        provider_config = """
terraform {
  required_version = ">= 0.14"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  # Configuration will be provided via environment variables or AWS CLI
  # AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
}
"""
        
        providers_file = Path("terraform/providers.tf")
        with open(providers_file, "w") as f:
            f.write(provider_config)
        
        logger.info("✅ Terraform providers configuration created")
    
    def create_sample_configs(self):
        """Create sample configuration files"""
        
        # Sample environment configuration
        env_sample = """# Sample environment configuration
# Copy this to .env and update with your values

# AWS Configuration
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here

# MCP Server Configuration  
MCP_HOST=0.0.0.0
MCP_PORT=8000

# Security Configuration
ALLOWED_SSH_CIDRS=10.0.0.0/8
"""
        
        with open(".env.sample", "w") as f:
            f.write(env_sample)
        
        # Sample batch commands file
        commands_sample = """# Sample batch commands file
# Lines starting with # are comments

create ec2 instance t2.micro named web-server-1
create s3 bucket my-app-data-bucket with versioning
create rds mysql database named app-db
generate terraform code for load balancer with auto scaling
"""
        
        with open("commands.sample", "w") as f:
            f.write(commands_sample)
        
        logger.info("✅ Sample configuration files created")
    
    def run_server(self):
        """Run the FastAPI server"""
        logger.info(f"🚀 Starting MCP Infrastructure Management Server")
        logger.info(f"📡 Server will be available at: http://{self.host}:{self.port}")
        logger.info(f"📚 API documentation at: http://{self.host}:{self.port}/docs")
        
        try:
            # Import here to avoid circular imports
            from mcp_fastapi_server import app
            
            uvicorn.run(
                app,
                host=self.host,
                port=self.port,
                log_level="info",
                reload=False,
                access_log=True
            )
        except ImportError as e:
            logger.error(f"❌ Failed to import FastAPI server: {e}")
            logger.error("Please ensure all dependencies are installed: pip install fastapi uvicorn")
            sys.exit(1)
        except Exception as e:
            logger.error(f"❌ Failed to start server: {e}")
            sys.exit(1)
    
    def run_client_interactive(self):
        """Run the client in interactive mode"""
        try:
            from run_client import interactive_mode
            interactive_mode()
        except ImportError as e:
            logger.error(f"❌ Failed to import client: {e}")
            sys.exit(1)
    
    def run_health_check(self):
        """Perform a comprehensive health check"""
        logger.info("🔍 Performing health check...")
        
        try:
            from mcp_client1 import MCPClient
            
            client = MCPClient()
            health_result = client.health_check()
            
            if 'error' in health_result:
                logger.error("❌ Health check failed - server not responding")
                return False
            else:
                logger.info("✅ Server is healthy")
                logger.info(f"  - Status: {health_result.get('status', 'unknown')}")
                logger.info(f"  - Terraform: {'✅' if health_result.get('terraform_available') else '❌'}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False

def main():
    """Main bootstrap function with command-line interface"""
    parser = argparse.ArgumentParser(
        description='MCP Infrastructure Management Bootstrap',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  server     Start the FastAPI server (default)
  client     Start interactive client
  setup      Setup directories and sample configs
  health     Run health check
  
Examples:
  python bootstrap.py                    # Start server
  python bootstrap.py server --port 9000  # Start server on port 9000
  python bootstrap.py client             # Start interactive client
  python bootstrap.py setup              # Setup environment
  python bootstrap.py health             # Check system health
        """
    )
    
    parser.add_argument('command', nargs='?', default='server', 
                       choices=['server', 'client', 'setup', 'health'],
                       help='Command to execute')
    parser.add_argument('--host', default='0.0.0.0', help='Server host')
    parser.add_argument('--port', type=int, default=8000, help='Server port')
    parser.add_argument('--dev', action='store_true', help='Development mode with auto-reload')
    
    args = parser.parse_args()
    
    # Initialize bootstrap
    bootstrap = MCPBootstrap(host=args.host, port=args.port)
    
    if args.command == 'setup':
        logger.info("🔧 Setting up MCP environment...")
        bootstrap.setup_terraform_providers()
        bootstrap.create_sample_configs()
        logger.info("✅ Setup completed!")
        logger.info("\nNext steps:")
        logger.info("1. Copy .env.sample to .env and update with your AWS credentials")
        logger.info("2. Run: python bootstrap.py server")
        logger.info("3. In another terminal: python bootstrap.py client")
        
    elif args.command == 'client':
        logger.info("🤖 Starting interactive client...")
        bootstrap.run_client_interactive()
        
    elif args.command == 'health':
        logger.info("🏥 Running health check...")
        if bootstrap.run_health_check():
            logger.info("✅ System is healthy")
        else:
            logger.error("❌ System health check failed")
            sys.exit(1)
            
    else:  # server (default)
        if args.dev:
            logger.info("🔥 Starting development server with auto-reload...")
            try:
                from mcp_fastapi_server import app
                uvicorn.run(
                    "mcp_fastapi_server:app",
                    host=args.host,
                    port=args.port,
                    reload=True,
                    log_level="debug"
                )
            except ImportError as e:
                logger.error(f"❌ Failed to start development server: {e}")
                sys.exit(1)
        else:
            bootstrap.run_server()

if __name__ == "__main__":
    main()