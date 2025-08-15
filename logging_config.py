# logging_config.py - Enhanced logging configuration for detailed debugging

import logging
import sys
from datetime import datetime
import os

def setup_detailed_logging(component_name="MCP", log_level=logging.DEBUG, log_to_file=True):
    """
    Setup detailed logging configuration for MCP components
    """
    
    # Create logs directory if it doesn't exist
    if log_to_file:
        os.makedirs("logs", exist_ok=True)
    
    # Create formatter with more details
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(detailed_formatter)
    
    # Create file handler if requested
    handlers = [console_handler]
    if log_to_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_handler = logging.FileHandler(f'logs/{component_name.lower()}_{timestamp}.log')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    
    # Set levels for specific loggers
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('fastapi').setLevel(logging.DEBUG)
    logging.getLogger('requests').setLevel(logging.DEBUG)
    logging.getLogger('urllib3').setLevel(logging.INFO)
    
    logger = logging.getLogger(component_name)
    logger.info(f"🔧 Enhanced logging initialized for {component_name}")
    logger.info(f"📊 Log level: {logging.getLevelName(log_level)}")
    logger.info(f"📁 Logging to file: {log_to_file}")
    
    return logger

# Add this to your existing files:

# For mcp_client.py - Add this at the top after imports:
def setup_client_logging():
    """Setup detailed logging for MCP Client"""
    from logging_config import setup_detailed_logging
    return setup_detailed_logging("MCP_CLIENT", logging.DEBUG)

# For mcp_fastapi_server.py - Add this at the top after imports:
def setup_server_logging():
    """Setup detailed logging for MCP Server"""  
    from logging_config import setup_detailed_logging
    return setup_detailed_logging("MCP_SERVER", logging.DEBUG)

# For terraform_generator.py - Add this for Terraform operations:
def setup_terraform_logging():
    """Setup detailed logging for Terraform operations"""
    from logging_config import setup_detailed_logging
    return setup_detailed_logging("TERRAFORM", logging.DEBUG)

# Enhanced subprocess execution with detailed logging
import subprocess
import logging

def run_command_with_detailed_logs(command, cwd=None, timeout=300, logger=None):
    """
    Run subprocess command with detailed logging
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    logger.info(f"🚀 Executing command: {' '.join(command)}")
    logger.info(f"📂 Working directory: {cwd or 'current'}")
    logger.info(f"⏱️  Timeout: {timeout} seconds")
    
    try:
        # Start process
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        logger.info(f"🔄 Process started with PID: {process.pid}")
        
        # Wait for completion
        stdout, stderr = process.communicate(timeout=timeout)
        
        logger.info(f"✅ Process completed with return code: {process.returncode}")
        
        # Log stdout if present
        if stdout:
            logger.info("📤 STDOUT:")
            for line in stdout.strip().split('\n'):
                if line.strip():
                    logger.info(f"  {line}")
        
        # Log stderr if present
        if stderr:
            if process.returncode == 0:
                logger.warning("⚠️  STDERR (non-fatal):")
            else:
                logger.error("❌ STDERR (error):")
            for line in stderr.strip().split('\n'):
                if line.strip():
                    if process.returncode == 0:
                        logger.warning(f"  {line}")
                    else:
                        logger.error(f"  {line}")
        
        return {
            'returncode': process.returncode,
            'stdout': stdout,
            'stderr': stderr,
            'success': process.returncode == 0
        }
        
    except subprocess.TimeoutExpired:
        logger.error(f"⏰ Command timed out after {timeout} seconds")
        process.kill()
        return {
            'returncode': -1,
            'stdout': '',
            'stderr': f'Command timed out after {timeout} seconds',
            'success': False
        }
    except Exception as e:
        logger.error(f"💥 Command execution failed: {str(e)}")
        return {
            'returncode': -1,
            'stdout': '',
            'stderr': str(e),
            'success': False
        }

# Progress tracking for long operations
class ProgressTracker:
    def __init__(self, operation_name, logger=None):
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger(__name__)
        self.start_time = datetime.now()
        
    def log_step(self, step, details=""):
        elapsed = datetime.now() - self.start_time
        self.logger.info(f"⚙️  [{self.operation_name}] Step: {step} | Elapsed: {elapsed} | {details}")
        
    def log_completion(self, success=True, details=""):
        elapsed = datetime.now() - self.start_time
        status = "✅ SUCCESS" if success else "❌ FAILED"
        self.logger.info(f"{status} [{self.operation_name}] Completed in {elapsed} | {details}")

# Usage examples for integration:

"""
# In mcp_fastapi_server.py, replace the run_terraform_commands function:

def run_terraform_commands(tf_dir: str) -> Dict[str, Any]:
    '''Execute Terraform init and apply commands with detailed logging'''
    logger = logging.getLogger(__name__)
    tracker = ProgressTracker("Terraform Deployment", logger)
    
    try:
        # Terraform init
        tracker.log_step("Initializing", f"Directory: {tf_dir}")
        init_result = run_command_with_detailed_logs(
            ["terraform", "init"], 
            cwd=tf_dir, 
            timeout=300, 
            logger=logger
        )
        
        # Terraform plan
        tracker.log_step("Planning", "Validating configuration")
        plan_result = run_command_with_detailed_logs(
            ["terraform", "plan"], 
            cwd=tf_dir, 
            timeout=300, 
            logger=logger
        )
        
        # Terraform apply
        tracker.log_step("Applying", "Deploying infrastructure")
        apply_result = run_command_with_detailed_logs(
            ["terraform", "apply", "-auto-approve"], 
            cwd=tf_dir, 
            timeout=600, 
            logger=logger
        )
        
        success = all([
            init_result['success'], 
            plan_result['success'], 
            apply_result['success']
        ])
        
        tracker.log_completion(success, f"All operations {'completed' if success else 'failed'}")
        
        return {
            "terraform_init_stdout": init_result['stdout'],
            "terraform_init_stderr": init_result['stderr'],
            "terraform_plan_stdout": plan_result['stdout'],
            "terraform_plan_stderr": plan_result['stderr'],
            "terraform_apply_stdout": apply_result['stdout'],
            "terraform_apply_stderr": apply_result['stderr'],
            "init_success": init_result['success'],
            "plan_success": plan_result['success'],
            "apply_success": apply_result['success']
        }
        
    except Exception as e:
        tracker.log_completion(False, str(e))
        logger.error(f"💥 Terraform execution failed: {str(e)}")
        return {"error": str(e)}
"""